# Automated Italian Vocabulary Video Pipeline

This repository focuses on **long-form educational vocabulary videos**, not fake phone/UI tutorials.

Give the pipeline exactly 20 Italian words. It automatically translates and explains them in English, creates a dedicated AI illustration for every word, lays out a polished 16:9 lesson card, narrates each lesson, adds subtle motion, creates a copyright-safe procedural background track, and renders a YouTube-ready MP4.

Each word gets about 17 seconds by default, giving about 5:40 of vocabulary lessons for 20 words plus intro/outro. Set `WORD_TARGET_SECONDS=20` for about 6:40. Use about 11–12 seconds per word for a strict four-minute version.

Every segment contains the Italian word, English translation on the right, part of speech, natural English explanation, example sentence, a dedicated generated illustration, English narration, subtle motion, and quiet background music. Concrete nouns receive an illustration of the thing; abstract nouns receive a visual metaphor; adjectives receive a scene demonstrating the quality.

The old generic iPhone UI renderer is no longer the visual concept for this workflow. The new structure is **word → meaning → dedicated AI illustration → English explanation → narration → motion → music**, making it reusable for hundreds of vocabulary videos.

## Run

Put exactly 20 Italian words in `italian_words.txt`, one per line:

```powershell
python run_demo.py
```

Or:

```powershell
python run_demo.py --words my_words.txt --title "20 Italian Words for Beginners"
```

## AI images

Set `OPENAI_API_KEY` to use the configured OpenAI image generator, or configure `IMAGE_GENERATOR_URL` for a local/custom image service. Each word's image is cached.

```powershell
$env:OPENAI_API_KEY="your-key"
python run_demo.py
```

`IMAGE_MODEL`, `IMAGE_SIZE`, and `IMAGE_QUALITY` are configurable.

## Music

Background music is generated locally from synthesized tones/chords rather than downloading a commercial song. Choose `meditative`, `funny`, or `adventure` with `MUSIC_MOOD`. Narration remains dominant.

## Main configuration

- `VOCAB_WORD_COUNT` — 20
- `WORD_TARGET_SECONDS` — 17
- `TTS_VOICE` — `en-US-GuyNeural`
- `TTS_CONCURRENCY` — 4
- `OLLAMA_MODEL` — `llama3.1`
- `OLLAMA_KEEP_ALIVE` — `30m`
- `IMAGE_PROVIDER` — `auto`, `openai`, or `custom`
- `IMAGE_MODEL` — `gpt-image-2`
- `IMAGE_SIZE` — `1536x1024`
- `IMAGE_QUALITY` — `medium`
- `MUSIC_MOOD` — `meditative`, `funny`, or `adventure`
- `MUSIC_VOLUME` — `0.12`
- `VIDEO_WIDTH` / `VIDEO_HEIGHT` — `1920×1080`
- `FPS` — `30`
- `VIDEO_BITRATE` — `8M`

## Batch production

`run_batch.py` accepts jobs in `topics.txt` using:

```text
italian_words.txt | 20 Italian Words You Should Know
another_words.txt | Italian Vocabulary for Travel
```

Each referenced word file must contain exactly 20 words, so the same design can be reused for dozens or hundreds of videos without manual editing.

## Tests

```powershell
python -m pytest -q tests
```

Offline tests do not call Ollama or the image API. A production render requires Ollama and an image-generation provider.
