import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024

stream = None
stream_lock = threading.Lock()
is_playing = False


def audio_callback(outdata, frames, time_info, status):
    outdata[:] = np.zeros((frames, 1), dtype=np.float32)


def start_audio():
    global stream, is_playing
    with stream_lock:
        if stream is not None:
            return
        stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=1,
            dtype='float32',
            callback=audio_callback
        )
        stream.start()
        is_playing = True


def stop_audio():
    global stream, is_playing
    with stream_lock:
        if stream is None:
            return
        stream.stop()
        stream.close()
        stream = None
        is_playing = False
