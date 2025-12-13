import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, RegisterEventHandler
from ament_index_python.packages import get_package_share_directory
from launch.event_handlers import OnProcessExit

# Launch the file
# ros2 launch rmitbot_bringup rmitbot.launch.py

def generate_launch_description():
    
    # Path to the package description
    pkg_path_description =  get_package_share_directory("rmitbot_description")
    pkg_path_controller =   get_package_share_directory("rmitbot_controller")
    pkg_path_localization = get_package_share_directory("rmitbot_localization")
    
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
    
    # Launch the teleop keyboard node
    teleopkeyboard = IncludeLaunchDescription(
        os.path.join(pkg_path_controller,"launch","teleopkeyboard.launch.py"),
        launch_arguments={"use_sim_time": "True"}.items()
    )

    # Launch ekf node
    localization = IncludeLaunchDescription(
        os.path.join(pkg_path_localization,"launch","localization.launch.py"),
    )
    
    return LaunchDescription([
        display, 
        gazebo,
        controller_delayed, 
        teleopkeyboard,
        localization, 
    ])