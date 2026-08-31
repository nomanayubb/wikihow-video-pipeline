"""Central configuration for the automated tutorial-video pipeline."""
import os

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
TTS_VOICE = os.environ.get("TTS_VOICE", "en-US-GuyNeural")
TTS_RATE = os.environ.get("TTS_RATE", "+0%")
VIDEO_WIDTH = int(os.environ.get("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.environ.get("VIDEO_HEIGHT", "1920"))
FPS = int(os.environ.get("FPS", "30"))
CAPTION_FONT = os.environ.get("CAPTION_FONT", "Arial-Bold")
CAPTION_SIZE = int(os.environ.get("CAPTION_SIZE", "64"))
CAPTION_COLOR = "white"
CAPTION_HIGHLIGHT_COLOR = "#FFD400"
MAX_STEPS_PER_ARTICLE = int(os.environ.get("MAX_STEPS_PER_ARTICLE", "12"))
MIN_VISUAL_SCENES = int(os.environ.get("MIN_VISUAL_SCENES", "15"))
MAX_VISUAL_SCENES = int(os.environ.get("MAX_VISUAL_SCENES", "20"))
TOPICS_FILE = "topics.txt"
OUTPUT_DIR = "output"
CACHE_DIR = "cache"
LOGS_DIR = "logs"
ASSETS_DIR = "assets"
SKIP_IF_OUTPUT_EXISTS = True
