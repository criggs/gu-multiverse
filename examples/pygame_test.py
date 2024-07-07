from random import randint
import pygame
import numpy
import time
from dispmanx import DispmanX

def random_color_with_alpha():
    return tuple(randint(0, 0xFF) for _ in range(3)) + (randint(0x44, 0xFF),)

display = DispmanX(pixel_format="RGBA", buffer_type="numpy")
#surface = pygame.image.frombuffer(display.buffer, display.size, display.pixel_format)
clock = pygame.time.Clock()


frame_count = 0
start = time.time()
for _ in range(2000):
    #surface.fill(random_color_with_alpha())
    #display.update()
    display.snapshot()
    #n_buff = numpy.frombuffer(display._output_buffer)
    
    if frame_count % 100 == 0:
        print(display._buffer)
        print(f'FPS: {frame_count / (time.time() - start)}')

    frame_count += 1
