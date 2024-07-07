import termios
import numpy
import serial
import threading
import signal
import struct
import logging
import time

__version__ = '0.0.3'

MODE_DEFAULT = 0
MODE_HUB75 = 1

# Class to represent a single Galactic Unicorn display
# handy place to store the serial port opening and such
class Display:
    # Just in case we get fancy and use RGB565 or RGB332
    BYTES_PER_PIXEL = 4

    WAVEFORM_NOISE = 128
    WAVEFORM_SQUARE = 64
    WAVEFORM_SAW = 32
    WAVEFORM_TRIANGLE = 16
    WAVEFORM_SINE = 8
    WAVEFORM_WAVE = 1

    PHASE_ATTACK = 0
    PHASE_DECAY = 1
    PHASE_SUSTAIN = 2
    PHASE_RELEASE = 3
    PHASE_OFF = 4

    def __init__(self, port, w, h, x, y, rotate=0, dummy=False, mode=MODE_DEFAULT):
        self.path = port
        self.port = None
        self.mode = mode
        self.w = w
        self.h = h
        self.x = x
        self.y = y
        self.rotate = int(rotate / 90)

        if rotate in (90, 270):
            self.w, self.h = (self.h, self.w)

        self.is_setup = False
        self.dummy = dummy

        self._thread = None
        self._stop_flag = threading.Event()
        self._port_write_lock = threading.Lock()
        self._message_queue = []
        self._buffer = None
        self._frame_count = 0

    def setup(self):
        if self.dummy:
            # Nothing to do here, move along
            self.is_setup = True
            return
        try:
            logging.debug(f"{self.x},{self.y}: Creating serial port")
            self.port = serial.Serial(self.path, write_timeout=1)
            logging.debug(f"{self.x},{self.y}: Clearing display")
            self.clear()
            self.is_setup = True
        except Exception as e:
            logging.debug(f"{self.x},{self.y}: Exception while setting up display", exc_info = e)
            self.port = None
            self.is_setup = False
            
    def start(self):
        logging.debug(f"{self.x},{self.y}: Starting thread")
        if self._thread is not None:
            raise Exception("Thread is already started")
        self._thread = threading.Thread(target=self.run, name=f'Multiverse-Display-{self.x},{self.y}')
        self._thread.start()
            
    def run(self):
        logging.debug(f"{self.x},{self.y}: Running....")
        while not self._stop_flag.wait(timeout=0.005):
            if self.dummy:
                # Nothing to do here, move along
                continue
            try:
                # If the display was closed, or the connection died, and no one stopped the thread,
                # we want to re-run setup to re-establish the conneciton
                if not self.is_setup:
                    self.setup()
                self._update_display()
                self._write_messages()
                # Not sure if we need to do this, but lets make sure the input buffer doesn't fill up and block something
                if self.port is not None and self.port.isOpen():
                    self.port.reset_input_buffer()
            except Exception as e:
                logging.debug(
                    f"{self.x},{self.y}: Exception in run loop. Closing port to attempt re-attaching", exc_info=e
                )
                self._close()

        logging.debug(f"{self.x},{self.y}: Running loop has finished")
        self.clear()
        self._close()
        logging.debug(f"{self.x},{self.y}: Run is done")


    def _update_display(self):
        start = time.time()
        if self._buffer is not None:
            self.write(header=b"multiverse:data", data=self._buffer)
        self._frame_count += 1
        if self._frame_count % 100 == 0:
            frame_time = time.time() - start
            print(f"Frame time: {frame_time * 1000}ms, FPS: {1/frame_time}")

    def write(self, header, data=None):
        if self.port is None:
            return

        # All writes to the port should be protected by this lock to prevent interleaved messages
        self._port_write_lock.acquire()

        
        if self.dummy:
            #simulate 10ms transmission time
            time.sleep(0.010)
            return

        try:
            self.port.write(header)
            if data is not None:
                self.port.write(data)
            self.port.flush()
        
        except serial.SerialTimeoutException as e:
            logging.debug(
                f"{self.x},{self.y}: Timeout while writing. Waiting to write: {self.port.out_waiting}. Waiting to read: {self.port.in_waiting}", exc_info = e
            )
            self._close()
        except serial.SerialException as e:
            logging.debug(f"{self.x},{self.y}: SerialException while writing.", exc_info = e)
            self._close()
        except termios.error as e:
            logging.debug(f"{self.x},{self.y}: termios.error while writing.", exc_info = e)
            self._close()
        except Exception as e:
            logging.debug(f"{self.x},{self.y}: Error while writing", exc_info = e)
            raise e # don't want to swallow the exception
        finally:
            self._port_write_lock.release()

    def _write_display_buffer(self):
        self.write(self._buffer)

    def _write_messages(self):
        queue_size = len(self._message_queue)
        for i in range(0,queue_size):
            header,data = self._message_queue.pop(0)
            self.write(header=header,data=data)

    def clear(self):
        zeros = numpy.zeros((self.w, self.h, self.BYTES_PER_PIXEL), dtype=numpy.uint8).tobytes()
        self.write(header=b"multiverse:data", data=zeros)
        if self._thread is not None:
            self._buffer = zeros

    def bootloader(self):
        if self.port is None:
            return
        if self._thread is not None:
            self._stop_flag.set()
            self._thread.join()
            self._message_queue.clear()
        self.write(header=b"multiverse:_usb")

    def reset(self):
        if self.port is None:
            return
        if self._thread is not None:
            self._stop_flag.set()
            self._thread.join()
            self._message_queue.clear()
        self.write(header=b"multiverse:_rst")

    def play_note(self, channel, frequency, waveform=WAVEFORM_TRIANGLE, attack=10, decay=200, sustain=0, release=0, phase=PHASE_ATTACK):
        header = b"multiverse:note"
        data  = struct.pack("<BHBHHHHB", channel, int(frequency), waveform, attack, decay, sustain, release, phase)
        self._message_queue.append((header,data))
        if not self._thread is not None:
            self._write_messages()

    def update(self, source):
        #TODO move this to the multiverse. The display shouldn't get the whole buffer,
        # or be responsible for determining what to display out of it. Let the multiverse
        # decide
        source = source[self.y:self.y + self.h, self.x:self.x + self.w]
        
        # Get the source buffer width
        bh, bw, depth = source.shape

        # Create a new target buffer matching the display size
        target = numpy.zeros((self.h, self.w, depth), dtype=numpy.uint32)
    
        # Copy any pixels available from the source to the target buffer
        target[0:bh, 0:bw] = source

        # Conversion into Interstate 75's 10bit per pixel interleaved format
        if self.mode == MODE_HUB75 and self.h in (32, 64):
            #new_buffer = numpy.zeros(target.shape, dtype=numpy.uint32)

            # Interleave upper and lower display sections
            # new_buffer[::,::2] = target[:int(self.h / 2)].reshape(self.h, int(self.w / 2), depth)
            # new_buffer[::,1::2] = target[int(self.h / 2):].reshape(self.h, int(self.w / 2), depth)


            # Pack into 10bit, uint32, 0b00rrrrrrrrrrggggggggggbbbbbbbbbb
            # target = (new_buffer[::,::,0] & 0x3ff) << 20 | (new_buffer[::,::,1] & 0x3ff) << 10 | (new_buffer[::,::,2] & 0x3ff)
            

            # first_pixel = target[0,0]
            # print(f'RGBX = {first_pixel}')
            
            # r = first_pixel[2]
            # g = first_pixel[1]
            # b = first_pixel[0]

            # r565 = r >> 3
            # g565 = g >> 2
            # b565 = b >> 3

            # rgb565 = ((r565) << 11) | ((g565) << 5) | (b565)
            # print(f'rgb565: {r565} {g565} {b565} #{hex(rgb565)}')
            # Pack into RGB565, rrrrrggggggbbbbb
            target = ((target[::,::,2] >> 3 ) << 11 | (target[::,::,1] >> 2 ) << 5 | (target[::,::,0] >> 3 )).astype(numpy.dtype('>u2'))

        else:
            # Pack into 8bit, uint32, 0b00000000bbbbbbbbggggggggrrrrrrrr
            target = numpy.clip(target, 0, 255).astype(numpy.uint8)

        target = numpy.rot90(target, self.rotate).tobytes()
        #print(f'{target[0]} {target[1]} {target[2]} {target[3]}')

        if self._thread is not None:
            # This is thread safe, since we're replacing the old buffer with a new one
            # It's also a copy, becauses of tobytes, so we don't need to worry about another thread
            # changing it on us
            self._buffer = target
        else:
            self.write(header=b"multiverse:data", data=target)

    def stop(self):
        self._stop_flag.set()
        if self._thread is not None:
            self._thread.join()
        self.clear()

    
    def stop(self):
        logging.debug(f"{self.x},{self.y}: Stopping display thread")
        self._stop_flag.set()

    def join(self):
        if self._thread is None:
            logging.debug(f"{self.x},{self.y}: No thread to join, returning")
            return
        logging.debug(f"{self.x},{self.y}: Waiting for thread to stop")
        self._thread.join()

    def _close(self):
        logging.debug(f"{self.x},{self.y}: Cleaning up and Closing port")
        if self.port is not None and self.port.isOpen():
            try:
                logging.debug(f"{self.x},{self.y}: Resetting input buffer")
                self.port.reset_input_buffer()
            except Exception as e:
                logging.debug(
                    f"{self.x},{self.y}: Exception while resetting input buffer."
                )
                logging.debug(e)

            try:
                logging.debug(f"{self.x},{self.y}: Resetting output buffer")
                self.port.reset_output_buffer()
            except Exception as e:
                logging.debug(
                    f"{self.x},{self.y}: Exception while resetting input buffer."
                )
                logging.debug(e)
            try:
                logging.debug(f"{self.x},{self.y}: Closing port")
                self.port.close()
            except Exception as e:
                logging.debug(f"{self.x},{self.y}: Exception while closing port.")
                logging.debug(e)
        logging.debug(f"{self.x},{self.y}: Unsetting port")
        self.port = None
        self.is_setup = False

    def __del__(self):
        if self.port is None or not self.port.isOpen():
            return
        try:
            logging.debug(f"{self.x},{self.y}: __del__ cleaning up display")
            self._stop_flag.set()
            self._close()
        except:
            pass


