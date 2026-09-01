import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from vocabulary_generator import _valid, _validate_words, load_words
from vocabulary_visual import render_card
from tts import synthesize_many


def test_input_validation_requires_exact_word_count():
    words = [f"w{i}" for i in range(config.VOCAB_WORD_COUNT)]
    assert _validate_words(words) == words


def test_input_validation_rejects_duplicate_words():
    words = ["casa"] * config.VOCAB_WORD_COUNT
    try:
        _validate_words(words)
    except ValueError as exc:
        assert "Duplicate" in str(exc)
    else:
        raise AssertionError("duplicate vocabulary was accepted")


def test_load_words_ignores_comments(tmp_path):
    words = [f"word{i}" for i in range(config.VOCAB_WORD_COUNT)]
    path = tmp_path / "words.txt"
    path.write_text("# comment\n" + "\n".join(words) + "\n", encoding="utf-8")
    assert load_words(str(path)) == words


def test_lesson_contract():
    lesson = {
        "italian": "casa",
        "english": "house",
        "part_of_speech": "noun",
        "explanation": "A place where people live and feel at home.",
        "example": "The house is near the beach.",
        "image_prompt": "A warm Italian home in golden evening light, with a welcoming doorway and garden.",
    }
    assert _valid(lesson)


def test_card_render(tmp_path):
    from PIL import Image
    image_path = tmp_path / "art.png"
    card_path = tmp_path / "card.png"
    Image.new("RGB", (1536, 1024), (100, 120, 150)).save(image_path)
    lesson = {
        "italian": "casa",
        "english": "house",
        "part_of_speech": "noun",
        "explanation": "A place where people live.",
        "example": "The house is beautiful.",
    }
    render_card(lesson, str(image_path), str(card_path), 1, 5)
    with Image.open(card_path) as image:
        assert image.size == (config.VIDEO_WIDTH, config.VIDEO_HEIGHT)


def test_tts_empty_batch():
    assert synthesize_many([]) == []
