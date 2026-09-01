cmake_minimum_required(VERSION 3.16)

project(acc-hidden-profile LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt5 5.15 REQUIRED COMPONENTS Core Gui Quick)

add_executable(acc-hidden-profile
    src/main.cpp
    resources/resources.qrc
)

target_link_libraries(acc-hidden-profile
    PRIVATE
        Qt5::Core
        Qt5::Gui
        Qt5::Quick
)

if(WIN32)
    set_target_properties(acc-hidden-profile PROPERTIES WIN32_EXECUTABLE TRUE)
endif()
