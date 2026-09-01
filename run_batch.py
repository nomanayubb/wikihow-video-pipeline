"""Batch entry point for multiple 20-word vocabulary videos."""
import os
import re
import sys
import time
import traceback
from datetime import datetime

import config
from video_builder import build_video


def slugify(title: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower()).strip("-")
    return s[:80] or "untitled"


def load_topics(path: str) -> list:
    if not os.path.exists(path):
        print(f"ERROR: vocabulary file not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.lstrip().startswith("#")]


def main():
    # Each non-comment line in topics.txt can point to a 20-word file.
    topics = load_topics(config.TOPICS_FILE)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.LOGS_DIR, exist_ok=True)
    log_path = os.path.join(config.LOGS_DIR, f"run_{datetime.now():%Y-%m-%d_%H%M%S}.log")

    def log(msg):
        print(msg)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    ok = skipped = failed = 0
    log(f"=== Vocabulary batch started: {len(topics)} jobs ===")
    for i, job in enumerate(topics, 1):
        # Format: path/to/words.txt | Optional YouTube title
        parts = [p.strip() for p in job.split("|", 1)]
        words_path = parts[0]
        title = parts[1] if len(parts) == 2 else f"{config.VOCAB_WORD_COUNT} Italian Words"
        out_path = os.path.join(config.OUTPUT_DIR, f"{i:03d}_{slugify(title)}.mp4")
        if config.SKIP_IF_OUTPUT_EXISTS and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            log(f"[{i}/{len(topics)}] SKIP: {title}")
            skipped += 1
            continue
        log(f"[{i}/{len(topics)}] Building: {title}")
        t0 = time.monotonic()
        try:
            build_video(title, out_path, words_path)
            log(f"    -> done in {time.monotonic() - t0:.0f}s -> {out_path}")
            ok += 1
        except KeyboardInterrupt:
            log("Interrupted by user.")
            raise
        except Exception as exc:
            log(f"    -> FAILED: {exc}")
            log("    " + traceback.format_exc().replace("\n", "\n    "))
            failed += 1
    log(f"=== Finished. ok={ok} skipped={skipped} failed={failed} ===")
    log(f"Log saved to: {log_path}")


if __name__ == "__main__":
    main()
