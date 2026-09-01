# Automated Italian Vocabulary Video Pipeline

This repository now focuses on **long-form educational vocabulary videos**, not fake phone/UI tutorials.

Give the pipeline exactly 20 Italian words. It automatically:

1. asks Ollama to translate every word and write a natural English explanation;
2. creates a roughly 17–20 second English lesson for each word;
3. generates a dedicated AI illustration for every word;
4. builds a polished 16:9 split-screen composition with the Italian word, English translation, part of speech, explanation, and example on the right;
5. adds subtle motion and professional transitions;
6. generates copyright-safe procedural background music;
7. synthesizes English narration with Edge TTS;
8. assembles everything into a roughly 5–7 minute YouTube-ready MP4.

With 20 words × 17 seconds, the vocabulary lessons alone are about 5:40, plus intro/outro. Set `WORD_TARGET_SECONDS=20` for about 6:40 of lessons.

## Run

Put exactly 20 words in `italian_words.txt`, one per line, then:

```powershell
python run_demo.py
```

Or use another word file:

```powershell
python run_demo.py --words my_words.txt --title "20 Italian Words for Beginners"
```

## AI image generation

Vocabulary mode intentionally **does not create fake phone screens or generic button templates**. Each word gets its own illustration prompt based on its meaning.

By default, if `OPENAI_API_KEY` is available, the pipeline uses the OpenAI Images API. The image model is configurable with `IMAGE_MODEL` and currently defaults to `gpt-image-2`.

On Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your-key"
python run_demo.py
```

A custom/local image service can be used instead with `IMAGE_GENERATOR_URL` and `IMAGE_PROVIDER=custom`.

## Music

The background track is generated locally from synthesized chords and tones, so the pipeline does not need to download a copyrighted song. Choose a mood:

```powershell
$env:MUSIC_MOOD="meditative"
# or: funny / adventure
```

The default volume is intentionally low so narration remains clear.

## Main configuration

- `VOCAB_WORD_COUNT` — default `20`
- `WORD_TARGET_SECONDS` — default `17`; use `20` for ~20 seconds per word
- `TTS_VOICE` — default `en-US-GuyNeural`
- `TTS_RATE` — default `+0%`
- `TTS_CONCURRENCY` — default `4`
- `OLLAMA_URL` — default `http://localhost:11434/api/generate`
- `OLLAMA_MODEL` — default `llama3.1`
- `OLLAMA_KEEP_ALIVE` — default `30m`
- `IMAGE_PROVIDER` — `auto`, `openai`, or `custom`
- `IMAGE_MODEL` — default `gpt-image-2`
- `IMAGE_SIZE` — default `1536x1024`
- `IMAGE_QUALITY` — default `medium`
- `MUSIC_MOOD` — `meditative`, `funny`, or `adventure`
- `MUSIC_VOLUME` — default `0.12`
- `VIDEO_WIDTH` / `VIDEO_HEIGHT` — default `1920×1080`
- `FPS` — default `30`
- `VIDEO_BITRATE` — default `8M`

## Design philosophy

The old tutorial renderer used abstract phone-shaped UI elements. That is unsuitable for a reusable vocabulary channel because the visuals have to match arbitrary concepts rather than pretend to reproduce real device screens.

The new visual system is concept-first: **word → meaning → dedicated AI illustration → English explanation → narration → motion → music**. A concrete noun gets a visual of the object; an abstract noun gets a visual metaphor; an adjective gets a scene that demonstrates the quality. This makes the same pipeline reusable across hundreds of vocabulary videos.

## Tests

```powershell
python -m pytest -q tests
```

The offline test suite does not call Ollama or the image API. A full production run requires the configured AI image provider and Ollama.
