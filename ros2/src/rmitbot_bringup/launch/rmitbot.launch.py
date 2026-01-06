import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, RegisterEventHandler, ExecuteProcess, DeclareLaunchArgument
from ament_index_python.packages import get_package_share_directory
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition

# Launch the file
# For simulation: ros2 launch rmitbot_bringup rmitbot.launch.py use_sim_time:=true
# For real robot: ros2 launch rmitbot_bringup rmitbot.launch.py use_sim_time:=false
# For RPI5: ros2 launch rmitbot_bringup rmitbot.launch.py use_sim_time:=false robot_mode:=rpi5
# For Ubuntu PC: ros2 launch rmitbot_bringup rmitbot.launch.py use_sim_time:=false robot_mode:=pc

def generate_launch_description():

    # Declare launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time if true, real time if false'
    )

    robot_mode_arg = DeclareLaunchArgument(
        'robot_mode',
        default_value='simulation',
        description='Robot mode: simulation, rpi5, or pc'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_mode = LaunchConfiguration('robot_mode')

    # Launch rviz - always available
    display = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_description"),
            "launch", "display.launch.py"
        ),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items()
    )

    # Launch gazebo - only for simulation
    gazebo = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_description"),
            "launch", "gazebo.launch.py"
        ),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items(),
        condition=IfCondition(use_sim_time)
    )

    # Launch hardware - only for real robot (RPI5)
    hardware = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_firmware"),
            "launch", "hardware.launch.py"
        ),
        condition=UnlessCondition(use_sim_time)
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

    # Launch the controller manager 3s after gazebo/hardware, to make sure the robot has spawned
    controller_delayed = TimerAction(
        period = 3.,
        actions=[controller]
    )

    # Launch the twistmux instead of keyboard node only (for navigation)
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

    # Launch the rplidar hardware (for real robot)
    rplidar = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rmitbot_mapping"),
            "launch", "rplidar.launch.py"
        ),
        launch_arguments={
            "use_sim_time": use_sim_time
        }.items(),
        condition=UnlessCondition(use_sim_time)
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
             f'ros2 launch rmitbot_navigation nav.launch.py use_sim_time:={use_sim_time}']
    )

    # Launch the navigation 10s after slamtoolbox, to make sure that a map is available
    navigation_delayed = TimerAction(
        period = 10.,
        actions=[nav2_in_new_terminal]
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

    # Launch vision (AprilTag detection) - DISABLED
    # vision = IncludeLaunchDescription(
    #     os.path.join(
    #         get_package_share_directory("rmitbot_vision"),
    #         "launch",
    #         "apriltag.launch.py"
    #     ),
    #     launch_arguments={
    #         "use_sim_time": use_sim_time
    #     }.items()
    # )

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

    # Launch monitoring bash terminal
    monitor_terminal = ExecuteProcess(
        cmd=['xterm', '-hold', '-e', 'bash', '-lc',
             'source /home/crystal/realrobot/lesson8_ws/install/setup.bash; '
             'export QT_QPA_PLATFORM=xcb; export LIBGL_DRI3_DISABLE=1; export GZ_SIM_RENDER_ENGINE=ogre2; '
             'echo "🤖 RMIT Robot System Monitor"; '
             'echo "================================"; '
             'echo "Available commands:"; '
             'echo "  ros2 topic list"; '
             'echo "  ros2 topic echo /scan"; '
             'echo "  ros2 topic echo /odom"; '
             'echo "  ros2 topic echo /cmd_vel"; '
             'echo "  ros2 node list"; '
             'echo "  ros2 service list"; '
             'echo "  rviz2"; '
             'echo ""; '
             'echo "Web Interface: http://localhost:8080"; '
             'echo "================================"; '
             'bash']
    )

    return LaunchDescription([
        use_sim_time_arg,
        robot_mode_arg,

        # Core components (always launched)
        display,

        # Conditional launches based on use_sim_time
        gazebo,      # Only for simulation
        hardware,    # Only for real robot

        # Controller (delayed to ensure robot is spawned)
        controller_delayed,

        # Twist mux for command multiplexing
        twistmux,

        # Localization (EKF)
        localization,

        # Hardware-specific components
        rplidar,     # Only for real robot

        # SLAM mapping
        mapping,

        # Navigation (delayed to ensure map is available)
        navigation_delayed,

        # Camera (RPI5 Camera Module 3)
        camera,

        # Vision (AprilTag detection) - DISABLED
        # vision,

        # Web interface
        webapp,

        # Monitoring terminal
        monitor_terminal,
    ])