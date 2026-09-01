"""Turn a list of Italian words into rich English vocabulary lessons."""
import hashlib
import json
import os
import re
import time
import requests

import config


def _cache_path(words):
    key = "|".join(w.strip().lower() for w in words)
    h = hashlib.sha256((key + "|vocab-v1").encode("utf-8")).hexdigest()[:16]
    return os.path.join(config.CACHE_DIR, f"vocabulary_{h}.json")


def _extract_json(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        raw = re.sub(r"^json\s*", "", raw, flags=re.I)
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("Ollama did not return vocabulary JSON")
    return json.loads(match.group(0))


def _valid(item):
    return isinstance(item, dict) and all(
        str(item.get(k, "")).strip()
        for k in ("italian", "english", "part_of_speech", "explanation", "example", "image_prompt")
    )


def _prompt(words):
    payload = json.dumps(words, ensure_ascii=False)
    return f"""You are an expert English teacher and YouTube educational scriptwriter.
Create one polished, engaging vocabulary lesson for every Italian word below.
The video is entirely in English except for the Italian word itself.
Each lesson will be narrated for about {config.WORD_TARGET_SECONDS} seconds.
Explain the meaning naturally and descriptively, including nuance, common usage,
part of speech, and one simple example sentence. Do not pad with repetition.
For concrete nouns, explain what the object/thing looks like and where it is used.
For abstract nouns, explain the idea or feeling with a vivid everyday example.
For adjectives, explain what quality they describe and give a vivid contrast.
Create an image prompt that depicts the word's meaning, not text, logos, or UI.
The image prompt must work for a beautiful editorial YouTube illustration.
Return ONLY valid JSON with this exact shape:
{{"words":[{{"italian":"...","english":"...","part_of_speech":"...","explanation":"...","example":"...","image_prompt":"..."}}]}}
Do not omit or reorder words.
ITALIAN WORDS: {payload}"""


def generate_lessons(words, use_cache=True, progress=None):
    words = [w.strip() for w in words if w.strip()]
    if not words:
        raise ValueError("No Italian words were supplied")
    if len(words) != config.VOCAB_WORD_COUNT:
        raise ValueError(f"Expected exactly {config.VOCAB_WORD_COUNT} Italian words, got {len(words)}")

    path = _cache_path(words)
    if use_cache and os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            lessons = data.get("words", [])
            if len(lessons) == len(words) and all(_valid(x) for x in lessons):
                print("[VOCAB] lessons loaded from cache", flush=True)
                return data
        except (OSError, json.JSONDecodeError):
            pass

    started = time.monotonic()
    print(f"[VOCAB] generating {len(words)} English lessons with Ollama...", flush=True)
    with requests.post(
        config.OLLAMA_URL,
        json={
            "model": config.OLLAMA_MODEL,
            "prompt": _prompt(words),
            "stream": False,
            "format": "json",
            "keep_alive": config.OLLAMA_KEEP_ALIVE,
            "options": {
                "temperature": 0.35,
                "num_ctx": config.OLLAMA_VOCAB_CONTEXT,
                "num_predict": config.OLLAMA_VOCAB_PREDICT,
            },
        },
        timeout=(config.OLLAMA_CONNECT_TIMEOUT, config.OLLAMA_READ_TIMEOUT),
    ) as r:
        r.raise_for_status()
        raw = r.json().get("response", "")

    data = _extract_json(raw)
    lessons = data.get("words", [])
    if len(lessons) != len(words) or not all(_valid(x) for x in lessons):
        raise ValueError("Ollama returned an incomplete vocabulary lesson set")
    for expected, lesson in zip(words, lessons):
        if lesson["italian"].strip().lower() != expected.lower():
            raise ValueError(f"Ollama reordered or changed vocabulary word: {expected}")

    data["words"] = lessons
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    elapsed = time.monotonic() - started
    print(f"[VOCAB] lessons complete | elapsed={elapsed:.1f}s", flush=True)
    if progress:
        progress("Vocabulary lessons ready")
    return data


def load_words(path=None):
    path = path or config.VOCAB_FILE
    if not os.path.exists(path):
        raise FileNotFoundError(f"Vocabulary file not found: {path}")
    with open(path, encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip() and not line.lstrip().startswith("#")]
    return words
