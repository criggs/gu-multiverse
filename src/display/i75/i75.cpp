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
    

    void init() {
        hub75 = new Hub75(WIDTH, HEIGHT, nullptr, PANEL_GENERIC, false, Hub75::COLOR_ORDER::RGB);
        hub75->start(dma_complete);
    }

    void info(std::string_view text) {
    }

    void update() {

        frames++;
        uint64_t frame_start = time_us_64();
        //hub75->flip();

        // graphics.set_pen(0, 0, 0);
        // graphics.clear();
        graphics.set_pen(255, 0, 0);
        graphics.set_font("bitmap5");
        graphics.text("Frames: " + std::to_string(frames), Point(0, 0), WIDTH, 1);

        graphics.set_pen(0, 255, 0);
        graphics.set_font("bitmap5");
        graphics.text("Frames: " + std::to_string(frames), Point(0, 6), WIDTH, 1);


        graphics.set_pen(0, 0, 255);
        graphics.set_font("bitmap5");
        graphics.text("Frames: " + std::to_string(frames), Point(0, 12), WIDTH, 1);



        hub75->update(&graphics);
        if(frames % 100){
            uint64_t frame_time = time_us_64() - frame_start;
            // Serial out the frame time...
        }
    }

    void play_note(uint8_t channel, uint16_t freq, uint8_t waveform, uint16_t a, uint16_t d, uint16_t s, uint16_t r, uint8_t phase) {
        // No audio support on i75
    }

    void play_audio(uint8_t *audio_buffer, size_t len) {
        // No audio support on i75
    }
}