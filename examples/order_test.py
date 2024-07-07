import numpy
# import scipy
import time
import random
from multiverse import Multiverse, Display, MODE_HUB75
from dispmanx import DispmanX

display = Multiverse(
    Display("/dev/serial/by-id/usb-Pimoroni_Multiverse_E661410403177438-if00", 160, 32, 0, 0, mode=MODE_HUB75),
)


display.setup()

# Full buffer size
WIDTH = 32
HEIGHT = 160
BYTES_PER_PIXEL = 4


pi_display = DispmanX(pixel_format="RGB", buffer_type="numpy")

bitmap = numpy.zeros((WIDTH, HEIGHT, 3), dtype=numpy.uint8)

sum_total = 0
num_frames = 0




while True:
    t_start = time.time()


    pi_display.snapshot()
    # Update the displays from the buffer
    
    #display.update(numpy.roll(fix, 200, axis=0))
    display.update(numpy.roll(pi_display._buffer[...,[2,1,0]], num_frames, axis=0))

    # Just FPS stuff, move along!
    t_end = time.time()
    t_total = t_end - t_start

    sum_total += t_total
    num_frames += 1

    #time.sleep(1.0 / 120)

    if num_frames % 100 == 0:
        print(f'FPS: {num_frames/sum_total}')
        print(pi_display._buffer.shape)
