"""
Step 3: Get an image per step from Pexels (free stock photos, licensed for
this kind of use). Falls back to a plain generated slide if no photo matches
or no API key is set, so the pipeline never hard-fails on this step.
"""
import os
import hashlib
import requests
from PIL import Image, ImageDraw, ImageFont

import config

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


def _cache_path(keywords: str) -> str:
    h = hashlib.sha256(keywords.encode("utf-8")).hexdigest()[:16]
    return os.path.join(config.CACHE_DIR, f"img_{h}.jpg")


def _fallback_slide(text: str, out_path: str):
    """Plain title-card image if no stock photo is available."""
    img = Image.new("RGB", (config.VIDEO_WIDTH, config.VIDEO_HEIGHT), color=(24, 26, 32))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
    except OSError:
        font = ImageFont.load_default()

    # crude word-wrap
    words, lines, line = text.split(), [], ""
    for w in words:
        test = f"{line} {w}".strip()
        if draw.textlength(test, font=font) > config.VIDEO_WIDTH - 120:
            lines.append(line)
            line = w
        else:
            line = test
    lines.append(line)

    total_h = len(lines) * 90
    y = (config.VIDEO_HEIGHT - total_h) // 2
    for l in lines:
        w = draw.textlength(l, font=font)
        draw.text(((config.VIDEO_WIDTH - w) / 2, y), l, font=font, fill="white")
        y += 90

    img.save(out_path, quality=90)


def get_image(keywords: str, step_title: str = "") -> str:
    """Returns a local file path to an image for this step."""
    cache_file = _cache_path(keywords)
    if os.path.exists(cache_file):
        return cache_file

    os.makedirs(config.CACHE_DIR, exist_ok=True)

    if config.PEXELS_API_KEY:
        try:
            resp = requests.get(
                PEXELS_SEARCH_URL,
                headers={"Authorization": config.PEXELS_API_KEY},
                params={"query": keywords, "per_page": 1, "orientation": "portrait"
                        if config.VIDEO_HEIGHT > config.VIDEO_WIDTH else "landscape"},
                timeout=20,
            )
            resp.raise_for_status()
            photos = resp.json().get("photos", [])
            if photos:
                img_url = photos[0]["src"]["large2x"]
                img_data = requests.get(img_url, timeout=20).content
                with open(cache_file, "wb") as f:
                    f.write(img_data)
                return cache_file
        except requests.RequestException:
            pass  # fall through to fallback slide

    _fallback_slide(step_title or keywords, cache_file)
    return cache_file


if __name__ == "__main__":
    path = get_image("laptop windows update screen", "Open Windows Update settings")
    print("Saved:", path)
