import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    
    pkg_path = get_package_share_directory("rmitbot_webapp")
    www_path = os.path.join(pkg_path, 'www')
    
    # Rosbridge WebSocket server on port 9090
    rosbridge_server = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        parameters=[{
            'port': 9090,
            'use_sim_time': False,
        }],
        output='screen',
    )
    
    # Simple HTTP server to serve the webapp
    http_server = ExecuteProcess(
        cmd=['python3', '-m', 'http.server', '8000', '--directory', www_path],
        output='screen',
        name='http_server',
    )
    
    return LaunchDescription([
        rosbridge_server,
        http_server,
    ])
