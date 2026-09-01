"""Configuration for the automated Italian vocabulary video pipeline."""
import os

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
OLLAMA_KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "30m")
OLLAMA_CONNECT_TIMEOUT = float(os.environ.get("OLLAMA_CONNECT_TIMEOUT", "10"))
OLLAMA_READ_TIMEOUT = float(os.environ.get("OLLAMA_READ_TIMEOUT", "180"))
OLLAMA_PROGRESS_INTERVAL = float(os.environ.get("OLLAMA_PROGRESS_INTERVAL", "1.0"))
OLLAMA_VOCAB_CONTEXT = int(os.environ.get("OLLAMA_VOCAB_CONTEXT", "4096"))
OLLAMA_VOCAB_PREDICT = int(os.environ.get("OLLAMA_VOCAB_PREDICT", "2600"))

TTS_VOICE = os.environ.get("TTS_VOICE", "en-US-GuyNeural")
TTS_RATE = os.environ.get("TTS_RATE", "+0%")
TTS_CONCURRENCY = int(os.environ.get("TTS_CONCURRENCY", "4"))
WORD_TARGET_SECONDS = float(os.environ.get("WORD_TARGET_SECONDS", "17"))
VOCAB_WORD_COUNT = int(os.environ.get("VOCAB_WORD_COUNT", "20"))
VOCAB_TITLE = os.environ.get("VOCAB_TITLE", "20 Italian Words You Should Know")
VOCAB_FILE = os.environ.get("VOCAB_FILE", "italian_words.txt")

# AI image generation. OpenAI is used automatically when OPENAI_API_KEY exists.
# IMAGE_GENERATOR_URL can point to a local/custom image API instead.
IMAGE_PROVIDER = os.environ.get("IMAGE_PROVIDER", "auto")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-2")
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1536x1024")
IMAGE_QUALITY = os.environ.get("IMAGE_QUALITY", "medium")
IMAGE_GENERATOR_URL = os.environ.get("IMAGE_GENERATOR_URL", "")
IMAGE_GENERATOR_TIMEOUT = float(os.environ.get("IMAGE_GENERATOR_TIMEOUT", "180"))

# Copyright-safe generated music. No stock music is required.
MUSIC_MOOD = os.environ.get("MUSIC_MOOD", "meditative")
MUSIC_BPM = int(os.environ.get("MUSIC_BPM", "68"))
MUSIC_VOLUME = float(os.environ.get("MUSIC_VOLUME", "0.12"))

VIDEO_WIDTH = int(os.environ.get("VIDEO_WIDTH", "1920"))
VIDEO_HEIGHT = int(os.environ.get("VIDEO_HEIGHT", "1080"))
FPS = int(os.environ.get("FPS", "30"))
VIDEO_THREADS = int(os.environ.get("VIDEO_THREADS", "4"))
FFMPEG_PRESET = os.environ.get("FFMPEG_PRESET", "medium")
VIDEO_BITRATE = os.environ.get("VIDEO_BITRATE", "8M")

OUTPUT_DIR = "output"
CACHE_DIR = "cache"
LOGS_DIR = "logs"
ASSETS_DIR = "assets"
SKIP_IF_OUTPUT_EXISTS = True
