add_executable(
  fund
    ${CMAKE_CURRENT_SOURCE_DIR}/fund.cc 
)

target_link_libraries(
  fund
  PRIVATE
    ipc
)
