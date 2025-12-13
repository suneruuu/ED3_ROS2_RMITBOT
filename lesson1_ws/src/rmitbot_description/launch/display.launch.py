import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from ament_index_python.packages import get_package_share_directory
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command, LaunchConfiguration

# Launch the file
# ros2 launch rmitbot_description display.launch.py

def generate_launch_description():
    # Path to the package
    pkg_path_description = get_package_share_directory("rmitbot_description")
    urdf_path = os.path.join(pkg_path_description, 'urdf', 'rmitbot.urdf.xacro')
    # Compile the xacro to urdf
    robot_description = ParameterValue(Command(['xacro ', urdf_path]), value_type=str)
    # Publish the robot static TF from the urdf
    robot_state_publisher = Node(
        package=    'robot_state_publisher',
        executable= 'robot_state_publisher',
        parameters=[{"robot_description": robot_description}]
        )
    
    # Publish the joint state TF
    joint_state_publisher_gui = Node(
        package=    'joint_state_publisher_gui',
        executable= 'joint_state_publisher_gui',
    )
    
    # Path to the rviz config file
    rviz_path = os.path.join(pkg_path_description, 'rviz', 'display.rviz')
    # This node launches RViz2 with the specified configuration file
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_path],
    )
    
    return LaunchDescription([
        robot_state_publisher, 
        joint_state_publisher_gui,
        rviz, 
    ])