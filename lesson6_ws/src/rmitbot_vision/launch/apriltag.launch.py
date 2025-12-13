import os 
from ament_index_python.packages import get_package_share_directory 
from launch import LaunchDescription 
from launch.actions import DeclareLaunchArgument, LogInfo 
from launch_ros.actions import Node 
from launch.substitutions import LaunchConfiguration 

def generate_launch_description():
    image_proc_node = Node(
        package="image_proc",
        executable="rectify_node",
        name="rectify_node",
        # namespace="camera",   # so it uses /camera/image and /camera/camera_info
        output="screen",
        remappings=[ 
            ('/image', '/camera/image'), 
            ('/camera_info', '/camera/camera_info'), 
            ('/image_rect', '/camera_image_rect'),], 
    )
    
    apriltag_params = os.path.join(get_package_share_directory("rmitbot_vision"), "config", "apriltag_params.yaml") 
    apriltag_node = Node( 
        package='apriltag_ros', 
        executable='apriltag_node', 
        name='apriltag_node', 
        output='screen', 
        parameters=[
            apriltag_params,  
            {"use_sim_time": True},
        ], 
        remappings=[ 
            # ('/image', '/camera/image'), 
            # ('/camera_info', '/camera/camera_info')
            # ("image_rect", "/camera_image_rect"),
            ("image_rect", "/camera/image"),
            ("camera_info", "/camera/camera_info"), 
            ], 
    ) 

    return LaunchDescription([
        # image_proc_node, 
        apriltag_node, 
    ])


    
