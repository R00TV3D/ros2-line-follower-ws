import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Int8MultiArray
from cv_bridge import CvBridge
import cv2
import numpy as np


class VirtualSensorNode(Node):
    def __init__(self):
        super().__init__('virtual_sensor_node')

        # Tunable parameters for lighting and line thickness
        self.declare_parameter('brightness_threshold', 80)  # 0-255: below this is considered BLACK
        self.declare_parameter('fill_ratio_trigger', 0.25)  # 25% dark pixels in a zone triggers a '1'

        self.sub_image = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10
        )
        self.pub_sensors = self.create_publisher(Int8MultiArray, '/line_sensors', 10)
        self.pub_debug = self.create_publisher(Image, '/line_sensors/debug_image', 10)

        self.bridge = CvBridge()
        self.num_zones = 7
        self.get_logger().info('7-Zone Virtual Sensor Node Started.')

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        height, width, _ = frame.shape

        # 1. Crop Region of Interest (Bottom 60% of the frame)
        roi_y_start = int(height * 0.40)
        roi = frame[roi_y_start:height, 0:width]

        # 2. Convert to Grayscale & Apply Gaussian Blur to kill camera noise
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 3. Threshold: Low brightness (< threshold) -> Black (0), High brightness -> White (255)
        thresh_val = self.get_parameter('brightness_threshold').value
        _, binary = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)

        # 4. Divide horizontally into 7 equal zones
        zone_width = width // self.num_zones
        sensor_array = []
        fill_trigger = self.get_parameter('fill_ratio_trigger').value

        debug_frame = roi.copy()

        for i in range(self.num_zones):
            x_start = i * zone_width
            # Ensure the 7th zone covers any remainder pixels at the right edge
            x_end = (i + 1) * zone_width if i < self.num_zones - 1 else width

            zone = binary[:, x_start:x_end]
            total_pixels = zone.size
            # Count black pixels (where pixel value == 0)
            black_pixels = total_pixels - cv2.countNonZero(zone)
            black_ratio = black_pixels / float(total_pixels)

            # 1 = Black line detected in this zone, 0 = White background
            is_black = 1 if black_ratio >= fill_trigger else 0
            sensor_array.append(is_black)

            # Draw visual overlay for debugging
            box_color = (0, 255, 0) if is_black else (0, 0, 255)  # Green = Line, Red = Background
            cv2.rectangle(debug_frame, (x_start, 0), (x_end - 1, roi.shape[0] - 1), box_color, 2)
            cv2.putText(
                debug_frame,
                f'{is_black} ({int(black_ratio*100)}%)',
                (x_start + 5, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                box_color,
                2
            )

        # 5. Publish the 7-element array [s0, s1, s2, s3, s4, s5, s6]
        sensor_msg = Int8MultiArray()
        sensor_msg.data = sensor_array
        self.pub_sensors.publish(sensor_msg)

        # 6. Publish annotated ROI so you can view it in rqt_image_view
        debug_msg = self.bridge.cv2_to_imgmsg(debug_frame, encoding='bgr8')
        self.pub_debug.publish(debug_msg)


def main(args=None):
    rclpy.init(args=args)
    node = VirtualSensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()