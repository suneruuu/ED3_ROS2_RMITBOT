# RMIT Robot System - Enhanced Version

Hệ thống robot hoàn chỉnh với các tính năng:
- ✅ AprilTag Vision Detection
- ✅ Robot Localization (EKF)
- ✅ Navigation2 với obstacle avoidance
- ✅ Web Interface điều khiển từ xa
- ✅ Camera Module 3 RPI support
- ✅ Multi-machine setup (RPI5 + Ubuntu PC)

## Cấu trúc Packages

- `rmitbot_description`: URDF, meshes, camera config
- `rmitbot_controller`: Mecanum drive controller
- `rmitbot_firmware`: ESP32 interface
- `rmitbot_mapping`: SLAM với RPLidar A1
- `rmitbot_localization`: EKF sensor fusion
- `rmitbot_navigation`: Navigation2 với twist_mux
- `rmitbot_vision`: AprilTag detection
- `rmitbot_webapp`: Web interface Flask
- `rmitbot_bringup`: Launch files chính

## Setup Hệ thống

### 1. Cài đặt Dependencies

```bash
# ROS2 Jazzy dependencies
sudo apt update
sudo apt install -y \
    ros-jazzy-apriltag-ros \
    ros-jazzy-robot-localization \
    ros-jazzy-nav2-bringup \
    ros-jazzy-slam-toolbox \
    ros-jazzy-twist-mux \
    ros-jazzy-v4l2-camera \
    ros-jazzy-web-video-server \
    ros-jazzy-image-pipeline \
    python3-flask \
    python3-opencv
```

### 2. Build Workspace

```bash
cd /home/crystal/realrobot/lesson8_ws
colcon build --symlink-install
source install/setup.bash
```

### 3. Test System

```bash
# Test cho simulation
./test_system.sh simulation

# Test cho RPI5
./test_system.sh rpi5

# Test cho PC
./test_system.sh pc
```

## Chạy Hệ thống

### Simulation Mode

```bash
source /opt/ros/jazzy/setup.bash
cd ~/realrobot/lesson8_ws
source install/setup.bash

# Option 1: Use easy launcher
./launch_robot.sh simulation

# Option 2: Manual launch with Gazebo environment
QT_QPA_PLATFORM=xcb LIBGL_DRI3_DISABLE=1 GZ_SIM_RENDER_ENGINE=ogre2 \
ros2 launch rmitbot_bringup rmitbot.launch.py use_sim_time:=true

# Option 3: Source environment first
source setup_gazebo_env.sh
ros2 launch rmitbot_bringup rmitbot.launch.py use_sim_time:=true
```

### Real Robot - RPI5 + Ubuntu PC

#### Trên RPI5:

```bash
# Setup network
./setup_ros2_network.sh rpi5 <PC_IP>
source ~/.bashrc

# Launch robot hardware
source /opt/ros/jazzy/setup.bash
cd ~/lesson8_ws
source install/setup.bash
ros2 launch rmitbot_bringup rmitbot_rpi5.launch.py
```

#### Trên Ubuntu PC:

```bash
# Setup network
./setup_ros2_network.sh pc <RPI5_IP>
source ~/.bashrc

# Launch visualization & control
source /opt/ros/jazzy/setup.bash
cd ~/realrobot/lesson8_ws
source install/setup.bash
ros2 launch rmitbot_bringup rmitbot_pc.launch.py
```

## Tính năng chính

### 1. AprilTag Vision
- Detect AprilTag 36h11
- Publish pose estimation
- Camera calibration support

### 2. Robot Localization
- EKF fusion: IMU + Odometry
- Publish /odometry/filtered
- 2D navigation mode

### 3. Navigation2
- SLAM mapping với RPLidar A1
- Autonomous navigation
- Obstacle avoidance
- Goal setting via RViz

### 4. Web Interface
- Remote control via web browser
- Camera streaming with real-time feed
- Robot status monitoring
- Joystick and arrow key controls
- Speed control with adjustable limits
- Mobile-friendly responsive design

**Access Methods:**
- From same device: `http://localhost:8080`
- From other devices: `./get_ip.sh` to get IP, then `http://YOUR_IP:8080`
- RPI5: `http://RPI5_IP:8080`
- PC: `http://PC_IP:8080` (when running PC launch file)

### 5. Multi-machine Setup
- RPI5: Hardware control, sensors, camera
- Ubuntu PC: Visualization, navigation planning
- ROS2 network communication

## Troubleshooting

### Camera không hoạt động
```bash
# Kiểm tra camera device
ls /dev/video*
v4l2-ctl --list-devices

# Test camera
ros2 run v4l2_camera v4l2_camera_node
```

### ROS2 network không kết nối
```bash
# Kiểm tra network config
echo $ROS_DOMAIN_ID
ros2 topic list
ros2 node list

# Reset network config
./setup_ros2_network.sh <mode> <remote_ip>
```

### Build errors
```bash
# Clean build
rm -rf build/ install/ log/
colcon build --symlink-install

# Check dependencies
rosdep install --from-paths src --ignore-src -r -y
```

## Hardware Requirements

### RPI5:
- Raspberry Pi 5
- Camera Module 3
- RPLidar A1
- ESP32 với mecanum wheels
- IMU sensor

### Ubuntu PC:
- Ubuntu 22.04 + ROS2 Jazzy
- WiFi connection to RPI5
- Sufficient RAM for RViz + Navigation

## Web Interface Features

- 🎮 Joystick control
- 📹 Live camera feed
- 🗺️ Map visualization
- 📊 Robot status
- 🎯 Goal setting
- 📱 Mobile responsive
