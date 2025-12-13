import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import Command, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

# Launch the file
# ros2 launch rmitbot_description gazebo.launch.py

def generate_launch_description():
    # Path to the package
    pkg_path = get_package_share_directory("rmitbot_description")
    # Path to the world file
    world_path = os.path.join(pkg_path, 'world', 'room_8x8.world')
    
    # Resource path for gazebo. Required while using stl (robot CAD), and sdf (world)
    gz_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=[str(Path(pkg_path).parent.resolve())]
    )

    
    # Launch Gazebo 
    gz_sim = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        [os.path.join(get_package_share_directory("ros_gz_sim"), "launch"), "/gz_sim.launch.py"]),
        launch_arguments={"gz_args": f"-r -v 4 {world_path}"}.items()
    )
    
    # Spawn the robot in Gazebo
    gz_spawn_entity = Node(
        package=    "ros_gz_sim",
        executable= "create",
        output=     "screen",
        arguments=  ["-topic", "robot_description","-name", "rmitbot"],
    )
    
    # Spawn AprilTag
    spawn_tag = Node(
        package=    "ros_gz_sim",
        executable= "create",
        output=     "screen",
        arguments=[
            "-file", os.path.join(pkg_path, "models", "apriltag_36h11_0", "model.sdf"),
            # "-name", "tag0", 
            "-name", "apriltag_36h11_0",
            # "-x", "3.8", "-y", "0", "-z", "0.2",
            # "-R", "0", "-P", "1.5708", "-Y", "0"   # pitch 90° → vertical tag
    ],
)

    # Bridge between ROS2 and Gazebo
    gz_ros2_bridge = Node(
        package=    "ros_gz_bridge",
        executable= "parameter_bridge",
        arguments=[ "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock", 
                    "/imu@sensor_msgs/msg/Imu[gz.msgs.IMU", 
                    "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
                    "/camera/image@sensor_msgs/msg/Image[gz.msgs.Image",
                    "/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo", 
                    ], 
        # remappings=[('/imu', '/imu/out')], 
    )

    return LaunchDescription([
        gz_resource_path,
        gz_sim,
        gz_spawn_entity,
        spawn_tag, 
        gz_ros2_bridge,
    ])