import os
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
from scene_planner import _valid_scene
from tts import synthesize_many
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
    scenes = [
        {
            'narration': 'Do this',
            'visual_type': 'button_demo',
            'screen': 'Settings',
            'target': 'Button',
            'action': 'tap',
            'callout': '',
        }
        for _ in range(config.MIN_VISUAL_SCENES)
    ]
    assert config.MIN_VISUAL_SCENES <= len(scenes) <= config.MAX_VISUAL_SCENES
    assert all(_valid_scene(scene) for scene in scenes)


def test_tts_empty_batch_is_fast_and_safe():
    assert synthesize_many([]) == []
