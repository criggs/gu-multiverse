import numpy
import time
import random
import sys
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

if len(sys.argv) == 2:
    if sys.argv[1] == "bl":
        display.bootloader()
    if sys.argv[1] == "rst":
        display.reset()
    sys.exit(0)

# Full buffer size
WIDTH = 160
HEIGHT = 32
BYTES_PER_PIXEL = 4

# Fire stuff
FIRE_SPAWNS = 5
DAMPING_FACTOR = 0.97
HEAT = 10.0

# Palette conversion, this is actually pretty nifty
PALETTE = numpy.array([
    [0, 0, 0, 0],
    [20, 20, 20, 0],
    [0, 30, 180, 0],
    [0, 160, 220, 0],
    [180, 255, 255, 0]
], dtype=numpy.uint8)

# FIIIREREEEEEEE
heat = numpy.zeros((HEIGHT, WIDTH), dtype=numpy.float32)
last_update = 0

# UPDATE THE FIIIIIIIIIIIIREEEEEEEEEEEEEEEEEEEEEEEEEE
def update(fps):
    global last_update

    if time.time() - last_update < (1.0 / fps):
        return
    
    last_update = time.time()

    # Clear the bottom two rows (off screen)
    heat[HEIGHT - 1][:] = 0.0
    heat[HEIGHT - 2][:] = 0.0

    # Add random fire spawns
    for c in range(FIRE_SPAWNS):
        x = random.randint(0, WIDTH - 4) + 2
        heat[HEIGHT - 1][x - 1:x + 1] = HEAT / 2.0
        heat[HEIGHT - 2][x - 1:x + 1] = HEAT

    # Propagate the fire upwards
    a = numpy.roll(heat, -1, axis=0)  # y + 1, x
    b = numpy.roll(heat, -2, axis=0)  # y + 2, x
    c = numpy.roll(heat, -1, axis=0)  # y + 1
    d = numpy.roll(c, 1, axis=1)      # y + 1, x + 1
    e = numpy.roll(c, -1, axis=1)     # y + 1, x - 1

    # Average over 5 adjacent pixels and apply damping
    heat[:] += a + b + d + e
    heat[:] *= DAMPING_FACTOR / 5.0


# Framerate counters, don't mind these
sum_total = 0
num_frames = 0


while True:
    t_start = time.time()

    # Update the fire
    update(60)

    # Convert the fire buffer to RGB 888X (uint32 as four bytes)
    buf = heat.clip(0.0, 1.0) * 4
    buf = buf.astype(numpy.uint8)
    buf = PALETTE[buf]

    #buf[:] = [0, 0, 255, 0]

    # Update the displays from the buffer
    display.update(buf)

    # Just FPS stuff, move along!
    t_end = time.time()
    t_total = t_end - t_start

    sum_total += t_total
    num_frames += 1

    if num_frames == 60:
        print(f"Took {sum_total:.04f}s for 60 frames, {num_frames / sum_total:.02f} FPS")
        num_frames = 0
        sum_total = 0
