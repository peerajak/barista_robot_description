#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_prefix
import random
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch import LaunchDescription
import xacro
from launch_ros.parameter_descriptions import ParameterValue
def generate_launch_description():

    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    pkg_barista_robot_gazebo = get_package_share_directory('barista_robot_gazebo')
    pkg_barista_robot_description= get_package_share_directory('barista_robot_description')
    # We get the whole install dir
    # We do this to avoid having to copy or softlink manually the packages so that gazebo can find them
    description_package_name = "barista_robot_description"
    install_dir = get_package_prefix(description_package_name)
    model_arg = DeclareLaunchArgument(name="model", default_value=os.path.join(
                                        pkg_barista_robot_description, "urdf", "barista_robot_model_ign.urdf.xacro"
                                        ),
                                      description="Absolute path to robot urdf file"
    )
    world_arg = DeclareLaunchArgument(name="world", default_value=os.path.join(
                                        pkg_barista_robot_gazebo, "worlds", "lidar_world.sdf"
                                        ),
                                      description="Absolute path to world sdf files"
    )
    # Set the path to the WORLD model files. Is to find the models inside the models folder in barista_robot_description package
    gazebo_models_path = '/home/peerajak/ros2_ws/install/barista_robot_description/share/'
    # os.environ["GAZEBO_MODEL_PATH"] = gazebo_models_path

    if 'GAZEBO_MODEL_PATH' in os.environ:
        os.environ['GAZEBO_MODEL_PATH'] =  os.environ['GAZEBO_MODEL_PATH'] + ':' + install_dir + '/share' + ':' + gazebo_models_path
    else:
        os.environ['GAZEBO_MODEL_PATH'] =  install_dir + "/share" + ':' + gazebo_models_path

    if 'GAZEBO_PLUGIN_PATH' in os.environ:
        os.environ['GAZEBO_PLUGIN_PATH'] = os.environ['GAZEBO_PLUGIN_PATH'] + ':' + install_dir + '/lib'
    else:
        os.environ['GAZEBO_PLUGIN_PATH'] = install_dir + '/lib'

    os.environ['IGN_GAZEBO_RESOURCE_PATH'] =  install_dir + "/share" + ':' + gazebo_models_path

    

    print("GAZEBO MODELS PATH=="+str(os.environ["GAZEBO_MODEL_PATH"]))
    print("GAZEBO PLUGINS PATH=="+str(os.environ["GAZEBO_PLUGIN_PATH"]))

    # Gazebo ignition launch
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory("ros_gz_sim"), "launch"), "/gz_sim.launch.py"]),
                launch_arguments=[
                    ("gz_args", [" -v 4", " -r ",  "empty.sdf"] #LaunchConfiguration("world"),]
                    )
                ]
             )

    # Spawn ROBOT Set Gazebo
    # Position and orientation
    # [X, Y, Z]
    position = [0.0, 0.0, 0.2]
    # [Roll, Pitch, Yaw]
    orientation = [0.0, 0.0, 0.0]
    # Base Name or robot
    robot_base_name = "barista"
    entity_name = robot_base_name+"-"+str(int(random.random()*100000))
    robot_description = ParameterValue(Command([
            "xacro ",
            LaunchConfiguration("model"),
        ]),
        value_type=str
    )
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=['-entity',
                   entity_name,
                   '-x', str(position[0]), '-y', str(position[1]
                                                     ), '-z', str(position[2]),
                   '-R', str(orientation[0]), '-P', str(orientation[1]
                                                        ), '-Y', str(orientation[2]),
                   '-topic', '/robot_description'
                   ]
    )

    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan"
        ],
        remappings=[
            ('/imu', '/imu/out'),
        ]
    )





    package_description = "barista_robot_description"
    xacro_file = 'barista_robot_model_ign.urdf.xacro'
    xacro_file_with_path = os.path.join(get_package_share_directory(package_description), "urdf", xacro_file)

    # convert XACRO file into URDF
    doc = xacro.parse(open(xacro_file_with_path))
    xacro.process_doc(doc)
    robot_description_params = {'robot_description': doc.toxml(),'use_sim_time': True}

    # Robot State Publisher

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        emulate_tty=True,
        parameters=[{"robot_description": robot_description,"use_sim_time": True}], 
        #parameters=[robot_description_params], 
        output="screen"
    )


    # RVIZ Configuration
    rviz_config_dir = os.path.join(get_package_share_directory(description_package_name), 'rviz', 'rviz_config.rviz')


    rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
            name='rviz_node',
            parameters=[{'use_sim_time': True}],
            arguments=['-d', rviz_config_dir])

    return LaunchDescription([
        model_arg,
        world_arg,
        # DeclareLaunchArgument(
        #   'world',
        #   default_value=[os.path.join(pkg_barista_robot_gazebo, 'worlds', 'empty_world_but_acube_abox.world'), ''],
        #   description='SDF world file'),
        gazebo,
        gz_spawn_entity,
        gz_ros2_bridge,
        robot_state_publisher_node,
        rviz_node,

        
    ])