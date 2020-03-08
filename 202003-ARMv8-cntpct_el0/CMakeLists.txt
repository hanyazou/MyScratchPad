cmake_minimum_required(VERSION 2.8)
project(counter)

add_compile_options(-DPLATFORM=RASPI64 -O3)
include_directories(include)

#
# library
#
add_library(counter SHARED
    src/counter.c
)
target_include_directories(counter PRIVATE
    src/
)

#
# sample executable
#
add_executable(sample
    samples/sample.c
)
target_link_libraries(sample
    counter
)

#
# test executables
#
add_executable(test
    test/test.c
    test/counter_test.c
)
target_include_directories(test PRIVATE
    src/
    test/
)
target_link_libraries(test
    counter
)

add_executable(test2
    test/test2.cpp
)
target_link_libraries(test2
    counter
)
