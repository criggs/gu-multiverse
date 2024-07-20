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

#Chris's test displays
# display_ids = [
#     "usb-Pimoroni_Multiverse_E661410403177438-if00",
#     "usb-Pimoroni_Multiverse_E660C0D1C70C8F39-if00",
#     "usb-Pimoroni_Multiverse_E6614104035FC222-if00",
#     "usb-Pimoroni_Multiverse_E661410403529522-if00",
#     "usb-Pimoroni_Multiverse_E6614104034BB822-if00",
#     "usb-Pimoroni_Multiverse_E6614104033B8122-if00",
#     "usb-Pimoroni_Multiverse_E661410403762728-if00",
#     "usb-Pimoroni_Multiverse_E6614104035E8322-if00"
# ]
# displays = [ Display(f"/dev/serial/by-id/{id}", 160, 32, 0,   i * 32, mode=MODE_HUB75) for i, id in enumerate(display_ids) ]

#Museum displays
display_ids = [
    "usb-Pimoroni_Multiverse_E661410403314736-if00",
    "usb-Pimoroni_Multiverse_E6614104036F7A38-if00",
	"usb-Pimoroni_Multiverse_E661410403677138-if00",
	"usb-Pimoroni_Multiverse_E6614104031E9832-if00",
	"usb-Pimoroni_Multiverse_E6614104034EB634-if00",
	"usb-Pimoroni_Multiverse_E6614104032F5032-if00",
	"usb-Pimoroni_Multiverse_E661410403916D38-if00",
	"usb-Pimoroni_Multiverse_E661410403798632-if00"
]
displays = [ Display(f"/dev/serial/by-id/{id}", 256, 32, 0,   i * 32, mode=MODE_HUB75) for i, id in enumerate(display_ids) ]


display = Multiverse(*displays)

display.setup(use_threads=True)

# Full buffer size
WIDTH = 256
HEIGHT = 256
BYTES_PER_PIXEL = 4
MAX_COLOUR = 256 # 10 bit

INITIAL_LIFE = int(WIDTH * HEIGHT / 2)        # Number of live cells to seed
GENERATION_TIME = 0.1     # MS between generations
MINIMUM_LIFE = int(WIDTH * HEIGHT / 10)         # Auto reseed when only this many alive cells remain
SMOOTHED = True           # Enable for a more organic if somewhat unsettling feel

DECAY = 0.95              # Rate at which smoothing effect decays, higher number = more persistent, 1.0 = no decay
TENACITY = 32             # Rate at which smoothing effect increases

HSV_OFFSET = 0.3


def palette(offset=0.3):
    # for c in range(MAX_COLOUR):
    #     yield c
    #     yield 0
    #     yield c // 2
    #     yield 0
    for h in range(256):
       for c in colorsys.hsv_to_rgb(offset + h / 1024.0, 1.0, h / 255.0):
           yield int(c * 255)
       yield 0 # padding byte


# Palette conversion, this is actually pretty nifty
PALETTE = numpy.fromiter(palette(HSV_OFFSET), dtype=numpy.uint16).reshape((MAX_COLOUR, 4))

life = numpy.zeros((HEIGHT, WIDTH), dtype=numpy.float32)

# UPDATE THE FIIIIIIIIIIIIREEEEEEEEEEEEEEEEEEEEEEEEEE
def update():
    global last_gen

    duration[:] += life * TENACITY
    duration[:] *= DECAY

    if time.time() - last_gen < GENERATION_TIME:
        return

    last_gen = time.time()

    if numpy.sum(life) < MINIMUM_LIFE:
        seed_life()
        return

    # Rollin' rollin' rollin.
    _N = numpy.roll(life, -1, axis=0)
    _NW = numpy.roll(_N, -1, axis=1)
    _NE = numpy.roll(_N, 1, axis=1)
    _S = numpy.roll(life, 1, axis=0)
    _SW = numpy.roll(_S, -1, axis=1)
    _SE = numpy.roll(_S, 1, axis=1)
    _W = numpy.roll(life, -1, axis=1)
    _E = numpy.roll(life, 1, axis=1)

    # Compute the total neighbours for each cell
    neighbours[:] = _N + _NW + _NE + _S + _SW + _SE + _W + _E

    next_generation[:] = life[:]

    # Any cells with exactly three neighbours should always stay alive
    next_generation[:] += neighbours[:] == 3

    # Any alive cells with less than two neighbours should die
    next_generation[:] -= (neighbours[:] < 2) * life

    # Any alive cells with more than three neighbours should die
    next_generation[:] -= (neighbours[:] > 3) * life

    life[:] = numpy.clip(next_generation, 0, 1)


def seed_life():
    global PALETTE

    HSV_OFFSET = random.randint(0, 360) / 360.0

    PALETTE = numpy.fromiter(palette(HSV_OFFSET), dtype=numpy.uint8).reshape((256, 4))

    for _ in range(INITIAL_LIFE):
        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT - 1)
        life[y][x] = int(True)  # Avoid: TypeError: 'bool' object isn't iterable



life = numpy.zeros((HEIGHT, WIDTH), dtype=numpy.uint8)
next_generation = numpy.zeros((HEIGHT, WIDTH), dtype=numpy.uint8)
neighbours = numpy.zeros((HEIGHT, WIDTH), dtype=numpy.uint8)
duration = numpy.zeros((HEIGHT, WIDTH), dtype=numpy.float64)
last_gen = time.time()

# Framerate counters, don't mind these
sum_total = 0
num_frames = 0


seed_life()

while True:
    t_start = time.time()

    # Update the fire
    update()

    # Convert the fire buffer to RGB 888X (uint32 as four bytes)
    buf = numpy.clip(duration.round(0), 0, MAX_COLOUR - 1).astype(numpy.uint16)
    buf = PALETTE[buf]

    # Update the displays from the buffer
    display.update(buf)

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
