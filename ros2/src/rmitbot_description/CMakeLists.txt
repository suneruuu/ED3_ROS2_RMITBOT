cmake_minimum_required(VERSION 3.8)
project(rmitbot_description)

find_package(ament_cmake REQUIRED)

# =======================================
# Modification of .txt starts here
# =======================================
# Folder to be added for compilation
install(
  DIRECTORY meshes urdf launch rviz config
  DESTINATION share/${PROJECT_NAME}
)

# Install Python scripts
install(
  PROGRAMS src/opencv_camera_node.py src/gstreamer_camera_node.py src/camera_wrapper.py
  DESTINATION lib/${PROJECT_NAME}
)
# =======================================
# Modification of .txt ends here
# =======================================

ament_package()