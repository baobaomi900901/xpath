cmake_minimum_required(VERSION 3.20)

project(win32-shooting-range LANGUAGES CXX)

# Embed the MSVC runtime so each distributed EXE only needs Windows system DLLs.
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

add_executable(win32-shooting-range-uia WIN32
    src/main.cpp
)

add_executable(win32-shooting-range-uia-no-pane WIN32
    src/main.cpp
)

add_executable(win32-shooting-range-uia-random WIN32
    src/main.cpp
)

add_executable(win32-shooting-range-msaa WIN32
    src/msaa_main.cpp
)

add_executable(win32-shooting-range-canvas WIN32
    src/msaa_main.cpp
)

add_executable(win32-uia-pressure WIN32
    src/uia_pressure_main.cpp
)

foreach(depth IN ITEMS 500 1000 2000)
    add_executable(win32-uia-pressure-${depth} WIN32 src/uia_pressure_main.cpp)
    target_compile_definitions(win32-uia-pressure-${depth} PRIVATE WIN32_UIA_PRESSURE_FIXED_DEPTH=${depth})
    target_link_libraries(win32-uia-pressure-${depth} PRIVATE comctl32)
endforeach()

add_executable(uia-no-msaa-probe
    src/uia_no_msaa_probe.cpp
)

foreach(target IN ITEMS
    win32-shooting-range-uia
    win32-shooting-range-uia-no-pane
    win32-shooting-range-uia-random
    win32-shooting-range-msaa
    win32-shooting-range-canvas
    win32-uia-pressure
    win32-uia-pressure-500
    win32-uia-pressure-1000
    win32-uia-pressure-2000
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

target_compile_definitions(win32-shooting-range-uia PRIVATE
    WIN32_SHOOTING_RANGE_FORM_PANES=1
)
target_compile_definitions(win32-shooting-range-uia-no-pane PRIVATE
    WIN32_SHOOTING_RANGE_FORM_PANES=0
)
target_compile_definitions(win32-shooting-range-uia-random PRIVATE
    WIN32_SHOOTING_RANGE_FORM_PANES=1
    WIN32_SHOOTING_RANGE_RANDOM_FORM=1
)

target_compile_definitions(win32-shooting-range-msaa PRIVATE
    WIN32_SHOOTING_RANGE_ENABLE_MSAA=1
)
target_compile_definitions(win32-shooting-range-canvas PRIVATE
    WIN32_SHOOTING_RANGE_ENABLE_MSAA=0
)

target_link_libraries(win32-shooting-range-uia PRIVATE comctl32)
target_link_libraries(win32-shooting-range-uia-no-pane PRIVATE comctl32)
target_link_libraries(win32-shooting-range-uia-random PRIVATE comctl32)
target_link_libraries(win32-uia-pressure PRIVATE comctl32)
target_link_libraries(win32-shooting-range-msaa PRIVATE oleacc ole32 oleaut32)
target_link_libraries(uia-no-msaa-probe PRIVATE ole32 oleaut32 uiautomationcore)

if(MSVC)
    foreach(target IN ITEMS
        win32-shooting-range-uia
        win32-shooting-range-uia-no-pane
        win32-shooting-range-uia-random
        win32-shooting-range-msaa
        win32-shooting-range-canvas
        win32-uia-pressure
        win32-uia-pressure-500
        win32-uia-pressure-1000
        win32-uia-pressure-2000
        uia-no-msaa-probe
    )
        target_compile_options(${target} PRIVATE /utf-8 /W4 /permissive-)
    endforeach()
endif()

option(WIN32_SHOOTING_RANGE_BUILD_TESTS "Build in-process form model/provider tests" OFF)
if(WIN32_SHOOTING_RANGE_BUILD_TESTS)
    enable_testing()
    foreach(depth IN ITEMS 500 1000 2000)
        add_executable(win32-pressure-${depth}-tests tests/uia_pressure_depth_test.cpp)
        target_compile_features(win32-pressure-${depth}-tests PRIVATE cxx_std_17)
        target_compile_definitions(win32-pressure-${depth}-tests PRIVATE
            UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX
            WIN32_UIA_PRESSURE_FIXED_DEPTH=${depth}
        )
        target_link_libraries(win32-pressure-${depth}-tests PRIVATE comctl32)
        if(MSVC)
            target_compile_options(win32-pressure-${depth}-tests PRIVATE /utf-8 /W4 /permissive-)
        endif()
        add_test(NAME win32-pressure-${depth} COMMAND win32-pressure-${depth}-tests)
    endforeach()
    add_executable(win32-uia-random-form-tests tests/uia_random_form_test.cpp)
    target_compile_features(win32-uia-random-form-tests PRIVATE cxx_std_17)
    target_compile_definitions(win32-uia-random-form-tests PRIVATE
        UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX
        WIN32_SHOOTING_RANGE_FORM_PANES=1 WIN32_SHOOTING_RANGE_RANDOM_FORM=1
    )
    target_link_libraries(win32-uia-random-form-tests PRIVATE comctl32)
    if(MSVC)
        target_compile_options(win32-uia-random-form-tests PRIVATE /utf-8 /W4 /permissive- /EHsc)
    endif()
    add_test(NAME win32-uia-random-form COMMAND win32-uia-random-form-tests)
    foreach(backend IN ITEMS msaa canvas)
        add_executable(win32-form-${backend}-tests tests/form_items_test.cpp)
        target_compile_features(win32-form-${backend}-tests PRIVATE cxx_std_17)
        target_compile_definitions(win32-form-${backend}-tests PRIVATE
            UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX
        )
        if(backend STREQUAL "msaa")
            target_compile_definitions(win32-form-${backend}-tests PRIVATE WIN32_SHOOTING_RANGE_ENABLE_MSAA=1)
            target_link_libraries(win32-form-${backend}-tests PRIVATE oleacc ole32 oleaut32)
        else()
            target_compile_definitions(win32-form-${backend}-tests PRIVATE WIN32_SHOOTING_RANGE_ENABLE_MSAA=0)
        endif()
        if(MSVC)
            target_compile_options(win32-form-${backend}-tests PRIVATE /utf-8 /W4 /permissive- /EHsc)
        endif()
        add_test(NAME win32-form-${backend} COMMAND win32-form-${backend}-tests)
    endforeach()
endif()
