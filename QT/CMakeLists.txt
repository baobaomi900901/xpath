cmake_minimum_required(VERSION 3.16)

project(qt-shooting-ranges LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

find_package(QT NAMES Qt6 Qt5 REQUIRED COMPONENTS Core)
find_package(Qt${QT_VERSION_MAJOR} REQUIRED COMPONENTS Core Gui Widgets Quick QuickControls2 Test)
set(QT_LIB Qt${QT_VERSION_MAJOR})
if(MSVC)
    add_compile_options(/utf-8)
endif()

add_library(range-model STATIC src/range_model.cpp src/range_model.h)
target_include_directories(range-model PUBLIC src)
target_link_libraries(range-model PUBLIC ${QT_LIB}::Core ${QT_LIB}::Gui)
add_library(range-widgets STATIC src/widgets_window.cpp src/widgets_window.h)
target_link_libraries(range-widgets PUBLIC range-model ${QT_LIB}::Widgets)
add_executable(qt-widgets-range WIN32 src/widgets_main.cpp)
target_link_libraries(qt-widgets-range PRIVATE range-widgets)
add_executable(qt-quick-range WIN32 src/quick_main.cpp resources/range.qrc)
target_link_libraries(qt-quick-range PRIVATE range-model ${QT_LIB}::Quick ${QT_LIB}::QuickControls2)

include(CTest)
if(BUILD_TESTING)
    add_executable(qt-range-tests tests/range_test.cpp resources/range.qrc)
    target_link_libraries(qt-range-tests PRIVATE range-widgets ${QT_LIB}::Test ${QT_LIB}::Quick ${QT_LIB}::QuickControls2)
    add_test(NAME qt-range COMMAND qt-range-tests -o test-results.xml,xml)
    set_tests_properties(qt-range PROPERTIES TIMEOUT 60)
endif()

add_executable(acc-hidden-profile
    src/main.cpp
    resources/resources.qrc
)

target_link_libraries(acc-hidden-profile
    PRIVATE
        ${QT_LIB}::Core
        ${QT_LIB}::Gui
        ${QT_LIB}::Quick
)

if(WIN32)
    set_target_properties(acc-hidden-profile PROPERTIES WIN32_EXECUTABLE TRUE)
endif()
