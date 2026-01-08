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

    # Launch the controller manager (motor control, IMU, odometry)
    controller = IncludeLaunchDescription(
        os.path.join(pkg_path_controller, "launch", "controller.launch.py"),
    )
    
    # Launch the localization (EKF sensor fusion)
    localization = IncludeLaunchDescription(
        os.path.join(pkg_path_localization, "launch", "localization.launch.py"),
    )
    
    # RPI launches: controller, localization
    # PC launches:  display, teleopkeyboard (via rmitbot.launch.py)
    return LaunchDescription([
        controller,
        localization,
    ])
