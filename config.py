"""Configuration for the automated Italian vocabulary video pipeline."""
import os


def _int(name, default, minimum=1):
    value = int(os.environ.get(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _float(name, default, minimum=0.0):
    value = float(os.environ.get(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
OLLAMA_KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "30m")
OLLAMA_CONNECT_TIMEOUT = _float("OLLAMA_CONNECT_TIMEOUT", 10)
# Streaming keeps the connection active while a slow local model generates.
OLLAMA_READ_TIMEOUT = _float("OLLAMA_READ_TIMEOUT", 300)
OLLAMA_RETRIES = _int("OLLAMA_RETRIES", 2, 1)
OLLAMA_PROGRESS_INTERVAL = _float("OLLAMA_PROGRESS_INTERVAL", 1.0)
OLLAMA_VOCAB_CONTEXT = _int("OLLAMA_VOCAB_CONTEXT", 4096)
OLLAMA_VOCAB_PREDICT = _int("OLLAMA_VOCAB_PREDICT", 700)

TTS_VOICE = os.environ.get("TTS_VOICE", "en-US-GuyNeural")
TTS_RATE = os.environ.get("TTS_RATE", "+0%")
TTS_CONCURRENCY = _int("TTS_CONCURRENCY", 4)
TTS_RETRIES = _int("TTS_RETRIES", 3, 1)
WORD_TARGET_SECONDS = _float("WORD_TARGET_SECONDS", 18.0, 5.0)
VOCAB_WORD_COUNT = _int("VOCAB_WORD_COUNT", 20)
VOCAB_TITLE = os.environ.get("VOCAB_TITLE", "20 Italian Words You Should Know")
VOCAB_FILE = os.environ.get("VOCAB_FILE", "italian_words.txt")
DEMO_WORDS_FILE = os.environ.get("DEMO_WORDS_FILE", "demo_words.txt")
TOPICS_FILE = os.environ.get("TOPICS_FILE", "topics.txt")

IMAGE_PROVIDER = os.environ.get("IMAGE_PROVIDER", "auto").lower()
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-2")
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1536x1024")
IMAGE_QUALITY = os.environ.get("IMAGE_QUALITY", "medium")
IMAGE_GENERATOR_URL = os.environ.get("IMAGE_GENERATOR_URL", "")
IMAGE_GENERATOR_TIMEOUT = _float("IMAGE_GENERATOR_TIMEOUT", 180, 10)
IMAGE_CONCURRENCY = _int("IMAGE_CONCURRENCY", 3)
IMAGE_RETRIES = _int("IMAGE_RETRIES", 3, 1)

MUSIC_MOOD = os.environ.get("MUSIC_MOOD", "meditative").lower()
MUSIC_BPM = _int("MUSIC_BPM", 68, 40)
MUSIC_VOLUME = _float("MUSIC_VOLUME", 0.10)

VIDEO_WIDTH = _int("VIDEO_WIDTH", 1920, 320)
VIDEO_HEIGHT = _int("VIDEO_HEIGHT", 1080, 240)
FPS = _int("FPS", 30, 12)
VIDEO_THREADS = _int("VIDEO_THREADS", 4)
FFMPEG_PRESET = os.environ.get("FFMPEG_PRESET", "medium")
VIDEO_BITRATE = os.environ.get("VIDEO_BITRATE", "8M")

OUTPUT_DIR = "output"
CACHE_DIR = "cache"
LOGS_DIR = "logs"
ASSETS_DIR = "assets"
SKIP_IF_OUTPUT_EXISTS = True
MIN_WORDS = _int("MIN_WORDS", 4)
MAX_WORDS = _int("MAX_WORDS", 100)

if MIN_WORDS > MAX_WORDS:
    raise ValueError("MIN_WORDS cannot exceed MAX_WORDS")
if WORD_TARGET_SECONDS * VOCAB_WORD_COUNT < 180:
    raise ValueError("WORD_TARGET_SECONDS must keep a 20-word production video at least 3 minutes")
