import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'line_follower_pkg'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='7-Zone Camera Line Follower',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_publisher = line_follower_pkg.camera_publisher:main',
            'virtual_sensor_node = line_follower_pkg.virtual_sensor_node:main',
            'line_follower_controller = line_follower_pkg.line_follower_controller:main',
        ],
    },
)
