import os
import threading
import wave

import numpy as np
import sounddevice as sd

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

_SOUND_FILES = {
    "punch": "boing.wav",
    "headbutt": "bonk.wav",
    "throw": "whoosh.wav",
    "grab": "pop.wav",
}

# Preload sounds as float32 numpy arrays
_SOUNDS = {}
_SAMPLE_RATE = 22050
for _key, _filename in _SOUND_FILES.items():
    _path = os.path.join(_ASSETS_DIR, _filename)
    if os.path.exists(_path):
        with wave.open(_path, "r") as _wf:
            _SAMPLE_RATE = _wf.getframerate()
            _n = _wf.getnframes()
            _raw = _wf.readframes(_n)
            _arr = np.frombuffer(_raw, dtype=np.int16).astype(np.float32) / 32767.0
            _SOUNDS[_key] = _arr

# Persistent audio stream with callback — zero main-thread blocking
_lock = threading.Lock()
_current_sound = None  # numpy array currently playing
_play_pos = 0          # current read position


def _audio_callback(outdata, frames, time_info, status):
    global _current_sound, _play_pos
    with _lock:
        if _current_sound is None:
            outdata[:] = 0
            return
        remaining = len(_current_sound) - _play_pos
        if remaining <= 0:
            outdata[:] = 0
            _current_sound = None
            _play_pos = 0
            return
        chunk = min(frames, remaining)
        outdata[:chunk, 0] = _current_sound[_play_pos:_play_pos + chunk]
        if chunk < frames:
            outdata[chunk:] = 0
        _play_pos += chunk


_stream = sd.OutputStream(
    samplerate=_SAMPLE_RATE,
    channels=1,
    dtype="float32",
    callback=_audio_callback,
    blocksize=512,
    latency="low",
)
_stream.start()


def play(hit_type):
    """Play the sound for a given hit type (non-blocking, near-instant)."""
    global _current_sound, _play_pos
    data = _SOUNDS.get(hit_type)
    if data is not None:
        with _lock:
            _current_sound = data
            _play_pos = 0
