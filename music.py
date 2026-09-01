"""Generate a copyright-safe procedural background soundtrack."""
import math
import os
import struct
import wave

import config

MOODS = {
    "meditative": [220.00, 261.63, 329.63, 392.00],
    "funny": [261.63, 329.63, 392.00, 523.25],
    "adventure": [196.00, 246.94, 293.66, 392.00],
}


def generate(duration, out_path, mood=None):
    mood = (mood or config.MUSIC_MOOD).lower()
    roots = MOODS.get(mood, MOODS["meditative"])
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
        return out_path

    rate = 22050
    channels = 2
    amplitude = 0.055
    total = int(duration * rate)
    beat = 60.0 / config.MUSIC_BPM
    chord_len = beat * 4
    frames = bytearray()

    with wave.open(out_path + ".tmp", "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        chunk = []
        for i in range(total):
            t = i / rate
            chord = roots[int(t / chord_len) % len(roots)]
            pulse = math.sin(2 * math.pi * chord * t)
            third = math.sin(2 * math.pi * chord * 1.25 * t + 0.4)
            fifth = math.sin(2 * math.pi * chord * 1.5 * t + 1.1)
            pad = (pulse + 0.55 * third + 0.35 * fifth) / 1.9
            shimmer = 0.12 * math.sin(2 * math.pi * chord * 2.0 * t)
            tremolo = 0.82 + 0.18 * math.sin(2 * math.pi * 0.16 * t)
            value = amplitude * (pad + shimmer) * tremolo
            # gentle fade-in/out avoids clicks at the boundaries
            if t < 1.5:
                value *= t / 1.5
            if duration - t < 2.0:
                value *= max(0.0, (duration - t) / 2.0)
            sample = max(-1.0, min(1.0, value))
            pcm = int(sample * 32767)
            chunk.append(struct.pack("<hh", pcm, pcm))
            if len(chunk) >= 2048:
                wf.writeframes(b"".join(chunk))
                chunk.clear()
        if chunk:
            wf.writeframes(b"".join(chunk))
    os.replace(out_path + ".tmp", out_path)
    return out_path
