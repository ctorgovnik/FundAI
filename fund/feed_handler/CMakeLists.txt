find_package(Boost REQUIRED)

add_library(feed_handler
    factory.cc
    sim/sim_feed_handler.cc
    live/live_feed_handler.cc
)

target_include_directories(feed_handler
    PUBLIC  ${CMAKE_CURRENT_SOURCE_DIR}       # feed_handler.hh, market_event.hh
            ${CMAKE_CURRENT_SOURCE_DIR}/..    # config.hh
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/sim
            ${CMAKE_CURRENT_SOURCE_DIR}/live
)

target_link_libraries(feed_handler PUBLIC Boost::headers)
target_compile_definitions(feed_handler PUBLIC BOOST_ERROR_CODE_HEADER_ONLY)

# Tests
add_executable(feed_handler_test tests/feed_handler_test.cc)
# Force gtest FetchContent headers before Homebrew system includes to prevent ABI mismatch
target_include_directories(feed_handler_test BEFORE PRIVATE
    ${CMAKE_BINARY_DIR}/_deps/googletest-src/googletest/include
)
target_link_libraries(feed_handler_test PRIVATE feed_handler gtest gtest_main)
include(GoogleTest)
gtest_add_tests(TARGET feed_handler_test)
