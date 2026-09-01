"""Command-line entry point for the Italian vocabulary video generator."""
import argparse
import os

import config
from vocabulary_video import build_video


def main():
    parser = argparse.ArgumentParser(description="Create a polished Italian-to-English vocabulary video")
    parser.add_argument("--words", default="demo_words.txt", help="Italian word file; one word per line")
    parser.add_argument("--output", default=os.path.join(config.OUTPUT_DIR, "demo_vocabulary.mp4"))
    parser.add_argument("--title", default="Italian Vocabulary — Learn Through Stories")
    parser.add_argument("--mood", choices=("meditative", "funny", "adventure"), default=config.MUSIC_MOOD)
    args = parser.parse_args()
    config.MUSIC_MOOD = args.mood
    print(f"Input: {args.words}")
    print(f"Output: {args.output}")
    print(f"Words required: {config.VOCAB_WORD_COUNT}")
    print(f"Ollama: {config.OLLAMA_URL} | model={config.OLLAMA_MODEL}")
    print(f"Image provider: {config.IMAGE_PROVIDER} | model={config.IMAGE_MODEL}")
    print(f"Music: {config.MUSIC_MOOD}")
    return 0 if build_video(args.title, args.output, args.words) else 1


if __name__ == "__main__":
    raise SystemExit(main())
