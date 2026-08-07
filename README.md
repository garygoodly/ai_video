# Knowledge Video Factory

Desktop workflow for producing Taiwan, Japan, and Global finance-news videos.

## What changed in this build

### Precise topic visuals

The visual pipeline is topic-centric. One defensible visual can remain on screen
for several narration sentences. The source order is:

1. A current historical market chart when the topic maps to a supported index,
   FX pair, commodity, crypto asset, or major stock.
2. Hero images from the research source URLs (`og:image` / `twitter:image`).
3. Openverse.
4. Wikimedia Commons.
5. If a new topic has no precise asset, reuse the last verified visual. For the
   first topic, strict mode stops instead of inserting a fake-looking card.

Market charts use real observations and include title, update date, latest value,
X/Y labels, units, and source attribution. The provider tries Yahoo Finance and
then Stooq where a fallback mapping is known. It never fabricates chart points.

### Clean workspace layout

New sessions use:

```
workspace/<session>/
  research/
  script/
  storyboard/
  assets/
    source/
    rendered/        # exact 1920x1080 visuals used by FFmpeg
    media.json
  voice/
    narration.mp3
    cue_timing.json  # exact TTS cue boundaries
  subtitle/
  timeline/
  video/
  _preview/
```

The old ambiguous `images/` and `media/` split is no longer created for new sessions.

### Voice engines and preview

The Modify / Regenerate page now has a voice-engine selector and a **Play Voice
Preview** button. The preview uses the selected speaker, speed, and pitch and is
played with `ffplay`.

- **Microsoft Edge TTS** is installed by the normal requirements file.
- **Kokoro** is an optional local/open-weight engine. Install it with:

```
pip install -r requirements-optional-voices.txt
```

If Kokoro is not installed, selecting it gives a clear installation message.

### Subtitle synchronization after speed changes

Narration is synthesized using the exact same cue segmentation used for subtitles.
Each audio cue is measured after synthesis and its exact start/end time is written
to `voice/cue_timing.json`. Subtitles are then generated from those recorded
boundaries.

Therefore changing voice speed causes the dependency chain:

```
voice -> cue timing -> subtitles -> timeline -> video
```

No ASR transcription is used for subtitle text. Approved script characters and
Arabic numerals stay unchanged.

## Installation

Python 3.11+ is recommended.

```
pip install -r requirements.txt
```

Install FFmpeg and ensure both commands are available:

```
ffmpeg -version
ffplay -version
```

Optional local Kokoro voices:

```
pip install -r requirements-optional-voices.txt
```

## Start

Windows:

```
run_gui.bat
```

or:

```
python main.py
```

## Editing an existing video

Open the completed project and choose **Modify / Regenerate**. You can change
voice engine, speaker, speed, pitch, subtitle style, segmentation, or media.
Only dependent stages are invalidated and rebuilt; you do not need to manually
delete workspace files.
