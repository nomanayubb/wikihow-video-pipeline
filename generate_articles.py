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


def _call_ollama(prompt, timeout=90):
    """Generate with Ollama streaming, with a hard output cap for fast completion."""
    started = time.monotonic()
    token_count = 0
    chunks = []
    last_report = started

    print('[OLLAMA] Request sent; waiting for generation...', flush=True)
    try:
        with requests.post(
            config.OLLAMA_URL,
            json={
                'model': config.OLLAMA_MODEL,
                'prompt': prompt,
                'stream': True,
                'format': 'json',
                'options': {
                    'temperature': 0.1,
                    'num_ctx': 4096,
                    'num_predict': 900,
                },
            },
            timeout=(10, timeout),
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
                    token_count += 1

                now = time.monotonic()
                if piece and (now - last_report >= 1.0):
                    elapsed = now - started
                    rate = token_count / elapsed if elapsed else 0
                    print(
                        f'[OLLAMA] generating... chunks={token_count} | '
                        f'{rate:.1f} chunks/s | elapsed={elapsed:.1f}s',
                        flush=True,
                    )
                    last_report = now

                if data.get('done'):
                    elapsed = now - started
                    print(
                        f'[OLLAMA] generation complete | chunks={token_count} | '
                        f'elapsed={elapsed:.1f}s',
                        flush=True,
                    )
                    break
    except requests.RequestException:
        raise

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


def _prompt(title, retry=False):
    retry_note = (
        '\nIMPORTANT: The previous response was invalid. You MUST include a non-empty steps array. '
        'Return exactly one JSON object and nothing else.\n'
        if retry else ''
    )
    return f'''Create an ORIGINAL, accurate, spoken YouTube tutorial for: "{title}".
Do not copy any existing article.
{retry_note}
Keep the response SHORT so it can be generated quickly: use 6-8 logical steps maximum, with 1-2 short spoken sentences per step.
Return ONLY one valid JSON object using this exact structure:
{{
  "title": "publishable title",
  "intro": "short hook",
  "problem": "the problem this solves",
  "steps": [
    {{
      "step_title": "short label",
      "narration": "1-2 natural spoken sentences",
      "visual_goal": "exactly what the viewer must see",
      "interaction": "tap|long_press|swipe|press_buttons|type|none",
      "target": "exact UI control or object",
      "tip": "short optional useful tip"
    }}
  ],
  "outro": "brief conclusion"
}}
Use at most 8 logical steps.
Each step MUST have non-empty narration.
Do not invent uncertain UI details. If a detail is uncertain, describe it generically and let the visual planner use a neutral instructional graphic.'''


def generate_article(title, use_cache=True):
    path = _cache_path(title)
    if use_cache and os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            cached = json.load(f)
        if _valid_article(cached):
            return cached
        try:
            os.remove(path)
        except OSError:
            pass

    last_error = None
    for attempt in range(2):
        try:
            raw = _call_ollama(_prompt(title, retry=attempt == 1))
            article = _extract_json(raw)
            if _valid_article(article):
                os.makedirs(config.CACHE_DIR, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(article, f, indent=2, ensure_ascii=False)
                return article
            last_error = ValueError('Ollama returned JSON without a valid non-empty steps array')
        except (ValueError, json.JSONDecodeError, requests.RequestException) as exc:
            last_error = exc

    raise ValueError(f'Invalid tutorial returned for {title}: {last_error}')
