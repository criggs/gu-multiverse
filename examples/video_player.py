import threading
from typing import List
import time
import logging
import imageio.v3 as iio
import numpy
import re

BLACK = (0,0,0)
WHITE = (255,255,255)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)

'''
From http://trac.ffmpeg.org/wiki/Scaling#Specifyingscalingalgorithm
'''
SCLAING_ALGORITHMS = [
    'fast_bilinear',
    'bilinear',
    'bicubic',
    'experimental',
    'neighbor',
    'area',
    'bicublin',
    'gauss',
    'sinc',
    'lanczos',
    'spline'
]

'''
[[255 255 255]
 [255 255 254]
 [255 253 254]
 [255 254  43]
 [255 255   0]
 [255 255   8]
 [255 255   6]
 [ 55 255 203]
 [  0 255 255]
 [  8 255 255]
 [  6 255 255]
 [  0 255  84]
 [  0 255   0]
 [163 116 129]
 [255   0 255]
 [255   0 175]
 [255  12   0]
 [255  10   0]
 [255  11   0]
 [255  15   0]
 [171  18  55]
 [  0  14 255]
 [  2  10 255]
 [  0  10 255]
 [  0  12 255]
 [  2   7 219]
 [  8   6   7]
 [  7   7   7]]
'''

'''
[[255 255 255]
 [255 255   6]
 [  6 255 255]
 [  0 255   0]
 [255   0 255]
 [255  11   0]
 [  0  10 255]
 [  7   7   7]]
'''

NO_SIGNAL_COLORS = {
 (255, 255, 255),
 (255, 255,   6),
 (  6, 255, 255),
 (  0, 255,   0),
 (255,   0, 255),
 (255,  11,   0),
 (  0,  11, 255),
 (  7,   7,   7)
}

NO_SIGNAL_ART = """\
11111111111111111111111111111111
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
10000000000000000000000000000001
11111111111111111111111111111111
"""
NO_SIGNAL_ART_COLOR = (255,0,0)

NO_SIGNAL_ART_FRAME = []
for line in NO_SIGNAL_ART.splitlines():
    row = []
    for column in line:
        if column == '1':
            row.append(NO_SIGNAL_ART_COLOR)
        else:
            row.append((0,0,0))

    NO_SIGNAL_ART_FRAME.append(row)



