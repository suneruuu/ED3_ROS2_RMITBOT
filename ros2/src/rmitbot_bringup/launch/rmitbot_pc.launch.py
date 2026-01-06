#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess, DeclareLaunchArgument
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration

# Launch file specifically for Ubuntu PC (connects to RPI5 via ROS2 network)
# ros2 launch rmitbot_bringup rmitbot_pc.launch.py

def generate_launch_description():

    # Declare launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true, real time if false'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')

    # Launch rviz - for visualization
    display = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_description"),
            "launch", "display.launch.py"
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

    # Launch navigation in new Xterm terminal
    nav2_in_new_terminal = ExecuteProcess(
        cmd=['xterm', '-hold', '-e', 'bash', '-lc',
             'source /home/crystal/realrobot/lesson8_ws/install/setup.bash; '
             'export QT_QPA_PLATFORM=xcb; export LIBGL_DRI3_DISABLE=1; export GZ_SIM_RENDER_ENGINE=ogre2; '
             'ros2 launch rmitbot_navigation nav.launch.py use_sim_time:=false']
    )

    # Launch the navigation 10s after slamtoolbox, to make sure that a map is available
    navigation_delayed = TimerAction(
        period = 10.,
        actions=[nav2_in_new_terminal]
    )

    # Web server for PC access
    web_server = Node(
        package='rmitbot_webapp',
        executable='web_server',
        name='robot_web_server',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )

    # Launch monitoring bash terminal
    monitor_terminal = ExecuteProcess(
        cmd=['xterm', '-hold', '-e', 'bash', '-lc',
             'source /home/crystal/realrobot/lesson8_ws/install/setup.bash; '
             'export QT_QPA_PLATFORM=xcb; export LIBGL_DRI3_DISABLE=1; export GZ_SIM_RENDER_ENGINE=ogre2; '
             'echo "🤖 RMIT Robot System Monitor - PC Side"; '
             'echo "====================================="; '
             'echo "Available commands:"; '
             'echo "  ros2 topic list"; '
             'echo "  ros2 topic echo /scan"; '
             'echo "  ros2 topic echo /odom"; '
             'echo "  ros2 topic echo /cmd_vel"; '
             'echo "  ros2 node list"; '
             'echo "  ros2 service list"; '
             'echo "  rviz2"; '
             'echo ""; '
             'echo "Web Interface: http://localhost:8080 (PC)"; '
             'echo "Web Interface: http://RPI5_IP:8080 (RPI5)"; '
             'echo "====================================="; '
             'bash']
    )

    return LaunchDescription([
        use_sim_time_arg,

        # Visualization and control (PC specific)
        display,

        # Twist mux for command multiplexing
        twistmux,

        # SLAM mapping
        mapping,

        # Navigation (delayed to ensure map is available)
        navigation_delayed,

        # Web server for PC access
        # web_server,

        # Monitoring terminal
        monitor_terminal,
    ])
