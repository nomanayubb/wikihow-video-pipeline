"""Generate an original, structured tutorial script for the video pipeline."""
import hashlib
import json
import os
import re
import requests
import config


def _cache_path(title):
    h = hashlib.sha256(title.encode('utf-8')).hexdigest()[:16]
    return os.path.join(config.CACHE_DIR, f'article_{h}.json')


def _call_ollama(prompt):
    r = requests.post(config.OLLAMA_URL, json={
        'model': config.OLLAMA_MODEL, 'prompt': prompt, 'stream': False, 'format': 'json'
    }, timeout=240)
    r.raise_for_status()
    return r.json()['response']


def _extract_json(raw):
    raw = raw.strip()
    if raw.startswith('```'):
        parts = raw.split('```')
        raw = parts[1] if len(parts) > 1 else raw
        raw = re.sub(r'^\s*json\s*', '', raw, flags=re.I)
    match = re.search(r'\{.*\}', raw, re.S)
    return json.loads(match.group(0) if match else raw)


def generate_article(title, use_cache=True):
    path = _cache_path(title)
    if use_cache and os.path.exists(path):
        with open(path, encoding='utf-8') as f: return json.load(f)

    prompt = f'''Create an ORIGINAL, accurate, spoken YouTube tutorial for: "{title}".
Do not copy any existing article. Return ONLY valid JSON.
{{"title":"publishable title","intro":"short hook","problem":"the problem this solves","steps":[{{"step_title":"short label","narration":"2-4 natural spoken sentences","visual_goal":"exactly what the viewer must see","interaction":"tap|long_press|swipe|press_buttons|type|none","target":"exact UI control or object","tip":"optional useful tip"}}],"outro":"brief conclusion"}}
Use at most {config.MAX_STEPS_PER_ARTICLE} logical steps. Do not invent uncertain UI details; if a detail is uncertain, describe it generically and let the visual planner use a neutral instructional graphic.'''
    article = _extract_json(_call_ollama(prompt))
    if not isinstance(article.get('steps'), list) or not article['steps']:
        raise ValueError(f'Invalid tutorial returned for {title}')
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: json.dump(article, f, indent=2, ensure_ascii=False)
    return article
