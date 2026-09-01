"""Reliable AI illustration generation for vocabulary lessons."""
import base64
import hashlib
import os
import time
from pathlib import Path

import requests

import config


def _cache_path(prompt):
    digest = hashlib.sha256((prompt + "|image-v2").encode("utf-8")).hexdigest()[:20]
    return Path(config.CACHE_DIR) / "vocab_images" / f"{digest}.png"


def _write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def _request_with_retry(method, url, **kwargs):
    last = None
    for attempt in range(config.IMAGE_RETRIES + 1):
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last = exc
            if attempt < config.IMAGE_RETRIES:
                time.sleep(min(2 ** attempt, 4))
    raise last


def _openai_image(prompt, out_path):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return False
    response = _request_with_retry(
        "POST",
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": config.IMAGE_MODEL,
            "prompt": prompt,
            "size": config.IMAGE_SIZE,
            "quality": config.IMAGE_QUALITY,
            "output_format": "png",
        },
        timeout=(10, config.IMAGE_GENERATOR_TIMEOUT),
    )
    items = response.json().get("data") or []
    if not items:
        raise RuntimeError("Image API returned no image")
    item = items[0]
    if item.get("b64_json"):
        _write_atomic(Path(out_path), base64.b64decode(item["b64_json"]))
        return True
    if item.get("url"):
        image = _request_with_retry("GET", item["url"], timeout=(10, config.IMAGE_GENERATOR_TIMEOUT))
        _write_atomic(Path(out_path), image.content)
        return True
    raise RuntimeError("Image API returned no usable image payload")


def _custom_image(prompt, out_path):
    if not config.IMAGE_GENERATOR_URL:
        return False
    response = _request_with_retry(
        "POST",
        config.IMAGE_GENERATOR_URL,
        json={"prompt": prompt, "width": 1536, "height": 1024},
        timeout=(10, config.IMAGE_GENERATOR_TIMEOUT),
    )
    if response.headers.get("content-type", "").startswith("image/"):
        _write_atomic(Path(out_path), response.content)
        return True
    data = response.json()
    if data.get("b64_json") or data.get("image"):
        payload = data.get("b64_json") or data.get("image")
        _write_atomic(Path(out_path), base64.b64decode(payload))
        return True
    if data.get("url"):
        image = _request_with_retry("GET", data["url"], timeout=(10, config.IMAGE_GENERATOR_TIMEOUT))
        _write_atomic(Path(out_path), image.content)
        return True
    raise RuntimeError("Custom image endpoint returned no usable image payload")


def generate(prompt, word):
    """Generate and cache one semantic illustration; never invent UI/screenshot art."""
    out_path = _cache_path(prompt)
    if out_path.is_file() and out_path.stat().st_size > 1024:
        return str(out_path)
    style = (
        "Premium editorial illustration for a professional language-learning YouTube channel. "
        "Clear semantic storytelling, cinematic but natural lighting, tasteful modern art direction, "
        "rich depth, visually memorable composition, no text, no letters, no labels, no watermark, "
        "no logos, no user interface, no phone, no screenshot, landscape 3:2 composition."
    )
    full_prompt = f"{style}\nSubject word: {word}.\nMeaning visualization: {prompt}"
    provider = config.IMAGE_PROVIDER
    if provider in ("auto", "openai") and _openai_image(full_prompt, str(out_path)):
        return str(out_path)
    if provider in ("auto", "custom") and _custom_image(full_prompt, str(out_path)):
        return str(out_path)
    raise RuntimeError("No AI image provider is configured. Set OPENAI_API_KEY or IMAGE_GENERATOR_URL.")
