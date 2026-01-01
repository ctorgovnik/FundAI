add_library(fund_abi INTERFACE)

target_include_directories(fund_abi 
    INTERFACE 
        ${CMAKE_CURRENT_SOURCE_DIR}
    )

target_compile_options(fund_abi INTERFACE
    -Wall
    -Wextra
)
