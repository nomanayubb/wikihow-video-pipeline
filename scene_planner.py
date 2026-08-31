import hashlib, json, os, re, requests
import config


def _path(title):
    h = hashlib.sha256((title+'|scene-v3').encode()).hexdigest()[:16]
    return os.path.join(config.CACHE_DIR, f'scenes_{h}.json')


def _ask(prompt):
    # Keep the request bounded: scene planning is a single generation and should
    # not wait several minutes before the pipeline can report a useful error.
    r = requests.post(
        config.OLLAMA_URL,
        json={
            'model': config.OLLAMA_MODEL,
            'prompt': prompt,
            'stream': False,
            'format': 'json',
            'options': {
                'temperature': 0.1,
                'num_ctx': 4096,
                'num_predict': 2200,
            },
        },
        timeout=(10, 120),
    )
    r.raise_for_status()
    return r.json()['response']


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
        with open(path, encoding='utf-8') as f: return json.load(f)

    prompt = f'''You are the visual director for a fully automated YouTube tutorial.
Create 12-15 distinct visual moments for this tutorial. No physical phone, screenshots,
or recordings are available. Every visual will be rendered automatically as a controlled
phone UI animation, diagram, zoom, highlight, or card.
TUTORIAL: {json.dumps(article, ensure_ascii=False)}
Return ONLY JSON: {{"scenes":[{{"scene_title":"short title","narration":"1-2 spoken sentences","visual_type":"phone_ui|button_demo|zoom|diagram|before_after|tip_card|title_card","screen":"exact UI screen or conceptual state","target":"exact control to highlight or empty","action":"tap|long_press|swipe|press_buttons|zoom|none","callout":"short label or empty"}}]}}
Rules: 12-15 scenes; visuals must directly demonstrate narration; use exact controls when known;
if exact UI is uncertain use a neutral diagram rather than inventing UI; include intro, action sequence,
result and useful tip; narration must be natural and concise. Keep every field short.'''

    data = _parse(_ask(prompt))
    scenes = data.get('scenes', [])
    if not 12 <= len(scenes) <= 15:
        raise ValueError(f'Expected 12-15 scenes, got {len(scenes)}')
    result = {'title': article['title'], 'scenes': scenes}
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: json.dump(result, f, indent=2, ensure_ascii=False)
    return result
