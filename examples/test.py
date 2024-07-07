import numpy
import time
import random
import colorsys
from multiverse import Multiverse, Display, MODE_HUB75
import logging
import sys

DEBUG = False

root = logging.getLogger()
if DEBUG:
    root.setLevel(logging.DEBUG)
else:
    root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.handlers.clear()
root.addHandler(handler)

display = Multiverse(
    Display("/dev/serial/by-id/usb-Pimoroni_Multiverse_E661410403177438-if00", 160, 32, 0, 0, mode=MODE_HUB75),
    Display("/dev/serial/by-id/dummy", 256, 32, 0, 32 * 1, dummy=True, mode=MODE_HUB75),
    Display("/dev/serial/by-id/dummy", 256, 32, 0, 32 * 2, dummy=True, mode=MODE_HUB75),
    Display("/dev/serial/by-id/dummy", 256, 32, 0, 32 * 3, dummy=True, mode=MODE_HUB75),
    Display("/dev/serial/by-id/dummy", 256, 32, 0, 32 * 4, dummy=True, mode=MODE_HUB75),
    Display("/dev/serial/by-id/dummy", 256, 32, 0, 32 * 5, dummy=True, mode=MODE_HUB75),
    Display("/dev/serial/by-id/dummy", 256, 32, 0, 32 * 6, dummy=True, mode=MODE_HUB75),
    Display("/dev/serial/by-id/dummy", 256, 32, 0, 32 * 7, dummy=True, mode=MODE_HUB75),
)

display.setup(use_threads=True)

# Full buffer size
WIDTH = 256
HEIGHT = 256
BYTES_PER_PIXEL = 4
MAX_COLOUR = 256 # 10 bit

bitmap = numpy.zeros((HEIGHT, WIDTH, 4), dtype=numpy.uint32)

rgbx = [0,0,0,0] # [b, g, r, x]
state = 2

def update():
    global state
    global rgbx
    global bitmap

    if rgbx[state] == 255:
        # Rotate the color to sweep
        rgbx[state] = 0
        state = (state - 1) % 3
    else:
        rgbx[state] += 1
    
    bitmap[:] = rgbx


# Framerate counters, don't mind these
sum_total = 0
num_frames = 0


def toRGB565(rgb888x_pixel):
    print(f'RGBX = {rgb888x_pixel}')
    r = rgb888x_pixel[2]
    g = rgb888x_pixel[1]
    b = rgb888x_pixel[0]

    r565 = r >> 3
    g565 = g >> 2
    b565 = b >> 3

    rgb565 = ((r565) << 8) | ((g565) << 5) | (b565)
    print(f'rgb565: {r565} {g565} {b565} {rgb565:#06x} {rgb565}')



toRGB565([0,0,0,0])
toRGB565([127,0,0,0])
toRGB565([255,0,0,0])
toRGB565([0,127,0,0])
toRGB565([0,255,0,0])
toRGB565([0,0,127,0])
toRGB565([0,0,255,0])

#sys.exit(0)

while True:
    t_start = time.time()

    # Update the fire
    update()
    # Update the displays from the buffer
    display.update(bitmap)
    #toRGB565(bitmap[0][0])
    
    # Just FPS stuff, move along!
    t_end = time.time()
    t_total = t_end - t_start

    sum_total += t_total
    num_frames += 1

    time.sleep(1.0 / 60)

    if num_frames == 60:
        print(f"Took {sum_total:.04f}s for 60 frames, {num_frames / sum_total:.02f} FPS")
        num_frames = 0
        sum_total = 0
