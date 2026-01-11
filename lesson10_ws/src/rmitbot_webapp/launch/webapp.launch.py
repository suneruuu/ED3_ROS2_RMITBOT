import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    
    pkg_path = get_package_share_directory("rmitbot_webapp")
    www_path = os.path.join(pkg_path, 'www')
    
    # Rosbridge WebSocket server on port 9090
    # Allow CORS from teamb.quykhang.cloud for remote web app access
    rosbridge_server = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        parameters=[{
            'port': 9090,
            'use_sim_time': False,
            'origins': ['https://teamb.quykhang.cloud', 'http://teamb.quykhang.cloud'],
        }],
        output='screen',
    )
    
    # Simple HTTP server to serve the webapp
    http_server = ExecuteProcess(
        cmd=['python3', '-m', 'http.server', '8000', '--directory', www_path],
        output='screen',
        name='http_server',
    )
    
    # CORS proxy for camera (proxies 8081 -> 8080 with CORS headers)
    camera_proxy_script = os.path.join(pkg_path, 'scripts', 'camera_proxy.py')
    
    camera_proxy = ExecuteProcess(
        cmd=['python3', camera_proxy_script],
        output='screen',
        name='camera_cors_proxy',
    )
    
    # Web video server to stream camera feed on port 8080
    web_video_server = Node(
        package='web_video_server',
        executable='web_video_server',
        name='web_video_server',
        parameters=[{
            'port': 8080,
            'ros_threads': 2,
        }],
        output='screen',
    )
    
    return LaunchDescription([
        rosbridge_server,
        http_server,
        web_video_server,
        camera_proxy,
    ])
