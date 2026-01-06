#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np
import yaml
import os
from ament_index_python.packages import get_package_share_directory

class OpenCVCameraNode(Node):
    def __init__(self):
        super().__init__('opencv_camera_node')
        
        # Parameters
        self.declare_parameter('video_device', '/dev/video0')
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 30)
        self.declare_parameter('camera_frame_id', 'camera_link_optical')
        self.declare_parameter('camera_info_url', '')
        
        # Get parameters
        self.video_device = self.get_parameter('video_device').get_parameter_value().string_value
        self.width = self.get_parameter('width').get_parameter_value().integer_value
        self.height = self.get_parameter('height').get_parameter_value().integer_value
        self.fps = self.get_parameter('fps').get_parameter_value().integer_value
        self.camera_frame_id = self.get_parameter('camera_frame_id').get_parameter_value().string_value
        self.camera_info_url = self.get_parameter('camera_info_url').get_parameter_value().string_value
        
        # Initialize CV bridge
        self.bridge = CvBridge()
        
        # Publishers
        self.image_pub = self.create_publisher(Image, '/camera/image', 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)
        
        # Load camera info
        self.camera_info = self.load_camera_info()
        
        # Initialize camera
        self.cap = None
        self.init_camera()
        
        # Timer for publishing
        timer_period = 1.0 / self.fps
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        self.get_logger().info(f'OpenCV Camera Node started - Device: {self.video_device}, Resolution: {self.width}x{self.height}')

    def init_camera(self):
        """Initialize camera with multiple backends"""
        backends = [
            cv2.CAP_V4L2,
            cv2.CAP_GSTREAMER,
            cv2.CAP_ANY
        ]
        
        for backend in backends:
            try:
                self.get_logger().info(f'Trying to open camera with backend: {backend}')
                
                # Try different device indices
                for device_idx in [0, 1, 2]:
                    self.cap = cv2.VideoCapture(device_idx, backend)
                    
                    if self.cap.isOpened():
                        # Set properties
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                        
                        # Test capture
                        ret, frame = self.cap.read()
                        if ret and frame is not None:
                            self.get_logger().info(f'Camera opened successfully with device {device_idx}, backend {backend}')
                            self.get_logger().info(f'Actual resolution: {frame.shape[1]}x{frame.shape[0]}')
                            return
                        else:
                            self.cap.release()
                            self.cap = None
                    
            except Exception as e:
                self.get_logger().warn(f'Failed to open camera with backend {backend}: {e}')
                if self.cap:
                    self.cap.release()
                    self.cap = None
        
        self.get_logger().error('Failed to open camera with any backend')

    def load_camera_info(self):
        """Load camera calibration info"""
        camera_info = CameraInfo()
        camera_info.header.frame_id = self.camera_frame_id
        camera_info.width = self.width
        camera_info.height = self.height
        
        if self.camera_info_url:
            try:
                # Parse package:// URL
                if self.camera_info_url.startswith('package://'):
                    parts = self.camera_info_url[10:].split('/', 1)
                    package_name = parts[0]
                    relative_path = parts[1]
                    package_path = get_package_share_directory(package_name)
                    yaml_path = os.path.join(package_path, relative_path)
                else:
                    yaml_path = self.camera_info_url
                
                with open(yaml_path, 'r') as f:
                    calib_data = yaml.safe_load(f)
                
                camera_info.k = calib_data['camera_matrix']['data']
                camera_info.d = calib_data['distortion_coefficients']['data']
                camera_info.r = calib_data['rectification_matrix']['data']
                camera_info.p = calib_data['projection_matrix']['data']
                camera_info.distortion_model = calib_data['distortion_model']
                
                self.get_logger().info(f'Loaded camera calibration from {yaml_path}')
                
            except Exception as e:
                self.get_logger().warn(f'Failed to load camera info: {e}')
                # Use default values
                camera_info.k = [525.0, 0.0, 320.0, 0.0, 525.0, 240.0, 0.0, 0.0, 1.0]
                camera_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
                camera_info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
                camera_info.p = [525.0, 0.0, 320.0, 0.0, 0.0, 525.0, 240.0, 0.0, 0.0, 0.0, 1.0, 0.0]
                camera_info.distortion_model = 'plumb_bob'
        else:
            # Default camera info
            camera_info.k = [525.0, 0.0, 320.0, 0.0, 525.0, 240.0, 0.0, 0.0, 1.0]
            camera_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
            camera_info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
            camera_info.p = [525.0, 0.0, 320.0, 0.0, 0.0, 525.0, 240.0, 0.0, 0.0, 0.0, 1.0, 0.0]
            camera_info.distortion_model = 'plumb_bob'
        
        return camera_info

    def timer_callback(self):
        """Capture and publish camera frame"""
        if self.cap is None or not self.cap.isOpened():
            self.get_logger().warn('Camera not available, attempting to reinitialize...')
            self.init_camera()
            return
        
        try:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                # Convert to ROS Image message
                ros_image = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
                ros_image.header.stamp = self.get_clock().now().to_msg()
                ros_image.header.frame_id = self.camera_frame_id
                
                # Update camera info timestamp
                self.camera_info.header.stamp = ros_image.header.stamp
                
                # Publish
                self.image_pub.publish(ros_image)
                self.camera_info_pub.publish(self.camera_info)
                
            else:
                self.get_logger().warn('Failed to capture frame')
                
        except Exception as e:
            self.get_logger().error(f'Error in timer callback: {e}')

    def destroy_node(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = OpenCVCameraNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
