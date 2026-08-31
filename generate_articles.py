"""Generate an original, structured tutorial script for the video pipeline."""
import hashlib
import json
import os
import re
import time
import requests
import config


def _cache_path(title):
    h = hashlib.sha256(title.encode('utf-8')).hexdigest()[:16]
    return os.path.join(config.CACHE_DIR, f'article_{h}.json')


def _call_ollama(prompt):
    """Stream Ollama output with no read-timeout; keep generation deliberately small."""
    started = time.monotonic()
    chunks = []
    chunk_count = 0
    last_report = started
    print('[OLLAMA] generating... (no read timeout; waiting for Ollama)', flush=True)

    with requests.post(
        config.OLLAMA_URL,
        json={
            'model': config.OLLAMA_MODEL,
            'prompt': prompt,
            'stream': True,
            'format': 'json',
            'keep_alive': '10m',
            'options': {
                'temperature': 0.05,
                'num_ctx': 2048,
                'num_predict': 650,
                'top_k': 20,
                'top_p': 0.8,
            },
        },
        timeout=(10, None),
        stream=True,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            piece = data.get('response', '')
            if piece:
                chunks.append(piece)
                chunk_count += 1
            now = time.monotonic()
            if piece and now - last_report >= 1.0:
                elapsed = now - started
                rate = chunk_count / elapsed if elapsed else 0
                print(f'[OLLAMA] chunks={chunk_count} | {rate:.1f} chunks/s | elapsed={elapsed:.1f}s', flush=True)
                last_report = now
            if data.get('done'):
                elapsed = now - started
                print(f'[OLLAMA] complete | chunks={chunk_count} | elapsed={elapsed:.1f}s', flush=True)
                break

    response = ''.join(chunks).strip()
    if not response:
        raise ValueError('Ollama returned an empty response')
    return response


def _extract_json(raw):
    raw = raw.strip()
    if raw.startswith('```'):
        parts = raw.split('```')
        raw = parts[1] if len(parts) > 1 else raw
        raw = re.sub(r'^\s*json\s*', '', raw, flags=re.I)
    match = re.search(r'\{.*\}', raw, re.S)
    if not match:
        raise ValueError('Ollama did not return a JSON object')
    return json.loads(match.group(0))


def _valid_article(article):
    if not isinstance(article, dict):
        return False
    steps = article.get('steps')
    if not isinstance(steps, list) or not steps:
        return False
    return all(isinstance(step, dict) and str(step.get('narration', '')).strip() for step in steps)


def _prompt(title):
    return f'''Create a SHORT original spoken YouTube tutorial for: "{title}".
Return ONLY valid JSON. Do not use markdown.
Use exactly 5-6 logical steps. Keep every field extremely short.
Schema:
{{"title":"short title","intro":"one short sentence","problem":"one short sentence","steps":[{{"step_title":"label","narration":"one short spoken sentence","visual_goal":"what viewer sees","interaction":"tap|long_press|swipe|press_buttons|type|none","target":"control or object","tip":"short tip"}}],"outro":"one short sentence"}}
Every step MUST have non-empty narration. Do not invent uncertain UI details; use a neutral visual description when needed.'''


def generate_article(title, use_cache=True):
    path = _cache_path(title)
    if use_cache and os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            cached = json.load(f)
        if _valid_article(cached):
            print('[OLLAMA] tutorial loaded from cache', flush=True)
            return cached
        try:
            os.remove(path)
        except OSError:
            pass

    raw = _call_ollama(_prompt(title))
    article = _extract_json(raw)
    if not _valid_article(article):
        raise ValueError(f'Invalid tutorial returned for {title}')
    article.setdefault('title', title)
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(article, f, indent=2, ensure_ascii=False)
    return article
