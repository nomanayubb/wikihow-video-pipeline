"""
Step 1: Turn a topic title into an ORIGINAL step-by-step article.

Input:  a title string (e.g. "Easiest Ways to Uninstall a Problematic Windows Update")
Output: structured JSON: {title, intro, steps:[{title, narration}]}

This does NOT scrape or copy any existing article. It asks a local LLM
(via Ollama, free, runs on your machine) to write fresh how-to content on
the same subject. Cached to disk so re-runs are free and instant.

Setup (one-time):
    1. Install Ollama: https://ollama.com/download
    2. Pull a model:   ollama pull llama3.1
    3. Ollama runs a local server automatically after install
       (http://localhost:11434) - nothing else to start.
"""
import json
import hashlib
import os
import re
import requests

import config


def _cache_path(title: str) -> str:
    h = hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]
    return os.path.join(config.CACHE_DIR, f"article_{h}.json")


def _call_ollama(prompt: str) -> str:
    resp = requests.post(
        config.OLLAMA_URL,
        json={
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",   # ask Ollama to constrain output to valid JSON
        },
        timeout=180,   # local generation can be slower than a hosted API
    )
    resp.raise_for_status()
    data = resp.json()
    return data["response"]


def _extract_json(raw: str) -> dict:
    """Local models sometimes wrap JSON in prose or code fences - clean that up."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    # If there's still leading/trailing text, grab the outermost {...}
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


def generate_article(title: str, use_cache: bool = True) -> dict:
    cache_file = _cache_path(title)
    if use_cache and os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    prompt = f"""Write an ORIGINAL, practical how-to guide on this topic: "{title}"

Do not copy or paraphrase any specific existing article - write this from your own
general knowledge of the subject, in your own words and structure.

Return ONLY valid JSON, no markdown fences, no preamble, in this exact shape:
{{
  "title": "short punchy video title",
  "intro": "1-2 sentence spoken hook introducing the problem/topic",
  "steps": [
    {{
      "step_title": "short label, 3-6 words",
      "narration": "2-4 natural spoken sentences explaining this step, as if a friendly narrator is talking to the viewer",
      "image_keywords": "2-4 word search phrase for a stock photo that visually matches this step"
    }}
  ]
}}

Include at most {config.MAX_STEPS_PER_ARTICLE} steps, ordered logically. Keep language simple and spoken, not written/formal."""

    raw = _call_ollama(prompt)
    article = _extract_json(raw)

    # Basic shape check - local models occasionally miss a field
    assert "steps" in article and isinstance(article["steps"], list) and article["steps"], \
        f"Ollama returned an unexpected shape for '{title}': {article}"

    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(article, f, indent=2, ensure_ascii=False)

    return article


if __name__ == "__main__":
    import sys
    title = sys.argv[1] if len(sys.argv) > 1 else "Easiest Ways to Uninstall a Problematic Windows Update"
    art = generate_article(title)
    print(json.dumps(art, indent=2))
