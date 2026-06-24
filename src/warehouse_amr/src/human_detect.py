#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO


class HumanDetectionNode(Node):
    def __init__(self):
        super().__init__('human_detection_node')

        self.model = YOLO('yolov8n.pt')  # downloads automatically on first run
        self.bridge = CvBridge()

        self.image_sub = self.create_subscription(
            Image, '/depth_camera/image', self.image_callback, 10)
        self.annotated_pub = self.create_publisher(Image, '/human_detection/image', 10)
        self.detected_pub  = self.create_publisher(Bool, '/human_detection/detected', 10)
        self.cmd_vel_pub   = self.create_publisher(Twist, '/cmd_vel', 10)

        self.get_logger().info('YOLO human detection node started.')

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'cv_bridge error: {e}')
            return

        results = self.model(frame, classes=[0], conf=0.3, verbose=False)  # class 0 = person

        detected = False
        for result in results:
            for box in result.boxes:
                detected = True
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'person {conf:.2f}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if detected:
            cv2.putText(frame, 'STOP: HUMAN DETECTED', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            stop = Twist()
            self.cmd_vel_pub.publish(stop)
            self.get_logger().warn('Human detected — stopping robot.')

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
