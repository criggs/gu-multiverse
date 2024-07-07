import numpy
# import scipy
import time
import random
from multiverse import Multiverse, Display, MODE_HUB75

from . import bcm_host


bcm_host.bcm_host_init()
handle = bcm_host.vc_dispmanx_display_open(self._display.device_id)
        if handle == 0:
            raise DispmanXRuntimeError(f"Error opening device ID #{self._display.device_id}")


display = Multiverse(
    Display("/dev/serial/by-id/usb-Pimoroni_Multiverse_E661410403177438-if00", 160, 32, 0, 0, mode=MODE_HUB75),
)




display.setup()

# Full buffer size
WIDTH = 32
HEIGHT = 160
BYTES_PER_PIXEL = 4

bitmap = numpy.zeros((WIDTH, HEIGHT, 3), dtype=numpy.uint8)

sum_total = 0
num_frames = 0

def update():

    x = num_frames % WIDTH
    y = (num_frames // WIDTH) % HEIGHT

    bitmap[x][y] = (255,0,0)
    print(f"x:{x} y:{y}")





while True:
    t_start = time.time()

    # Update the fire
    update()

    # Update the displays from the buffer
    display.update(bitmap)

    # Just FPS stuff, move along!
    t_end = time.time()
    t_total = t_end - t_start

    sum_total += t_total
    num_frames += 1

    time.sleep(1.0 / 120)
