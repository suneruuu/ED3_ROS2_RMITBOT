from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'rmitbot_webapp'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'templates'), glob('rmitbot_webapp/templates/*')),
        (os.path.join('share', package_name, 'static'), glob('rmitbot_webapp/static/*')),
    ],
    install_requires=[
        'setuptools',
        'flask',
        'flask-socketio',
        'eventlet',
        'opencv-python',
        'cv-bridge',
    ],
    zip_safe=True,
    maintainer='crystal',
    maintainer_email='crystal@todo.todo',
    description='RMIT Robot Web Interface',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'web_server = rmitbot_webapp.web_server:main',
        ],
    },
)
