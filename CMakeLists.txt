cmake_minimum_required(VERSION 3.20)

set(MODULE_NAME "engine_module" CACHE STRING "Project and library target name")

project(${MODULE_NAME} VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_EXTENSIONS OFF)

if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    include(CTest)
endif()

string(MAKE_C_IDENTIFIER "${PROJECT_NAME}" MODULE_OPTION_PREFIX)
string(TOUPPER "${MODULE_OPTION_PREFIX}" MODULE_OPTION_PREFIX)

if(NOT COMMAND module_add_dependency)
    function(module_add_dependency DEP_NAME)
        set(options REQUIRED GIT_SHALLOW)
        set(oneValueArgs SOURCE_DIR GIT_REPOSITORY GIT_TAG PACKAGE)
        set(multiValueArgs COMPONENTS)
        cmake_parse_arguments(ARGS "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

        string(TOUPPER "${DEP_NAME}" DEP_NAME_UPPER)
        set(_version_var "${DEP_NAME}_VERSION")
        if(ARGS_GIT_TAG)
            set(${_version_var} "${ARGS_GIT_TAG}" CACHE STRING "Version or tag for ${DEP_NAME}")
        elseif(NOT DEFINED ${_version_var})
            set(${_version_var} "" CACHE STRING "Version or tag for ${DEP_NAME}")
        endif()

        if(TARGET ${DEP_NAME} OR DEFINED ${DEP_NAME}_SOURCE_DIR OR DEFINED FETCHCONTENT_SOURCE_DIR_${DEP_NAME_UPPER})
            return()
        endif()

        if(ARGS_SOURCE_DIR)
            add_subdirectory(${ARGS_SOURCE_DIR} ${PROJECT_BINARY_DIR}/_deps/${DEP_NAME})
            return()
        endif()

        if(ARGS_GIT_REPOSITORY)
            include(FetchContent)
            set(_fetch_args GIT_REPOSITORY "${ARGS_GIT_REPOSITORY}")
            if(NOT "${${_version_var}}" STREQUAL "")
                list(APPEND _fetch_args GIT_TAG "${${_version_var}}")
            endif()
            if(ARGS_GIT_SHALLOW)
                list(APPEND _fetch_args GIT_SHALLOW TRUE)
            endif()
            FetchContent_Declare(${DEP_NAME} ${_fetch_args})
            FetchContent_MakeAvailable(${DEP_NAME})
            return()
        endif()

        if(ARGS_PACKAGE)
            set(_package_args)
            if(NOT "${${_version_var}}" STREQUAL "")
                list(APPEND _package_args "${${_version_var}}")
            endif()
            if(ARGS_REQUIRED)
                list(APPEND _package_args REQUIRED)
            endif()
            if(ARGS_COMPONENTS)
                list(APPEND _package_args COMPONENTS ${ARGS_COMPONENTS})
            endif()
            find_package(${ARGS_PACKAGE} ${_package_args})
            return()
        endif()

        message(FATAL_ERROR "module_add_dependency(${DEP_NAME}) requires SOURCE_DIR, GIT_REPOSITORY or PACKAGE.")
    endfunction()
endif()

option(BUILD_TESTS "Build ${PROJECT_NAME} tests" ON)
option(ENABLE_COVERAGE "Enable ${PROJECT_NAME} coverage instrumentation" OFF)

file(GLOB_RECURSE MODULE_SOURCES CONFIGURE_DEPENDS src/*.cpp)
add_library(${PROJECT_NAME} ${MODULE_SOURCES})
add_library(${PROJECT_NAME}::${PROJECT_NAME} ALIAS ${PROJECT_NAME})
target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_23)
target_include_directories(${PROJECT_NAME}
    PUBLIC
        $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

if(BUILD_TESTS)
    enable_testing()
    if(NOT TARGET GTest::gtest_main)
        find_package(GTest QUIET)
    endif()
    if(NOT TARGET GTest::gtest_main)
        if(MSVC)
            set(gtest_force_shared_crt ON)
        endif()
        module_add_dependency(googletest
            GIT_REPOSITORY https://github.com/google/googletest.git
            GIT_TAG v1.18.0
            GIT_SHALLOW
        )
    endif()

    file(GLOB_RECURSE TEST_SOURCES CONFIGURE_DEPENDS tests/*.cpp)
    add_executable(${PROJECT_NAME}_tests ${TEST_SOURCES})
    target_link_libraries(${PROJECT_NAME}_tests
        PRIVATE
            ${PROJECT_NAME}::${PROJECT_NAME}
            GTest::gtest_main
    )
    include(GoogleTest)
    gtest_discover_tests(${PROJECT_NAME}_tests)
endif()

if(ENABLE_COVERAGE)
    if(NOT BUILD_TESTS)
        message(FATAL_ERROR "Coverage reporting requires BUILD_TESTS=ON")
    endif()
    if(NOT CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        message(FATAL_ERROR "Coverage instrumentation is supported with GCC or Clang")
    endif()

    find_program(GCOVR_EXECUTABLE gcovr)
    set(GCOVR_COMMAND)
    if(GCOVR_EXECUTABLE)
        set(GCOVR_COMMAND ${GCOVR_EXECUTABLE})
    else()
        find_package(Python3 COMPONENTS Interpreter QUIET)
        if(Python3_Interpreter_FOUND)
            execute_process(
                COMMAND ${Python3_EXECUTABLE} -m gcovr --version
                RESULT_VARIABLE GCOVR_PYTHON_RESULT
                OUTPUT_QUIET
                ERROR_QUIET
            )
            if(GCOVR_PYTHON_RESULT EQUAL 0)
                set(GCOVR_COMMAND ${Python3_EXECUTABLE} -m gcovr)
            endif()
        endif()
    endif()
    target_compile_options(${PROJECT_NAME} PRIVATE --coverage -O0 -g)
    target_link_options(${PROJECT_NAME} PUBLIC --coverage)
    target_compile_options(${PROJECT_NAME}_tests PRIVATE --coverage -O0 -g)
    target_link_options(${PROJECT_NAME}_tests PRIVATE --coverage)

    if(GCOVR_COMMAND)
        add_custom_target(${PROJECT_NAME}_coverage
            COMMAND ${CMAKE_CTEST_COMMAND} --test-dir ${PROJECT_BINARY_DIR} --output-on-failure
            COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BINARY_DIR}/coverage
            COMMAND ${GCOVR_COMMAND}
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
    else()
        message(STATUS "gcovr was not found. '${PROJECT_NAME}_coverage' will fail until gcovr is installed (for example: python3 -m pip install gcovr).")
        add_custom_target(${PROJECT_NAME}_coverage
            COMMAND ${CMAKE_COMMAND} -E echo "gcovr is required to build ${PROJECT_NAME}_coverage. Install it and re-run the build."
            COMMAND ${CMAKE_COMMAND} -E false
            DEPENDS ${PROJECT_NAME}_tests
            WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
            COMMENT "Coverage tool missing"
            VERBATIM
        )
    endif()
endif()