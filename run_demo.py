"""Generate one long-form Italian vocabulary YouTube video."""
import argparse
import os
import sys

import config
from video_builder import build_video


def main():
    parser = argparse.ArgumentParser(description="Generate an automated Italian vocabulary video")
    parser.add_argument("--words", default=config.VOCAB_FILE, help="Text file containing exactly 20 Italian words")
    parser.add_argument("--output", default=None)
    parser.add_argument("--title", default=config.VOCAB_TITLE)
    args = parser.parse_args()

    output = args.output or os.path.join(config.OUTPUT_DIR, "italian_vocabulary.mp4")
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    print(f"Generating: {args.title}")
    print(f"Words: {args.words} | count must be {config.VOCAB_WORD_COUNT}")
    print(f"Ollama: {config.OLLAMA_URL} | model: {config.OLLAMA_MODEL}")
    print(f"Image provider: {config.IMAGE_PROVIDER} | model: {config.IMAGE_MODEL}")
    try:
        path = build_video(args.title, output, args.words)
    except Exception as exc:
        print(f"VIDEO FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
    print(f"VIDEO COMPLETE: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
