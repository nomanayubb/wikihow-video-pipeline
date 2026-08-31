"""Text-to-speech audio plus word-level timestamps using edge-tts."""
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
                    "start": chunk["offset"] / 10_000_000,
                    "duration": chunk["duration"] / 10_000_000,
                })
    return words


async def _synthesize_many(items, voice: str, rate: str, max_concurrency: int):
    semaphore = asyncio.Semaphore(max(1, max_concurrency))

    async def one(index, text, out_path):
        async with semaphore:
            words = await _synthesize(text, out_path, voice, rate)
            return index, words

    tasks = [
        asyncio.create_task(one(i, text, out_path))
        for i, (text, out_path) in enumerate(items)
    ]
    results = await asyncio.gather(*tasks)
    return [words for _, words in sorted(results)]


def synthesize(text: str, out_path: str, voice: str = None, rate: str = None) -> list:
    """Blocking wrapper. Returns word timestamps in seconds."""
    voice = voice or config.TTS_VOICE
    rate = rate or config.TTS_RATE
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    return asyncio.run(_synthesize(text, out_path, voice, rate))


def synthesize_many(items, voice: str = None, rate: str = None, max_concurrency: int = 3) -> list:
    """Synthesize multiple scenes concurrently and return timestamps in input order."""
    voice = voice or config.TTS_VOICE
    rate = rate or config.TTS_RATE
    for _, out_path in items:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if not items:
        return []
    return asyncio.run(_synthesize_many(items, voice, rate, max_concurrency))


if __name__ == "__main__":
    w = synthesize(
        "Press Windows plus I to open settings, then go to Windows Update.",
        "cache/test.mp3",
    )
    for item in w:
        print(f"{item['start']:.2f}s  {item['text']}")
