cmake_minimum_required(VERSION 3.20)

if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    set(MODULE_NAME "engine_module" CACHE STRING "Project and library target name")
else()
    get_filename_component(MODULE_NAME "${CMAKE_CURRENT_SOURCE_DIR}" NAME)
endif()
project(${MODULE_NAME} VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_EXTENSIONS OFF)

if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    include(CTest)
endif()

string(MAKE_C_IDENTIFIER "${PROJECT_NAME}" MODULE_OPTION_PREFIX)
string(TOUPPER "${MODULE_OPTION_PREFIX}" MODULE_OPTION_PREFIX)

option(${MODULE_OPTION_PREFIX}_BUILD_TESTS "Build ${PROJECT_NAME} tests" ON)
option(${MODULE_OPTION_PREFIX}_ENABLE_COVERAGE "Enable ${PROJECT_NAME} coverage instrumentation" OFF)

file(GLOB_RECURSE MODULE_SOURCES src/*.cpp)
add_library(${PROJECT_NAME} ${MODULE_SOURCES})
add_library(${PROJECT_NAME}::${PROJECT_NAME} ALIAS ${PROJECT_NAME})
target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_23)
target_include_directories(${PROJECT_NAME}
    PUBLIC
        $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

if(${MODULE_OPTION_PREFIX}_BUILD_TESTS AND BUILD_TESTING)
    enable_testing()
    if(NOT TARGET GTest::gtest_main)
        find_package(GTest QUIET)
    endif()
    if(NOT TARGET GTest::gtest_main)
        include(FetchContent)
        FetchContent_Declare(
            googletest
            GIT_REPOSITORY https://github.com/google/googletest.git
            GIT_TAG v1.18.0
            GIT_SHALLOW TRUE
        )
        if(MSVC)
            set(gtest_force_shared_crt ON)
        endif()
        FetchContent_MakeAvailable(googletest)
    endif()

    add_executable(${PROJECT_NAME}_tests tests/module_test.cpp)
    target_link_libraries(${PROJECT_NAME}_tests
        PRIVATE
            ${PROJECT_NAME}::${PROJECT_NAME}
            GTest::gtest_main
    )
    include(GoogleTest)
    gtest_discover_tests(${PROJECT_NAME}_tests)
endif()

if(${MODULE_OPTION_PREFIX}_ENABLE_COVERAGE)
    if(NOT ${MODULE_OPTION_PREFIX}_BUILD_TESTS OR NOT BUILD_TESTING)
        message(FATAL_ERROR "Coverage reporting requires ${MODULE_OPTION_PREFIX}_BUILD_TESTS=ON and BUILD_TESTING=ON")
    endif()
    if(NOT CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        message(FATAL_ERROR "Coverage instrumentation is supported with GCC or Clang")
    endif()

    find_program(GCOVR_EXECUTABLE gcovr REQUIRED)
    target_compile_options(${PROJECT_NAME} PRIVATE --coverage -O0 -g)
    target_link_options(${PROJECT_NAME} PUBLIC --coverage)
    target_compile_options(${PROJECT_NAME}_tests PRIVATE --coverage -O0 -g)
    target_link_options(${PROJECT_NAME}_tests PRIVATE --coverage)

    add_custom_target(${PROJECT_NAME}_coverage
        COMMAND ${CMAKE_CTEST_COMMAND} --test-dir ${PROJECT_BINARY_DIR} --output-on-failure
        COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BINARY_DIR}/coverage
        COMMAND ${GCOVR_EXECUTABLE}
            --root ${PROJECT_SOURCE_DIR}
            --object-directory ${PROJECT_BINARY_DIR}
            --filter ${PROJECT_SOURCE_DIR}/src/
            --html-details ${PROJECT_BINARY_DIR}/coverage/index.html
            --json-summary ${PROJECT_BINARY_DIR}/coverage/summary.json
            --print-summary
        DEPENDS ${PROJECT_NAME}_tests
        WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
        COMMENT "Running ${PROJECT_NAME} tests and generating the HTML coverage report"
        VERBATIM
    )
endif()