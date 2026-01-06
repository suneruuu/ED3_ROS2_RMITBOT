import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Declare launch argument for simulation/real robot mode
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time if true, real time if false'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')

    # Web server node
    web_server_node = Node(
        package='rmitbot_webapp',
        executable='web_server',
        name='robot_web_server',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # Web video server for camera streaming (alternative method)
    web_video_server_node = Node(
        package='web_video_server',
        executable='web_video_server',
        name='web_video_server',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'port': 8081},
            {'server_threads': 1},
        ],
    )

    return LaunchDescription([
        use_sim_time_arg,
        web_server_node,
        # web_video_server_node,  # Optional: uncomment if you want additional video server
    ])
