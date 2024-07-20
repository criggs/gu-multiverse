add_library(display INTERFACE)


include(libraries/hershey_fonts/hershey_fonts)
include(libraries/bitmap_fonts/bitmap_fonts)
include(libraries/pico_graphics/pico_graphics)
include(${PIMORONI_PICO_PATH}/drivers/hub75/hub75.cmake)

target_sources(display INTERFACE
  ${CMAKE_CURRENT_LIST_DIR}/i75.cpp
)

target_include_directories(display INTERFACE
  ${CMAKE_CURRENT_LIST_DIR}
)

target_compile_definitions(display INTERFACE
	PICO_DEFAULT_UART_TX_PIN=28
	PICO_DEFAULT_UART_RX_PIN=29
)

target_link_libraries(display INTERFACE
    hub75
    pico_graphics
    hershey_fonts
    bitmap_fonts

    pico_stdlib
    hardware_adc
    hardware_pio
    hardware_dma
)

set(DISPLAY_NAME "Interstate 75")