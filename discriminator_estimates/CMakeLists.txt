cmake_minimum_required(VERSION 3.15)
project(discriminator_estimates LANGUAGES C CXX)

# C17 если компилятор поддерживает, иначе fallback
set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED OFF)

set(SOURCES
  src/discrcg.c
  src/discrea.c
  src/discrqa.c
  src/discrsd.c
  src/discr_common.c
)

# --- Статическая библиотека (для C++ тестов) ---
add_library(discr STATIC ${SOURCES})
target_include_directories(discr PUBLIC include/)

# --- Shared библиотека (для Python ctypes) ---
add_library(discr_shared SHARED ${SOURCES})
target_include_directories(discr_shared PUBLIC include/)
if(WIN32)
  set_target_properties(discr_shared PROPERTIES
    WINDOWS_EXPORT_ALL_SYMBOLS ON
    OUTPUT_NAME "discr"
  )
endif()

# --- Compiler warnings ---
if(MSVC)
  target_compile_options(discr PRIVATE /W4)
  target_compile_options(discr_shared PRIVATE /W4)
  # _USE_MATH_DEFINES для M_PI
  target_compile_definitions(discr PRIVATE _USE_MATH_DEFINES)
  target_compile_definitions(discr_shared PRIVATE _USE_MATH_DEFINES)
else()
  target_compile_options(discr PRIVATE -Wall -Wextra -pedantic)
  target_compile_options(discr_shared PRIVATE -Wall -Wextra -pedantic)
endif()

# --- C++ тесты (простые, без фреймворка) ---
add_executable(test_discr test_cpp/test_main.cpp)
target_link_libraries(test_discr PRIVATE discr)
target_include_directories(test_discr PRIVATE include/)
set_target_properties(test_discr PROPERTIES
  CXX_STANDARD 17
  CXX_STANDARD_REQUIRED ON
)

# --- Google Test (gtest) ---
include(FetchContent)
fetchcontent_declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG        v1.15.2
)
# Для Windows: не переопределять runtime library
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
fetchcontent_makeavailable(googletest)

enable_testing()

# Gtest-тесты на данных sinc(x)
set(GTEST_SOURCES
  test_gtest/test_discr_cg_gtest.cpp
  test_gtest/test_discr_sd_gtest.cpp
  test_gtest/test_discr_qa_gtest.cpp
  test_gtest/test_discr_ea_gtest.cpp
  test_gtest/test_discr_common_gtest.cpp
)

add_executable(test_discr_gtest ${GTEST_SOURCES})
target_link_libraries(test_discr_gtest PRIVATE discr GTest::gtest_main)
target_include_directories(test_discr_gtest PRIVATE include/)
set_target_properties(test_discr_gtest PROPERTIES
  CXX_STANDARD 17
  CXX_STANDARD_REQUIRED ON
)

include(GoogleTest)
gtest_discover_tests(test_discr_gtest)
