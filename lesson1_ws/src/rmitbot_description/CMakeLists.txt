cmake_minimum_required(VERSION 3.8)
project(rmitbot_description)

find_package(ament_cmake REQUIRED)

# =======================================
# Modification of .txt starts here
# =======================================
# Install resource folders (urdf, meshes, launch, rviz)
install(
  DIRECTORY meshes urdf launch rviz
  DESTINATION share/${PROJECT_NAME}
)
# =======================================
# Modification of .txt ends here
# =======================================

ament_package()
