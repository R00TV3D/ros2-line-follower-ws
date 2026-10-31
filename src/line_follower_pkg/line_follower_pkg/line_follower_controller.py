import rclpy
from rclpy.node import Node
from std_msgs.msg import Int8MultiArray
from geometry_msgs.msg import Twist


class LineFollowerController(Node):
    def __init__(self):
        super().__init__('line_follower_controller')

        # Control parameters
        self.declare_parameter('base_speed', 1.3)  # m/s forward speed
        self.declare_parameter('kp', 1)          # Proportional steering gain
        self.declare_parameter('kd', 0.4)          # Derivative gain (dampens wobbling)

        self.sub_sensors = self.create_subscription(
            Int8MultiArray, '/line_sensors', self.sensor_callback, 10
        )
        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 10)

        # Weights from Far-Left (-3.0) to Far-Right (+3.0)
        self.weights = [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0]
        self.last_error = 0.0

        self.get_logger().info('Line Follower Controller started. Publishing to /cmd_vel.')

    def sensor_callback(self, msg):
        sensors = list(msg.data)  # e.g. [0, 0, 1, 1, 1, 0, 0]
        if len(sensors) != 7:
            return

        base_speed = self.get_parameter('base_speed').value
        kp = self.get_parameter('kp').value
        kd = self.get_parameter('kd').value

        active_count = sum(sensors)
        cmd = Twist()

        # Case 1: All 7 sensors see black (Crossroad / Stop line)
        if active_count == 7:
            cmd.linear.x = base_speed
            cmd.angular.z = 0.0
            self.get_logger().info('All sensors active (Intersection). Moving straight slowly.')

        # Case 2: No sensors see black (Line lost) -> Spin toward last seen side
        elif active_count == 0:
            cmd.linear.x = -0.4
            if self.last_error < 0:
                cmd.angular.z = 0.5  # Last seen on left -> turn left
            else:
                cmd.angular.z = -0.5  # Last seen on right -> turn right
            self.get_logger().warning(f'Line lost! Searching (last_error={self.last_error:.2f})')

        # Case 3: Normal line tracking (1 to 6 sensors active)
        else:
            weighted_sum = sum(w * s for w, s in zip(self.weights, sensors))
            error = weighted_sum / float(active_count)  # Ranges from -3.0 to +3.0

            derivative = error - self.last_error
            self.last_error = error

            # Negative sign because error < 0 (left) requires positive angular.z (CCW left turn)
            angular_z = -(kp * error + kd * derivative)

            # Automatically slow down on sharp turns (when |error| is large)
            turn_penalty = min(abs(error) / 3.5, 0.65)
            cmd.linear.x = base_speed * (1.0 - turn_penalty)
            cmd.angular.z = angular_z

        self.pub_cmd.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = LineFollowerController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Stop the robot safely on exit
        stop_msg = Twist()
        node.pub_cmd.publish(stop_msg)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()