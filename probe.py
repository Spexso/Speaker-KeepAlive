"""Find a keep-alive signal your speaker accepts.

Usage: python probe.py <freq_hz> <level_dbfs>
e.g.   python probe.py 30 -50
Plays that tone to the current default output until Ctrl+C and prints elapsed time.
"""
import sys
import time
import numpy as np
import sounddevice as sd

freq = float(sys.argv[1]) if len(sys.argv) > 1 else 30
db = float(sys.argv[2]) if len(sys.argv) > 2 else -50
amp = 10 ** (db / 20)
rate = 44100
phase = 0


def cb(outdata, frames, time_info, status):
    global phase
    t = (phase + np.arange(frames)) / rate
    outdata[:, 0] = (np.sin(2 * np.pi * freq * t) * amp).astype(np.float32)
    phase += frames


print(f"Device: {sd.query_devices(kind='output')['name']}")
print(f"Tone:   {freq:g} Hz at {db:g} dBFS  (Ctrl+C to stop)")
start = time.time()
with sd.OutputStream(samplerate=rate, channels=1, dtype='float32', callback=cb):
    try:
        while True:
            m, s = divmod(int(time.time() - start), 60)
            print(f"\r{m:02d}:{s:02d} elapsed", end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print()
