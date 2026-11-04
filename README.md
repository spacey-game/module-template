# C++23 Module Template

![Coverage](coverage.svg)

A small CMake-based starting point for a module that can be built on its own or
included in a larger engine with `add_subdirectory`.

## Configure and build

Requires CMake 3.20 or newer and Ninja.

```sh
cmake --preset default
cmake --build --preset default --parallel
ctest --preset default
```

The configure presets use isolated directories under `build/`: the default
preset uses `build/default`, and coverage uses `build/coverage`. The default
preset uses the `engine_module` name. To rename the project and library target,
change `MODULE_NAME`, the matching option names, and the coverage target name in
the presets and workflows. The target can then be linked as `<name>::<name>`.
Rename the `module` include folder and C++ namespace separately if you want them
to match the chosen project name.

Tests use GoogleTest. CMake uses an installed `GTest::gtest_main` target when
available; otherwise it fetches GoogleTest v1.18.0, so a network connection is
needed on the first configure.

Tests, examples, and coverage use options prefixed by the module name in
uppercase. For example, a standalone module named `physics` uses
`PHYSICS_BUILD_TESTS`, `PHYSICS_BUILD_EXAMPLES`, and `PHYSICS_ENABLE_COVERAGE`.
They can be disabled independently:

```sh
cmake --preset default -DMODULE_NAME=physics -DPHYSICS_BUILD_TESTS=OFF -DPHYSICS_BUILD_EXAMPLES=OFF
```

When included with `add_subdirectory`, the module target name comes from its
directory name. The prefixed options are then independent for each module.
The engine's top-level CMake project should call `include(CTest)` so tests from
all modules are discoverable from the root build directory. `BUILD_TESTING=OFF`
disables tests across the entire engine; a module-prefixed option disables
tests only for that module.

## VS Code

The workspace recommends CMake Tools and clangd. The `.vscode` settings disable
the C/C++ extension's IntelliSense engine, and `.clangd` reads compile commands
from the preset's `build/` directory.

In a multi-module build, the first module that needs GoogleTest fetches it and
the other modules reuse the same `GTest::gtest_main` target. The engine can
provide that target before adding modules, or declare `googletest` with
`FetchContent` first to centrally control its version.

## Coverage

Install `gcovr`, then configure with coverage instrumentation enabled:

```sh
cmake --preset coverage
cmake --build --preset coverage --parallel
```

If `gcovr` is not installed, `cmake --preset coverage` still configures so the
project can be opened in IDEs, and the `engine_module_coverage` build target
fails with an explicit install hint.

The target runs CTest and writes an HTML report to
`build/coverage/coverage/index.html`, plus a JSON summary. Coverage is supported
with GCC and Clang. GitHub Actions runs tests on Linux and Windows, and validates
the coverage workflow on pull requests. It updates the repository's
`coverage.svg` badge from Linux coverage on pushes to `main`.
The badge workflow needs permission to push commits to that branch; change its
branch filter if the repository uses a different default branch.