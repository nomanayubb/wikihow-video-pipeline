"""Batch entry point with resumable output handling and structured logging."""
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
        print("Create it with one topic title per line, then re-run.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip() and not line.lstrip().startswith("#")]
    # Preserve order while avoiding accidental duplicate work.
    return list(dict.fromkeys(topics))


def main():
    topics = load_topics(config.TOPICS_FILE)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.LOGS_DIR, exist_ok=True)

    log_path = os.path.join(config.LOGS_DIR, f"run_{datetime.now():%Y-%m-%d_%H%M%S}.log")

    def log(msg):
        print(msg, flush=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    log(f"=== Batch run started: {len(topics)} unique topics ===")
    ok, skipped, failed = 0, 0, 0
    batch_start = time.monotonic()

    for i, title in enumerate(topics, start=1):
        out_path = os.path.join(config.OUTPUT_DIR, f"{i:03d}_{slugify(title)}.mp4")

        if config.SKIP_IF_OUTPUT_EXISTS and os.path.isfile(out_path) and os.path.getsize(out_path) > 0:
            log(f"[{i}/{len(topics)}] SKIP (already done): {title}")
            skipped += 1
            continue

        log(f"[{i}/{len(topics)}] Building: {title}")
        t0 = time.monotonic()
        try:
            build_video(title, out_path)
            elapsed = time.monotonic() - t0
            log(f"    -> done in {elapsed:.0f}s -> {out_path}")
            ok += 1
        except KeyboardInterrupt:
            log("    -> INTERRUPTED by user")
            raise
        except Exception as exc:
            log(f"    -> FAILED after {time.monotonic() - t0:.0f}s: {type(exc).__name__}: {exc}")
            log("    " + traceback.format_exc().replace("\n", "\n    "))
            failed += 1

    total_elapsed = time.monotonic() - batch_start
    log(f"=== Finished in {total_elapsed:.0f}s. ok={ok} skipped={skipped} failed={failed} ===")
    log(f"Log saved to: {log_path}")


if __name__ == "__main__":
    main()
