import os 
from ament_index_python.packages import get_package_share_directory 
from launch import LaunchDescription 
from launch.actions import DeclareLaunchArgument, LogInfo 
from launch_ros.actions import Node 
from launch.substitutions import LaunchConfiguration 

def generate_launch_description():
    # Declare launch argument for simulation/real robot mode
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time if true, real time if false'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')

    image_proc_node = Node(
        package="image_proc",
        executable="rectify_node",
        name="rectify_node",
        # namespace="camera",   # so it uses /camera/image and /camera/camera_info
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
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
            {"use_sim_time": use_sim_time},
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
        use_sim_time_arg,
        # image_proc_node,
        apriltag_node,
    ])


    
