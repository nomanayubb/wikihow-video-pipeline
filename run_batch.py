"""
Daily entry point.

Usage:
    python run_batch.py

Reads config.TOPICS_FILE (default topics.txt, one topic per line),
generates one finished mp4 per topic into output/, logs results to
logs/run_<date>.log, and skips topics that already have a finished
video (safe to re-run / resume after a crash or Ctrl+C).
"""
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
        print(f"ERROR: topics file not found: {path}")
        print("Create it with 100 lines, one topic title per line, then re-run.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    return lines


def main():
    topics = load_topics(config.TOPICS_FILE)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.LOGS_DIR, exist_ok=True)

    log_path = os.path.join(config.LOGS_DIR, f"run_{datetime.now():%Y-%m-%d_%H%M%S}.log")
    log_lines = []

    def log(msg):
        print(msg)
        log_lines.append(msg)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    log(f"=== Batch run started: {len(topics)} topics ===")

    ok, skipped, failed = 0, 0, 0

    for i, title in enumerate(topics, start=1):
        out_path = os.path.join(config.OUTPUT_DIR, f"{i:03d}_{slugify(title)}.mp4")

        if config.SKIP_IF_OUTPUT_EXISTS and os.path.exists(out_path):
            log(f"[{i}/{len(topics)}] SKIP (already done): {title}")
            skipped += 1
            continue

        log(f"[{i}/{len(topics)}] Building: {title}")
        t0 = time.time()
        try:
            build_video(title, out_path)
            log(f"    -> done in {time.time() - t0:.0f}s -> {out_path}")
            ok += 1
        except Exception as e:
            log(f"    -> FAILED: {e}")
            log("    " + traceback.format_exc().replace("\n", "\n    "))
            failed += 1

    log(f"=== Finished. ok={ok} skipped={skipped} failed={failed} ===")
    log(f"Log saved to: {log_path}")


if __name__ == "__main__":
    main()
