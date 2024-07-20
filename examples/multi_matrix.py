import numpy
# import scipy
import time
import random
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

display.setup()

# Full buffer size
WIDTH = 160
HEIGHT = 32 * 8
BYTES_PER_PIXEL = 4

# Fire stuff
FIRE_SPAWNS = 5
DAMPING_FACTOR = 0.98
matrix = 4.0

# Palette conversion, this is actually pretty nifty
PALETTE = numpy.array([
    [0, 0, 0, 0],
    [0, 20, 0, 0],
    [0, 30, 0, 0],
    [0, 160, 0, 0],
    [0, 255, 0, 0],
    [0, 255, 30, 30],
    [0, 255, 100, 100],
    [0, 255, 200, 200],
    [0, 255, 245, 245],
    [0, 255, 255, 255],
    [0, 255, 255, 255]
], dtype=numpy.uint8)


matrix = numpy.zeros((HEIGHT, WIDTH), dtype=numpy.float32)


def update():
    matrix[:] *= 0.65

    for _ in range(10):
        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT // 2)
        matrix[y][x] = random.randint(128, 255) / 255.0

    # Propagate downwards
    old = matrix * 0.5
    matrix[:] = numpy.roll(matrix, 1, axis=0)
    matrix[:] += old


# Framerate counters, don't mind these
sum_total = 0
num_frames = 0


while True:
    t_start = time.time()

    # Update the fire
    update()

    # Convert the fire buffer to RGB 888X (uint32 as four bytes)
    buf = matrix
    # buf = scipy.ndimage.rotate(buf, (t_start * 45) % 360, reshape=False)
    buf = buf.clip(0.0, 1.0) * (len(PALETTE) - 1)
    buf = buf.astype(numpy.uint8)
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
