find_package(Boost REQUIRED)

add_library(engine Engine.cc)

target_include_directories(engine
    PUBLIC  ${CMAKE_CURRENT_SOURCE_DIR}
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/..
)

target_link_libraries(engine PUBLIC Boost::headers)
