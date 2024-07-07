import time
import random
import sys
import math
import numpy
from multiverse import Multiverse, Display
import logging

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
    Display("/dev/serial/by-id/usb-Pimoroni_Multiverse_E6614104037D9F30-if00", 53, 11, 0,  0),
    Display("/dev/serial/by-id/usb-Pimoroni_Multiverse_E661410403422430-if00", 53, 11, 0, 11),
    Display("/dev/serial/by-id/usb-Pimoroni_Multiverse_E661410403868C2C-if00", 53, 11, 0, 22),
    Display("/dev/serial/by-id/usb-Pimoroni_Multiverse_E6614103E7301237-if00", 53, 11, 0, 33),
    Display("/dev/serial/by-id/usb-Pimoroni_Multiverse_E6614C311B425233-if00", 53, 11, 0, 44),
    Display("/dev/serial/by-id/usb-Pimoroni_Multiverse_E6614103E786A622-if00", 53, 11, 0, 55)
)

display.setup(False)

notes = [440, 880, 400]

while True:
    display.play_note(0, notes[0], attack=300)
    display.play_note(1, notes[1], attack=10, waveform=Display.WAVEFORM_SAW)
    notes += [notes.pop(0)]
    time.sleep(0.5)
