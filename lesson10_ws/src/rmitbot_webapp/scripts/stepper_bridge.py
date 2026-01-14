#!/usr/bin/env python3
"""
Stepper Motor Serial Bridge Node

This node subscribes to /stepper_motor/command and forwards commands
to the ESP32 stepper motor controller via serial port.

Commands:
  'a' - Spin anticlockwise (CCW)
  'b' - Spin clockwise (CW)  
  'c' - Enable torque hold
  'o' - Stop motor (no power)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import serial.tools.list_ports


class StepperBridgeNode(Node):
    def __init__(self):
        super().__init__('stepper_bridge_node')
        
        # Declare parameters
        self.declare_parameter('serial_port', '')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('auto_detect', True)
        
        # Get parameters
        self.serial_port = self.get_parameter('serial_port').get_parameter_value().string_value
        self.baud_rate = self.get_parameter('baud_rate').get_parameter_value().integer_value
        self.auto_detect = self.get_parameter('auto_detect').get_parameter_value().bool_value
        
        # Serial connection
        self.serial_conn = None
        
        # Create subscriber
        self.subscription = self.create_subscription(
            String,
            '/stepper_motor/command',
            self.command_callback,
            10
        )
        
        # Status publisher (create BEFORE connect_serial)
        self.status_pub = self.create_publisher(String, '/stepper_motor/status', 10)
        
        # Try to connect to serial port
        self.connect_serial()
        
        # Timer to check serial connection
        self.timer = self.create_timer(5.0, self.check_connection)
        
        self.get_logger().info('Stepper Bridge Node started')
        self.get_logger().info(f'Subscribing to: /stepper_motor/command')
        
    def find_esp32_port(self):
        """Auto-detect ESP32 serial port"""
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # Common ESP32 identifiers
            if 'CP210' in port.description or 'CH340' in port.description or \
               'USB' in port.description or 'Serial' in port.description:
                self.get_logger().info(f'Found potential ESP32 at {port.device}: {port.description}')
                return port.device
                
            # Check by VID/PID for common ESP32 USB chips
            if port.vid == 0x10C4 or port.vid == 0x1A86 or port.vid == 0x303A:
                self.get_logger().info(f'Found ESP32 by VID at {port.device}')
                return port.device
        
        # List all available ports for debugging
        self.get_logger().warn('Could not auto-detect ESP32. Available ports:')
        for port in ports:
            self.get_logger().warn(f'  {port.device}: {port.description} (VID:{port.vid}, PID:{port.pid})')
        
        return None
    
    def connect_serial(self):
        """Connect to the ESP32 serial port"""
        import time
        try:
            # Auto-detect if no port specified
            if not self.serial_port and self.auto_detect:
                self.serial_port = self.find_esp32_port()
                
            if not self.serial_port:
                self.get_logger().error('No serial port found. Set serial_port parameter or connect ESP32.')
                return False
                
            self.get_logger().info(f'Connecting to {self.serial_port} at {self.baud_rate} baud...')
            
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=1.0,
                dsrdtr=False,  # Don't use DTR/DSR flow control
                rtscts=False,  # Don't use RTS/CTS flow control
            )
            
            # Wait for ESP32 to boot after serial connection (DTR reset)
            self.get_logger().info('Waiting for ESP32 to boot...')
            time.sleep(2.0)
            
            # Clear any boot messages from buffer
            self.serial_conn.reset_input_buffer()
            
            self.get_logger().info(f'Connected to stepper motor ESP32 on {self.serial_port}')
            self.publish_status('connected')
            return True
            
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to connect to serial port: {e}')
            self.serial_conn = None
            self.publish_status('disconnected')
            return False
    
    def check_connection(self):
        """Periodically check and reconnect serial if needed"""
        if self.serial_conn is None or not self.serial_conn.is_open:
            self.get_logger().warn('Serial connection lost. Attempting to reconnect...')
            self.serial_port = ''  # Reset to trigger auto-detect
            self.connect_serial()
    
    def command_callback(self, msg):
        """Handle incoming stepper motor commands"""
        command = msg.data.strip().lower()
        
        valid_commands = ['a', 'b', 'c', 'o']
        
        if command not in valid_commands:
            self.get_logger().warn(f'Invalid command: {command}. Use a/b/c/o')
            return
            
        if self.serial_conn is None or not self.serial_conn.is_open:
            self.get_logger().error('Serial not connected. Cannot send command.')
            self.publish_status('disconnected')
            return
        
        try:
            # Send command to ESP32
            self.serial_conn.write(f'{command}\n'.encode())
            self.get_logger().info(f'Sent command: {command}')
            
            # Publish status
            status_map = {
                'a': 'spinning_ccw',
                'b': 'spinning_cw',
                'c': 'holding',
                'o': 'stopped'
            }
            self.publish_status(status_map.get(command, 'unknown'))
            
        except serial.SerialException as e:
            self.get_logger().error(f'Serial write error: {e}')
            self.serial_conn = None
            self.publish_status('error')
    
    def publish_status(self, status):
        """Publish stepper motor status"""
        msg = String()
        msg.data = status
        self.status_pub.publish(msg)
    
    def destroy_node(self):
        """Clean up on shutdown"""
        if self.serial_conn and self.serial_conn.is_open:
            # Stop motor before disconnecting
            try:
                self.serial_conn.write(b'o\n')
                self.serial_conn.close()
            except:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    node = StepperBridgeNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
