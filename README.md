# Topic-to-Video Pipeline

Turns tutorial titles into finished narrated vertical videos without a physical
phone, manual screenshots, or manual recording.

The pipeline creates an original tutorial script with Ollama, plans a compact
set of instructional scenes, renders deterministic phone/UI-style visuals,
generates neural narration with word-level timing, burns synchronized captions,
and assembles the final MP4.

## Architecture

`title → Ollama script → scene storyboard → automated visuals → Edge TTS → synced captions → MP4`

The visual engine intentionally does **not** pretend to be a real screenshot.
When exact UI details are uncertain, the planner is instructed to use a neutral
instructional diagram instead of inventing a UI state.

## Performance optimizations

- Ollama responses stream continuously with live chunk/character rate reporting.
- Ollama now has a configurable read timeout, so a genuinely stalled request can
  fail instead of hanging forever.
- `keep_alive` defaults to 30 minutes so the model is less likely to unload
  between article generation and scene planning.
- Article and scene JSON caches use versioned keys and atomic writes.
- Scene planning is configurable through `MIN_VISUAL_SCENES` and
  `MAX_VISUAL_SCENES` instead of hard-coded README/code contracts.
- TTS is synthesized concurrently with a small bounded concurrency of 3,
  reducing the repeated network wait across scenes.
- Batch mode removes duplicate topics and skips only non-empty finished files.
- Image downloads use bounded connect/read timeouts and atomic cache writes.

## One-time setup on Windows

1. Install Python 3.10+.
2. Install Ollama from the official Ollama website.
3. Pull the model:
   ```powershell
   ollama pull llama3.1
   ```
4. Verify it:
   ```powershell
   ollama list
   ```
5. From the repository folder install Python dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```

`edge-tts` supplies narration and does not require a voice API key. MoviePy
uses FFmpeg through `imageio-ffmpeg` for rendering.

## Demo

The default demo is:

`How to customize the Lock Screen on iPhone 17 Pro Max`

Run:

```powershell
python run_demo.py
```

Or choose another title:

```powershell
python run_demo.py --title "How to take a screenshot on iPhone 17 Pro Max"
```

The result is written to `output/demo.mp4` unless `--output` is supplied.

## Automated tests

Run the offline tests locally:

```powershell
python -m pytest -q tests
```

GitHub Actions compiles the project and runs these tests automatically. The
suite does not require Ollama, a physical iPhone, or the Pexels API.

## Batch mode

Put one tutorial title per line in `topics.txt`, then run:

```powershell
python run_batch.py
```

Blank lines and lines beginning with `#` are ignored. Duplicate topics are
removed while preserving their first occurrence. Completed non-empty MP4 files
are skipped so an interrupted run can be resumed.

## Configuration

Settings are in `config.py` and can also be overridden with environment
variables:

- `OLLAMA_URL` — default `http://localhost:11434/api/generate`
- `OLLAMA_MODEL` — default `llama3.1`
- `OLLAMA_KEEP_ALIVE` — default `30m`
- `OLLAMA_CONNECT_TIMEOUT` — default `10` seconds
- `OLLAMA_READ_TIMEOUT` — default `180` seconds between streamed response reads
- `OLLAMA_PROGRESS_INTERVAL` — default `1.0` second
- `OLLAMA_ARTICLE_CONTEXT` / `OLLAMA_ARTICLE_PREDICT` — default `2048` / `500`
- `OLLAMA_SCENE_CONTEXT` / `OLLAMA_SCENE_PREDICT` — default `3072` / `1100`
- `TTS_VOICE` — default `en-US-GuyNeural`
- `TTS_RATE` — default `+0%`
- `VIDEO_WIDTH` / `VIDEO_HEIGHT` — default 1080×1920
- `FPS` — default 30
- `MIN_VISUAL_SCENES` / `MAX_VISUAL_SCENES` — default 10 / 12

If Ollama is slow on your machine, the live log now shows character throughput
and elapsed time rather than making the pipeline appear frozen at 5%.

## Important limitation

The project can automate instructional visuals, but it cannot guarantee
pixel-identical replicas of every iOS screen without a trusted source of current
screen specifications/assets. The planner therefore avoids claiming an
invented screen is an exact Apple screenshot. This is intentional: accuracy is
preferred over fabricated UI.

## Files

| File | Purpose |
|---|---|
| `config.py` | Central configuration |
| `generate_articles.py` | Title → original tutorial JSON via Ollama |
| `scene_planner.py` | Tutorial → configurable visual storyboard |
| `visual_engine.py` | Scene → automated instructional visual |
| `image_sourcer.py` | Optional Pexels image source with fallback |
| `tts.py` | Narration → MP3 + word timestamps, including batched TTS |
| `video_builder.py` | Visuals + narration + captions → MP4 |
| `run_demo.py` | One-command local demo |
| `run_batch.py` | Resumable batch entry point |
| `tests/` | Offline automated tests |
| `topics.txt` | Tutorial titles |
