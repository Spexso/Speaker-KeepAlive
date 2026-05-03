import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024

stream = None
stream_lock = threading.Lock()
is_playing = False
_phase = 0.0


def audio_callback(outdata, frames, time_info, status):
    global _phase
    # 20 Hz sine at ~-80 dB — inaudible but prevents driver silence detection
    t = (_phase + np.arange(frames)) / SAMPLE_RATE
    outdata[:, 0] = (np.sin(2 * np.pi * 20 * t) * 1e-4).astype(np.float32)
    _phase = (_phase + frames) % SAMPLE_RATE


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
