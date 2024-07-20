/*
 * The MIT License (MIT)
 *
 * Copyright (c) 2021 Raspberry Pi (Trading) Ltd.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

#include <stdlib.h>
#include <stdio.h>
#include <string>
#include <string_view>

#include "display.hpp"
#include "pico/bootrom.h"
#include "hardware/structs/rosc.h"
#include "hardware/watchdog.h"
#include "pico/timeout_helper.h"
#include "pico/multicore.h"
#include "pico/mutex.h"

#include "bsp/board.h"
#include "tusb.h"

#include "cdc_uart.h"
#include "get_serial.h"

// UART0 for Picoprobe debug
// UART1 for picoprobe to target device

using namespace pimoroni;

const size_t COMMAND_LEN = 4;
uint8_t command_buffer[COMMAND_LEN];
uint8_t command_frame_buffer[display::BUFFER_SIZE];
uint8_t display_frame_buffer[display::BUFFER_SIZE];
std::string_view command((const char *)command_buffer, COMMAND_LEN);



////////////

bool has_frame = false;
auto_init_mutex(has_frame_mutex);

void signal_has_new_frame(){
    mutex_enter_blocking(&has_frame_mutex);
    has_frame = true;
    mutex_exit(&has_frame_mutex);
}

bool has_new_frame(){
    bool result = false;
    mutex_enter_blocking(&has_frame_mutex);
    if(has_frame){
        //Reset the flag
        has_frame = false;
        result = true;
    }
    mutex_exit(&has_frame_mutex);
    return result;
}

///////////


//uint16_t audio_buffer[22050] = {0};

bool cdc_wait_for(std::string_view data, uint timeout_ms=1000) {
    timeout_state ts;
    absolute_time_t until = delayed_by_ms(get_absolute_time(), timeout_ms);
    check_timeout_fn check_timeout = init_single_timeout_until(&ts, until);

    for(auto expected_char : data) {
        char got_char;
        while(1){
            tud_task();
            if (cdc_task((uint8_t *)&got_char, 1) == 1) break;
            if(check_timeout(&ts)) return false;
        }
        if (got_char != expected_char) return false;
    }
    return true;
}

size_t cdc_get_bytes(const uint8_t *buffer, const size_t len, const uint timeout_ms=1000) {
    memset((void *)buffer, len, 0);

    uint8_t *p = (uint8_t *)buffer;

    timeout_state ts;
    absolute_time_t until = delayed_by_ms(get_absolute_time(), timeout_ms);
    check_timeout_fn check_timeout = init_single_timeout_until(&ts, until);

    size_t bytes_remaining = len;
    while (bytes_remaining && !check_timeout(&ts)) {
        tud_task(); // tinyusb device task
        size_t bytes_read = cdc_task(p, std::min(bytes_remaining, MAX_UART_PACKET));
        bytes_remaining -= bytes_read;
        p += bytes_read;
    }
    return len - bytes_remaining;
}

uint16_t cdc_get_data_uint16() {
    uint16_t len;
    tud_task();
    cdc_get_bytes((uint8_t *)&len, 2);
    return len;
}

uint8_t cdc_get_data_uint8() {
    uint8_t len;
    tud_task();
    cdc_get_bytes((uint8_t *)&len, 1);
    return len;
}

/**
 * Core 0 is responsible for communication and receiving frame data.
 * 
 * Frames are retrieved, and stored in a buffer for the display thread to use.
 * 
 */
