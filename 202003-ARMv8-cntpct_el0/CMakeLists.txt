cmake_minimum_required(VERSION 2.8)
project(counter)

add_compile_options(-DPLATFORM=RASPI64 -O3)
include_directories(include)

add_library(counter SHARED
    src/counter.c
)

add_executable(test
    src/test/main.c
)

target_link_libraries(test
    counter
)
