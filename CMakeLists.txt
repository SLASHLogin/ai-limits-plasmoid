cmake_minimum_required(VERSION 3.16)
project(limit-widget VERSION 1.2.0 LANGUAGES NONE)

include(CTest)

set(CMAKE_INSTALL_BINDIR "bin" CACHE PATH "User executables directory")
set(CMAKE_INSTALL_DATADIR "share" CACHE PATH "Shared data directory")
set(PLASMA_APPLETS_INSTALL_DIR "${CMAKE_INSTALL_DATADIR}/plasma/plasmoids"
    CACHE PATH "Directory in which Plasma applets are installed")

install(DIRECTORY package/
    DESTINATION "${PLASMA_APPLETS_INSTALL_DIR}/dev.slashlogin.ailimits"
    PATTERN "*.qmlc" EXCLUDE)
install(PROGRAMS
    package/contents/tools/limit-widget-helper
    helper/limit-widget-claude-statusline
    helper/limit-widget-setup
    DESTINATION "${CMAKE_INSTALL_BINDIR}")

if(BUILD_TESTING)
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    add_test(
        NAME helper
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_helper.py"
    )
    set_tests_properties(helper PROPERTIES
        ENVIRONMENT "LIMIT_WIDGET_HELPER=${CMAKE_CURRENT_SOURCE_DIR}/package/contents/tools/limit-widget-helper"
    )
endif()

add_custom_target(check-qml
    COMMAND ${CMAKE_COMMAND} -E echo "Run qmllint with the Qt/KDE import path from your Plasma installation."
    VERBATIM
)
