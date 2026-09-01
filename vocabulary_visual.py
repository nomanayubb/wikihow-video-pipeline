"""Premium split-screen vocabulary cards with subtle motion."""
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import config
from image_generator import generate as generate_image


def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _fit_image(source, size):
    image = Image.open(source).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (18, 22, 30))
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def render_card(lesson, image_path, out_path, index, total):
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    canvas = Image.new("RGB", (w, h), (12, 16, 24))
    draw = ImageDraw.Draw(canvas)

    # Elegant two-column layout: generated art on the left, English lesson on the right.
    art_w = int(w * 0.52)
    art = _fit_image(image_path, (art_w - 72, h - 160)).filter(ImageFilter.GaussianBlur(0.15))
    canvas.paste(art, (36, 80))
    draw.rounded_rectangle((36, 80, art_w - 36, h - 80), radius=34, outline=(255, 255, 255), width=2)

    x = art_w + 40
    right_w = w - x - 70
    draw.text((x, 72), f"{index:02d} / {total:02d}", font=_font(24, True), fill=(150, 160, 178))
    italian = str(lesson["italian"])
    english = str(lesson["english"])
    pos = str(lesson["part_of_speech"])
    draw.text((x, 125), italian, font=_font(70, True), fill=(255, 255, 255))
    draw.text((x, 215), english, font=_font(42, True), fill=(255, 210, 80))
    draw.text((x, 275), pos.upper(), font=_font(21, True), fill=(150, 160, 178))

    y = 335
    for label, value in (("MEANING", lesson["explanation"]), ("EXAMPLE", lesson["example"])):
        draw.text((x, y), label, font=_font(20, True), fill=(120, 180, 255))
        y += 34
        lines = textwrap.wrap(str(value), width=max(28, int(right_w / 18)))
        for line in lines[:7 if label == "MEANING" else 4]:
            draw.text((x, y), line, font=_font(27), fill=(235, 238, 244))
            y += 38
        y += 24

    draw.line((x, h - 78, w - 70, h - 78), fill=(70, 80, 98), width=2)
    draw.text((x, h - 62), "Italian → English vocabulary", font=_font(20), fill=(130, 140, 158))
    canvas.save(out_path, format="PNG")
    return out_path


def build_card(lesson, work_dir, index, total):
    image_path = generate(lesson["image_prompt"], lesson["italian"])
    card_path = os.path.join(work_dir, f"card_{index:02d}.png")
    return render_card(lesson, image_path, card_path, index, total), image_path
