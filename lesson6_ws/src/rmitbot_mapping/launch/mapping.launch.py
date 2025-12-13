import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription

# ros2 launch rmitbot_mapping slam.launch.py use_sim_time:=true
# ros2 launch rmitbot_mapping slam.launch.py use_sim_time:=false
# Command line
# ros2 launch slam_toolbox online_async_launch.py params_file:=./scr/rmitbot_mapping/config/slam.yaml use_sim_time:=true

pkg_path_slam_toolbox = get_package_share_directory("slam_toolbox")
pkg_path_mapping = get_package_share_directory("rmitbot_mapping")
config_mapping =   os.path.join(pkg_path_mapping, 'config', 'slam.yaml')

def generate_launch_description():
    
    slam_mapping = IncludeLaunchDescription(
        os.path.join(pkg_path_slam_toolbox,"launch","online_async_launch.py"),
        launch_arguments={
            'params_file': config_mapping,             
            'use_sim_time': "true", 
            }.items()
    )
    
    return LaunchDescription([
        slam_mapping,
    ])
    