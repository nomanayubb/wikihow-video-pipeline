"""Deterministic instructional visual generation; no physical device required."""
import os, textwrap
from PIL import Image, ImageDraw, ImageFont
import config


def _font(size, bold=False):
    paths=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "Arial.ttf"]
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p,size)
    return ImageFont.load_default()


def render(scene, path):
    w,h=config.VIDEO_WIDTH,config.VIDEO_HEIGHT
    im=Image.new('RGB',(w,h),(12,14,18)); d=ImageDraw.Draw(im)
    # clean device frame; all labels come from the scene planner, never a fabricated screenshot
    frame=(110,90,w-110,h-90); screen=(155,170,w-155,h-170)
    d.rounded_rectangle(frame, radius=58, fill=(3,4,6), outline=(75,78,88), width=5)
    d.rounded_rectangle(screen, radius=42, fill=(246,247,250))
    d.rounded_rectangle((w//2-80,190,w//2+80,225),radius=18,fill=(18,19,22))
    title=str(scene.get('screen') or scene.get('scene_title') or 'Tutorial')
    target=str(scene.get('target') or '')
    callout=str(scene.get('callout') or '')
    action=str(scene.get('action') or '')
    d.text((205,285),'Tutorial demonstration',font=_font(27,True),fill=(75,78,88))
    lines=textwrap.wrap(title,width=27)
    y=370
    for line in lines[:7]:
        d.text((205,y),line,font=_font(43,True),fill=(20,21,25)); y+=58
    if target:
        box_y=min(y+55, h-520)
        d.rounded_rectangle((205,box_y,w-205,box_y+120),radius=24,fill=(232,236,242),outline=(235,65,70),width=7)
        d.text((240,box_y+35),target,font=_font(31,True),fill=(25,26,30))
    if action in {'tap','long_press','swipe','press_buttons'}:
        cx,cy=w//2,min(h-430,(y+260))
        d.ellipse((cx-46,cy-46,cx+46,cy+46),fill=(255,255,255),outline=(80,82,90),width=5)
        d.text((cx-115,cy+65),action.replace('_',' ').title(),font=_font(27),fill=(30,31,35))
    if callout:
        d.rounded_rectangle((170,h-330,w-170,h-225),radius=24,fill=(255,215,0))
        d.text((205,h-302),callout,font=_font(27,True),fill=(12,12,12))
    im.save(path,quality=95)
    return path
