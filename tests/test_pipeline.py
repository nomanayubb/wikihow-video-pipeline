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
from vocabulary_generator import _valid


def test_visual_engine_output():
    scene = {
        'scene_title': 'Illustration test',
        'screen': 'Vocabulary concept',
        'target': 'Meaning',
        'action': 'none',
        'callout': 'Test',
    }
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'scene.png')
        render(scene, path)
        assert os.path.isfile(path)
        with Image.open(path) as im:
            assert im.size == (config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
            assert im.format == 'PNG'


def test_vocabulary_lesson_contract():
    lesson = {
        'italian': 'casa',
        'english': 'house',
        'part_of_speech': 'noun',
        'explanation': 'A place where people live.',
        'example': 'La casa è grande.',
        'image_prompt': 'A warm welcoming home.',
    }
    assert _valid(lesson)


def test_scene_contract():
    scenes = [
        {
            'narration': 'Do this',
            'visual_type': 'diagram',
            'screen': 'Concept',
            'target': 'Meaning',
            'action': 'none',
            'callout': '',
        }
        for _ in range(config.MIN_VISUAL_SCENES)
    ]
    assert config.MIN_VISUAL_SCENES <= len(scenes) <= config.MAX_VISUAL_SCENES
    assert all(_valid_scene(scene) for scene in scenes)


def test_tts_empty_batch_is_fast_and_safe():
    assert synthesize_many([]) == []
