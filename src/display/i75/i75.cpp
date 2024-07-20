#include "display.hpp"
#include <cstdlib>
#include "pico/stdlib.h"

using namespace pimoroni;

Hub75 *hub75;

void __isr dma_complete() {
    hub75->dma_complete();
}

namespace display {

    uint8_t buffer[BUFFER_SIZE];
    PicoGraphics_PenRGB565 graphics(WIDTH, HEIGHT, &buffer);

    uint64_t frames = 0;
    uint64_t fps_window_start = 0;
    uint64_t fps_window_us = 0;
    uint32_t measured_fps = 0;

    void init() {
        hub75 = new Hub75(WIDTH, HEIGHT, nullptr, PANEL_GENERIC, false, Hub75::COLOR_ORDER::RGB);
        hub75->start(dma_complete);
    }

    void info(std::string_view text) {
    }

    void draw_debug_info(){
        graphics.set_pen(0, 0, 0);
        Rect background(0, 0, 6 * 7, 7);
        graphics.rectangle(background);
        graphics.set_pen(255, 255, 255);
        graphics.set_font("bitmap5");
        graphics.text("FPS: " + std::to_string(measured_fps), Point(0, 0), WIDTH, 1);
    }

    void update() {
        
        //TODO: Add a compile flag or a runtime flag to enable this
        draw_debug_info();

        hub75->update(&graphics);
        if((frames % 100) == 0){
            if(fps_window_start){
                fps_window_us = time_us_64() - fps_window_start;
                measured_fps = 100.0 / ((double)fps_window_us / 1000000.0);
            }
            fps_window_start = time_us_64();
            // Serial out the frame time...
        }
        frames++;
    }

    void play_note(uint8_t channel, uint16_t freq, uint8_t waveform, uint16_t a, uint16_t d, uint16_t s, uint16_t r, uint8_t phase) {
        // No audio support on i75
    }

    void play_audio(uint8_t *audio_buffer, size_t len) {
        // No audio support on i75
    }
}