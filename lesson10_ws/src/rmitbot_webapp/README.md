# RMITBOT Web Teleop

A mobile-friendly web application to control the RMITBOT via touchscreen.

## Features

- **9-Button Control Pad** - Full directional control including diagonals
- **Mode Toggle** - Switch between Normal (rotation) and Holonomic (strafing) modes
- **Speed Control** - Adjustable linear velocity (0.1 - 1.0 m/s)
- **WebSocket Connection** - Real-time communication via rosbridge

## Prerequisites

Install rosbridge on your ROS2 Jazzy system:

```bash
sudo apt install ros-jazzy-rosbridge-server
```

## Building

```bash
cd ~/lesson10_ws
colcon build --packages-select rmitbot_webapp
source install/setup.bash
```

## Usage

### 1. Launch the webapp server

```bash
ros2 launch rmitbot_webapp webapp.launch.py
```

This starts:
- **rosbridge_websocket** on port 9090
- **HTTP server** on port 8000

### 2. Open on your mobile device

Navigate to: `http://<robot-ip>:8000`

### 3. Connect to ROS

1. Enter the robot's IP address (or `localhost` if on same machine)
2. Tap "Connect"
3. Wait for "Connected" status

### 4. Control the robot

- **Hold buttons** to move (release to stop)
- **Toggle mode** for strafing vs rotation
- **Adjust speed** with the slider

## Control Modes

### Normal Mode 🚗
| Button | Action |
|--------|--------|
| ↑ FWD | Drive forward |
| ↓ BWD | Drive backward |
| ← ROT L | Rotate left (CCW) |
| → ROT R | Rotate right (CW) |
| Diagonals | Combined forward/backward + rotation |

### Holonomic Mode ⚡
| Button | Action |
|--------|--------|
| ↑ FWD | Drive forward |
| ↓ BWD | Drive backward |
| ← LEFT | Strafe left |
| → RIGHT | Strafe right |
| Diagonals | Diagonal strafing |

## Topics

- **Publishes**: `/cmd_vel` (`geometry_msgs/msg/TwistStamped`)

## Troubleshooting

**Cannot connect?**
- Ensure rosbridge is running: `ros2 node list | grep rosbridge`
- Check firewall allows ports 8000 and 9090
- Verify IP address is correct

**Robot not moving?**
- Check `ros2 topic echo /cmd_vel` to see messages
- Ensure robot controller is running
- Verify twist_mux is configured if using multiple cmd_vel sources
