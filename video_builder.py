"""
Step 4: Stitch everything into one finished mp4 per article.

For each step: its image is shown for exactly as long as its narration audio
lasts. Word-by-word animated captions are burned in, synced to the same
word-boundary timestamps edge-tts gave us.
"""
import os
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips,
    TextClip, concatenate_audioclips
)

import config
from generate_articles import generate_article
from tts import synthesize
from image_sourcer import get_image


def _caption_clips(words: list, clip_duration: float):
    """One TextClip per word, shown only during its own time window,
    positioned near the bottom, highlighted while active."""
    clips = []
    for w in words:
        start = w["start"]
        dur = max(w["duration"], 0.15)
        if start >= clip_duration:
            continue
        dur = min(dur, clip_duration - start)
        txt = TextClip(
            w["text"],
            fontsize=config.CAPTION_SIZE,
            font=config.CAPTION_FONT,
            color=config.CAPTION_HIGHLIGHT_COLOR,
            stroke_color="black",
            stroke_width=3,
        ).set_start(start).set_duration(dur).set_position(("center", config.VIDEO_HEIGHT * 0.78))
        clips.append(txt)
    return clips


def _build_step_clip(step: dict, step_index: int, work_dir: str):
    narration = step["narration"]
    audio_path = os.path.join(work_dir, f"step_{step_index}.mp3")
    words = synthesize(narration, audio_path)

    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration

    img_path = get_image(step.get("image_keywords", step["step_title"]), step["step_title"])
    image_clip = (
        ImageClip(img_path)
        .set_duration(duration)
        .resize(height=config.VIDEO_HEIGHT)
        .set_position("center")
    )
    # crop/pad to exact frame size
    image_clip = image_clip.on_color(
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
        color=(0, 0, 0),
        pos="center",
    )

    captions = _caption_clips(words, duration)

    composite = CompositeVideoClip(
        [image_clip, *captions], size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
    ).set_duration(duration).set_audio(audio_clip)

    return composite


def build_video(title: str, out_path: str):
    work_dir = os.path.join(config.CACHE_DIR, "_work")
    os.makedirs(work_dir, exist_ok=True)

    article = generate_article(title)
    all_steps = article["steps"][: config.MAX_STEPS_PER_ARTICLE]

    clips = []

    # Intro clip
    intro_audio_path = os.path.join(work_dir, "intro.mp3")
    intro_words = synthesize(article["intro"], intro_audio_path)
    intro_audio = AudioFileClip(intro_audio_path)
    intro_img = get_image(article["title"], article["title"])
    intro_image_clip = (
        ImageClip(intro_img)
        .set_duration(intro_audio.duration)
        .resize(height=config.VIDEO_HEIGHT)
        .on_color(size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT), color=(0, 0, 0), pos="center")
    )
    intro_captions = _caption_clips(intro_words, intro_audio.duration)
    intro_clip = CompositeVideoClip(
        [intro_image_clip, *intro_captions], size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
    ).set_duration(intro_audio.duration).set_audio(intro_audio)
    clips.append(intro_clip)

    for i, step in enumerate(all_steps, start=1):
        clips.append(_build_step_clip(step, i, work_dir))

    final = concatenate_videoclips(clips, method="compose")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    final.write_videofile(
        out_path, fps=config.FPS, codec="libx264", audio_codec="aac",
        threads=4, verbose=False, logger=None,
    )

    for c in clips:
        c.close()

    return out_path


if __name__ == "__main__":
    build_video(
        "Easiest Ways to Uninstall a Problematic Windows Update",
        "output/test_video.mp4",
    )
