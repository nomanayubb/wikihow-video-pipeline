"""Render a fully automated tutorial from a title.

The renderer uses the AI storyboard and creates controlled instructional phone
mockups, highlights, arrows, callouts and diagrams. No physical phone footage
or manual screenshots are required.
"""
import os
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, TextClip

import config
from generate_articles import generate_article
from scene_planner import plan_scenes
from tts import synthesize


def _font(size, bold=False):
    candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "Arial.ttf"]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _scene_image(scene, path):
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    img = Image.new("RGB", (w, h), (18, 20, 25))
    d = ImageDraw.Draw(img)
    title_font, body_font, small_font = _font(48, True), _font(34, True), _font(27)
    d.rounded_rectangle((100, 90, w-100, h-90), radius=65, outline=(90, 95, 110), width=6, fill=(8, 9, 12))
    px1, py1, px2, py2 = 155, 180, w-155, h-180
    d.rounded_rectangle((px1, py1, px2, py2), radius=42, fill=(242, 243, 247))
    screen = str(scene.get("screen") or scene.get("scene_title") or "Tutorial step")
    target = str(scene.get("target") or "")
    callout = str(scene.get("callout") or "")
    vt = scene.get("visual_type", "phone_ui")
    if vt in ("diagram", "tip_card", "title_card"):
        d.rounded_rectangle((px1+45, py1+80, px2-45, py2-80), radius=30, fill=(28, 30, 36))
        d.text((px1+85, py1+170), scene.get("scene_title", "Tutorial"), font=title_font, fill="white")
        d.multiline_text((px1+85, py1+280), screen, font=body_font, fill=(225,225,230), spacing=18, width=px2-px1-170)
    else:
        d.text((px1+45, py1+55), "iPhone tutorial", font=small_font, fill=(70,70,80))
        d.multiline_text((px1+65, py1+145), screen, font=body_font, fill=(20,20,25), spacing=14, width=px2-px1-130)
        if target:
            y = min(py2-250, py1+390)
            d.rounded_rectangle((px1+80, y, px2-80, y+105), radius=24, outline=(235, 70, 70), width=7)
            d.text((px1+110, y+25), target, font=small_font, fill=(30,30,35))
        action = scene.get("action", "")
        if action in ("tap", "long_press", "press_buttons", "swipe"):
            cx, cy = (w//2, min(py2-160, py1+620))
            d.ellipse((cx-45, cy-45, cx+45, cy+45), fill=(255,255,255), outline=(80,80,90), width=5)
            d.text((cx-120, cy+65), action.replace('_',' ').title(), font=small_font, fill=(25,25,30))
    if callout:
        bbox = d.textbbox((0,0), callout, font=small_font)
        tw = bbox[2]-bbox[0]
        d.rounded_rectangle((w//2-tw//2-35, h-260, w//2+tw//2+35, h-175), radius=22, fill=(255,210,0))
        d.text((w//2-tw//2, h-242), callout, font=small_font, fill=(10,10,10))
    img.save(path)


def _caption_clips(words, duration):
    out=[]
    for word in words:
        start=word['start']
        if start>=duration: continue
        dur=min(max(word['duration'],0.15), duration-start)
        out.append(TextClip(word['text'], fontsize=config.CAPTION_SIZE, font=config.CAPTION_FONT,
                            color=config.CAPTION_HIGHLIGHT_COLOR, stroke_color='black', stroke_width=3)
                    .set_start(start).set_duration(dur).set_position(('center', config.VIDEO_HEIGHT*0.82)))
    return out


def build_video(title, out_path):
    work_dir=os.path.join(config.CACHE_DIR, '_work', str(abs(hash(title))))
    os.makedirs(work_dir, exist_ok=True)
    article=generate_article(title)
    storyboard=plan_scenes(article)
    clips=[]
    for i, scene in enumerate(storyboard['scenes'], 1):
        narration=scene['narration']
        audio_path=os.path.join(work_dir, f'scene_{i:02d}.mp3')
        words=synthesize(narration, audio_path)
        audio=AudioFileClip(audio_path)
        image_path=os.path.join(work_dir, f'scene_{i:02d}.png')
        _scene_image(scene, image_path)
        base=ImageClip(image_path).set_duration(audio.duration).resize((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
        captions=_caption_clips(words, audio.duration)
        clip=CompositeVideoClip([base,*captions], size=(config.VIDEO_WIDTH,config.VIDEO_HEIGHT)).set_duration(audio.duration).set_audio(audio)
        clips.append(clip)
    final=concatenate_videoclips(clips, method='compose')
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    final.write_videofile(out_path, fps=config.FPS, codec='libx264', audio_codec='aac', threads=4, verbose=False, logger=None)
    for c in clips: c.close()
    final.close()
    return out_path


if __name__ == '__main__':
    build_video('How to customize the Lock Screen on iPhone 17 Pro Max', 'output/demo.mp4')
