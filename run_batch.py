"""Batch renderer for many independent Italian vocabulary video jobs."""
import os
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import config
from vocabulary_video import build_video


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80] or "vocabulary-video"


def load_jobs(path):
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Batch job file not found: {path}")
    jobs = []
    for raw in source.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|", 1)]
        words_path = Path(parts[0])
        if not words_path.is_absolute():
            words_path = source.parent / words_path
        title = parts[1] if len(parts) == 2 and parts[1] else config.VOCAB_TITLE
        jobs.append((words_path, title))
    if not jobs:
        raise ValueError("No batch jobs found")
    return jobs


def main():
    jobs = load_jobs("topics.txt")
    Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(config.LOGS_DIR).mkdir(parents=True, exist_ok=True)
    log_path = Path(config.LOGS_DIR) / f"batch_{datetime.now():%Y%m%d_%H%M%S}.log"

    def log(message):
        print(message, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")

    ok = skipped = failed = 0
    log(f"=== Batch started: {len(jobs)} videos ===")
    try:
        for index, (words_path, title) in enumerate(jobs, 1):
            output = Path(config.OUTPUT_DIR) / f"{index:03d}_{_slug(title)}.mp4"
            if config.SKIP_IF_OUTPUT_EXISTS and output.is_file() and output.stat().st_size > 100_000:
                log(f"[{index}/{len(jobs)}] SKIP {title}")
                skipped += 1
                continue
            started = time.monotonic()
            log(f"[{index}/{len(jobs)}] START {title}")
            try:
                build_video(title, str(output), str(words_path))
                log(f"[{index}/{len(jobs)}] DONE {output} in {time.monotonic() - started:.0f}s")
                ok += 1
            except KeyboardInterrupt:
                log("Interrupted by user.")
                raise
            except Exception as exc:
                failed += 1
                log(f"[{index}/{len(jobs)}] FAILED {type(exc).__name__}: {exc}")
                log(traceback.format_exc())
    finally:
        log(f"=== Batch finished: ok={ok} skipped={skipped} failed={failed} ===")
        log(f"Log: {log_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
