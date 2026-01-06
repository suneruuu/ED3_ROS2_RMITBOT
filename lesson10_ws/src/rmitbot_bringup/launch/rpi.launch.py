import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from ament_index_python.packages import get_package_share_directory

# Launch the file on RPI
# ros2 launch rmitbot_bringup rmitbot_rpi.launch.py

def generate_launch_description():
    
    # Path to the packages
    pkg_path_controller =   get_package_share_directory("rmitbot_controller")
    pkg_path_localization = get_package_share_directory("rmitbot_localization")
    pkg_path_mapping = get_package_share_directory("rmitbot_mapping")
    
    # Launch the controller manager
    controller = IncludeLaunchDescription(
        os.path.join(pkg_path_controller, "launch", "controller.launch.py"),
    )
        
    # Launch ekf node for localization
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
    
    # Launch the mapping node (SLAM)
    mapping = IncludeLaunchDescription(
        os.path.join(pkg_path_mapping, "launch", "mapping.launch.py"),
    )
    
    # RPI: controller, localization, rplidar, mapping
    return LaunchDescription([
        controller,
        localization,
        rplidar,
        mapping,
    ])
