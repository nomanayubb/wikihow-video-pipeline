"""Central configuration for the automated tutorial-video pipeline."""
import os

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
# Small, fast defaults for local CPU/GPU Ollama. Override with environment variables if needed.
OLLAMA_KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "10m")
OLLAMA_ARTICLE_CONTEXT = int(os.environ.get("OLLAMA_ARTICLE_CONTEXT", "2048"))
OLLAMA_ARTICLE_PREDICT = int(os.environ.get("OLLAMA_ARTICLE_PREDICT", "650"))
OLLAMA_SCENE_CONTEXT = int(os.environ.get("OLLAMA_SCENE_CONTEXT", "3072"))
OLLAMA_SCENE_PREDICT = int(os.environ.get("OLLAMA_SCENE_PREDICT", "1300"))
TTS_VOICE = os.environ.get("TTS_VOICE", "en-US-GuyNeural")
TTS_RATE = os.environ.get("TTS_RATE", "+0%")
VIDEO_WIDTH = int(os.environ.get("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.environ.get("VIDEO_HEIGHT", "1920"))
FPS = int(os.environ.get("FPS", "30"))
CAPTION_FONT = os.environ.get("CAPTION_FONT", "Arial-Bold")
CAPTION_SIZE = int(os.environ.get("CAPTION_SIZE", "64"))
CAPTION_COLOR = "white"
CAPTION_HIGHLIGHT_COLOR = "#FFD400"
MAX_STEPS_PER_ARTICLE = int(os.environ.get("MAX_STEPS_PER_ARTICLE", "6"))
MIN_VISUAL_SCENES = int(os.environ.get("MIN_VISUAL_SCENES", "10"))
MAX_VISUAL_SCENES = int(os.environ.get("MAX_VISUAL_SCENES", "12"))
TOPICS_FILE = "topics.txt"
OUTPUT_DIR = "output"
CACHE_DIR = "cache"
LOGS_DIR = "logs"
ASSETS_DIR = "assets"
SKIP_IF_OUTPUT_EXISTS = True
