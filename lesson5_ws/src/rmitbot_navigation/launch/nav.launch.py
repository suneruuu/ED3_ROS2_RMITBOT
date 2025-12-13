import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch.actions import IncludeLaunchDescription, ExecuteProcess, TimerAction
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node 


def generate_launch_description():
    
    nav_pkg_path = get_package_share_directory("rmitbot_navigation")
    nav_config_file = os.path.join(nav_pkg_path, 'config', 'nav2_params.yaml')

    
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('nav2_bringup'),
                'launch',
                'navigation_launch.py'
            ])
        ),
        launch_arguments={
            'use_sim_time': True,
            'params_file': nav_config_file,
            # 'autostart': 'False',
            # 'use_composition': 'True',
        }.items(), 
    )
    
    nav2_planner = Node(
        package=    'nav2_planner',
        executable= 'planner_server',
        name=       'planner_server',
        output=     'screen',
        parameters=[{'use_sim_time': True}, nav_config_file]
    )
    
    nav2_controller = Node(
        package=    'nav2_controller',
        executable= 'controller_server',
        name=       'controller_server',
        output=     'screen',
        parameters=[{'use_sim_time': True}, nav_config_file], 
        remappings=[('/cmd_vel', '/cmd_vel_navigation_unstamped')]
        )
        
    nav2_bt_navigator = Node(
        package=    'nav2_bt_navigator',
        executable= 'bt_navigator',
        name=       'bt_navigator',
        output=     'screen',
        parameters=[{'use_sim_time': True}, nav_config_file]
        )
    
    nav2_behavior_server = Node(
        package=    'nav2_behaviors',
        executable= 'behavior_server',
        name=       'behavior_server',
        output=     'screen',
        parameters=[{'use_sim_time': True}, nav_config_file], 
        remappings=[('/cmd_vel', '/cmd_vel_bt_server')]
        )
    
    nav2_smoother_server = Node(
        package=    'nav2_smoother',
        executable= 'smoother_server',
        name=       'smoother_server',
        output=     'screen',
        parameters=[{'use_sim_time': True}, nav_config_file]
    )
    
    nav2_lifecycle_manager = Node(
        package=    'nav2_lifecycle_manager',
        executable= 'lifecycle_manager',
        name=       'lifecycle_manager_navigation',
        output=     'screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': [
                'planner_server',
                'controller_server',
                'bt_navigator', 
                'behavior_server', 
                'smoother_server', 
                ]
            }]
        )
    
    return LaunchDescription([
        # nav2_launch, 
        nav2_planner, 
        nav2_controller,
        nav2_bt_navigator, 
        nav2_behavior_server,
        nav2_smoother_server, 
        nav2_lifecycle_manager, 
        ])


    