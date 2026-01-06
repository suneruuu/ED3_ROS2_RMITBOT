#!/bin/bash

# Set up environment for libcamera
export LD_LIBRARY_PATH=/usr/local/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH

# Set up logging directory to avoid rcutils logging errors
export ROS_LOG_DIR=/tmp/ros_logs
mkdir -p $ROS_LOG_DIR

# Disable problematic logging
export RCUTILS_LOGGING_USE_STDOUT=1
export RCUTILS_LOGGING_BUFFERED_STREAM=1

# Run camera_ros with proper environment
exec ros2 run camera_ros camera_node "$@"
