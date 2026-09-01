"""Reliable per-word Italian-to-English lesson generation with caching."""
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
    digest = hashlib.sha256((key + "|vocab-v4").encode("utf-8")).hexdigest()[:20]
    return os.path.join(config.CACHE_DIR, "lessons", f"{digest}.json")


def _word_cache_path(word):
    digest = hashlib.sha256((word.strip().casefold() + "|word-v4").encode("utf-8")).hexdigest()[:20]
    return os.path.join(config.CACHE_DIR, "lesson_words", f"{digest}.json")


def _extract_json(raw):
    raw = str(raw).strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        raw = re.sub(r"^\s*json\s*", "", raw, flags=re.I)
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("Ollama returned no JSON object")
    return json.loads(match.group(0))


def _valid(lesson):
    if not isinstance(lesson, dict) or not all(str(lesson.get(field, "")).strip() for field in FIELDS):
        return False
    spoken = len(str(lesson["explanation"]).split()) + len(str(lesson["example"]).split())
    return spoken >= 24


def validate_words(words, expected_count=None):
    cleaned = []
    for raw in words:
        word = str(raw).strip()
        if word and not word.lstrip().startswith("#"):
            cleaned.append(word)
    expected = config.VOCAB_WORD_COUNT if expected_count is None else int(expected_count)
    if expected < config.MIN_WORDS or expected > config.MAX_WORDS:
        raise ValueError(f"expected_count must be between {config.MIN_WORDS} and {config.MAX_WORDS}")
    if len(cleaned) != expected:
        raise ValueError(f"Expected exactly {expected} Italian words, got {len(cleaned)}")
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


def load_words(path=None, expected_count=None):
    path = os.fspath(path or config.VOCAB_FILE)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Vocabulary file not found: {path}")
    with open(path, encoding="utf-8-sig") as handle:
        return validate_words(handle.readlines(), expected_count=expected_count)


def _prompt_word(word):
    target = config.WORD_TARGET_SECONDS
    return f"""You are an expert Italian-to-English teacher and professional YouTube educator.
Create one genuinely useful English lesson for this Italian word. The finished video is in English except for the Italian word.
Support approximately {target:.0f} seconds of natural narration without filler.
Return ONLY valid JSON with these exact fields:
{{"italian":"{word}","english":"precise natural English translation, best everyday meaning first","part_of_speech":"noun/verb/adjective/etc.","explanation":"30-50 useful English words explaining meaning, nuance, context, and how a learner uses or recognizes it","example":"one natural English example sentence","image_prompt":"detailed cinematic illustration prompt clearly representing the meaning"}}
For concrete nouns, show the real object in a believable context. For abstract nouns, show a vivid human situation or visual metaphor. For adjectives, show a scene where the quality is obvious.
The image prompt must contain no text, labels, logos, phone UI, screenshots, or watermarks.
ITALIAN WORD: {word}"""


def _write_json_atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    os.replace(temp, path)


def _load_cached_word(word):
    path = _word_cache_path(word)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            lesson = json.load(handle)
        if _valid(lesson) and str(lesson["italian"]).strip().casefold() == word.strip().casefold():
            return lesson
    except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError):
        pass
    return None


def _generate_one(word):
    cached = _load_cached_word(word)
    if cached is not None:
        return cached, True

    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": _prompt_word(word),
        "stream": False,
        "format": "json",
        "keep_alive": config.OLLAMA_KEEP_ALIVE,
        "options": {
            "temperature": 0.25,
            "num_ctx": min(config.OLLAMA_VOCAB_CONTEXT, 4096),
            "num_predict": min(config.OLLAMA_VOCAB_PREDICT, 700),
        },
    }
    attempts = max(1, int(getattr(config, "OLLAMA_RETRIES", 3)))
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            started = time.monotonic()
            response = requests.post(
                config.OLLAMA_URL,
                json=payload,
                timeout=(config.OLLAMA_CONNECT_TIMEOUT, config.OLLAMA_READ_TIMEOUT),
            )
            response.raise_for_status()
            lesson = _extract_json(response.json().get("response", ""))
            if isinstance(lesson, dict) and "words" in lesson:
                items = lesson.get("words") or []
                if len(items) != 1:
                    raise ValueError("Ollama returned the wrong number of word lessons")
                lesson = items[0]
            if not _valid(lesson):
                raise ValueError("Ollama returned an incomplete or too-short lesson")
            if str(lesson["italian"]).strip().casefold() != word.strip().casefold():
                raise ValueError(f"Ollama changed the supplied word: {word}")
            _write_json_atomic(_word_cache_path(word), lesson)
            print(f"[OLLAMA] {word}: complete in {time.monotonic() - started:.1f}s", flush=True)
            return lesson, False
        except (requests.RequestException, ValueError, json.JSONDecodeError, KeyError, TypeError) as exc:
            last_error = exc
            print(f"[OLLAMA] {word}: attempt {attempt}/{attempts} failed: {exc}", flush=True)
            if attempt < attempts:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(f"Ollama failed for '{word}' after {attempts} attempts: {last_error}") from last_error


def generate_lessons(words, use_cache=True, progress=None, expected_count=None):
    words = validate_words(words, expected_count=expected_count)
    path = _cache_path(words)
    if use_cache and os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as handle:
                cached = json.load(handle)
            lessons = cached.get("words", [])
            if [str(x.get("italian", "")).strip().casefold() for x in lessons] == [w.casefold() for w in words] and all(_valid(x) for x in lessons):
                print("[LESSONS] loaded from cache", flush=True)
                return cached
        except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError):
            pass

    started = time.monotonic()
    lessons = []
    total = len(words)
    print(f"[LESSONS] generating {total} lessons with Ollama, one word at a time", flush=True)
    for index, word in enumerate(words, 1):
        # Re-check word cache even when the set cache is absent/incomplete.
        if use_cache:
            lesson = _load_cached_word(word)
            cached = lesson is not None
            if lesson is None:
                lesson, cached = _generate_one(word)
        else:
            lesson, cached = _generate_one(word)
        lessons.append(lesson)
        elapsed = time.monotonic() - started
        status = "cache" if cached else "Ollama"
        print(f"[LESSONS] {index}/{total} {word} | {status} | elapsed={elapsed:.1f}s", flush=True)
        if progress:
            progress(index, total, word)

    result = {"words": lessons}
    _write_json_atomic(path, result)
    print(f"[LESSONS] complete | elapsed={time.monotonic() - started:.1f}s", flush=True)
    return result
