# Topic-to-Video Pipeline

Turns a list of topic titles into finished narrated videos, fully automated:
original script written per topic → AI voice with word timing → matching
stock images synced to narration → word-by-word animated captions burned in
→ one mp4 per topic.

This does **not** scrape WikiHow or any other site. It writes original
content based on the topic title you give it, and sources images from
Pexels' free, licensed stock photo library. That's what keeps it legally
safe to run at scale.

**Fully free to run** — article writing uses Ollama (a local LLM on your
own machine, no API key, no per-use cost), voice uses edge-tts (free), and
images use Pexels' free tier. Nothing in this pipeline requires a paid API.

## One-time setup

1. Install Python 3.10+ and ffmpeg:
   ```bash
   # ffmpeg (required by moviepy)
   sudo apt install ffmpeg      # Linux
   brew install ffmpeg          # Mac
   # Windows: download from ffmpeg.org and add to PATH
   ```

2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Ollama (free local LLM, for writing the articles):
   - Download from https://ollama.com/download and install it
   - Pull a model (one-time, a few GB download):
     ```bash
     ollama pull llama3.1
     ```
   - Ollama runs a local server automatically in the background after
     install — nothing to start manually. It listens on
     `http://localhost:11434`.
   - Your machine needs ~8GB+ RAM free for `llama3.1`. If that's tight,
     use a smaller model instead: `ollama pull llama3.2` (about 3GB, still
     good for this) and set `OLLAMA_MODEL=llama3.2`.

4. Get one free key:
   - **Pexels API key** (free, for step images): https://www.pexels.com/api/

5. Set it as an environment variable (recommended) or paste into `config.py`:
   ```bash
   export PEXELS_API_KEY="..."
   ```

6. Test the pipeline on one topic:
   ```bash
   python video_builder.py
   ```
   This builds `output/test_video.mp4` from the Windows Update example.
   Watch it before running the full batch — check voice, image relevance,
   and caption timing look right, and adjust `config.py` (voice, video
   size, font size, etc.) if needed.

## Daily use

1. Replace the contents of `topics.txt` with your 100 new topic titles,
   one per line (plain titles, not links — e.g.
   `Easiest Ways to Uninstall a Problematic Windows Update`).

2. Run:
   ```bash
   python run_batch.py
   ```

3. Walk away. Finished videos land in `output/`, numbered and named after
   each topic (`001_easiest-ways-to-uninstall-a-problematic-windows-update.mp4`).
   Progress and any errors are logged to `logs/run_<timestamp>.log`.

If the run gets interrupted (crash, closed laptop, Ctrl+C), just run
`python run_batch.py` again — it skips any topic that already has a
finished video in `output/` and picks up where it left off.

## Cost per day (100 videos)

- **Ollama**: $0 — runs on your own machine, no API, no per-use charge.
- **edge-tts**: $0 — no key.
- **Pexels**: $0 — free tier.

The only real cost is your own electricity and time — generating 100
articles locally will use your CPU/GPU for a while. See "Tuning" below if
it's too slow.

## Tuning

All the knobs live in `config.py`:
- `TTS_VOICE` — swap narrator voice (list more with `edge-tts --list-voices`)
- `VIDEO_WIDTH` / `VIDEO_HEIGHT` — vertical (Shorts/Reels) vs landscape
- `MAX_STEPS_PER_ARTICLE` — cap video length
- `CAPTION_SIZE` / `CAPTION_HIGHLIGHT_COLOR` — caption look
- `OLLAMA_MODEL` — smaller model = faster but slightly lower quality
  writing. `llama3.2` is a good speed/quality tradeoff if `llama3.1` feels
  slow on your machine.

If article generation feels slow at 100/day: it's running locally on your
CPU/GPU, so speed depends on your hardware. A machine with a decent GPU
will be much faster than CPU-only. Since articles are cached by title
(`cache/article_*.json`), re-running the same topic twice costs nothing
the second time.

## Files

| File | Purpose |
|---|---|
| `config.py` | All settings and keys |
| `generate_articles.py` | Topic title → original article JSON via Ollama (cached) |
| `tts.py` | Text → voice audio + word timestamps |
| `image_sourcer.py` | Step keywords → matching stock photo (cached) |
| `video_builder.py` | Assembles one article into one mp4 |
| `run_batch.py` | **Daily entry point** — runs all 100 topics |
| `topics.txt` | Your daily input — one topic per line |
