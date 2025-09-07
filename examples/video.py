import os, signal, time, sys, threading, getopt
import logging
from multiverse import Multiverse, Display, MODE_HUB75
from typing import List
import logging
import imageio.v3 as iio
from video_player import VideoPlayer

def setup_logger():
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.handlers.clear()
    root.addHandler(handler)

def set_debug():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

_sig_handler_called = False

def main(argv):
    debug = False
    setup_logger()
    video_size = "1280x720"
    scale_algo = "lanczos"

    opts, args = getopt.getopt(argv, "hdo:b:", ["output=", "brightness=", "video_size=", "scale_algo="])
    for opt, arg in opts:
        if opt == "-h":
            logging.info("main.py [-d] -o <output_device> <video_file>")
            sys.exit()
        elif opt == "-d":
            debug = True
        elif opt in ("-o", "--output"):
         output = arg
        elif opt in ("--video_size"):
         video_size = arg
        elif opt in ("--scale_algo"):
         scale_algo = arg

    if debug:
        set_debug()

    video_file = args[0]

    video_player = None

    def signal_handler(sig, frame):
        global _sig_handler_called
        logging.info("Interrupted or Terminated. Attempting safe shutdown.")
        if _sig_handler_called:
            logging.info("Force closing")
            sys.exit(1)
        _sig_handler_called = True
        if video_player is not None:
            video_player.stop()
            
        if display is not None:
            display.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)



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

    display_ids_2 = [
        "usb-Pimoroni_Multiverse_E6617C93E329452A-if00",
        "usb-Pimoroni_Multiverse_E6617C93E3548529-if00",
        "usb-Pimoroni_Multiverse_E6617C93E376A72A-if00",
        "usb-Pimoroni_Multiverse_E6617C93E3145428-if00",
        "usb-Pimoroni_Multiverse_E6617C93E31D8E2A-if00",
        "usb-Pimoroni_Multiverse_E6617C93E3803E28-if00",
        "usb-Pimoroni_Multiverse_E6617C93E3157928-if00",
        "usb-Pimoroni_Multiverse_E6617C93E3728D2A-if00"
    ]

    displays = [ Display(f"/dev/serial/by-id/{id}", 128, 32, 128,   i * 32, mode=MODE_HUB75) for i, id in enumerate(display_ids) ]

    displays = displays + [ Display(f"/dev/serial/by-id/{id}", 128, 32, 0,   i * 32, mode=MODE_HUB75) for i, id in enumerate(display_ids_2) ]

    display = Multiverse(*displays)

    display.setup(use_threads=True)

    try:
        video_player = VideoPlayer(video_file, display, fit_mode=VideoPlayer.FIT_HEIGHT, video_size=video_size, scale_algo=scale_algo)
        video_player.start()

        # Wait for the threads to stop        
        video_player.join()

        display.stop()
        display.join()
        sys.exit(0)
        
    except Exception as e:
        logging.error("Exception from Main Run. Stopping Program.", exc_info=e)
        if video_player is not None:
            video_player.stop()
        if display is not None:
            display.stop()
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv[1:])