import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    pkg = get_package_share_directory('warehouse_amr')
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    world_file = os.path.join(pkg, 'worlds', 'no_roof_small_warehouse.world')
    urdf_file = os.path.join(pkg, 'urdf', 'warehouse_amr.urdf.xacro')
    robot_description = ParameterValue(Command(['xacro ', urdf_file]), value_type=str)

    gazebo = ExecuteProcess(
        cmd=['ign', 'gazebo', '-r', world_file],
        output='screen'
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'warehouse_amr', '-topic', 'robot_description',
                   '-x', '0.0', '-y', '0.0', '-z', '0.1'],
        output='screen'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': use_sim_time}],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': os.path.join(pkg, 'config', 'bridge.yaml'),
                     'use_sim_time': use_sim_time}],
        output='screen'
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    map_to_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    lidar_frame_alias = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'lidar_link', 'warehouse_amr/base_footprint/lidar'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    depth_camera_frame_alias = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=['0', '0', '0', '-1.5707', '0', '-1.5707', 'depth_camera_link', 'warehouse_amr/base_footprint/depth_camera'],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen"
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        gazebo,
        robot_state_publisher,
        spawn_robot,
        bridge,
        map_to_odom,
        lidar_frame_alias,
        depth_camera_frame_alias,
        rviz,
    ])
