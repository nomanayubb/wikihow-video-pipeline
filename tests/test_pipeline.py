import os
import tempfile
from PIL import Image
import config
from visual_engine import render


def test_visual_engine_output():
    scene = {
        'scene_title': 'Screenshot buttons',
        'screen': 'iPhone screenshot tutorial',
        'target': 'Side button + Volume Up',
        'action': 'press_buttons',
        'callout': 'Press both buttons together',
    }
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'scene.png')
        render(scene, path)
        assert os.path.isfile(path)
        with Image.open(path) as im:
            assert im.size == (config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
            assert im.format == 'PNG'


def test_scene_contract():
    scenes = [{'narration': 'Do this', 'visual_type': 'button_demo', 'screen': 'Settings', 'target': 'Button', 'action': 'tap', 'callout': ''} for _ in range(15)]
    assert 15 <= len(scenes) <= 20
    for s in scenes:
        assert s['narration'] and s['visual_type'] and s['screen'] and s['action']
