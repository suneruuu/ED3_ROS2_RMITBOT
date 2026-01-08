import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from ament_index_python.packages import get_package_share_directory

# Launch the file on Raspberry Pi
# ros2 launch rmitbot_bringup rpi.launch.py

def generate_launch_description():
    
    # Path to the packages
    pkg_path_controller = get_package_share_directory("rmitbot_controller")
    pkg_path_localization = get_package_share_directory("rmitbot_localization")
    pkg_path_mapping = get_package_share_directory("rmitbot_mapping")
    
    # Launch the controller manager (ros2_control with hardware interface)
    controller = IncludeLaunchDescription(
        os.path.join(pkg_path_controller, "launch", "controller.launch.py"),
    )
    
    # Launch the localization node (robot_localization EKF)
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
    
    # Launch the slamtoolbox for mapping
    slamtoolbox = IncludeLaunchDescription(
        os.path.join(pkg_path_mapping, "launch", "mapping.launch.py"),
        launch_arguments={
            "use_sim_time": "False"
        }.items()
    )
    
    # RPI nodes: controller, localization, rplidar, slamtoolbox
    return LaunchDescription([
        controller,
        localization,
        rplidar,
        slamtoolbox,
    ])
