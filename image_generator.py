"""AI illustration generation for vocabulary lessons.

Uses OpenAI's Images API when OPENAI_API_KEY is configured, or a generic
JSON image endpoint via IMAGE_GENERATOR_URL for local ComfyUI-style adapters.
No placeholder phone/UI art is used in vocabulary mode.
"""
import base64
import hashlib
import json
import os
import requests

import config


def _path(prompt):
    h = hashlib.sha256((prompt + "|image-v1").encode("utf-8")).hexdigest()[:16]
    return os.path.join(config.CACHE_DIR, "vocab_images", f"{h}.png")


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def _openai_image(prompt, out_path):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return False
    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": config.IMAGE_MODEL,
            "prompt": prompt,
            "size": config.IMAGE_SIZE,
            "quality": config.IMAGE_QUALITY,
            "output_format": "png",
        },
        timeout=config.IMAGE_GENERATOR_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json().get("data", [])
    if not data:
        raise RuntimeError("Image API returned no image")
    item = data[0]
    if item.get("b64_json"):
        _write(out_path, base64.b64decode(item["b64_json"]))
        return True
    if item.get("url"):
        image = requests.get(item["url"], timeout=config.IMAGE_GENERATOR_TIMEOUT)
        image.raise_for_status()
        _write(out_path, image.content)
        return True
    raise RuntimeError("Image API returned neither base64 data nor a URL")


def _generic_endpoint(prompt, out_path):
    if not config.IMAGE_GENERATOR_URL:
        return False
    response = requests.post(
        config.IMAGE_GENERATOR_URL,
        json={"prompt": prompt, "width": 1536, "height": 1024},
        timeout=config.IMAGE_GENERATOR_TIMEOUT,
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "image/" in content_type:
        _write(out_path, response.content)
        return True
    data = response.json()
    if data.get("b64_json"):
        _write(out_path, base64.b64decode(data["b64_json"]))
        return True
    if data.get("image"):
        _write(out_path, base64.b64decode(data["image"]))
        return True
    if data.get("url"):
        image = requests.get(data["url"], timeout=config.IMAGE_GENERATOR_TIMEOUT)
        image.raise_for_status()
        _write(out_path, image.content)
        return True
    raise RuntimeError("Configured image endpoint returned no usable image")


def generate(prompt, word):
    out_path = _path(prompt)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return out_path
    style = (
        "Create a premium editorial educational illustration for a YouTube vocabulary video. "
        "Visually communicate the concept clearly, cinematic composition, tasteful color palette, "
        "soft depth, beautiful lighting, polished modern illustration, no written words, no labels, "
        "no watermark, no logo, no app interface, no phone UI."
    )
    full_prompt = f"{style} Subject: {word}. {prompt}"
    if config.IMAGE_PROVIDER in ("auto", "openai") and _openai_image(full_prompt, out_path):
        return out_path
    if config.IMAGE_PROVIDER in ("auto", "custom") and _generic_endpoint(full_prompt, out_path):
        return out_path
    raise RuntimeError(
        "No AI image generator is configured. Set OPENAI_API_KEY or IMAGE_GENERATOR_URL."
    )
