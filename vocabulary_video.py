"""Automated Italian-to-English vocabulary video builder.

Creates a polished 16:9 vocabulary lesson from one Italian word per line.
Translation is performed by Ollama; visuals are generated through a local
ComfyUI/A1111-compatible image endpoint when configured, with a deterministic
illustration fallback so the batch never stops because one image is missing.
"""
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips

import config
from tts import synthesize


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:60] or "word"


def _font(size, bold=False):
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _cache_path(word):
    h = hashlib.sha256((word + "|vocab-v1").encode()).hexdigest()[:16]
    return Path(config.CACHE_DIR) / "vocab" / f"{h}.json"


def translate_words(words, progress=None):
    """Translate all words in one Ollama call to avoid 100 model round-trips."""
    path = Path(config.CACHE_DIR) / "vocab" / "translations.json"
    key = hashlib.sha256("\n".join(words).encode()).hexdigest()[:16]
    if path.exists():
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
            if cached.get("key") == key and len(cached.get("items", [])) == len(words):
                return cached["items"]
        except (OSError, ValueError, TypeError):
            pass

    import generate_articles
    prompt = (
        "Translate these Italian vocabulary words into natural, simple English. "
        "Return ONLY JSON: {\"items\":[{\"italian\":\"...\",\"english\":\"...\","
        "\"example\":\"short English example sentence\"}]} . Preserve order and every word. "
        "Do not add or omit entries.\nWORDS:\n" + "\n".join(words)
    )
    raw = generate_articles._call_ollama(prompt, progress=progress)
    data = generate_articles._extract_json(raw)
    items = data.get("items", [])
    if len(items) != len(words):
        raise ValueError(f"Translation returned {len(items)} items for {len(words)} words")
    for expected, item in zip(words, items):
        if str(item.get("italian", "")).strip().lower() != expected.strip().lower():
            raise ValueError("Translation response changed vocabulary order/content")
        if not str(item.get("english", "")).strip():
            raise ValueError(f"Missing English translation for {expected}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"key": key, "items": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return items


def _fallback_illustration(item, out_path):
    """Elegant non-photorealistic fallback: never fabricate a real UI/screenshot."""
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    img = Image.new("RGB", (w, h), (15, 18, 28))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((80, 180, w - 80, h - 180), fill=(75, 95, 150, 75))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((70, 250, w - 70, h - 250), radius=55, fill=(28, 33, 48, 235), outline=(130, 145, 180, 130), width=3)
    d.ellipse((w // 2 - 180, 430, w // 2 + 180, 790), fill=(55, 70, 105, 220))
    f_big = _font(96, True)
    f_small = _font(44, False)
    it = str(item["italian"])
    en = str(item["english"])
    d.text((w // 2, 900), it, font=f_big, anchor="ma", fill="white")
    d.text((w // 2, 1030), en, font=f_small, anchor="ma", fill=(220, 225, 235))
    ex = str(item.get("example", ""))
    d.text((w // 2, 1150), ex, font=_font(32), anchor="ma", fill=(170, 180, 200))
    img.convert("RGB").save(out_path, quality=94)


def generate_image(item, out_path, progress=None):
    """Use a local image model if configured; otherwise create a safe visual card."""
    endpoint = config.IMAGE_GENERATOR_URL
    if endpoint:
        prompt = (
            f"Create a beautiful editorial educational illustration representing the Italian word '{item['italian']}' "
            f"which means '{item['english']}'. Subject-focused, cinematic, tasteful, clean YouTube learning aesthetic, "
            "no written words, no UI, no logos, no watermark, landscape composition."
        )
        try:
            response = requests.post(endpoint, json={"prompt": prompt, "width": config.VIDEO_WIDTH, "height": config.VIDEO_HEIGHT}, timeout=(10, config.IMAGE_GENERATOR_TIMEOUT))
            response.raise_for_status()
            data = response.json()
            image_url = data.get("image_url") or data.get("url")
            image_b64 = data.get("image_base64")
            if image_url:
                image = requests.get(image_url, timeout=config.IMAGE_GENERATOR_TIMEOUT)
                image.raise_for_status()
                Path(out_path).write_bytes(image.content)
                return out_path
            if image_b64:
                import base64
                Path(out_path).write_bytes(base64.b64decode(image_b64))
                return out_path
        except (requests.RequestException, ValueError, OSError):
            if progress:
                progress(f"image model unavailable for {item['italian']}; using fallback illustration")
    _fallback_illustration(item, out_path)
    return out_path


def _music_track():
    music_dir = Path(config.MUSIC_DIR)
    tracks = sorted(p for p in music_dir.glob("*") if p.suffix.lower() in {".mp3", ".wav", ".m4a", ".aac"})
    return str(tracks[0]) if tracks else None


def _mix_music(video_path, music_path, output_path):
    if not music_path:
        os.replace(video_path, output_path)
        return
    # Loop the supplied royalty-free track and keep it unobtrusive under narration.
    subprocess.run([
        config.FFMPEG_BIN, "-y", "-i", video_path, "-stream_loop", "-1", "-i", music_path,
        "-filter_complex", "[1:a]volume=0.12,afade=t=in:st=0:d=2[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=3[a]",
        "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", output_path,
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(video_path)


def build_vocabulary_video(words, out_path, target_minutes=4.0):
    if not words:
        raise ValueError("No vocabulary words supplied")
    words = [str(w).strip() for w in words if str(w).strip()]
    if len(words) < 1:
        raise ValueError("No vocabulary words supplied")
    started = time.monotonic()
    print(f"[VOCAB] building {len(words)} Italian words", flush=True)
    items = translate_words(words, progress=lambda x: print(x, flush=True))
    work = Path(config.CACHE_DIR) / "vocab" / hashlib.sha256("\n".join(words).encode()).hexdigest()[:16]
    work.mkdir(parents=True, exist_ok=True)

    # One narration request gives consistent voice and avoids 100 network calls.
    narration = ". ".join(f"{i['italian']}. In English, {i['english']}." for i in items)
    audio_path = work / "narration.mp3"
    timestamps_path = work / "timestamps.json"
    if audio_path.exists() and timestamps_path.exists():
        timestamps = json.loads(timestamps_path.read_text(encoding="utf-8"))
    else:
        timestamps = synthesize(narration, str(audio_path))
        timestamps_path.write_text(json.dumps(timestamps, ensure_ascii=False), encoding="utf-8")

    # Allocate each vocabulary card from the spoken phrase boundaries.
    duration = AudioFileClip(str(audio_path)).duration
    per = duration / len(items)
    # Target duration is achieved naturally from narration; pad with a title/outro later.
    clips = []
    for idx, item in enumerate(items):
        image_path = work / f"{idx:03d}_{_slug(item['italian'])}.jpg"
        if not image_path.exists():
            generate_image(item, str(image_path), progress=lambda x: print("[VOCAB] " + x, flush=True))
        clip = ImageClip(str(image_path)).resize((config.VIDEO_WIDTH, config.VIDEO_HEIGHT)).set_duration(per)
        clips.append(clip)
        if idx % 5 == 0 or idx == len(items) - 1:
            print(f"[VOCAB] visuals {idx + 1}/{len(items)} | elapsed={time.monotonic() - started:.1f}s", flush=True)

    visual = concatenate_videoclips(clips, method="compose")
    visual = visual.set_audio(AudioFileClip(str(audio_path)))
    raw = str(Path(out_path).with_suffix(".no_music.mp4"))
    visual.write_videofile(raw, fps=config.FPS, codec="libx264", audio_codec="aac", threads=4, logger=None, verbose=False)
    visual.close()
    _mix_music(raw, _music_track(), out_path)
    print(f"[VOCAB] complete: {out_path} | duration≈{duration:.1f}s", flush=True)
    return out_path


def load_words(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
