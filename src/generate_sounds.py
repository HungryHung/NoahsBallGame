"""Generate fun sound effect WAV files for the ball game.

Run once: python generate_sounds.py
Creates assets/boing.wav, assets/bonk.wav, assets/whoosh.wav, assets/pop.wav
"""

import os
import struct
import wave

import numpy as np

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
SAMPLE_RATE = 22050


def _write_wav(filename, samples):
    """Write mono 16-bit WAV file."""
    path = os.path.join(ASSETS_DIR, filename)
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767).astype(np.int16)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())


def _make_boing():
    """Bouncy spring 'boing' — rising frequency sweep with wobble."""
    duration = 0.35
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Frequency sweeps from 300 Hz to 900 Hz
    freq = 300 + 600 * (t / duration)
    # Add a wobble modulation
    wobble = 1.0 + 0.3 * np.sin(2 * np.pi * 12 * t)
    # Envelope: quick attack, medium decay
    env = np.exp(-3.0 * t) * wobble
    signal = env * np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
    return signal * 0.8


def _make_bonk():
    """Cartoon 'bonk' — low thud with quick decay."""
    duration = 0.25
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Low frequency thud dropping from 250 to 80 Hz
    freq = 250 - 170 * (t / duration)
    env = np.exp(-8.0 * t)
    thud = env * np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
    # Add a short click at the start for impact feel
    click_env = np.exp(-60.0 * t)
    click = click_env * np.sin(2 * np.pi * 800 * t) * 0.4
    signal = thud * 0.9 + click
    return signal * 0.8


def _make_whoosh():
    """Quick 'whoosh' — filtered noise burst."""
    duration = 0.3
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    noise = np.random.default_rng(42).uniform(-1, 1, len(t))
    # Bandpass-ish: mix two sine waves with noise modulation
    carrier = np.sin(2 * np.pi * 400 * t) + np.sin(2 * np.pi * 800 * t)
    env = np.sin(np.pi * t / duration) ** 2  # smooth bell curve
    signal = env * (noise * 0.5 + carrier * 0.2)
    return signal * 0.5


def _make_pop():
    """Short 'pop' — snappy click."""
    duration = 0.1
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = 600 - 400 * (t / duration)
    env = np.exp(-25.0 * t)
    signal = env * np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
    return signal * 0.8


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    _write_wav("boing.wav", _make_boing())
    _write_wav("bonk.wav", _make_bonk())
    _write_wav("whoosh.wav", _make_whoosh())
    _write_wav("pop.wav", _make_pop())

    print(f"Sound effects created in {ASSETS_DIR}:")
    print("  boing.wav  (punch)")
    print("  bonk.wav   (headbutt)")
    print("  whoosh.wav (throw)")
    print("  pop.wav    (grab)")


if __name__ == "__main__":
    main()
