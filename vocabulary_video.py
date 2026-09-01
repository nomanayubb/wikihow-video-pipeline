"""Production pipeline for Italian-to-English vocabulary YouTube videos."""
import hashlib
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from moviepy.editor import AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

import config
from image_generator import generate as generate_image
from music import generate as generate_music
from tts import synthesize_many
from vocabulary_generator import generate_lessons, load_words
from vocabulary_visual import render_card


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
            pass
    return ImageFont.load_default()


def _progress(percent, message, started):
    elapsed = time.monotonic() - started
    print(f"[{percent:3d}%] {message} | elapsed={elapsed:.1f}s", flush=True)


def _title_card(title, subtitle, path):
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    image = Image.new("RGB", (w, h), (8, 13, 23))
    draw = ImageDraw.Draw(image)
    draw.ellipse((w * 0.50, -120, w + 250, h + 240), fill=(28, 52, 84))
    draw.ellipse((-260, h * 0.55, w * 0.48, h + 300), fill=(42, 31, 61))
    title_font = _font(78, True)
    sub_font = _font(32, False)

    def centered(text, y, font, fill):
        box = draw.textbbox((0, 0), text, font=font)
        draw.text(((w - (box[2] - box[0])) / 2, y), text, font=font, fill=fill)

    centered(title, int(h * 0.37), title_font, (248, 250, 255))
    centered(subtitle, int(h * 0.53), sub_font, (255, 207, 91))
    image.save(path, format="PNG")
    return path


def _word_narration(lesson):
    return (
        f"The Italian word is {lesson['italian']}. In English, it means {lesson['english']}. "
        f"It is a {lesson['part_of_speech']}. {lesson['explanation']} "
        f"Here is a natural example: {lesson['example']}"
    )


def _generate_images(lessons, progress):
    results = [None] * len(lessons)
    total = len(lessons)
    with ThreadPoolExecutor(max_workers=config.IMAGE_CONCURRENCY) as pool:
        jobs = {
            pool.submit(generate_image, lesson["image_prompt"], lesson["italian"]): index
            for index, lesson in enumerate(lessons)
        }
        for done, future in enumerate(as_completed(jobs), 1):
            index = jobs[future]
            results[index] = future.result()
            progress(done, total, lessons[index]["italian"])
    return results


def _animated_clip(card_path, audio, duration):
    base = ImageClip(card_path).set_duration(duration)
    animated = base.resize(lambda t: 1.0 + 0.025 * min(1.0, t / max(duration, 0.1))).set_position("center")
    return CompositeVideoClip(
        [animated], size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
    ).set_duration(duration).set_audio(audio)


def build_video(title=None, out_path=None, words_path=None, expected_count=None):
    started = time.monotonic()
    title = title or config.VOCAB_TITLE
    out_path = out_path or os.path.join(config.OUTPUT_DIR, "italian_vocabulary.mp4")
    words = load_words(words_path, expected_count=expected_count)
    _progress(2, f"Validated {len(words)} Italian input words", started)

    work_key = hashlib.sha256(("\n".join(words) + "|" + title).encode("utf-8")).hexdigest()[:20]
    work_dir = os.path.join(config.CACHE_DIR, "vocabulary", work_key)
    os.makedirs(work_dir, exist_ok=True)

    lesson_data = generate_lessons(
        words,
        progress=lambda msg: _progress(12, msg, started),
        expected_count=expected_count,
    )
    lessons = lesson_data["words"]
    _progress(20, "English lessons ready", started)

    image_cache = os.path.join(work_dir, "image_index.txt")
    def image_progress(done, total, word):
        percent = 20 + int(done * 20 / total)
        _progress(percent, f"AI illustration {done}/{total}: {word}", started)

    image_paths = _generate_images(lessons, image_progress)
    with open(image_cache, "w", encoding="utf-8") as handle:
        handle.write("\n".join(image_paths))
    _progress(42, "All semantic illustrations ready", started)

    intro_path = os.path.join(work_dir, "intro.png")
    _title_card(title, f"{len(lessons)} Italian words  •  English meaning  •  real examples", intro_path)
    outro_path = os.path.join(work_dir, "outro.png")
    _title_card("Keep going", "A little Italian every day adds up.", outro_path)

    audio_items = [
        (
            "Welcome. We will learn each Italian word through its English meaning, a clear explanation, and a memorable visual example.",
            os.path.join(work_dir, "intro.mp3"),
        )
    ]
    for index, lesson in enumerate(lessons, 1):
        audio_items.append((_word_narration(lesson), os.path.join(work_dir, f"word_{index:02d}.mp3")))
    audio_items.append(
        (
            "Great work. Pause here, repeat the Italian words aloud, and try using them in your own sentences.",
            os.path.join(work_dir, "outro.mp3"),
        )
    )

    _progress(45, f"Generating English narration for {len(lessons)} words", started)
    synthesize_many(audio_items, max_concurrency=config.TTS_CONCURRENCY)
    _progress(58, "Narration complete", started)

    clips = []
    opened_audio = []
    intro_audio = AudioFileClip(audio_items[0][1])
    opened_audio.append(intro_audio)
    clips.append(ImageClip(intro_path).set_duration(intro_audio.duration).set_audio(intro_audio))

    for index, lesson in enumerate(lessons, 1):
        card_path = os.path.join(work_dir, f"card_{index:02d}.png")
        render_card(lesson, image_paths[index - 1], card_path, index, len(lessons))
        audio = AudioFileClip(audio_items[index][1])
        opened_audio.append(audio)
        duration = max(config.WORD_TARGET_SECONDS, audio.duration)
        clips.append(_animated_clip(card_path, audio, duration))
        percent = 58 + int(index * 30 / len(lessons))
        _progress(percent, f"Composed word {index}/{len(lessons)}: {lesson['italian']}", started)

    outro_audio = AudioFileClip(audio_items[-1][1])
    opened_audio.append(outro_audio)
    clips.append(ImageClip(outro_path).set_duration(outro_audio.duration).set_audio(outro_audio))

    final = concatenate_videoclips(clips, method="compose")
    final_duration = float(final.duration)
    music_path = os.path.join(work_dir, "music.wav")
    generate_music(final_duration, music_path, config.MUSIC_MOOD)
    music = AudioFileClip(music_path).volumex(config.MUSIC_VOLUME).set_duration(final_duration)
    final = final.set_audio(CompositeAudioClip([final.audio, music]))

    temp_output = os.path.join(work_dir, "render.tmp.mp4")
    _progress(92, f"Encoding {final_duration:.1f}s final video", started)
    try:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        final.write_videofile(
            temp_output,
            fps=config.FPS,
            codec="libx264",
            audio_codec="aac",
            threads=config.VIDEO_THREADS,
            preset=config.FFMPEG_PRESET,
            bitrate=config.VIDEO_BITRATE,
            verbose=False,
            logger=None,
        )
        os.replace(temp_output, out_path)
    finally:
        try:
            music.close()
        except Exception:
            pass
        try:
            final.close()
        except Exception:
            pass
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        for audio in opened_audio:
            try:
                audio.close()
            except Exception:
                pass

    if final_duration < 180 and expected_count == config.VOCAB_WORD_COUNT:
        raise RuntimeError(f"Unexpectedly short production video: {final_duration:.1f}s")
    _progress(100, f"Complete: {out_path} | duration={final_duration:.1f}s", started)
    return out_path