class VideoPlayer():

    FIT_WIDTH = 1
    FIT_HEIGHT = 2
    FIT_STRETCH = 3

    def __init__(self, video_file_path, display, fit_mode = FIT_WIDTH, scale_algo = 'lanczos', video_size = "1280x720", width=256, height=256):
        self.video_file_path = video_file_path
        logging.info(f'Playing video {video_file_path}')

        self.width = width
        self.height = height
        self._thread = None
        self._stop_flag = threading.Event()
        self.fps = 20
        self.fit_mode = fit_mode
        self.display = display

        if scale_algo not in SCLAING_ALGORITHMS:
            raise ValueError(f"Scale algorithm {scale_algo} is not recognized")
        self.scale_algo = scale_algo

        if not re.match(r'\d+x\d+', video_size):
            raise ValueError(f"video_size {video_size} does not match the WIDTHxHEIGHT format")
        self.video_size = video_size
        
        self.setup_video()


    def setup_video(self):
        
        self.enable_red = True
        self.enable_green = True
        self.enable_blue = True

        scale_param = f"{self.width}:{self.height}"
        if self.fit_mode == self.FIT_WIDTH:
            scale_param = f"{self.width}:-1"
        elif self.fit_mode == self.FIT_HEIGHT:
            scale_param = f"-1:{self.height}"


        logging.debug(f"Video Fit Mode: {self.fit_mode}. ffmpeg Scale Param: {scale_param}")
        if '<video' in self.video_file_path:
            self.fps = 60
            logging.info(f"Resetting FPS to {self.fps} for video capture")
            logging.info(f"input frame size: {self.video_size}, scale algorithm: {self.scale_algo}")
            #self.frame_iter = iio.imiter(self.video_file_path)
            self.frame_iter = iio.imiter(self.video_file_path,
                # input_params = ["-framerate", f"{self.fps}", "-video_size", "800x600"],
                input_params = ["-vcodec", "mjpeg", "-framerate", f"{self.fps}", "-video_size", self.video_size],
                #output_params=['-vf', f"scale={scale_param}:flags={self.scale_algo}"]
                #output_params=['-vf']
            )
        else:
            #scale_param = f"-1:{self.height}" if self.fit_mode == self.FIT_HEIGHT else f"{self.width}:-1"
            self.frame_iter = iio.imiter(
                self.video_file_path,
                plugin="pyav",
                format="rgb24",
                filter_sequence=[("scale", f"{scale_param}:flags={self.scale_algo}"),("fps", f"{self.fps}")]
            )
        self.frame = next(self.frame_iter)
        self.frame_count = 0
        self.video_start_time = time.time()
        self.observed_fps = self.fps
        logging.debug(f"Start time is {self.video_start_time}")
        logging.debug(f"Frame shape: {self.frame.shape}")

    def start(self):
        logging.debug(f"VideoPlayer: Starting thread")
        if self._thread is not None:
            raise Exception("Thread is already started")
        self._thread = threading.Thread(target=self.run, name=f'VideoPlayer')
        self._thread.start()
        logging.debug(f'VideoPlayer: {self._thread}')



    def delay_for_fps(self, frame_elapsed_time):
         # Hacky attempt to keep a fixed-ish framerate
        # Added specifically for video playback
        fps_delay = 1000/(self.fps)
        frame_draw_delay = frame_elapsed_time * 1000
        sync_offset = 0
        if(self.observed_fps < self.fps):
            #speed up
            sync_offset = - fps_delay / 2
        elif self.observed_fps > self.fps:
            #slow down
            sync_offset = fps_delay / 2
            
        actual_delay = max(0, fps_delay - frame_draw_delay + sync_offset)
        
        if self.frame_count % 100 == 1:
            logging.debug(f'FPS Delay: {fps_delay}, frame_draw_delay: {frame_draw_delay}, actual_delay: {actual_delay}')                        
        
        time.sleep(actual_delay / 1000)    

    def run(self):
        logging.debug(f"Running....")
        while not self._stop_flag.wait(timeout=0.005):
            try:
                start = time.time()
                self.loop()
                now = time.time()
                video_elapsed_time = now - self.video_start_time
                self.observed_fps = self.frame_count / video_elapsed_time
                if self.frame_count % 100 == 1:
                    logging.debug(f"Observed FPS: {self.observed_fps}")

                frame_elapsed_time = time.time() - start
                self.delay_for_fps(frame_elapsed_time)
            except Exception as e:
                logging.error(
                    f"Error while executing video player loop. Stopping.", exc_info=e
                )
                return

    def stop(self):
        logging.debug(f"Stopping display thread")
        self._stop_flag.set()

    def join(self):
        if self._thread is None:
            logging.debug(f"No thread to join, returning")
            return
        logging.debug(f"Waiting for thread to stop")
        self._thread.join()

    def loop(self):

        start = time.time()
        self.frame_count += 1

        first_line = self.frame[0,:,:]
        first_line = set([tuple(v) for v in first_line.tolist()])
        # res,ind = numpy.unique(first_line, axis=0, return_index=True)
        # unique_values = res[numpy.argsort(ind)]

        missing_no_signal_colors = NO_SIGNAL_COLORS - first_line

        if len(missing_no_signal_colors) == 0:
            self.frame = numpy.zeros((self.frame.shape[0], self.frame.shape[1], 3), dtype=numpy.uint8)
            # Set to dark/dim red for now
            # self.frame[...] = (100, 0, 0)
            self.frame = numpy.array(NO_SIGNAL_ART_FRAME, dtype=numpy.uint8)
        else:
            height = self.frame.shape[0]
            width = self.frame.shape[1]

            # 2 subframes per frame
            pixel_width = width // (256)

            # subsample the array
            self.frame = self.frame[pixel_width//2::pixel_width, pixel_width//2::pixel_width,:]

            # we should now have a 64x48 frame now

            # Grab the top left pixels


        # TODO: Do we want a way to set a grayscale w/ any base color?
        # Enable color channels based on the config
        if not self.enable_red:
            self.frame[:,:,0] = numpy.zeros([self.frame.shape[0], self.frame.shape[1]])
        if not self.enable_green:
            self.frame[:,:,1] = numpy.zeros([self.frame.shape[0], self.frame.shape[1]])
        if not self.enable_blue:
            self.frame[:,:,2] = numpy.zeros([self.frame.shape[0], self.frame.shape[1]])


        #pad the frame, if needed

        # TODO: This can be executed once per video and cached
        shape = self.frame.shape
        pad_h = self.height - shape[0]  if shape[0] < self.height else 0
        pad_w = self.width - shape[1]  if shape[1] < self.width else 0

        if pad_h > 0 or pad_w > 0:
            
            h_0 = pad_h // 2
            h_1 = h_0 + (pad_h % 2)

            w_0 = pad_w // 2
            w_1 = w_0 + (pad_w % 2)
            
            self.frame = numpy.pad(self.frame, ((h_0,h_1),(w_0,w_1),(0,0)), 'constant')

        x_start = 0
        y_start = 0

        # Center the frame vertically
        if shape[0] > self.height:
            y_start = (shape[0] - self.height) // 2

        # Center the frame horizontally
        # if shape[1] > self.width:
        #     x_start = ((shape[1] - self.width) // 2) + ((shape[1] - self.width) % 2)
        
        self.frame = self.frame[y_start: self.height + y_start, x_start: self.height + x_start]

        self.display.update(self.frame)
        
        elapsed = time.time() - start

        if self.frame_count  % 100 == 0:
            logging.debug(f'Drawing frame took {elapsed * 1000} ms, Frame shape: {self.frame.shape}, x/y start: {x_start},{y_start}')
            logging.debug(f'first line {first_line}')
            logging.debug(f"No signal result: {missing_no_signal_colors}")
            # logging.debug(f'Unique first line {unique_values}')
        
        try:

            start = time.time()
            self.frame = next(self.frame_iter)
            elapsed = time.time() - start

            if self.frame_count  % 100 == 0:
                logging.debug(f'Next video frame took {elapsed * 1000} ms')
        except StopIteration:
            #Restart the video!
            self.setup_video()

    def reset(self):
        self.setup_video()