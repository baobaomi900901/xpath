cmake_minimum_required(VERSION 3.21)
project(cef-shooting-range LANGUAGES CXX RC)
file(TO_CMAKE_PATH "${CEF_ROOT}" CEF_ROOT)

if(NOT WIN32 OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
  message(FATAL_ERROR "CEF range requires Windows x64")
endif()
if(NOT CEF_RANGE_MAJOR MATCHES "^(109|125|128|133|154)$")
  message(FATAL_ERROR "Set CEF_RANGE_MAJOR to 109, 125, 128, 133 or 154")
endif()
if(NOT EXISTS "${CEF_ROOT}/include/cef_version.h")
  message(FATAL_ERROR "CEF_ROOT must point to an extracted official CEF Windows x64 SDK")
endif()
file(READ "${CEF_ROOT}/include/cef_version.h" CEF_VERSION_HEADER)
string(REGEX MATCH "#define CEF_VERSION_MAJOR ([0-9]+)" CEF_MAJOR_MATCH "${CEF_VERSION_HEADER}")
if(NOT CMAKE_MATCH_1 STREQUAL CEF_RANGE_MAJOR)
  message(FATAL_ERROR "CEF_ROOT does not match CEF_RANGE_MAJOR")
endif()
string(REGEX MATCH "#define CEF_VERSION \"([^\"]+)\"" CEF_VERSION_MATCH "${CEF_VERSION_HEADER}")
set(RANGE_CEF_VERSION "${CMAKE_MATCH_1}")
string(REGEX MATCH "chromium-([0-9.]+)" CHROMIUM_VERSION_MATCH "${RANGE_CEF_VERSION}")
set(RANGE_CHROMIUM_VERSION "${CMAKE_MATCH_1}")

set(CMAKE_CONFIGURATION_TYPES Release CACHE STRING "Build configurations" FORCE)
set(USE_SANDBOX OFF CACHE BOOL "CEF test range sandbox" FORCE)
set(CEF_RUNTIME_LIBRARY_FLAG /MT)
list(APPEND CMAKE_MODULE_PATH "${CEF_ROOT}/cmake")
find_package(CEF REQUIRED)
add_subdirectory("${CEF_LIBCEF_DLL_WRAPPER_PATH}" libcef_dll_wrapper)
ADD_LOGICAL_TARGET("libcef_lib" "${CEF_LIB_DEBUG}" "${CEF_LIB_RELEASE}")

set(RANGE_TARGET "cef-shooting-range-${CEF_RANGE_MAJOR}")
set(RANGE_OUTPUT "${CMAKE_CURRENT_SOURCE_DIR}/dist/${CEF_RANGE_MAJOR}")
add_executable(${RANGE_TARGET} WIN32 src/main.cpp src/app.rc)
SET_EXECUTABLE_TARGET_PROPERTIES(${RANGE_TARGET})
target_compile_features(${RANGE_TARGET} PRIVATE cxx_std_17)
target_compile_definitions(${RANGE_TARGET} PRIVATE UNICODE _UNICODE NOMINMAX WIN32_LEAN_AND_MEAN)
target_compile_options(${RANGE_TARGET} PRIVATE /utf-8 /W4)
target_include_directories(${RANGE_TARGET} PRIVATE "${CEF_ROOT}" "${CMAKE_CURRENT_SOURCE_DIR}/src")
target_link_libraries(${RANGE_TARGET} PRIVATE libcef_lib libcef_dll_wrapper ${CEF_STANDARD_LIBS})
set_target_properties(${RANGE_TARGET} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE "${RANGE_OUTPUT}")
target_link_options(${RANGE_TARGET} PRIVATE /MANIFEST:NO)

file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/version.json"
  "{\n  \"cef_version\": \"${RANGE_CEF_VERSION}\",\n  \"chromium_version\": \"${RANGE_CHROMIUM_VERSION}\"\n}\n")
add_custom_command(TARGET ${RANGE_TARGET} POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_directory "${CEF_ROOT}/Release" "${RANGE_OUTPUT}"
  COMMAND ${CMAKE_COMMAND} -E copy_directory "${CEF_ROOT}/Resources" "${RANGE_OUTPUT}"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CMAKE_CURRENT_BINARY_DIR}/version.json" "${RANGE_OUTPUT}/version.json"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CEF_ROOT}/LICENSE.txt" "${RANGE_OUTPUT}/LICENSE-cef.txt"
  VERBATIM)
