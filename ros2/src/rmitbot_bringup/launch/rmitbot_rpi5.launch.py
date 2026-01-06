#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess, DeclareLaunchArgument
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration

# Launch file specifically for RPI5
# ros2 launch rmitbot_bringup rmitbot_rpi5.launch.py

def generate_launch_description():

    # Declare launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true, real time if false'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')

    # Launch hardware - mandatory for RPI5
    hardware = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_firmware"),
            "launch", "hardware.launch.py"
        ),
    )

    # Launch the controller manager spawner
    controller = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_controller"),
            "launch", "controller.launch.py"
        ),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items()
    )

    # Launch the controller manager 3s after hardware
    controller_delayed = TimerAction(
        period = 3.,
        actions=[controller]
    )

    # Launch the rplidar hardware
    rplidar = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_mapping"),
            "launch", "rplidar.launch.py"
        ),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items()
    )

    # Launch camera (RPI5 Camera Module 3)
    camera = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_description"),
            "launch",
            "camera.launch.py"
        ),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items()
    )

    # Launch localization (EKF)
    localization = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_localization"),
            "launch",
            "localization.launch.py"
        ),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items()
    )

    # Launch vision (AprilTag detection)
    vision = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_vision"),
            "launch",
            "apriltag.launch.py"
        ),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items()
    )

    # Launch the twistmux for command multiplexing
    twistmux = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_navigation"),
            "launch",
            "twistmux.launch.py"
        ),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items()
    )

    # Launch the mapping node
    mapping = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_mapping"),
            "launch",
            "slam.launch.py"
        ),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items()
    )

    # Launch web interface
    webapp = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_webapp"),
            "launch",
            "webapp.launch.py"
        ),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items()
    )

    return LaunchDescription([
        use_sim_time_arg,

        # Hardware components (RPI5 specific)
        hardware,
        rplidar,
        camera,

        # Controller (delayed to ensure hardware is ready)
        controller_delayed,

        # Twist mux for command multiplexing
        twistmux,

        # Localization (EKF)
        localization,

        # SLAM mapping
        mapping,

        # Vision (AprilTag detection)
        vision,

        # Web interface
        webapp,
    ])
