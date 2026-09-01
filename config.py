"""Central configuration for the automated video pipeline."""
import os

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
OLLAMA_KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "30m")
OLLAMA_CONNECT_TIMEOUT = float(os.environ.get("OLLAMA_CONNECT_TIMEOUT", "10"))
OLLAMA_READ_TIMEOUT = float(os.environ.get("OLLAMA_READ_TIMEOUT", "180"))
OLLAMA_PROGRESS_INTERVAL = float(os.environ.get("OLLAMA_PROGRESS_INTERVAL", "1.0"))
OLLAMA_ARTICLE_CONTEXT = int(os.environ.get("OLLAMA_ARTICLE_CONTEXT", "2048"))
OLLAMA_ARTICLE_PREDICT = int(os.environ.get("OLLAMA_ARTICLE_PREDICT", "500"))
OLLAMA_SCENE_CONTEXT = int(os.environ.get("OLLAMA_SCENE_CONTEXT", "3072"))
OLLAMA_SCENE_PREDICT = int(os.environ.get("OLLAMA_SCENE_PREDICT", "1100"))
TTS_VOICE = os.environ.get("TTS_VOICE", "en-US-GuyNeural")
TTS_RATE = os.environ.get("TTS_RATE", "+0%")

# Professional vocabulary videos default to 16:9.
VIDEO_WIDTH = int(os.environ.get("VIDEO_WIDTH", "1920"))
VIDEO_HEIGHT = int(os.environ.get("VIDEO_HEIGHT", "1080"))
FPS = int(os.environ.get("FPS", "30"))
CAPTION_FONT = os.environ.get("CAPTION_FONT", "Arial-Bold")
CAPTION_SIZE = int(os.environ.get("CAPTION_SIZE", "54"))
CAPTION_COLOR = "white"
CAPTION_HIGHLIGHT_COLOR = "#FFD400"
MAX_STEPS_PER_ARTICLE = int(os.environ.get("MAX_STEPS_PER_ARTICLE", "6"))
MIN_VISUAL_SCENES = int(os.environ.get("MIN_VISUAL_SCENES", "10"))
MAX_VISUAL_SCENES = int(os.environ.get("MAX_VISUAL_SCENES", "12"))

# Optional local image-model adapter (ComfyUI/A1111 compatible).
IMAGE_GENERATOR_URL = os.environ.get("IMAGE_GENERATOR_URL", "")
IMAGE_GENERATOR_TIMEOUT = float(os.environ.get("IMAGE_GENERATOR_TIMEOUT", "120"))
MUSIC_DIR = os.environ.get("MUSIC_DIR", os.path.join("assets", "music"))
FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "ffmpeg")

TOPICS_FILE = "topics.txt"
VOCAB_FILE = os.environ.get("VOCAB_FILE", "italian_words.txt")
OUTPUT_DIR = "output"
CACHE_DIR = "cache"
LOGS_DIR = "logs"
ASSETS_DIR = "assets"
SKIP_IF_OUTPUT_EXISTS = True
