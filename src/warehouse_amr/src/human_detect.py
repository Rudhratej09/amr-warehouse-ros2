#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
import cv2


class HumanDetectionNode(Node):
    def __init__(self):
        super().__init__('human_detection_node')
        cascade_path = '/usr/share/opencv4/haarcascades/haarcascade_fullbody.xml'
        self.detector = cv2.CascadeClassifier(cascade_path)
        if self.detector.empty():
            self.get_logger().error('Failed to load Haar cascade!')
            return
        self.get_logger().info('Haar cascade loaded.')

        self.bridge = CvBridge()

        self.image_sub = self.create_subscription(
            Image, '/depth_camera/image', self.image_callback, 10)
        self.annotated_pub = self.create_publisher(Image, '/human_detection/image', 10)
        self.detected_pub  = self.create_publisher(Bool, '/human_detection/detected', 10)
        self.cmd_vel_pub   = self.create_publisher(Twist, '/cmd_vel', 10)

        self.get_logger().info('Human detection node started.')

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'cv_bridge error: {e}')
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        humans = self.detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(30, 60)
        )

        detected = len(humans) > 0
        for (x, y, w, h) in humans:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, 'person', (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if detected:
            cv2.putText(frame, 'person ahead', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            stop = Twist()
            self.cmd_vel_pub.publish(stop)
            self.get_logger().warn('person detected — stopping robot.')
        try:
            annotated_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            annotated_msg.header = msg.header
            self.annotated_pub.publish(annotated_msg)
        except Exception as e:
            self.get_logger().error(f'Publish error: {e}')
        detected_msg = Bool()
        detected_msg.data = detected
        self.detected_pub.publish(detected_msg)


def main(args=None):
    rclpy.init(args=args)
    node = HumanDetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()