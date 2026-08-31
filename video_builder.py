"""Render fully automated tutorial videos without physical-device footage."""
import hashlib
import os
import time
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, TextClip

import config
from generate_articles import generate_article
from scene_planner import plan_scenes
from tts import synthesize_many
from visual_engine import render as render_visual


def _progress(percent, message, started):
    elapsed = time.monotonic() - started
    print(f"[{percent:3d}%] {message} | elapsed {elapsed:.1f}s", flush=True)


def _ollama_progress(stage_start, message, started):
    def report(detail):
        _progress(stage_start, f'{message} | {detail}', started)
    return report


def _caption_clips(words, duration):
    clips = []
    for word in words:
        start = max(0.0, float(word.get('start', 0)))
        if start >= duration:
            continue
        dur = min(max(float(word.get('duration', 0.15)), 0.12), duration - start)
        text = str(word.get('text', '')).strip()
        if not text:
            continue
        clips.append(TextClip(
            text,
            fontsize=config.CAPTION_SIZE,
            font=config.CAPTION_FONT,
            color=config.CAPTION_HIGHLIGHT_COLOR,
            stroke_color='black',
            stroke_width=3,
        ).set_start(start).set_duration(dur).set_position(('center', config.VIDEO_HEIGHT * 0.82)))
    return clips


def build_video(title, out_path):
    started = time.monotonic()
    safe_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()[:16]
    work_dir = os.path.join(config.CACHE_DIR, '_work', safe_hash)
    os.makedirs(work_dir, exist_ok=True)

    _progress(0, 'Starting pipeline', started)
    _progress(5, 'Generating tutorial with Ollama', started)
    article = generate_article(title, progress=_ollama_progress(5, 'Ollama tutorial generation', started))
    _progress(20, 'Tutorial generated', started)

    _progress(25, 'Planning visual scenes with Ollama', started)
    storyboard = plan_scenes(article, progress=_ollama_progress(25, 'Ollama scene planning', started))
    scenes = storyboard.get('scenes', [])
    if not scenes:
        raise RuntimeError('Storyboard produced no scenes')
    _progress(35, f'Scene plan ready: {len(scenes)} scenes', started)

    clips = []
    total = len(scenes)
    try:
        # Network TTS is the slowest repeated per-scene operation. Run a small
        # bounded batch concurrently, then render clips from the finished audio.
        tts_items = []
        render_scenes = []
        for i, scene in enumerate(scenes, 1):
            narration = str(scene.get('narration', '')).strip()
            if not narration:
                continue
            render_scenes.append((i, scene))
            tts_items.append((narration, os.path.join(work_dir, f'scene_{i:02d}.mp3')))

        if not tts_items:
            raise RuntimeError('Storyboard produced no renderable scenes')

        _progress(38, f'Generating narration for {len(tts_items)} scenes (concurrency=3)', started)
        timestamps = synthesize_many(tts_items, max_concurrency=3)
        _progress(55, 'Narration generation complete', started)

        for index, ((i, scene), words) in enumerate(zip(render_scenes, timestamps), 1):
            scene_start = time.monotonic()
            base_percent = 55 + int((index - 1) * 37 / total)
            audio_path = tts_items[index - 1][1]
            _progress(base_percent, f'Scene {i}/{total}: rendering visual', started)
            image_path = os.path.join(work_dir, f'scene_{i:02d}.png')
            render_visual(scene, image_path)
            audio = AudioFileClip(audio_path)
            try:
                base = ImageClip(image_path).set_duration(audio.duration).resize((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
                captions = _caption_clips(words, audio.duration)
                clip = CompositeVideoClip([base, *captions], size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT)).set_duration(audio.duration).set_audio(audio)
                clips.append(clip)
            except Exception:
                audio.close()
                raise
            elapsed_scene = time.monotonic() - scene_start
            done_percent = 55 + int(index * 37 / total)
            _progress(done_percent, f'Scene {i}/{total} complete ({elapsed_scene:.1f}s)', started)

        _progress(92, 'Encoding final MP4', started)
        final = concatenate_videoclips(clips, method='compose')
        try:
            os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
            final.write_videofile(out_path, fps=config.FPS, codec='libx264', audio_codec='aac', threads=4, verbose=False, logger=None)
        finally:
            final.close()
        _progress(100, f'Complete: {out_path}', started)
        return out_path
    finally:
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
