"""Run one complete tutorial-video demo using the local Ollama instance."""
import argparse
import os
import sys

import config
from video_builder import build_video

DEFAULT_TITLE = "How to customize the Lock Screen on iPhone 17 Pro Max"


def main():
    parser = argparse.ArgumentParser(description="Generate one automated tutorial video")
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    output = args.output or os.path.join(config.OUTPUT_DIR, "demo.mp4")
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    print(f"Generating: {args.title}")
    print(f"Ollama: {config.OLLAMA_URL} | model: {config.OLLAMA_MODEL}")
    try:
        path = build_video(args.title, output)
    except Exception as exc:
        print(f"DEMO FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
    print(f"DEMO COMPLETE: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
