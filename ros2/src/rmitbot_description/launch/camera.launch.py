#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition, UnlessCondition
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Declare launch argument for simulation/real robot mode
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time if true, real time if false'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')

    # Camera node for RPI5 Camera Module 3 (only for real robot)
    # Using wrapper script to avoid logging issues
    camera_wrapper_script = os.path.join(
        get_package_share_directory('rmitbot_description'),
        'scripts',
        'camera_node_wrapper.sh'
    )

    rpi_camera_node = ExecuteProcess(
        cmd=[
            camera_wrapper_script,
            '--ros-args',
            '-r', '__node:=camera',
            '-p', 'role:=viewfinder',
            '-p', 'width:=640',
            '-p', 'height:=480',
            '-p', 'format:=YUYV',
            '-p', 'camera_frame_id:=camera_link_optical'
        ],
        output='screen',
        condition=UnlessCondition(use_sim_time)
    )

    # Camera info publisher for simulation (Gazebo already provides camera)
    # No additional camera node needed for simulation as it's handled by Gazebo

    return LaunchDescription([
        use_sim_time_arg,
        rpi_camera_node,
    ])
