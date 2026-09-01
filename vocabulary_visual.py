"""Render a premium, reusable vocabulary frame for every generated illustration."""
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import config


PALETTE = {
    "bg": (10, 15, 26),
    "panel": (20, 27, 43),
    "white": (246, 248, 252),
    "muted": (153, 164, 184),
    "accent": (255, 203, 89),
    "blue": (116, 184, 255),
    "line": (63, 76, 101),
}


def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_cover(source, size):
    src = Image.open(source).convert("RGB")
    target_w, target_h = size
    scale = max(target_w / src.width, target_h / src.height)
    resized = src.resize((int(src.width * scale), int(src.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def _wrap(draw, text, font, max_width):
    words = str(text).split()
    lines, line = [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if line and draw.textlength(candidate, font=font) > max_width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def render_card(lesson, image_path, out_path, index, total):
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    canvas = Image.new("RGB", (w, h), PALETTE["bg"])
    draw = ImageDraw.Draw(canvas)

    # Soft visual depth behind the two-column layout.
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((40, 40, int(w * 0.65), h - 40), fill=(67, 103, 168, 45))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    margin = 46
    gap = 42
    art_w = int(w * 0.54)
    art_h = h - margin * 2
    art = _fit_cover(image_path, (art_w, art_h))
    art = art.filter(ImageFilter.GaussianBlur(0.1))
    canvas.paste(art, (margin, margin))
    draw.rounded_rectangle((margin, margin, margin + art_w, margin + art_h), radius=32, outline=(255, 255, 255), width=2)

    x = margin + art_w + gap
    right = w - margin
    max_width = right - x

    draw.text((x, 58), f"{index:02d}  /  {total:02d}", font=_font(24, True), fill=PALETTE["muted"])
    italian = str(lesson["italian"])
    english = str(lesson["english"])
    pos = str(lesson["part_of_speech"])

    italian_font = _font(76, True)
    english_font = _font(40, True)
    body_font = _font(27, False)
    label_font = _font(19, True)

    y = 122
    italian_lines = _wrap(draw, italian, italian_font, max_width)
    for line in italian_lines[:2]:
        draw.text((x, y), line, font=italian_font, fill=PALETTE["white"])
        y += 84

    draw.text((x, y + 2), english, font=english_font, fill=PALETTE["accent"])
    y += 60
    draw.text((x, y + 4), pos.upper(), font=label_font, fill=PALETTE["muted"])
    y += 50

    for label, value, max_lines in (("MEANING", lesson["explanation"], 7), ("EXAMPLE", lesson["example"], 4)):
        draw.text((x, y), label, font=label_font, fill=PALETTE["blue"])
        y += 33
        for line in _wrap(draw, value, body_font, max_width)[:max_lines]:
            draw.text((x, y), line, font=body_font, fill=PALETTE["white"])
            y += 38
        y += 18

    # A quiet visual signature and progress line make the card feel like a real channel identity.
    line_y = h - 62
    draw.line((x, line_y, right, line_y), fill=PALETTE["line"], width=2)
    draw.text((x, line_y + 12), "ITALIAN VOCABULARY  •  ENGLISH EXPLAINED", font=label_font, fill=PALETTE["muted"])
    return canvas.save(out_path, format="PNG") or out_path
