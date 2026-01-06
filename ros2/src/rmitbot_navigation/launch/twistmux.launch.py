import os 
from ament_index_python.packages import get_package_share_directory 
from launch import LaunchDescription 
from launch.actions import DeclareLaunchArgument, LogInfo 
from launch_ros.actions import Node 
from launch.substitutions import LaunchConfiguration 

# ros2 launch rmitbot_controller twistmux.launch.py 

def generate_launch_description():
    # Declare launch argument for simulation/real robot mode
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time if true, real time if false'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')

    # teleop_keyboard
    teleop_keyboard = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        output='screen',
        prefix='xterm -e',
        parameters=[
            {"use_sim_time": use_sim_time},
            {'stamped': True},
            {'frame_id': 'base_footprint'},],
        remappings=[('cmd_vel', '/cmd_vel_keyboard')],
    )

    # twist_stamper_node: navigation does not have time stamped
    twist_stamper_node = Node(
        package='twist_stamper',
        executable='twist_stamper',
        name='twist_stamper',
        parameters=[
            {'frame_id': 'base_footprint'},
            {"use_sim_time": use_sim_time}, ],
        remappings=[
            # ('/cmd_vel_in', '/cmd_vel_joystick_unstamped'),
            # ('/cmd_vel_out','/cmd_vel_joystick'),
            ('/cmd_vel_in', '/cmd_vel'),
            ('/cmd_vel_out','/cmd_vel_navigation'), ],
    )

    # twist_mux_node: mixing keyboard and navigation
    twistmux_params = os.path.join(get_package_share_directory("rmitbot_navigation"), "config", "twistmux.yaml")
    twistmux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        name='twist_mux_node',
        output='screen',
        parameters=[
            twistmux_params,
            {"use_sim_time": use_sim_time},
        ],
        remappings=[
            ('/cmd_vel_out', '/rmitbot_controller/cmd_vel')],
    )

    return LaunchDescription([
        use_sim_time_arg,
        twistmux_node,
        teleop_keyboard,
        twist_stamper_node,
    ])