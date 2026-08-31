import json
from pathlib import Path


def test_scene_schema_and_count():
    from scene_planner import _parse
    raw = json.dumps({"scenes": [{"scene_title": str(i), "narration": "Do this", "visual_type": "button_demo", "screen": "Settings", "target": "Button", "action": "tap", "callout": "Tap"} for i in range(15)]})
    data = _parse(raw)
    assert 15 <= len(data["scenes"]) <= 20
    required = {"scene_title", "narration", "visual_type", "screen", "target", "action", "callout"}
    assert all(required <= set(s) for s in data["scenes"])


def test_visual_engine_creates_valid_png(tmp_path):
    import config
    from visual_engine import render
    from PIL import Image
    path = tmp_path / "scene.png"
    render({"scene_title":"Screenshot","screen":"Screenshot controls","target":"Side + Volume Up","action":"press_buttons","callout":"Press together"}, str(path))
    with Image.open(path) as im:
        assert im.size == (config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
        assert im.format == "PNG"


def test_demo_scene_assets(tmp_path):
    from visual_engine import render
    for i in range(15):
        render({"scene_title":f"Scene {i+1}","screen":"Tutorial screen","target":"Next","action":"tap","callout":"Continue"}, str(tmp_path / f"scene_{i:02d}.png"))
    assert len(list(tmp_path.glob("scene_*.png"))) == 15
