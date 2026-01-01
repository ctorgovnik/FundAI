add_library(ipc STATIC
    ${CMAKE_CURRENT_SOURCE_DIR}/ring_buffer.c
    ${CMAKE_CURRENT_SOURCE_DIR}/shared_memory.c
)

target_include_directories(ipc 
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

add_executable(ipc_test
    ${CMAKE_CURRENT_SOURCE_DIR}/tests/shared_memory_test.cc
    ${CMAKE_CURRENT_SOURCE_DIR}/tests/ring_buffer_test.cc
)

target_link_libraries(ipc_test PRIVATE ipc gtest gtest_main)
