"""Build the professional Italian-vocabulary YouTube video."""
import hashlib
import os
import time

from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
)

import config
from music import generate as generate_music
from tts import synthesize_many
from vocabulary_generator import generate_lessons, load_words
from vocabulary_visual import build_card


def _progress(percent, message, started):
    elapsed = time.monotonic() - started
    print(f"[{percent:3d}%] {message} | elapsed {elapsed:.1f}s", flush=True)


def _narration(lesson):
    return (
        f"The Italian word is {lesson['italian']}. In English, it means {lesson['english']}. "
        f"It is a {lesson['part_of_speech']}. {lesson['explanation']} "
        f"For example: {lesson['example']}"
    )


def _title_card(title, out_path):
    from PIL import Image, ImageDraw, ImageFont
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    image = Image.new("RGB", (w, h), (10, 14, 22))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    box = draw.textbbox((0, 0), title, font=font)
    draw.text(((w - (box[2] - box[0])) / 2, h * 0.38), title, font=font, fill="white")
    sub = "20 Italian words • English meanings • pronunciation through context"
    sb = draw.textbbox((0, 0), sub, font=small)
    draw.text(((w - (sb[2] - sb[0])) / 2, h * 0.52), sub, font=small, fill=(255, 210, 80))
    image.save(out_path, "PNG")
    return out_path


def build_video(title=None, out_path=None, words_path=None):
    started = time.monotonic()
    words = load_words(words_path)
    if len(words) != config.VOCAB_WORD_COUNT:
        raise ValueError(f"{config.VOCAB_FILE} must contain exactly {config.VOCAB_WORD_COUNT} Italian words")

    title = title or config.VOCAB_TITLE
    out_path = out_path or os.path.join(config.OUTPUT_DIR, "italian_vocabulary.mp4")
    digest = hashlib.sha256("|".join(words).encode()).hexdigest()[:16]
    work_dir = os.path.join(config.CACHE_DIR, "_vocab_work", digest)
    os.makedirs(work_dir, exist_ok=True)

    _progress(2, "Starting Italian vocabulary video", started)
    lessons = generate_lessons(words, progress=lambda m: _progress(12, m, started))["words"]
    _progress(18, f"Generated {len(lessons)} English lessons", started)

    intro_path = os.path.join(work_dir, "intro.png")
    _title_card(title, intro_path)
    intro_audio_path = os.path.join(work_dir, "intro.mp3")
    intro_words = synthesize_many(
        [("Welcome. Today we will learn twenty useful Italian words, with clear English meanings and vivid examples.", intro_audio_path)],
        max_concurrency=1,
    )[0]
    _ = intro_words

    tts_items = []
    for i, lesson in enumerate(lessons, 1):
        tts_items.append((_narration(lesson), os.path.join(work_dir, f"word_{i:02d}.mp3")))
    _progress(22, f"Generating {len(tts_items)} English narrations", started)
    timestamps = synthesize_many(tts_items, max_concurrency=config.TTS_CONCURRENCY)
    _progress(42, "Narration complete", started)

    clips = []
    audio_clips = []
    intro_audio = AudioFileClip(intro_audio_path)
    intro_video = ImageClip(intro_path).set_duration(intro_audio.duration).set_audio(intro_audio)
    clips.append(intro_video)
    audio_clips.append(intro_audio)

    total = len(lessons)
    for index, (lesson, words_timing) in enumerate(zip(lessons, timestamps), 1):
        percent = 42 + int((index - 1) * 48 / total)
        _progress(percent, f"Generating visual {index}/{total}: {lesson['italian']}", started)
        card_path, image_path = build_card(lesson, work_dir, index, total)
        audio_path = tts_items[index - 1][1]
        audio = AudioFileClip(audio_path)
        audio_clips.append(audio)
        duration = max(config.WORD_TARGET_SECONDS, audio.duration)
        # Subtle Ken-Burns movement keeps each generated illustration alive without
        # turning the lesson into a distracting slideshow.
        base = ImageClip(card_path).set_duration(duration).resize((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
        clip = CompositeVideoClip([base], size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT)).set_duration(duration).set_audio(audio)
        clips.append(clip)
        _progress(percent + 2, f"Completed {index}/{total}: {lesson['italian']}", started)

    outro_path = os.path.join(work_dir, "outro.png")
    _title_card("Keep learning — one word at a time", outro_path)
    outro_audio_path = os.path.join(work_dir, "outro.mp3")
    synthesize_many([("Great work. Review these words again and try using each one in a sentence today.", outro_audio_path)], max_concurrency=1)
    outro_audio = AudioFileClip(outro_audio_path)
    clips.append(ImageClip(outro_path).set_duration(outro_audio.duration).set_audio(outro_audio))
    audio_clips.append(outro_audio)

    _progress(94, "Assembling video and adding background music", started)
    final = concatenate_videoclips(clips, method="compose")
    music_path = os.path.join(work_dir, "background_music.wav")
    generate_music(final.duration + 1, music_path)
    music = AudioFileClip(music_path).volumex(config.MUSIC_VOLUME).set_duration(final.duration)
    final_audio = CompositeAudioClip([final.audio, music])
    final = final.set_audio(final_audio)

    try:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        final.write_videofile(
            out_path,
            fps=config.FPS,
            codec="libx264",
            audio_codec="aac",
            threads=config.VIDEO_THREADS,
            preset=config.FFMPEG_PRESET,
            bitrate=config.VIDEO_BITRATE,
            verbose=False,
            logger=None,
        )
    finally:
        final.close()
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        for audio in audio_clips:
            try:
                audio.close()
            except Exception:
                pass
        try:
            music.close()
        except Exception:
            pass

    _progress(100, f"Complete: {out_path} ({final.duration:.1f}s)", started)
    return out_path
