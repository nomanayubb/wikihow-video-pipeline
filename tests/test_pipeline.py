from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from PIL import Image

from tts import synthesize_many
from vocabulary_generator import _valid, load_words, validate_words
from vocabulary_visual import render_card


def test_production_word_file_has_exact_count():
    words = load_words(ROOT / config.VOCAB_FILE, expected_count=config.VOCAB_WORD_COUNT)
    assert len(words) == config.VOCAB_WORD_COUNT


def test_demo_word_file_has_five_words():
    words = load_words(ROOT / config.DEMO_WORDS_FILE, expected_count=5)
    assert len(words) == 5


def test_input_validation_rejects_duplicates():
    words = [f"word-{i}" for i in range(config.VOCAB_WORD_COUNT - 1)] + ["word-0"]
    try:
        validate_words(words)
    except ValueError as exc:
        assert "Duplicate" in str(exc)
    else:
        raise AssertionError("duplicate vocabulary was accepted")


def test_input_validation_strips_bom_and_comments():
    words = [f"word-{i}" for i in range(5)]
    raw = ["\ufeff# comment", *words]
    assert validate_words(raw, expected_count=5) == words


def test_lesson_contract():
    lesson = {
        "italian": "casa",
        "english": "house",
        "part_of_speech": "noun",
        "explanation": "A place where people live and feel at home. It commonly describes a building or living space, and it can also mean home in a more personal sense.",
        "example": "The house is near the beach.",
        "image_prompt": "A beautiful welcoming Italian home at golden hour, with a garden and warm interior light.",
    }
    assert _valid(lesson)


def test_card_render(tmp_path):
    image_path = tmp_path / "art.png"
    card_path = tmp_path / "card.png"
    Image.new("RGB", (1536, 1024), (100, 120, 150)).save(image_path)
    lesson = {
        "italian": "casa",
        "english": "house",
        "part_of_speech": "noun",
        "explanation": "A place where people live and feel at home. This word can describe both the building and the idea of home.",
        "example": "The house is beautiful.",
    }
    render_card(lesson, str(image_path), str(card_path), 1, 5)
    with Image.open(card_path) as image:
        assert image.size == (config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
        assert image.format == "PNG"


def test_empty_tts_batch_is_safe():
    assert synthesize_many([]) == []
