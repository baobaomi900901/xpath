cmake_minimum_required(VERSION 3.20)

project(win32-shooting-range LANGUAGES CXX)

add_executable(win32-shooting-range-uia WIN32
    src/main.cpp
)

add_executable(win32-shooting-range-msaa WIN32
    src/msaa_main.cpp
)

add_executable(win32-shooting-range-canvas WIN32
    src/msaa_main.cpp
)

add_executable(uia-no-msaa-probe
    src/uia_no_msaa_probe.cpp
)

foreach(target IN ITEMS
    win32-shooting-range-uia
    win32-shooting-range-msaa
    win32-shooting-range-canvas
    uia-no-msaa-probe
)
    target_compile_features(${target} PRIVATE cxx_std_17)
    target_compile_definitions(${target} PRIVATE
        UNICODE
        _UNICODE
        WIN32_LEAN_AND_MEAN
        NOMINMAX
    )
endforeach()

target_compile_definitions(win32-shooting-range-msaa PRIVATE
    WIN32_SHOOTING_RANGE_ENABLE_MSAA=1
)
target_compile_definitions(win32-shooting-range-canvas PRIVATE
    WIN32_SHOOTING_RANGE_ENABLE_MSAA=0
)

target_link_libraries(win32-shooting-range-uia PRIVATE comctl32)
target_link_libraries(win32-shooting-range-msaa PRIVATE oleacc ole32 oleaut32)
target_link_libraries(uia-no-msaa-probe PRIVATE ole32 oleaut32 uiautomationcore)

if(MSVC)
    foreach(target IN ITEMS
        win32-shooting-range-uia
        win32-shooting-range-msaa
        win32-shooting-range-canvas
        uia-no-msaa-probe
    )
        target_compile_options(${target} PRIVATE /utf-8 /W4 /permissive-)
    endforeach()
endif()
