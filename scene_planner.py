import hashlib, json, os, re, time, requests
import config


def _path(title):
    h = hashlib.sha256((title+'|scene-v4').encode()).hexdigest()[:16]
    return os.path.join(config.CACHE_DIR, f'scenes_{h}.json')


def _ask(prompt):
    """Stream scene planning so the terminal always shows live progress; no read timeout."""
    started = time.monotonic()
    last_report = started
    chunks = []
    count = 0
    print('[SCENES] generating scene plan...', flush=True)
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
                'num_ctx': 3072,
                'num_predict': 1300,
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
                count += 1
            now = time.monotonic()
            if piece and now - last_report >= 1.0:
                elapsed = now - started
                rate = count / elapsed if elapsed else 0
                print(f'[SCENES] chunks={count} | {rate:.1f} chunks/s | elapsed={elapsed:.1f}s', flush=True)
                last_report = now
            if data.get('done'):
                break
    elapsed = time.monotonic() - started
    print(f'[SCENES] generation complete | chunks={count} | elapsed={elapsed:.1f}s', flush=True)
    raw = ''.join(chunks).strip()
    if not raw:
        raise ValueError('Ollama returned an empty scene plan')
    return raw


def _parse(raw):
    raw = raw.strip()
    if raw.startswith('```'):
        raw = raw.split('```')[1]
        if raw.lstrip().startswith('json'): raw = raw.lstrip()[4:]
    m = re.search(r'\{.*\}', raw, re.S)
    return json.loads(m.group(0) if m else raw)


def plan_scenes(article, use_cache=True):
    path = _path(article['title'])
    if use_cache and os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            cached = json.load(f)
        print('[SCENES] scene plan loaded from cache', flush=True)
        return cached

    prompt = f'''You are the visual director for a fully automated YouTube tutorial.
Create exactly 10-12 distinct visual moments. No physical phone, screenshots, or recordings are available.
Every visual is a controlled phone UI animation, diagram, zoom, highlight, or card.
TUTORIAL: {json.dumps(article, ensure_ascii=False)}
Return ONLY JSON with this schema:
{{"scenes":[{{"scene_title":"short","narration":"one short spoken sentence","visual_type":"phone_ui|button_demo|zoom|diagram|before_after|tip_card|title_card","screen":"short screen/state","target":"control or empty","action":"tap|long_press|swipe|press_buttons|zoom|none","callout":"short label or empty"}}]}}
Use exactly 10-12 scenes. Keep every field short. Visuals must directly match narration.
If exact UI is uncertain, use a neutral diagram instead of inventing details. Include intro, action sequence, result, and one useful tip.'''

    data = _parse(_ask(prompt))
    scenes = data.get('scenes', [])
    if not 10 <= len(scenes) <= 12:
        raise ValueError(f'Expected 10-12 scenes, got {len(scenes)}')
    result = {'title': article['title'], 'scenes': scenes}
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return result
