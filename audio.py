import ctypes
import threading
from ctypes import wintypes

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024

# Sub-bass reads as silence to the speaker: it only reproduces 100 Hz-20 kHz and
# filters below that before its idle detection (30 Hz @ -50 dBFS still let it
# power off every 15 min). 19 kHz is inside its range and survives SBC, but is
# above what adults can hear.
TONE_HZ = 19000
TONE_AMPLITUDE = 10 ** (-30 / 20)

# How often to check whether the default output device changed or the stream died
WATCHDOG_INTERVAL = 3.0

stream = None
stream_lock = threading.Lock()
is_playing = False
_phase = 0
_callbacks = 0  # bumped by the audio callback; a stalled count means a dead stream
_device_name = None
_watchdog = None
_watchdog_stop = threading.Event()

_winmm = ctypes.WinDLL("winmm")
_WAVE_MAPPER = 0xFFFFFFFF
_DRVM_MAPPER_PREFERRED_GET = 0x2015


class _WAVEOUTCAPSW(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD),
        ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * 32),
        ("dwFormats", wintypes.DWORD),
        ("wChannels", wintypes.WORD),
        ("wReserved1", wintypes.WORD),
        ("dwSupport", wintypes.DWORD),
    ]


def get_default_output_name():
    """Live query of the Windows default playback device (PortAudio caches its list)."""
    dev = wintypes.DWORD()
    flags = wintypes.DWORD()
    if _winmm.waveOutMessage(ctypes.c_void_p(_WAVE_MAPPER), _DRVM_MAPPER_PREFERRED_GET,
                             ctypes.byref(dev), ctypes.byref(flags)) != 0:
        return None
    caps = _WAVEOUTCAPSW()
    if _winmm.waveOutGetDevCapsW(ctypes.c_size_t(dev.value), ctypes.byref(caps),
                                 ctypes.sizeof(caps)) != 0:
        return None
    return caps.szPname


def audio_callback(outdata, frames, time_info, status):
    global _phase, _callbacks
    t = (_phase + np.arange(frames)) / SAMPLE_RATE
    outdata[:, 0] = (np.sin(2 * np.pi * TONE_HZ * t) * TONE_AMPLITUDE).astype(np.float32)
    _phase = (_phase + frames) % SAMPLE_RATE
    _callbacks += 1


def _open_stream():
    global stream, _device_name
    # Re-scan devices so we pick up the *current* default, not the one at launch
    try:
        sd._terminate()
    except sd.PortAudioError:
        pass  # already uninitialized because a previous re-init failed
    sd._initialize()
    _device_name = get_default_output_name()
    stream = sd.OutputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=1,
        dtype='float32',
        callback=audio_callback
    )
    stream.start()


def _close_stream():
    global stream
    if stream is None:
        return
    try:
        stream.stop()
        stream.close()
    except sd.PortAudioError:
        pass
    stream = None


def _watchdog_loop():
    last_callbacks = -1
    while not _watchdog_stop.wait(WATCHDOG_INTERVAL):
        with stream_lock:
            if not is_playing:
                continue
            try:
                # A stream can report active yet stop calling back (e.g. after sleep)
                healthy = (stream is not None and stream.active
                           and _callbacks != last_callbacks)
                last_callbacks = _callbacks
                if healthy and get_default_output_name() == _device_name:
                    continue
                _close_stream()
                _open_stream()
            except Exception:
                # No usable output right now; retry next tick. Never let this thread die.
                _close_stream()


def start_audio():
    global is_playing, _watchdog
    with stream_lock:
        if is_playing:
            return
        is_playing = True
        try:
            _open_stream()
        except sd.PortAudioError:
            _close_stream()  # watchdog will retry
    if _watchdog is None:
        _watchdog_stop.clear()
        _watchdog = threading.Thread(target=_watchdog_loop, daemon=True)
        _watchdog.start()


def stop_audio():
    global is_playing
    with stream_lock:
        is_playing = False
        _close_stream()
