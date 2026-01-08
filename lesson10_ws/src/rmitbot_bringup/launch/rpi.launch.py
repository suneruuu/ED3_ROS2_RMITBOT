import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from ament_index_python.packages import get_package_share_directory

# Launch the file on RPI
# ros2 launch rmitbot_bringup rpi.launch.py

def generate_launch_description():
    
    # Path to the packages
    pkg_path_controller = get_package_share_directory("rmitbot_controller")
    pkg_path_localization = get_package_share_directory("rmitbot_localization")
    pkg_path_mapping = get_package_share_directory("rmitbot_mapping")
    pkg_path_webapp = get_package_share_directory("rmitbot_webapp")
    
    # Launch the controller manager
    controller = IncludeLaunchDescription(
        os.path.join(pkg_path_controller, "launch", "controller.launch.py"),
    )
        
    # Launch ekf node
    localization = IncludeLaunchDescription(
        os.path.join(pkg_path_localization, "launch", "localization.launch.py"),
    )
    
    # Launch the rplidar hardware
    rplidar = IncludeLaunchDescription(
        os.path.join(pkg_path_mapping, "launch", "rplidar.launch.py"),
        launch_arguments={
            "use_sim_time": "False"
        }.items()
    )
    
    # Launch the mapping node
    mapping = IncludeLaunchDescription(
        os.path.join(pkg_path_mapping, "launch", "mapping.launch.py"),
    )
    
    # Launch the webapp for web-based teleop control (replaces keyboard teleop)
    webapp = IncludeLaunchDescription(
        os.path.join(pkg_path_webapp, "launch", "webapp.launch.py"),
    )
    
    # Delay rplidar to let controller initialize first
    rplidar_delayed = TimerAction(
        period=5.0,
        actions=[rplidar]
    )
    
    # Delay localization to ensure controller is ready
    localization_delayed = TimerAction(
        period=5.0,
        actions=[localization]
    )
    
    # Delay mapping to ensure rplidar is ready
    mapping_delayed = TimerAction(
        period=5.0,
        actions=[mapping]
    )
    
    # Delay webapp to ensure controller is ready
    webapp_delayed = TimerAction(
        period=5.0,
        actions=[webapp]
    )
    
    return LaunchDescription([
        controller,
        rplidar_delayed,
        localization_delayed,
        mapping_delayed,
        webapp_delayed,
    ])
