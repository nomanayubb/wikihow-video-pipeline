# Topic-to-Video Pipeline

Turns tutorial titles into finished narrated vertical videos without a physical
phone, manual screenshots, or manual recording.

The pipeline creates an original tutorial script with Ollama, plans 15–20
instructional scenes, renders deterministic phone/UI-style visuals and
animations from the scene instructions, generates neural narration with
word-level timing, burns synchronized captions, and assembles the final MP4.

## Architecture

`title → Ollama script → 15–20 scene storyboard → automated visuals → Edge TTS → synced captions → MP4`

The visual engine intentionally does **not** pretend to be a real screenshot.
When exact UI details are uncertain, the planner is instructed to use a neutral
instructional diagram instead of inventing a UI state.

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
   You should see `llama3.1:latest` (the code accepts the untagged `llama3.1`
   name by default).
5. From the repository folder install Python dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```

`edge-tts` supplies narration and does not require a voice API key. MoviePy
uses FFmpeg through `imageio-ffmpeg` for rendering.

## Demo: one command

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

GitHub Actions also compiles the project and runs these tests automatically.
These tests validate the visual engine and the 15–20 scene contract without
requiring a physical iPhone or external image API.

## Batch mode

Put one tutorial title per line in `topics.txt`, then run:

```powershell
python run_batch.py
```

The batch runner skips completed outputs and logs failures so an interrupted
run can be resumed.

## Configuration

Settings are in `config.py` and can also be overridden with environment
variables:

- `OLLAMA_URL` — default `http://localhost:11434/api/generate`
- `OLLAMA_MODEL` — default `llama3.1`
- `TTS_VOICE` — default `en-US-GuyNeural`
- `TTS_RATE` — default `+0%`
- `VIDEO_WIDTH` / `VIDEO_HEIGHT` — default 1080×1920
- `FPS` — default 30
- `MAX_STEPS_PER_ARTICLE` — default 12
- `MIN_VISUAL_SCENES` / `MAX_VISUAL_SCENES` — 15 / 20

## Important limitation

The project can automate the creation of instructional visuals, but it cannot
guarantee pixel-identical replicas of every iOS screen without a trusted source
of current screen specifications/assets. The planner therefore avoids claiming
an invented screen is an exact Apple screenshot. This is intentional: accuracy
is preferred over fabricated UI.

## Files

| File | Purpose |
|---|---|
| `config.py` | Central configuration |
| `generate_articles.py` | Title → original tutorial JSON via Ollama |
| `scene_planner.py` | Tutorial → 15–20 visual scene storyboard |
| `visual_engine.py` | Scene → automated instructional visual |
| `tts.py` | Narration → MP3 + word timestamps |
| `video_builder.py` | Visuals + narration + captions → MP4 |
| `run_demo.py` | One-command local demo |
| `run_batch.py` | Batch entry point |
| `tests/` | Offline automated tests |
| `topics.txt` | Tutorial titles |
