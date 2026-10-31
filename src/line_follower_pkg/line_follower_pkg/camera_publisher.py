import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2


class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')
        self.declare_parameter('camera_id', 0)
        self.declare_parameter('fps', 30.0)

        cam_id = self.get_parameter('camera_id').value
        fps = self.get_parameter('fps').value

        self.publisher_ = self.create_publisher(Image, '/camera/image_raw', 10)
        self.bridge = CvBridge()

        self.cap = cv2.VideoCapture(cam_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not self.cap.isOpened():
            self.get_logger().error(f'Failed to open camera with ID {cam_id}')

        self.timer = self.create_timer(1.0 / fps, self.timer_callback)
        self.get_logger().info(f'Camera Publisher started on /camera/image_raw at {fps} FPS')

    def timer_callback(self):
        ret, frame = self.cap.read()
        if ret:
            msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            self.publisher_.publish(msg)
        else:
            self.get_logger().warn('Failed to grab frame from camera')

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()