class Multiverse:
    def __init__(self, *args):
        self.displays = list(args)
        self._delegate_handler = None

    def setup(self, use_threads=True):
        for display in self.displays:
            if use_threads:
                display.start()
            else:
                display.setup()
        
        # Set up a signal handler if we don't have one. Otherwise
        # let the caller decide to register or handle the shutdown
        # of the multiverse themselves
        if not callable(signal.getsignal(signal.SIGINT)):
            self.register_signal_handler()

    def register_signal_handler(self):
        # Get any user signal handlers
        self._delegate_handler = signal.getsignal(signal.SIGINT)
        # Install our own
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig, frame):
        self.stop()
        if callable(self._delegate_handler):
            self._delegate_handler(sig, frame)

    def stop(self):
        logging.debug("Stopping multiverse displays")
        for d in self.displays:
            d.stop()
        logging.debug("Waiting for display threads to stop")
        for d in self.displays:
            d.join()
        logging.debug("Multiverse display stop complete")

    def add(self, display):
        self.displays.append(display)

    def bootloader(self):
        for display in self.displays:
            display.bootloader()

    def reset(self):
        for display in self.displays:
            display.reset()

    def update(self, buffer):
        for display in self.displays:
            display.update(buffer)

    def play_note(self, *args, **kwargs):
        for display in self.displays:
            display.play_note(*args, **kwargs)

