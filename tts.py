"""Edge TTS helpers with retries, atomic output, and bounded concurrency."""
import asyncio
import os

import edge_tts

import config


async def _synthesize(text: str, out_path: str, voice: str, rate: str):
    words = []
    temp_path = out_path + ".tmp"
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        with open(temp_path, "wb") as handle:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    handle.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    words.append({
                        "text": chunk["text"],
                        "start": chunk["offset"] / 10_000_000,
                        "duration": chunk["duration"] / 10_000_000,
                    })
        if not os.path.isfile(temp_path) or os.path.getsize(temp_path) == 0:
            raise RuntimeError("Edge TTS produced an empty audio file")
        os.replace(temp_path, out_path)
        return words
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


async def _one(index, text, out_path, voice, rate, semaphore):
    async with semaphore:
        last_error = None
        for attempt in range(config.TTS_RETRIES):
            try:
                return index, await _synthesize(text, out_path, voice, rate)
            except Exception as exc:
                last_error = exc
                if attempt + 1 < config.TTS_RETRIES:
                    await asyncio.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"TTS failed after {config.TTS_RETRIES} attempts for item {index + 1}: {last_error}") from last_error


async def _synthesize_many(items, voice, rate, max_concurrency):
    semaphore = asyncio.Semaphore(max(1, max_concurrency))
    tasks = [
        asyncio.create_task(_one(index, text, out_path, voice, rate, semaphore))
        for index, (text, out_path) in enumerate(items)
    ]
    results = await asyncio.gather(*tasks)
    return [words for _, words in sorted(results)]


def synthesize(text: str, out_path: str, voice: str = None, rate: str = None) -> list:
    voice = voice or config.TTS_VOICE
    rate = rate or config.TTS_RATE
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    return asyncio.run(_one(0, text, out_path, voice, rate, asyncio.Semaphore(1))).__iter__().__next__()[1]


def synthesize_many(items, voice: str = None, rate: str = None, max_concurrency: int = None) -> list:
    items = list(items)
    if not items:
        return []
    voice = voice or config.TTS_VOICE
    rate = rate or config.TTS_RATE
    max_concurrency = max_concurrency or config.TTS_CONCURRENCY
    for _, out_path in items:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    return asyncio.run(_synthesize_many(items, voice, rate, max_concurrency))
