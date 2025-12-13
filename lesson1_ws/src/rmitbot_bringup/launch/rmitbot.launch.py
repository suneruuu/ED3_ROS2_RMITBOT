import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from ament_index_python.packages import get_package_share_directory

# Launch the file
# ros2 launch rmitbot_bringup rmitbot.launch.py

def generate_launch_description():
    
    # Path to the package description
    pkg_path_description = get_package_share_directory("rmitbot_description")
    
    # Launch display.lauch.py
    display = IncludeLaunchDescription(
        os.path.join(pkg_path_description, "launch","display.launch.py"),
    )
    
    # Launch gazebo.lauch.py
    gazebo = IncludeLaunchDescription(
        os.path.join(pkg_path_description, "launch", "gazebo.launch.py"),
    )
    
    return LaunchDescription([
        display, 
        gazebo,
    ])