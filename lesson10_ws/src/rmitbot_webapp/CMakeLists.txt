cmake_minimum_required(VERSION 3.8)
project(rmitbot_webapp)

find_package(ament_cmake REQUIRED)

# Install launch files
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# Install web files
install(DIRECTORY www/
  DESTINATION share/${PROJECT_NAME}/www
)

# Install scripts
install(DIRECTORY scripts/
  DESTINATION share/${PROJECT_NAME}/scripts
)

ament_package()
