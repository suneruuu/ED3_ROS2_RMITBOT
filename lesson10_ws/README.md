# RMITBOT ROS2 Workspace

This workspace contains the ROS2 packages for running the RMITBOT with web-based control, camera streaming, and SLAM mapping.

## Prerequisites

- ROS2 Jazzy
- Required packages:
  - `rosbridge_server`
  - `web_video_server`
  - `rplidar_ros`
  - `slam_toolbox`
  - `robot_localization`
  - `ros2_control`
  - `navigation2`
  - `camera_ros`

## Build the Workspace

```bash
cd ~/ED3_ROS2_RMITBOT/lesson10_ws
colcon build
source install/setup.bash
```

## Running on Raspberry Pi (with Webapp and Camera)

### Option 1: Full RPI Launch (Recommended)

This launches everything: controller, localization, RPLIDAR, SLAM, and webapp.

**Terminal 1 - RPI Launch:**
```bash
cd ~/ED3_ROS2_RMITBOT/lesson10_ws
source install/setup.bash
ros2 launch rmitbot_bringup rpi.launch.py
```

**Terminal 2 - Camera Node:**
```bash
cd ~/ED3_ROS2_RMITBOT/lesson10_ws
source install/setup.bash
ros2 run camera_ros camera_node --ros-args -p width:=320 -p height:=240 -p format:=YUYV
```

### Option 2: Run Components Separately

**Terminal 1 - Controller:**
```bash
ros2 launch rmitbot_controller controller.launch.py
```

**Terminal 2 - Webapp:**
```bash
ros2 launch rmitbot_webapp webapp.launch.py
```

**Terminal 3 - Camera:**
```bash
ros2 run camera_ros camera_node --ros-args -p width:=320 -p height:=240 -p format:=YUYV
```

## Running on PC

Launch RViz, twist_mux, and Nav2 navigation on the PC to visualize and control the robot:

```bash
cd ~/ED3_ROS2_RMITBOT/lesson10_ws
source install/setup.bash
ros2 launch rmitbot_bringup rmitbot.launch.py
```

> **Note:** Ensure the RPI is running `rpi.launch.py` first and both devices are on the same network.

## Accessing the Web Interface

Once launched, access the webapp from any device on the same network:

| Service | URL | Description |
|---------|-----|-------------|
| **Web App** | `http://<RPI_IP>:8000` | Control interface |
| **Camera Stream** | `http://<RPI_IP>:8080/stream?topic=/camera/image_raw` | Live camera feed |
| **Rosbridge** | `ws://<RPI_IP>:9090` | WebSocket for ROS communication |

Replace `<RPI_IP>` with your Raspberry Pi's IP address.

## Troubleshooting

### Port Already in Use Error

If you see `[Errno 98] Address already in use`, kill the existing process:

```bash
# Kill rosbridge_websocket if port 9090 is in use
pkill -f rosbridge_websocket

# Kill web_video_server if port 8080 is in use
pkill -f web_video_server

# Kill http.server if port 8000 is in use
pkill -f "http.server"
```

### Camera Not Streaming

1. Ensure the camera node is running and publishing to `/camera/image_raw`
2. Check available topics: `ros2 topic list | grep camera`

### SLAM Toolbox Warning

The warning `maximum laser range setting exceeds the capabilities of the used Lidar` is normal and can be ignored. The RPLIDAR A1 has a 12m range while SLAM is configured for 20m.

## Network Configuration

For distributed ROS2 setup (PC + RPI), set the same `ROS_DOMAIN_ID` on both devices:

```bash
export ROS_DOMAIN_ID=0
```

## Packages Overview

| Package | Description |
|---------|-------------|
| `rmitbot_bringup` | Launch files for full system bringup |
| `rmitbot_controller` | ros2_control hardware interface |
| `rmitbot_description` | URDF robot model |
| `rmitbot_firmware` | Hardware interface plugin |
| `rmitbot_localization` | EKF sensor fusion |
| `rmitbot_mapping` | SLAM and RPLIDAR configuration |
| `rmitbot_navigation` | Nav2 navigation stack |
| `rmitbot_webapp` | Web-based teleoperation interface |
| `camera_ros` | RPI camera driver |
