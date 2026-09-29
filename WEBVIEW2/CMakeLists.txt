cmake_minimum_required(VERSION 3.20)
project(webview2-shooting-range LANGUAGES CXX RC)

if(NOT WIN32 OR NOT MSVC OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(FATAL_ERROR "This target requires Windows x64 and MSVC.")
endif()

file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/sdk-version.txt" WEBVIEW2_SDK_VERSION LIMIT_COUNT 1)
set(WEBVIEW2_SDK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/.tools/microsoft.web.webview2.${WEBVIEW2_SDK_VERSION}"
    CACHE PATH "Extracted Microsoft.Web.WebView2 NuGet package")
if(NOT EXISTS "${WEBVIEW2_SDK_DIR}/build/native/include/WebView2.h" OR
   NOT EXISTS "${WEBVIEW2_SDK_DIR}/build/native/x64/WebView2LoaderStatic.lib")
    message(FATAL_ERROR "WebView2 SDK missing. Run WEBVIEW2/build.ps1 first.")
endif()

add_executable(webview2-shooting-range WIN32 src/main.cpp src/app.rc)
target_compile_features(webview2-shooting-range PRIVATE cxx_std_17)
target_compile_definitions(webview2-shooting-range PRIVATE
    UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX _WIN32_WINNT=0x0A00)
target_compile_options(webview2-shooting-range PRIVATE /utf-8 /W4 /permissive-)
target_include_directories(webview2-shooting-range PRIVATE "${WEBVIEW2_SDK_DIR}/build/native/include")
target_link_libraries(webview2-shooting-range PRIVATE
    "${WEBVIEW2_SDK_DIR}/build/native/x64/WebView2LoaderStatic.lib"
    user32 gdi32 comctl32 ole32 oleaut32 shell32 shlwapi version advapi32)
# Keep the embedded per-monitor DPI manifest as the application's manifest.
target_link_options(webview2-shooting-range PRIVATE /MANIFEST:NO)
