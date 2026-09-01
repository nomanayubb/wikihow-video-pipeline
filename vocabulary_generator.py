"""Generate validated English lessons from an ordered list of Italian words."""
import hashlib
import json
import os
import re
import time

import requests

import config

FIELDS = ("italian", "english", "part_of_speech", "explanation", "example", "image_prompt")


def _cache_path(words):
    key = "\n".join(w.strip().casefold() for w in words)
    digest = hashlib.sha256((key + "|vocab-v2").encode("utf-8")).hexdigest()[:20]
    return os.path.join(config.CACHE_DIR, "lessons", f"{digest}.json")


def _extract_json(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        raw = re.sub(r"^\s*json\s*", "", raw, flags=re.I)
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("Ollama returned no JSON object")
    return json.loads(match.group(0))


def _valid(lesson):
    return isinstance(lesson, dict) and all(str(lesson.get(field, "")).strip() for field in FIELDS)


def _validate_words(words):
    cleaned = [str(w).strip() for w in words if str(w).strip() and not str(w).lstrip().startswith("#")]
    if len(cleaned) != config.VOCAB_WORD_COUNT:
        raise ValueError(f"Expected exactly {config.VOCAB_WORD_COUNT} Italian words, got {len(cleaned)}")
    seen = set()
    duplicates = []
    for word in cleaned:
        key = word.casefold()
        if key in seen:
            duplicates.append(word)
        seen.add(key)
    if duplicates:
        raise ValueError("Duplicate Italian words are not allowed: " + ", ".join(duplicates))
    return cleaned


def load_words(path=None):
    path = path or config.VOCAB_FILE
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Vocabulary file not found: {path}")
    with open(path, encoding="utf-8-sig") as handle:
        return _validate_words(handle.readlines())


def _prompt(words):
    payload = json.dumps(words, ensure_ascii=False)
    return f"""You are an expert Italian-to-English teacher and a professional educational YouTube writer.
Create one rich lesson for every Italian word in the supplied ordered list.
The finished video is entirely in English except when speaking or displaying the Italian word.
For each word write:
- a precise natural English translation;
- the part of speech;
- a clear, descriptive explanation that teaches nuance, context, and everyday usage;
- one natural English example sentence;
- a detailed image prompt for one beautiful cinematic editorial illustration.
Concrete nouns: show the real thing in a believable context.
Abstract nouns: communicate the idea or feeling with a strong visual metaphor or human situation.
Adjectives: show a scene that visibly demonstrates the quality.
Do not include text, labels, logos, phone UI, screenshots, watermarks, or typography in image prompts.
Aim for roughly 40-55 spoken words of useful teaching material per lesson; do not pad or repeat yourself.
Preserve order exactly and return ONLY valid JSON in this exact shape:
{{"words":[{{"italian":"...","english":"...","part_of_speech":"...","explanation":"...","example":"...","image_prompt":"..."}}]}}
ITALIAN WORDS: {payload}"""


def generate_lessons(words, use_cache=True, progress=None):
    words = _validate_words(words)
    path = _cache_path(words)
    if use_cache and os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as handle:
                cached = json.load(handle)
            lessons = cached.get("words", [])
            if len(lessons) == len(words) and all(_valid(x) for x in lessons):
                print("[LESSONS] loaded from cache", flush=True)
                return cached
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

    started = time.monotonic()
    print(f"[LESSONS] generating {len(words)} lessons with Ollama", flush=True)
    response = requests.post(
        config.OLLAMA_URL,
        json={
            "model": config.OLLAMA_MODEL,
            "prompt": _prompt(words),
            "stream": False,
            "format": "json",
            "keep_alive": config.OLLAMA_KEEP_ALIVE,
            "options": {
                "temperature": 0.25,
                "num_ctx": config.OLLAMA_VOCAB_CONTEXT,
                "num_predict": config.OLLAMA_VOCAB_PREDICT,
            },
        },
        timeout=(config.OLLAMA_CONNECT_TIMEOUT, config.OLLAMA_READ_TIMEOUT),
    )
    response.raise_for_status()
    raw = response.json().get("response", "")
    data = _extract_json(raw)
    lessons = data.get("words", [])
    if len(lessons) != len(words) or not all(_valid(x) for x in lessons):
        raise ValueError("Ollama returned an incomplete vocabulary lesson set")
    for expected, lesson in zip(words, lessons):
        if lesson["italian"].strip().casefold() != expected.casefold():
            raise ValueError(f"Ollama changed or reordered vocabulary word: {expected}")

    result = {"words": lessons}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)
    elapsed = time.monotonic() - started
    print(f"[LESSONS] complete | elapsed={elapsed:.1f}s", flush=True)
    if progress:
        progress("Lesson generation complete")
    return result
