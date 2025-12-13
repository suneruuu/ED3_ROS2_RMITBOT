import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, RegisterEventHandler, ExecuteProcess
from ament_index_python.packages import get_package_share_directory
from launch.event_handlers import OnProcessExit

# Launch the file
# ros2 launch rmitbot_bringup rmitbot.launch.py

def generate_launch_description():

    # Path to the package 
    pkg_path_description =  get_package_share_directory("rmitbot_description")
    pkg_path_controller =   get_package_share_directory("rmitbot_controller")
    pkg_path_localization = get_package_share_directory("rmitbot_localization")
    pkg_path_mapping = get_package_share_directory("rmitbot_mapping")
    pkg_path_navigation = get_package_share_directory("rmitbot_navigation")

    # Launch rviz
    display = IncludeLaunchDescription(
        os.path.join(pkg_path_description,"launch","display.launch.py"),
    )
    
    # Launch gazebo
    gazebo = IncludeLaunchDescription(
        os.path.join(pkg_path_description, "launch", "gazebo.launch.py"),
    )
    
    # Launch the controller manager
    controller = IncludeLaunchDescription(
        os.path.join(pkg_path_controller,"launch","controller.launch.py"),
    )
    
    # Launch the controller manager 3s after gazebo, to make sure the robot has spawned in simulation
    controller_delayed = TimerAction(
        period = 3., 
        actions=[controller]
    )
        
    # Launch ekf node
    localization = IncludeLaunchDescription(
        os.path.join(pkg_path_localization,"launch","localization.launch.py"),
    )
    
    # Launch the mapping node
    mapping = IncludeLaunchDescription(
        os.path.join(pkg_path_mapping,"launch","mapping.launch.py"),
    )
        
    # Launch the twistmux instead of keyboard node only
    twistmux = IncludeLaunchDescription(
        os.path.join(pkg_path_navigation,"launch","twistmux.launch.py"),
    )

    
    navigation = IncludeLaunchDescription(
        os.path.join(pkg_path_navigation,"launch","nav.launch.py"),
    )
    
    # Launch the navigation 10s after slamtoolbox, to make sure that a map is available
    navigation_delayed = TimerAction(
        period = 10., 
        actions=[navigation]
    )
    
    return LaunchDescription([
        display, 
        gazebo,
        controller_delayed, 
        twistmux,
        localization, 
        mapping, 
        navigation_delayed, 
    ])