import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    # Declare launch argument for simulation/real robot mode
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true, real time if false'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        use_sim_time_arg,

        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            output='screen',
            parameters=[{
                'serial_port': '/dev/ttyUSB1',
                'frame_id': 'laser_link',
                'angle_compensate': True,
                'scan_mode': 'Standard',
                'use_sim_time': use_sim_time, # This is important for simulation/hardware
            }]
        )
    ])