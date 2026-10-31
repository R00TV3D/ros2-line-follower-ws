import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    pkg_name = 'line_follower_pkg'
    pkg_share = get_package_share_directory(pkg_name)

    world_arg = DeclareLaunchArgument(
        'world',
        default_value='final_grading.sdf',
        description='Name of the SDF world file in the worlds directory'
    )

    world_file = LaunchConfiguration('world')
    world_path = PathJoinSubstitution([pkg_share, 'worlds', world_file])

    # 1. Start Gazebo Sim
    start_gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_path],
        output='screen'
    )

    # 2. Start Ros-GZ Image Bridge (Camera: Gazebo -> ROS 2)
    image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=['/camera/image_raw'],
        output='screen'
    )

    # 3. CRITICAL FIX: Start Parameter Bridge for /cmd_vel (ROS 2 -> Gazebo)
    cmd_vel_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry'
        ],
        output='screen'
    )

    # 4. Start Virtual Sensor Node
    virtual_sensor_node = TimerAction(
        period=3.0,
        actions=[
            Node(
                package=pkg_name,
                executable='virtual_sensor_node',
                output='screen'
            )
        ]
    )

    # 5. Start Line Follower Controller
    controller_node = TimerAction(
        period=5.0,
        actions=[
            Node(
                package=pkg_name,
                executable='line_follower_controller',
                output='screen'
            )
        ]
    )

    return LaunchDescription([
        world_arg,
        start_gazebo,
        image_bridge,
        cmd_vel_bridge,
        virtual_sensor_node,
        controller_node,
    ])