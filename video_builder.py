"""Render fully automated tutorial videos without physical-device footage."""
import os
import time
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, TextClip

import config
from generate_articles import generate_article
from scene_planner import plan_scenes
from tts import synthesize
from visual_engine import render as render_visual


def _progress(percent, message, started):
    elapsed = time.monotonic() - started
    print(f"[{percent:3d}%] {message} | elapsed {elapsed:.1f}s", flush=True)


def _caption_clips(words, duration):
    clips=[]
    for word in words:
        start=float(word.get('start',0))
        if start >= duration: continue
        dur=min(max(float(word.get('duration',0.15)),0.12), duration-start)
        clips.append(TextClip(str(word.get('text','')), fontsize=config.CAPTION_SIZE,
            font=config.CAPTION_FONT, color=config.CAPTION_HIGHLIGHT_COLOR,
            stroke_color='black', stroke_width=3)
            .set_start(start).set_duration(dur)
            .set_position(('center', config.VIDEO_HEIGHT*0.82)))
    return clips


def build_video(title, out_path):
    started = time.monotonic()
    work_dir=os.path.join(config.CACHE_DIR, '_work', str(abs(hash(title))))
    os.makedirs(work_dir, exist_ok=True)

    _progress(0, 'Starting pipeline', started)
    _progress(5, 'Generating tutorial with Ollama (percentage stays at 5% until Ollama responds)', started)
    article=generate_article(title)
    _progress(20, 'Tutorial generated', started)

    _progress(25, 'Planning visual scenes with Ollama', started)
    storyboard=plan_scenes(article)
    scenes = storyboard.get('scenes', [])
    if not scenes:
        raise RuntimeError('Storyboard produced no scenes')
    _progress(35, f'Scene plan ready: {len(scenes)} scenes', started)

    clips=[]
    total = len(scenes)
    for i, scene in enumerate(scenes, 1):
        narration=str(scene.get('narration','')).strip()
        if not narration:
            continue
        scene_start = time.monotonic()
        base_percent = 35 + int((i-1) * 55 / total)
        _progress(base_percent, f'Scene {i}/{total}: text-to-speech', started)
        audio_path=os.path.join(work_dir, f'scene_{i:02d}.mp3')
        words=synthesize(narration, audio_path)
        audio=AudioFileClip(audio_path)

        _progress(base_percent + 1, f'Scene {i}/{total}: rendering visual', started)
        image_path=os.path.join(work_dir, f'scene_{i:02d}.png')
        render_visual(scene, image_path)
        base=ImageClip(image_path).set_duration(audio.duration).resize((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
        captions=_caption_clips(words, audio.duration)
        clip=CompositeVideoClip([base,*captions], size=(config.VIDEO_WIDTH,config.VIDEO_HEIGHT)).set_duration(audio.duration).set_audio(audio)
        clips.append(clip)
        elapsed_scene = time.monotonic() - scene_start
        done_percent = 35 + int(i * 55 / total)
        _progress(done_percent, f'Scene {i}/{total} complete ({elapsed_scene:.1f}s)', started)

    if not clips:
        raise RuntimeError('Storyboard produced no renderable scenes')

    _progress(92, 'Encoding final MP4', started)
    final=concatenate_videoclips(clips, method='compose')
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    final.write_videofile(out_path, fps=config.FPS, codec='libx264', audio_codec='aac', threads=4, verbose=False, logger=None)
    for c in clips: c.close()
    final.close()
    _progress(100, f'Complete: {out_path}', started)
    return out_path


if __name__ == '__main__':
    build_video('How to customize the Lock Screen on iPhone 17 Pro Max', 'output/demo.mp4')