int core_0_main(void) {
    printf("Starting Core 0 main loop\n");   
    while (1) {
        tud_task();

        if(!cdc_wait_for("multiverse:")) {
            //display::info("mto");
            continue; // Couldn't get 16 bytes of command
        }

        if(cdc_get_bytes(command_buffer, COMMAND_LEN) != COMMAND_LEN) {
            //display::info("cto");
            continue;
        }

        if(command == "data") {

            //TODO: Mutex around the display_frame_buffer

            if (cdc_get_bytes(display_frame_buffer, display::BUFFER_SIZE) == display::BUFFER_SIZE) {
                //Nothing to do, the other core's loop will copy the command buffer to the display buffer
                signal_has_new_frame();
            }
            continue;
        }

        /*if(command == "wave") {
            uint16_t audio_len = cdc_get_data_uint16();
            if (cdc_get_bytes((uint8_t *)audio_buffer, audio_len) == audio_len) {
                display::play_audio((uint8_t *)audio_buffer, audio_len / 2);
            }
            continue;
        }*/

        if(command == "note") {
            uint8_t channel = cdc_get_data_uint8();
            uint16_t freq = cdc_get_data_uint16();

            uint8_t waveform = cdc_get_data_uint8();

            uint16_t a = cdc_get_data_uint16();
            uint16_t d = cdc_get_data_uint16();
            uint16_t s = cdc_get_data_uint16();
            uint16_t r = cdc_get_data_uint16();

            uint8_t phase = cdc_get_data_uint8();

            display::play_note(channel, freq, waveform, a, d, s, r, phase);
            //display::info("note");
        }

        if(command == "_rst") {
            display::info("RST");
            sleep_ms(500);
            save_and_disable_interrupts();
            rosc_hw->ctrl = ROSC_CTRL_ENABLE_VALUE_ENABLE << ROSC_CTRL_ENABLE_LSB;
            watchdog_reboot(0, 0, 0);
            continue;
        }

        if(command == "_usb") {
            display::info("USB");
            sleep_ms(500);
            save_and_disable_interrupts();
            rosc_hw->ctrl = ROSC_CTRL_ENABLE_VALUE_ENABLE << ROSC_CTRL_ENABLE_LSB;
            reset_usb_boot(0, 0);
            continue;
        }
    }
}

// /**
//  * Converts a buffer of rgb888 pixels into a buffer of rgb565 pixels
//  */
// void frame_rgb888_to_rgb565(uint8_t * frame_rgb565, uint8_t * frame_rgb888){
//     uint32_t rgb888_i = 0;
//     uint32_t rgb565_i = 0;
    
//     while(rgb888_i < display::BUFFER_SIZE){
//         uint8_t r = frame_rgb888[rgb888_i++];
//         uint8_t g = frame_rgb888[rgb888_i++];
//         uint8_t b = frame_rgb888[rgb888_i++];
//         rgb888_i++;

//         frame_rgb565[rgb565_i++] = (r & 0xF8) | (g >> 5); // Take 5 bits of Red component and 3 bits of G component
//         frame_rgb565[rgb565_i++] = ((g & 0x1C) << 3) | (b  >> 3); // Take remaining 3 Bits of G component and 5 bits of Blue component

//     }
// }

// /**
//  * Converts a buffer of rgb565 pixels into a buffer of rgb888 pixels
//  */
// void frame_rgb565_to_rgb888(uint8_t * frame_rgb565, uint8_t * frame_rgb888){
//     uint32_t rgb888_i = 0;
//     uint32_t rgb565_i = 0;
    
//     while(rgb888_i < display::BUFFER_SIZE){


//         /*
//         * 0brrrrrggggggbbbbb
//         */
//         uint8_t r5 = frame_rgb565[rgb565_i] & 0xF8; // 11111000 00000000
//         uint8_t g6 = ((frame_rgb565[rgb565_i] & 0x07) << 3) + (frame_rgb565[rgb565_i+1] & 0xE0);      // 00000111 11100000
//         uint8_t b5 = (frame_rgb565[rgb565_i+1] & 0x1F) << 3;      // 00000000 00011111

//         rgb565_i+=2;

//         /**
//          * 0b00rrrrrrrrrrggggggggggbbbbbbbbbb
//          */
//         uint32_t rgb10bit = r5 << 25 | g6 << 14 | b5 << 5;

//         frame_rgb888[rgb888_i++] = (rgb10bit >> 24) & 0xFF;
//         frame_rgb888[rgb888_i++] = (rgb10bit >> 16) & 0xFF;
//         frame_rgb888[rgb888_i++] = (rgb10bit >> 8) & 0xFF;
//         frame_rgb888[rgb888_i++] = rgb10bit & 0xFF;
//     }
// }

/**
 * This main loop is responsible for updating the display. It takes video frames and updates the display.
 */
void core_1_main(){
    printf("Starting Core 1 main loop\n");   
    while (1) {
        if(has_new_frame()){
            //Lets not copy the new frame data in until we read all of it from USB, since it's DMA'd
            memcpy(display::buffer, display_frame_buffer, display::BUFFER_SIZE);

            //TODO: Handle RGB565 to RGB888 conversion
            // frame_rgb565_to_rgb888(display_frame_rgb565, display_frame_buffer);

            display::update();
        }
    }
}

int main(void) {
    stdio_init_all();

    board_init(); // Wtf?
    usb_serial_init(); // ??
    //cdc_uart_init(); // From cdc_uart.c
    tusb_init(); // Tiny USB?

    display::init();

    multicore_launch_core1(core_1_main);
    core_0_main();

    return 0;
}