#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import Twist, TwistStamped
from sensor_msgs.msg import Image, CompressedImage
from nav_msgs.msg import Odometry
import threading
import json
import base64
import cv2
from cv_bridge import CvBridge
import numpy as np
import time
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import os

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, robot_server=None, **kwargs):
        self.robot_server = robot_server
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = self.robot_server.get_html_content()
            self.wfile.write(html_content.encode())
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            status = self.robot_server.get_status()
            self.wfile.write(json.dumps(status).encode())
        elif self.path == '/api/camera':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            camera_data = self.robot_server.get_camera_data()
            self.wfile.write(json.dumps(camera_data).encode())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/cmd_vel':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode())
                self.robot_server.handle_cmd_vel(data)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok'}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

class RobotWebServer(Node):
    def __init__(self):
        super().__init__('robot_web_server')

        # Initialize CV bridge
        self.bridge = CvBridge()

        # Robot state variables
        self.latest_image = None
        self.robot_pose = {'x': 0.0, 'y': 0.0, 'theta': 0.0}
        self.robot_velocity = {'linear': 0.0, 'angular': 0.0}
        self.camera_fps = 0
        self.last_image_time = self.get_clock().now()

        # Publishers
        self.cmd_vel_pub = self.create_publisher(
            TwistStamped,
            '/cmd_vel_keyboard',
            10
        )

        # Subscribers
        # QoS profile for camera compressed images (best-effort, depth 1)
        camera_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST
        )
        
        self.image_sub = self.create_subscription(
            CompressedImage,
            '/camera/image_raw/compressed',
            self.image_callback,
            camera_qos
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odometry/filtered',
            self.odom_callback,
            10
        )

        # Start web server in separate thread
        self.web_thread = threading.Thread(target=self.run_web_server)
        self.web_thread.daemon = True
        self.web_thread.start()

        self.get_logger().info('Robot Web Server started on http://0.0.0.0:8080')
    
    def image_callback(self, msg):
        try:
            # msg.data is already JPEG compressed, convert to base64 directly
            img_base64 = base64.b64encode(msg.data).decode('utf-8')
            self.latest_image = f"data:image/jpeg;base64,{img_base64}"

            # Calculate FPS
            current_time = self.get_clock().now()
            time_diff = (current_time - self.last_image_time).nanoseconds / 1e9
            if time_diff > 0:
                self.camera_fps = 1.0 / time_diff
            self.last_image_time = current_time

        except Exception as e:
            self.get_logger().error(f'Error processing camera image: {e}')
    
    def odom_callback(self, msg):
        # Extract position and orientation
        self.robot_pose['x'] = msg.pose.pose.position.x
        self.robot_pose['y'] = msg.pose.pose.position.y

        # Convert quaternion to yaw angle
        quat = msg.pose.pose.orientation
        siny_cosp = 2 * (quat.w * quat.z + quat.x * quat.y)
        cosy_cosp = 1 - 2 * (quat.y * quat.y + quat.z * quat.z)
        self.robot_pose['theta'] = np.arctan2(siny_cosp, cosy_cosp)

        # Extract velocities
        self.robot_velocity['linear'] = msg.twist.twist.linear.x
        self.robot_velocity['angular'] = msg.twist.twist.angular.z
    
    def get_status(self):
        return {
            'pose': self.robot_pose,
            'velocity': self.robot_velocity,
            'timestamp': time.time()
        }

    def get_camera_data(self):
        return {
            'image': self.latest_image,
            'fps': round(self.camera_fps, 1),
            'timestamp': time.time()
        }

    def handle_cmd_vel(self, data):
        try:
            # Create TwistStamped message
            twist_msg = TwistStamped()
            twist_msg.header.stamp = self.get_clock().now().to_msg()
            twist_msg.header.frame_id = 'base_footprint'

            twist_msg.twist.linear.x = float(data.get('linear_x', 0.0))
            twist_msg.twist.linear.y = float(data.get('linear_y', 0.0))
            twist_msg.twist.angular.z = float(data.get('angular_z', 0.0))

            # Publish command
            self.cmd_vel_pub.publish(twist_msg)

        except Exception as e:
            self.get_logger().error(f'Error processing cmd_vel: {e}')

    def get_html_content(self):
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RMIT Robot Control Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 20px;
        }

        .camera-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
        }

        .camera-container {
            position: relative;
            background: #000;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 15px;
        }

        #camera-feed {
            width: 100%;
            height: auto;
            max-height: 400px;
            object-fit: contain;
        }

        .camera-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #e9ecef;
            padding: 10px 15px;
            border-radius: 8px;
            font-weight: bold;
        }

        .control-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
        }

        .control-mode {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }

        .mode-switch {
            display: flex;
            background: #e9ecef;
            border-radius: 25px;
            padding: 5px;
        }

        .mode-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: bold;
        }

        .mode-btn.active {
            background: #667eea;
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }

        .mode-btn:not(.active) {
            background: transparent;
            color: #666;
        }

        .joystick-container {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }

        .joystick {
            width: 200px;
            height: 200px;
            border: 3px solid #667eea;
            border-radius: 50%;
            position: relative;
            background: radial-gradient(circle, #f8f9fa 0%, #e9ecef 100%);
            cursor: pointer;
            touch-action: none;
        }

        .joystick-knob {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.1s ease;
        }

        .arrow-controls {
            display: none;
            flex-direction: column;
            gap: 20px;
            margin: 0 auto 20px;
        }

        .arrow-controls.active {
            display: flex;
        }

        .arrow-movement-section {
            background: #e8f4fd;
            border-radius: 15px;
            padding: 20px;
            border: 2px solid #667eea;
        }

        .arrow-movement-section h4 {
            margin: 0 0 15px 0;
            color: #667eea;
            font-size: 1.1em;
            text-align: center;
        }

        .arrow-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
            max-width: 300px;
            margin: 0 auto;
        }

        .arrow-btn {
            width: 50px;
            height: 50px;
            border: none;
            border-radius: 10px;
            color: white;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }

        .movement-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }

        .movement-btn:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }

        .movement-btn:active {
            transform: translateY(0) scale(0.95);
            box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
        }

        .stop-btn {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
        }

        .stop-btn:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 8px 25px rgba(220, 53, 69, 0.4);
        }

        .stop-btn:active {
            transform: translateY(0) scale(0.95);
        }

        .arrow-orientation-section {
            background: #fff3cd;
            border-radius: 15px;
            padding: 20px;
            border: 2px solid #ffc107;
        }

        .arrow-orientation-section h4 {
            margin: 0 0 15px 0;
            color: #856404;
            font-size: 1.1em;
            text-align: center;
        }

        .arrow-rotation-controls {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 10px;
        }

        .arrow-rotate-btn {
            padding: 12px 20px;
            border: none;
            border-radius: 10px;
            color: white;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 80px;
            background: linear-gradient(135deg, #ffc107 0%, #ff8c00 100%);
            box-shadow: 0 4px 15px rgba(255, 193, 7, 0.3);
        }

        .arrow-rotate-btn:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 8px 25px rgba(255, 193, 7, 0.4);
        }

        .arrow-rotate-btn:active {
            transform: translateY(0) scale(0.95);
        }

        .stop-rotate-btn {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3) !important;
        }

        .stop-rotate-btn:hover {
            box-shadow: 0 8px 25px rgba(220, 53, 69, 0.4) !important;
        }

        .arrow-rotation-info {
            text-align: center;
            font-size: 0.85em;
            color: #856404;
            font-style: italic;
        }

        /* Button press animation */
        .arrow-btn.pressed, .arrow-rotate-btn.pressed {
            transform: translateY(0) scale(0.95);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }

        /* Ripple effect */
        .arrow-btn::before, .arrow-rotate-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
            transition: width 0.3s, height 0.3s;
        }

        .arrow-btn:active::before, .arrow-rotate-btn:active::before {
            width: 100px;
            height: 100px;
        }

        .speed-control-section {
            background: #e8f4fd;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border: 2px solid #667eea;
        }

        .speed-control-section h4 {
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 1.1em;
        }

        .speed-slider-container {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .speed-slider-container label {
            font-weight: bold;
            color: #333;
            font-size: 0.9em;
        }

        .speed-slider {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: #ddd;
            outline: none;
            -webkit-appearance: none;
        }

        .speed-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
        }

        .speed-slider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
        }

        .joystick-label {
            text-align: center;
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
            font-weight: bold;
        }

        .orientation-control {
            background: #fff3cd;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border: 2px solid #ffc107;
        }

        .orientation-control h4 {
            margin: 0 0 15px 0;
            color: #856404;
            font-size: 1.1em;
        }

        .orientation-buttons {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 15px;
        }

        .orient-btn {
            flex: 1;
            padding: 12px 8px;
            border: none;
            border-radius: 8px;
            background: linear-gradient(135deg, #ffc107 0%, #ff8c00 100%);
            color: white;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .orient-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 15px rgba(255, 193, 7, 0.4);
        }

        .orient-btn:active {
            transform: scale(0.95);
        }

        .orientation-slider-container {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .orientation-slider-container label {
            font-weight: bold;
            color: #856404;
            font-size: 0.9em;
        }

        .status-section {
            grid-column: 1 / -1;
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }

        .status-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        .status-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .status-label {
            color: #666;
            font-size: 0.9em;
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }

            .header h1 {
                font-size: 2em;
            }

            .joystick {
                width: 150px;
                height: 150px;
            }

            .joystick-knob {
                width: 45px;
                height: 45px;
            }
        }

        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            z-index: 1000;
        }

        .connected {
            background: #28a745;
        }

        .disconnected {
            background: #dc3545;
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connection-status">Connected</div>

    <div class="container">
        <div class="header">
            <h1>🤖 RMIT Robot Control</h1>
            <p>Advanced Mecanum Drive Control Interface</p>
        </div>

        <div class="main-content">
            <div class="camera-section">
                <h3>📹 Camera Feed</h3>
                <div class="camera-container">
                    <img id="camera-feed" src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQwIiBoZWlnaHQ9IjQ4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjY2NjIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPldhaXRpbmcgZm9yIGNhbWVyYS4uLjwvdGV4dD48L3N2Zz4=" alt="Camera Feed">
                </div>
                <div class="camera-info">
                    <span>FPS: <span id="camera-fps">0</span></span>
                    <span>Resolution: 640x480</span>
                </div>
            </div>

            <div class="control-section">
                <h3>🎮 Robot Control</h3>

                <div class="control-mode">
                    <div class="mode-switch">
                        <button class="mode-btn active" id="joystick-mode">Joystick</button>
                        <button class="mode-btn" id="arrow-mode">Arrow Keys</button>
                    </div>
                </div>

                <!-- Speed Control Section -->
                <div class="speed-control-section">
                    <h4>⚡ Speed Control</h4>
                    <div class="speed-slider-container">
                        <label for="speed-slider">Max Speed: <span id="speed-value">0.5</span> m/s</label>
                        <input type="range" id="speed-slider" min="0.1" max="1.0" step="0.1" value="0.5" class="speed-slider">
                    </div>
                </div>

                <div style="text-align: center; margin-bottom: 15px; font-size: 0.9em; color: #666;">
                    <div id="joystick-help">🎮 Drag joystick for Cartesian movement + Use orientation buttons</div>
                    <div id="arrow-help" style="display: none;">
                        ⌨️ WASD/Arrows: Movement | QEZC: Diagonal | RT: Rotation | Space: Stop
                    </div>
                </div>

                <div class="joystick-container" id="joystick-container">
                    <div class="joystick" id="joystick">
                        <div class="joystick-knob" id="joystick-knob"></div>
                    </div>
                    <div class="joystick-label">Cartesian Movement</div>
                </div>

                <!-- Orientation Control Section -->
                <div class="orientation-control" id="orientation-control">
                    <h4>🧭 Orientation Control</h4>
                    <div class="orientation-buttons">
                        <button class="orient-btn" id="rotate-left">↺ Left</button>
                        <button class="orient-btn" id="rotate-stop">⏹ Stop</button>
                        <button class="orient-btn" id="rotate-right">↻ Right</button>
                    </div>
                    <div class="orientation-slider-container">
                        <label for="angular-speed-slider">Angular Speed: <span id="angular-speed-value">1.0</span> rad/s</label>
                        <input type="range" id="angular-speed-slider" min="0.2" max="2.0" step="0.2" value="1.0" class="speed-slider">
                    </div>
                </div>

                <div class="arrow-controls" id="arrow-controls">
                    <!-- Movement Control Section -->
                    <div class="arrow-movement-section">
                        <h4>🎮 Movement Control</h4>
                        <div class="arrow-grid">
                            <!-- Row 1 -->
                            <div></div>
                            <button class="arrow-btn movement-btn" id="forward-left" title="Forward-Left (Q)">↖</button>
                            <button class="arrow-btn movement-btn" id="forward" title="Forward (W/↑)">↑</button>
                            <button class="arrow-btn movement-btn" id="forward-right" title="Forward-Right (E)">↗</button>
                            <div></div>

                            <!-- Row 2 -->
                            <button class="arrow-btn movement-btn" id="left" title="Left (A/←)">←</button>
                            <div></div>
                            <button class="arrow-btn stop-btn" id="stop" title="Stop (Space)">⏹</button>
                            <div></div>
                            <button class="arrow-btn movement-btn" id="right" title="Right (D/→)">→</button>

                            <!-- Row 3 -->
                            <div></div>
                            <button class="arrow-btn movement-btn" id="backward-left" title="Backward-Left (Z)">↙</button>
                            <button class="arrow-btn movement-btn" id="backward" title="Backward (S/↓)">↓</button>
                            <button class="arrow-btn movement-btn" id="backward-right" title="Backward-Right (C)">↘</button>
                            <div></div>
                        </div>
                    </div>

                    <!-- Orientation Control Section for Arrow Mode -->
                    <div class="arrow-orientation-section">
                        <h4>🧭 Rotation Control</h4>
                        <div class="arrow-rotation-controls">
                            <button class="arrow-rotate-btn" id="arrow-rotate-left" title="Rotate Left">↺ Left</button>
                            <button class="arrow-rotate-btn stop-rotate-btn" id="arrow-rotate-stop" title="Stop Rotation">⏹ Stop</button>
                            <button class="arrow-rotate-btn" id="arrow-rotate-right" title="Rotate Right">↻ Right</button>
                        </div>
                        <div class="arrow-rotation-info">
                            <span>Use rotation buttons or R/T keys</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="status-section">
            <h3>📊 Robot Status</h3>
            <div class="status-grid">
                <div class="status-card">
                    <div class="status-value" id="pos-x">0.00</div>
                    <div class="status-label">Position X (m)</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="pos-y">0.00</div>
                    <div class="status-label">Position Y (m)</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="pos-theta">0.00</div>
                    <div class="status-label">Orientation (rad)</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="vel-linear">0.00</div>
                    <div class="status-label">Linear Velocity (m/s)</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="vel-angular">0.00</div>
                    <div class="status-label">Angular Velocity (rad/s)</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="max-speed-display">0.5</div>
                    <div class="status-label">Max Speed Setting (m/s)</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="max-angular-speed-display">1.0</div>
                    <div class="status-label">Max Angular Speed (rad/s)</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Robot Web Interface JavaScript
        class RobotController {
            constructor() {
                this.isJoystickMode = true;
                this.isDragging = false;
                this.joystickCenter = { x: 0, y: 0 };
                this.maxDistance = 85;
                this.currentVelocity = { linear_x: 0, linear_y: 0, angular_z: 0 };
                this.maxSpeed = 0.5;
                this.maxAngularSpeed = 1.0;
                this.isRotating = false;

                this.initializeElements();
                this.setupEventListeners();
                this.startUpdateLoop();
            }

            initializeElements() {
                this.joystickModeBtn = document.getElementById('joystick-mode');
                this.arrowModeBtn = document.getElementById('arrow-mode');
                this.joystickContainer = document.getElementById('joystick-container');
                this.arrowControls = document.getElementById('arrow-controls');

                this.joystick = document.getElementById('joystick');
                this.joystickKnob = document.getElementById('joystick-knob');

                this.forwardBtn = document.getElementById('forward');
                this.backwardBtn = document.getElementById('backward');
                this.leftBtn = document.getElementById('left');
                this.rightBtn = document.getElementById('right');
                this.stopBtn = document.getElementById('stop');

                // Diagonal movement buttons
                this.forwardLeftBtn = document.getElementById('forward-left');
                this.forwardRightBtn = document.getElementById('forward-right');
                this.backwardLeftBtn = document.getElementById('backward-left');
                this.backwardRightBtn = document.getElementById('backward-right');

                // Speed control elements
                this.speedSlider = document.getElementById('speed-slider');
                this.speedValue = document.getElementById('speed-value');
                this.angularSpeedSlider = document.getElementById('angular-speed-slider');
                this.angularSpeedValue = document.getElementById('angular-speed-value');

                // Orientation control elements (Joystick mode)
                this.rotateLeftBtn = document.getElementById('rotate-left');
                this.rotateRightBtn = document.getElementById('rotate-right');
                this.rotateStopBtn = document.getElementById('rotate-stop');
                this.orientationControl = document.getElementById('orientation-control');

                // Arrow mode orientation control elements
                this.arrowRotateLeftBtn = document.getElementById('arrow-rotate-left');
                this.arrowRotateRightBtn = document.getElementById('arrow-rotate-right');
                this.arrowRotateStopBtn = document.getElementById('arrow-rotate-stop');

                this.cameraFeed = document.getElementById('camera-feed');
                this.cameraFps = document.getElementById('camera-fps');
                this.connectionStatus = document.getElementById('connection-status');

                this.posX = document.getElementById('pos-x');
                this.posY = document.getElementById('pos-y');
                this.posTheta = document.getElementById('pos-theta');
                this.velLinear = document.getElementById('vel-linear');
                this.velAngular = document.getElementById('vel-angular');
                this.maxSpeedDisplay = document.getElementById('max-speed-display');
                this.maxAngularSpeedDisplay = document.getElementById('max-angular-speed-display');
            }

            setupEventListeners() {
                this.joystickModeBtn.addEventListener('click', () => this.switchMode(true));
                this.arrowModeBtn.addEventListener('click', () => this.switchMode(false));

                this.joystick.addEventListener('mousedown', (e) => this.startJoystickDrag(e));
                this.joystick.addEventListener('touchstart', (e) => this.startJoystickDrag(e));

                document.addEventListener('mousemove', (e) => this.updateJoystick(e));
                document.addEventListener('touchmove', (e) => this.updateJoystick(e));

                document.addEventListener('mouseup', () => this.stopJoystickDrag());
                document.addEventListener('touchend', () => this.stopJoystickDrag());

                this.setupArrowControls();
                this.setupSpeedControls();
                this.setupOrientationControls();
                this.setupArrowOrientationControls();

                document.addEventListener('keydown', (e) => this.handleKeyDown(e));
                document.addEventListener('keyup', (e) => this.handleKeyUp(e));
            }

            setupArrowControls() {
                const updateArrowControls = () => {
                    const maxVel = this.maxSpeed;
                    const diagVel = maxVel * 0.707; // √2/2 for diagonal movement

                    const controls = [
                        // Basic directions
                        { btn: this.forwardBtn, vel: { linear_x: maxVel, linear_y: 0, angular_z: 0 } },
                        { btn: this.backwardBtn, vel: { linear_x: -maxVel, linear_y: 0, angular_z: 0 } },
                        { btn: this.leftBtn, vel: { linear_x: 0, linear_y: maxVel, angular_z: 0 } },
                        { btn: this.rightBtn, vel: { linear_x: 0, linear_y: -maxVel, angular_z: 0 } },
                        { btn: this.stopBtn, vel: { linear_x: 0, linear_y: 0, angular_z: 0 } },

                        // Diagonal directions
                        { btn: this.forwardLeftBtn, vel: { linear_x: diagVel, linear_y: diagVel, angular_z: 0 } },
                        { btn: this.forwardRightBtn, vel: { linear_x: diagVel, linear_y: -diagVel, angular_z: 0 } },
                        { btn: this.backwardLeftBtn, vel: { linear_x: -diagVel, linear_y: diagVel, angular_z: 0 } },
                        { btn: this.backwardRightBtn, vel: { linear_x: -diagVel, linear_y: -diagVel, angular_z: 0 } }
                    ];

                    controls.forEach(({ btn, vel }) => {
                        btn.addEventListener('mousedown', () => {
                            this.addPressedEffect(btn);
                            this.setVelocity(vel);
                        });
                        btn.addEventListener('touchstart', () => {
                            this.addPressedEffect(btn);
                            this.setVelocity(vel);
                        });
                        btn.addEventListener('mouseup', () => {
                            this.removePressedEffect(btn);
                            this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                        });
                        btn.addEventListener('mouseleave', () => {
                            this.removePressedEffect(btn);
                            this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                        });
                        btn.addEventListener('touchend', () => {
                            this.removePressedEffect(btn);
                            this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                        });
                    });
                };

                updateArrowControls();
                this.updateArrowControls = updateArrowControls; // Store reference for later updates
            }

            setupSpeedControls() {
                this.speedSlider.addEventListener('input', (e) => {
                    this.maxSpeed = parseFloat(e.target.value);
                    this.speedValue.textContent = this.maxSpeed.toFixed(1);
                    this.maxSpeedDisplay.textContent = this.maxSpeed.toFixed(1);
                });

                this.angularSpeedSlider.addEventListener('input', (e) => {
                    this.maxAngularSpeed = parseFloat(e.target.value);
                    this.angularSpeedValue.textContent = this.maxAngularSpeed.toFixed(1);
                    this.maxAngularSpeedDisplay.textContent = this.maxAngularSpeed.toFixed(1);
                });
            }

            setupOrientationControls() {
                this.rotateLeftBtn.addEventListener('mousedown', () => {
                    this.isRotating = true;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: this.maxAngularSpeed });
                });

                this.rotateRightBtn.addEventListener('mousedown', () => {
                    this.isRotating = true;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: -this.maxAngularSpeed });
                });

                this.rotateStopBtn.addEventListener('mousedown', () => {
                    this.isRotating = false;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                });

                // Stop rotation on mouse up
                [this.rotateLeftBtn, this.rotateRightBtn].forEach(btn => {
                    btn.addEventListener('mouseup', () => {
                        this.isRotating = false;
                        this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                    });
                    btn.addEventListener('touchend', () => {
                        this.isRotating = false;
                        this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                    });
                });

                // Touch events
                this.rotateLeftBtn.addEventListener('touchstart', () => {
                    this.isRotating = true;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: this.maxAngularSpeed });
                });

                this.rotateRightBtn.addEventListener('touchstart', () => {
                    this.isRotating = true;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: -this.maxAngularSpeed });
                });

                this.rotateStopBtn.addEventListener('touchstart', () => {
                    this.isRotating = false;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                });
            }

            setupArrowOrientationControls() {
                // Arrow mode rotation controls
                this.arrowRotateLeftBtn.addEventListener('mousedown', () => {
                    this.addPressedEffect(this.arrowRotateLeftBtn);
                    this.isRotating = true;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: this.maxAngularSpeed });
                });

                this.arrowRotateRightBtn.addEventListener('mousedown', () => {
                    this.addPressedEffect(this.arrowRotateRightBtn);
                    this.isRotating = true;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: -this.maxAngularSpeed });
                });

                this.arrowRotateStopBtn.addEventListener('mousedown', () => {
                    this.addPressedEffect(this.arrowRotateStopBtn);
                    this.isRotating = false;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                });

                // Stop rotation on mouse up
                [this.arrowRotateLeftBtn, this.arrowRotateRightBtn].forEach(btn => {
                    btn.addEventListener('mouseup', () => {
                        this.removePressedEffect(btn);
                        this.isRotating = false;
                        this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                    });
                    btn.addEventListener('mouseleave', () => {
                        this.removePressedEffect(btn);
                        this.isRotating = false;
                        this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                    });
                });

                this.arrowRotateStopBtn.addEventListener('mouseup', () => {
                    this.removePressedEffect(this.arrowRotateStopBtn);
                });

                // Touch events
                this.arrowRotateLeftBtn.addEventListener('touchstart', () => {
                    this.addPressedEffect(this.arrowRotateLeftBtn);
                    this.isRotating = true;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: this.maxAngularSpeed });
                });

                this.arrowRotateRightBtn.addEventListener('touchstart', () => {
                    this.addPressedEffect(this.arrowRotateRightBtn);
                    this.isRotating = true;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: -this.maxAngularSpeed });
                });

                this.arrowRotateStopBtn.addEventListener('touchstart', () => {
                    this.addPressedEffect(this.arrowRotateStopBtn);
                    this.isRotating = false;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                });

                [this.arrowRotateLeftBtn, this.arrowRotateRightBtn].forEach(btn => {
                    btn.addEventListener('touchend', () => {
                        this.removePressedEffect(btn);
                        this.isRotating = false;
                        this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                    });
                });

                this.arrowRotateStopBtn.addEventListener('touchend', () => {
                    this.removePressedEffect(this.arrowRotateStopBtn);
                });
            }

            addPressedEffect(element) {
                element.classList.add('pressed');
            }

            removePressedEffect(element) {
                element.classList.remove('pressed');
            }

            switchMode(isJoystick) {
                this.isJoystickMode = isJoystick;

                const joystickHelp = document.getElementById('joystick-help');
                const arrowHelp = document.getElementById('arrow-help');

                if (isJoystick) {
                    this.joystickModeBtn.classList.add('active');
                    this.arrowModeBtn.classList.remove('active');
                    this.joystickContainer.style.display = 'flex';
                    this.arrowControls.classList.remove('active');
                    this.orientationControl.style.display = 'block';
                    joystickHelp.style.display = 'block';
                    arrowHelp.style.display = 'none';
                } else {
                    this.arrowModeBtn.classList.add('active');
                    this.joystickModeBtn.classList.remove('active');
                    this.joystickContainer.style.display = 'none';
                    this.arrowControls.classList.add('active');
                    this.orientationControl.style.display = 'none';
                    joystickHelp.style.display = 'none';
                    arrowHelp.style.display = 'block';
                }

                this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                this.isRotating = false;
            }

            startJoystickDrag(e) {
                if (!this.isJoystickMode) return;

                this.isDragging = true;
                const rect = this.joystick.getBoundingClientRect();
                this.joystickCenter = {
                    x: rect.left + rect.width / 2,
                    y: rect.top + rect.height / 2
                };

                e.preventDefault();
            }

            updateJoystick(e) {
                if (!this.isDragging || !this.isJoystickMode) return;

                const clientX = e.clientX || (e.touches && e.touches[0].clientX);
                const clientY = e.clientY || (e.touches && e.touches[0].clientY);

                if (!clientX || !clientY) return;

                const deltaX = clientX - this.joystickCenter.x;
                const deltaY = clientY - this.joystickCenter.y;
                const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

                let knobX = deltaX;
                let knobY = deltaY;

                if (distance > this.maxDistance) {
                    knobX = (deltaX / distance) * this.maxDistance;
                    knobY = (deltaY / distance) * this.maxDistance;
                }

                this.joystickKnob.style.transform = `translate(${knobX - 30}px, ${knobY - 30}px)`;

                const normalizedX = knobX / this.maxDistance;
                const normalizedY = -knobY / this.maxDistance;

                // Only Cartesian movement, no rotation (unless currently rotating)
                const angularZ = this.isRotating ? this.currentVelocity.angular_z : 0;

                this.setVelocity({
                    linear_x: normalizedY * this.maxSpeed,
                    linear_y: -normalizedX * this.maxSpeed,
                    angular_z: angularZ
                });
            }

            stopJoystickDrag() {
                if (!this.isDragging) return;

                this.isDragging = false;
                this.joystickKnob.style.transform = 'translate(-30px, -30px)';
                this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
            }

            handleKeyDown(e) {
                if (this.isJoystickMode) return;

                const maxVel = this.maxSpeed;
                const diagVel = maxVel * 0.707; // √2/2 for diagonal movement

                switch(e.key) {
                    // Basic directions
                    case 'ArrowUp':
                    case 'w':
                        this.setVelocity({ linear_x: maxVel, linear_y: 0, angular_z: 0 });
                        break;
                    case 'ArrowDown':
                    case 's':
                        this.setVelocity({ linear_x: -maxVel, linear_y: 0, angular_z: 0 });
                        break;
                    case 'ArrowLeft':
                    case 'a':
                        this.setVelocity({ linear_x: 0, linear_y: maxVel, angular_z: 0 });
                        break;
                    case 'ArrowRight':
                    case 'd':
                        this.setVelocity({ linear_x: 0, linear_y: -maxVel, angular_z: 0 });
                        break;

                    // Diagonal directions
                    case 'q':
                    case 'Q':
                        this.setVelocity({ linear_x: diagVel, linear_y: diagVel, angular_z: 0 }); // Forward-Left
                        break;
                    case 'e':
                    case 'E':
                        this.setVelocity({ linear_x: diagVel, linear_y: -diagVel, angular_z: 0 }); // Forward-Right
                        break;
                    case 'z':
                    case 'Z':
                        this.setVelocity({ linear_x: -diagVel, linear_y: diagVel, angular_z: 0 }); // Backward-Left
                        break;
                    case 'c':
                    case 'C':
                        this.setVelocity({ linear_x: -diagVel, linear_y: -diagVel, angular_z: 0 }); // Backward-Right
                        break;

                    // Rotation controls for Arrow Keys mode
                    case 'r':
                    case 'R':
                        this.isRotating = true;
                        this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: this.maxAngularSpeed }); // Rotate Left
                        this.addPressedEffect(this.arrowRotateLeftBtn);
                        break;
                    case 't':
                    case 'T':
                        this.isRotating = true;
                        this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: -this.maxAngularSpeed }); // Rotate Right
                        this.addPressedEffect(this.arrowRotateRightBtn);
                        break;

                    case ' ':
                        this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                        this.isRotating = false;
                        break;
                }
                e.preventDefault();
            }

            handleKeyUp(e) {
                if (this.isJoystickMode) return;

                const movementKeys = [
                    'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
                    'w', 'a', 's', 'd', 'q', 'e', 'z', 'c',
                    'W', 'A', 'S', 'D', 'Q', 'E', 'Z', 'C'
                ];

                const rotationKeys = ['r', 'R', 't', 'T'];

                if (movementKeys.includes(e.key)) {
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                } else if (rotationKeys.includes(e.key)) {
                    this.isRotating = false;
                    this.setVelocity({ linear_x: 0, linear_y: 0, angular_z: 0 });
                    this.removePressedEffect(this.arrowRotateLeftBtn);
                    this.removePressedEffect(this.arrowRotateRightBtn);
                }
            }

            setVelocity(velocity) {
                this.currentVelocity = velocity;
                this.sendCommand();
            }

            async sendCommand() {
                try {
                    await fetch('/api/cmd_vel', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(this.currentVelocity)
                    });
                } catch (error) {
                    console.error('Error sending command:', error);
                }
            }

            async updateStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();

                    if (data.pose) {
                        this.posX.textContent = data.pose.x.toFixed(2);
                        this.posY.textContent = data.pose.y.toFixed(2);
                        this.posTheta.textContent = data.pose.theta.toFixed(2);
                    }

                    if (data.velocity) {
                        this.velLinear.textContent = data.velocity.linear.toFixed(2);
                        this.velAngular.textContent = data.velocity.angular.toFixed(2);
                    }

                    this.connectionStatus.textContent = 'Connected';
                    this.connectionStatus.className = 'connection-status connected';
                } catch (error) {
                    this.connectionStatus.textContent = 'Disconnected';
                    this.connectionStatus.className = 'connection-status disconnected';
                }
            }

            async updateCamera() {
                try {
                    const response = await fetch('/api/camera');
                    const data = await response.json();

                    if (data.image) {
                        this.cameraFeed.src = data.image;
                    }

                    this.cameraFps.textContent = data.fps || 0;
                } catch (error) {
                    console.error('Error updating camera:', error);
                }
            }

            startUpdateLoop() {
                setInterval(() => {
                    this.updateStatus();
                    this.updateCamera();
                }, 100);
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            new RobotController();
        });
    </script>
</body>
</html>'''

    def run_web_server(self):
        handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, robot_server=self, **kwargs)
        with socketserver.TCPServer(("", 8080), handler) as httpd:
            self.get_logger().info("Web server running on http://0.0.0.0:8080")
            httpd.serve_forever()

def main(args=None):
    rclpy.init(args=args)
    
    try:
        web_server = RobotWebServer()
        rclpy.spin(web_server)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
