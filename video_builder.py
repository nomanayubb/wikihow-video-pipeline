"""Render fully automated tutorial videos without physical-device footage."""
import os
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, TextClip

import config
from generate_articles import generate_article
from scene_planner import plan_scenes
from tts import synthesize
from visual_engine import render as render_visual


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
    work_dir=os.path.join(config.CACHE_DIR, '_work', str(abs(hash(title))))
    os.makedirs(work_dir, exist_ok=True)
    article=generate_article(title)
    storyboard=plan_scenes(article)
    clips=[]
    for i, scene in enumerate(storyboard['scenes'], 1):
        narration=str(scene.get('narration','')).strip()
        if not narration: continue
        audio_path=os.path.join(work_dir, f'scene_{i:02d}.mp3')
        words=synthesize(narration, audio_path)
        audio=AudioFileClip(audio_path)
        image_path=os.path.join(work_dir, f'scene_{i:02d}.png')
        render_visual(scene, image_path)
        base=ImageClip(image_path).set_duration(audio.duration).resize((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
        captions=_caption_clips(words, audio.duration)
        clip=CompositeVideoClip([base,*captions], size=(config.VIDEO_WIDTH,config.VIDEO_HEIGHT)).set_duration(audio.duration).set_audio(audio)
        clips.append(clip)
    if not clips:
        raise RuntimeError('Storyboard produced no renderable scenes')
    final=concatenate_videoclips(clips, method='compose')
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    final.write_videofile(out_path, fps=config.FPS, codec='libx264', audio_codec='aac', threads=4, verbose=False, logger=None)
    for c in clips: c.close()
    final.close()
    return out_path


if __name__ == '__main__':
    build_video('How to customize the Lock Screen on iPhone 17 Pro Max', 'output/demo.mp4')
