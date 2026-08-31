"""Create a compact visual storyboard from a generated tutorial."""
import hashlib
import json
import os
import re
import time
import requests
import config


def _path(title):
    h = hashlib.sha256((title + '|scene-v6-optimized').encode()).hexdigest()[:16]
    return os.path.join(config.CACHE_DIR, f'scenes_{h}.json')


def _ask(prompt, progress=None):
    """Stream scene planning with live progress and a configurable stall timeout."""
    started = time.monotonic()
    last_report = started
    chunks = []
    count = 0
    char_count = 0
    progress = progress or (lambda message: print(message, flush=True))
    print('[SCENES] generating scene plan...', flush=True)
    with requests.post(
        config.OLLAMA_URL,
        json={
            'model': config.OLLAMA_MODEL,
            'prompt': prompt,
            'stream': True,
            'format': 'json',
            'keep_alive': config.OLLAMA_KEEP_ALIVE,
            'options': {
                'temperature': 0.05,
                'num_ctx': config.OLLAMA_SCENE_CONTEXT,
                'num_predict': config.OLLAMA_SCENE_PREDICT,
                'top_k': 20,
                'top_p': 0.8,
            },
        },
        timeout=(config.OLLAMA_CONNECT_TIMEOUT, config.OLLAMA_READ_TIMEOUT),
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
                count += 1
                char_count += len(piece)
            now = time.monotonic()
            if piece and now - last_report >= config.OLLAMA_PROGRESS_INTERVAL:
                elapsed = now - started
                rate = char_count / elapsed if elapsed else 0
                progress(f'[SCENES] chunks={count} | chars={char_count} | {rate:.0f} chars/s | elapsed={elapsed:.1f}s')
                last_report = now
            if data.get('done'):
                break
    elapsed = time.monotonic() - started
    rate = char_count / elapsed if elapsed else 0
    print(f'[SCENES] generation complete | chunks={count} | chars={char_count} | {rate:.0f} chars/s | elapsed={elapsed:.1f}s', flush=True)
    raw = ''.join(chunks).strip()
    if not raw:
        raise ValueError('Ollama returned an empty scene plan')
    return raw


def _parse(raw):
    raw = raw.strip()
    if raw.startswith('```'):
        parts = raw.split('```')
        raw = parts[1] if len(parts) > 1 else raw
        if raw.lstrip().lower().startswith('json'):
            raw = raw.lstrip()[4:]
    m = re.search(r'\{.*\}', raw, re.S)
    if not m:
        raise ValueError('Ollama did not return a JSON object for scenes')
    return json.loads(m.group(0))


def _valid_scene(scene):
    return isinstance(scene, dict) and all(str(scene.get(k, '')).strip() for k in ('narration', 'visual_type', 'screen', 'action'))


def plan_scenes(article, use_cache=True, progress=None):
    path = _path(article['title'])
    if use_cache and os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                cached = json.load(f)
            scenes = cached.get('scenes', [])
            if config.MIN_VISUAL_SCENES <= len(scenes) <= config.MAX_VISUAL_SCENES and all(_valid_scene(s) for s in scenes):
                print('[SCENES] scene plan loaded from cache', flush=True)
                return cached
        except (OSError, json.JSONDecodeError):
            pass

    target_count = max(config.MIN_VISUAL_SCENES, min(config.MAX_VISUAL_SCENES, 10))
    prompt = f'''You are the visual director for a fully automated YouTube tutorial.
Create exactly {target_count} visual moments. No physical phone, screenshots, or recordings are available.
Every visual is a controlled phone UI animation, diagram, zoom, highlight, or card.
TUTORIAL: {json.dumps(article, ensure_ascii=False)}
Return ONLY JSON:
{{"scenes":[{{"scene_title":"short","narration":"one short spoken sentence","visual_type":"phone_ui|button_demo|zoom|diagram|before_after|tip_card|title_card","screen":"short screen/state","target":"control or empty","action":"tap|long_press|swipe|press_buttons|zoom|none","callout":"short label or empty"}}]}}
Use exactly {target_count} scenes. Keep every field short. Match each visual directly to narration.
If exact UI is uncertain, use a neutral diagram. Include intro, action sequence, result, and one useful tip.'''

    data = _parse(_ask(prompt, progress=progress))
    scenes = data.get('scenes', [])
    if len(scenes) != target_count:
        raise ValueError(f'Expected exactly {target_count} scenes, got {len(scenes)}')
    if not all(_valid_scene(s) for s in scenes):
        raise ValueError('Scene plan contains an incomplete scene')
    result = {'title': article['title'], 'scenes': scenes}
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)
    return result
