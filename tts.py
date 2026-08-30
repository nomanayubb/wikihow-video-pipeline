"""
Step 2: Text -> speech audio + word-level timestamps.

Uses edge-tts (free, Microsoft neural voices, no API key). Returns both the
mp3 file path and a list of word boundaries so captions/images can be
synced precisely to what's being said.
"""
import asyncio
import os
import edge_tts

import config


async def _synthesize(text: str, out_path: str, voice: str, rate: str):
    words = []
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 10_000_000,   # 100ns ticks -> seconds
                    "duration": chunk["duration"] / 10_000_000,
                })
    return words


def synthesize(text: str, out_path: str, voice: str = None, rate: str = None) -> list:
    """Blocking wrapper. Returns list of {text, start, duration} in seconds."""
    voice = voice or config.TTS_VOICE
    rate = rate or config.TTS_RATE
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    return asyncio.run(_synthesize(text, out_path, voice, rate))


if __name__ == "__main__":
    w = synthesize(
        "Press Windows plus I to open settings, then go to Windows Update.",
        "cache/test.mp3",
    )
    for item in w:
        print(f"{item['start']:.2f}s  {item['text']}")
