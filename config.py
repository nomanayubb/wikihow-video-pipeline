"""
Central config. Fill in your keys below, or set them as environment
variables with the same names (env vars override the values here).
"""
import os

# --- Required ---
PEXELS_API_KEY    = os.environ.get("PEXELS_API_KEY", "")      # free key: https://www.pexels.com/api/

# --- Article generation (Ollama - free, runs locally, no API key) ---
OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")     # run `ollama pull llama3.1` first

# --- Voice ---
TTS_VOICE = "en-US-GuyNeural"     # edge-tts voice. Try en-US-JennyNeural, en-GB-RyanNeural, etc.
TTS_RATE  = "+0%"                  # e.g. "+10%" to speak faster

# --- Video ---
VIDEO_WIDTH   = 1080
VIDEO_HEIGHT  = 1920               # vertical (Shorts/Reels/TikTok). Use 1920x1080 for landscape.
FPS           = 30
CAPTION_FONT  = "Arial-Bold"
CAPTION_SIZE  = 64
CAPTION_COLOR = "white"
CAPTION_HIGHLIGHT_COLOR = "#FFD400"   # word being spoken right now
MAX_STEPS_PER_ARTICLE = 12            # cap so videos don't run too long

# --- Paths ---
TOPICS_FILE   = "topics.txt"
OUTPUT_DIR    = "output"
CACHE_DIR     = "cache"
LOGS_DIR      = "logs"
ASSETS_DIR    = "assets"

# --- Batch behavior ---
SKIP_IF_OUTPUT_EXISTS = True   # resume-safe: won't redo a video that already exists
