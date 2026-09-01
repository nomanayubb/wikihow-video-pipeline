# Italian Vocabulary Video Pipeline

A production-oriented, code-driven system for turning an Italian word list into a polished English-language YouTube vocabulary video.

## What the program does

You provide a plain text file with **20 Italian words**, one per line. The pipeline then:

1. validates the input and rejects duplicates;
2. asks Ollama for an English lesson for every word;
3. creates a semantic image prompt tailored to the word type;
4. generates one dedicated AI illustration per word;
5. creates English narration;
6. builds a professional 16:9 split-screen lesson card with Italian on the left visual and English explanation on the right;
7. applies subtle motion so the video is not a dead slideshow;
8. adds a quiet procedural background soundtrack;
9. assembles and encodes the final MP4 with atomic output replacement.

There is **no fake iPhone screen generator in the production path**.

## Input

`italian_words.txt` contains exactly 20 words:

```text
casa
sole
mare
amicizia
...
```

Comments beginning with `#` and blank lines are ignored.

A five-word `demo_words.txt` is included so the design can be tested without replacing the production list.

## Timing

The default target is **18 seconds per word**. Twenty words therefore provide about 6 minutes of vocabulary content before a short intro and outro. Set `WORD_TARGET_SECONDS=20` for about 6:40 of word segments.

The program never assumes that the generated narration has exactly the target length. Each visual segment lasts at least the configured target, and longer narration is allowed to continue naturally.

## Run the demo

Install dependencies, start Ollama, configure an image provider, then run:

```powershell
python run_demo.py
```

The demo reads `demo_words.txt` and writes `output/demo_vocabulary.mp4`.

For production:

```powershell
python run_demo.py --words italian_words.txt --title "20 Italian Words You Should Know" --mood meditative
```

## AI images

The current image adapter supports the OpenAI Images API and a generic custom JSON/image endpoint. Set one of:

```powershell
$env:OPENAI_API_KEY="your-key"
```

or:

```powershell
$env:IMAGE_GENERATOR_URL="http://localhost:8188/generate"
```

`IMAGE_PROVIDER=auto` tries OpenAI first when a key is present, then the custom endpoint. Images are cached by prompt hash, so reruns do not regenerate successful images.

The OpenAI image integration currently defaults to `gpt-image-2`, the image-generation model listed in the current OpenAI model catalog. citeturn646426search0

## Music

Music is synthesized locally from code, so the pipeline does not download commercial tracks. Select one of `meditative`, `funny`, or `adventure` with `--mood` or `MUSIC_MOOD`.

## Batch production

`topics.txt` contains one job per line:

```text
demo_words.txt | Italian Vocabulary Demo
italian_words.txt | 20 Italian Words You Should Know
sets/travel.txt | Italian Travel Vocabulary
```

Each job is independent. A failed video does not stop later jobs, and completed non-empty MP4 files are skipped on a rerun.

## Main environment settings

- `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_KEEP_ALIVE`
- `OLLAMA_CONNECT_TIMEOUT`, `OLLAMA_READ_TIMEOUT`
- `OLLAMA_VOCAB_CONTEXT`, `OLLAMA_VOCAB_PREDICT`
- `VOCAB_WORD_COUNT` — default 20
- `WORD_TARGET_SECONDS` — default 18
- `TTS_VOICE`, `TTS_RATE`, `TTS_CONCURRENCY`
- `IMAGE_PROVIDER`, `IMAGE_MODEL`, `IMAGE_SIZE`, `IMAGE_QUALITY`
- `IMAGE_CONCURRENCY`, `IMAGE_RETRIES`
- `MUSIC_MOOD`, `MUSIC_BPM`, `MUSIC_VOLUME`
- `VIDEO_WIDTH`, `VIDEO_HEIGHT`, `FPS`, `VIDEO_BITRATE`

## Validation

Run:

```powershell
python -m compileall -q .
python -m pytest -q tests
```

The automated tests cover input validation, lesson schema validation, card rendering, and safe empty TTS batches. Production rendering still depends on your local Ollama and configured image-generation service being reachable; no software can honestly guarantee zero future failures from external services.
