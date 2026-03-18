add_subdirectory(execution_engine)

add_executable(fund_os main.cc)

target_include_directories(fund_os PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(fund_os PRIVATE engine)
