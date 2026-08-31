"""Optional stock-image sourcing with a deterministic local fallback."""
import hashlib
import os

import requests
from PIL import Image, ImageDraw, ImageFont

import config

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


def _cache_path(keywords: str) -> str:
    h = hashlib.sha256(keywords.strip().lower().encode("utf-8")).hexdigest()[:16]
    return os.path.join(config.CACHE_DIR, f"img_{h}.jpg")


def _fallback_slide(text: str, out_path: str):
    """Create a readable fallback slide when stock search is unavailable."""
    img = Image.new("RGB", (config.VIDEO_WIDTH, config.VIDEO_HEIGHT), color=(24, 26, 32))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
    except OSError:
        font = ImageFont.load_default()

    words, lines, line = text.split(), [], ""
    for word in words:
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=font) > config.VIDEO_WIDTH - 120 and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)

    total_h = len(lines) * 90
    y = (config.VIDEO_HEIGHT - total_h) // 2
    for current in lines:
        width = draw.textlength(current, font=font)
        draw.text(((config.VIDEO_WIDTH - width) / 2, y), current, font=font, fill="white")
        y += 90

    tmp = out_path + ".tmp"
    img.save(tmp, quality=90)
    os.replace(tmp, out_path)


def get_image(keywords: str, step_title: str = "") -> str:
    """Return a local image path, using Pexels when configured and cached otherwise."""
    cache_file = _cache_path(keywords)
    if os.path.isfile(cache_file) and os.path.getsize(cache_file) > 0:
        return cache_file

    os.makedirs(config.CACHE_DIR, exist_ok=True)
    if config.PEXELS_API_KEY:
        try:
            orientation = "portrait" if config.VIDEO_HEIGHT > config.VIDEO_WIDTH else "landscape"
            resp = requests.get(
                PEXELS_SEARCH_URL,
                headers={"Authorization": config.PEXELS_API_KEY},
                params={"query": keywords, "per_page": 1, "orientation": orientation},
                timeout=(5, 15),
            )
            resp.raise_for_status()
            photos = resp.json().get("photos", [])
            if photos:
                img_url = photos[0].get("src", {}).get("large2x")
                if img_url:
                    image_resp = requests.get(img_url, timeout=(5, 20))
                    image_resp.raise_for_status()
                    tmp = cache_file + ".tmp"
                    with open(tmp, "wb") as f:
                        f.write(image_resp.content)
                    os.replace(tmp, cache_file)
                    return cache_file
        except (requests.RequestException, ValueError, KeyError, TypeError):
            pass

    _fallback_slide(step_title or keywords, cache_file)
    return cache_file


if __name__ == "__main__":
    path = get_image("laptop windows update screen", "Open Windows Update settings")
    print("Saved:", path)
