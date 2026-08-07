# Finance Video Factory

A resumable desktop workflow for creating daily finance-news YouTube videos with ChatGPT, without requiring an OpenAI API key.

## Redesigned workflow

### Start a new session

1. Launch the application.
2. Select **Start New Session**.
3. Enter a project name. The default is `<current date> Finance Daily`.
4. The project name is used only for the workspace folder and resume list.
5. No video topic or category is required. The Research prompt asks ChatGPT to identify the most important finance events from today and yesterday.

### Manual ChatGPT checkpoints

The application has three manual checkpoints:

1. Research
2. Script
3. Storyboard

At each checkpoint:

1. Click **Copy Prompt** on the left.
2. Paste the prompt into ChatGPT.
3. Copy ChatGPT's JSON response.
4. Paste it into the JSON editor on the right.
5. The application automatically checks the JSON after you stop typing.
6. Valid JSON is automatically saved and **Next** becomes available.

The editor accepts either plain JSON or a fenced `json` code block.

### Automatic production

After Storyboard is valid, the application continues through:

- Media download
- Voice generation
- Subtitle generation
- Timeline creation
- Video rendering

FFmpeg must be installed and available on PATH.

### Resume a session

Select **Resume Last Session** to see all saved projects. The application scans the workspace files and continues from the first incomplete stage. A session can be resumed after Research, Script, Storyboard, or any partially completed automatic stage.

## Installation

```bash
pip install -r requirements.txt
```

## Start

Windows:

```text
Double-click run_gui.bat
```

Command line:

```bash
python main.py
```

Linux or macOS:

```bash
chmod +x run_gui.sh
./run_gui.sh
```

## Workspace layout

Each session is stored below `workspace/`:

```text
workspace/<project-name>/
├── metadata.json
├── research/
├── script/
├── storyboard/
├── media/
├── voice/
├── subtitle/
├── timeline/
└── video/
```

The final video is saved as `video/video.mp4` inside the session workspace.

## Media-search fallback behavior

Wikimedia searches now try progressively broader terms. If no usable image is
available or Wikimedia is temporarily unreachable, the application creates a
local placeholder image and continues production instead of stopping the
session. Existing media metadata is retained when resuming an interrupted run.

## Video rendering behavior

The renderer now:

- renders every storyboard scene image in timeline order;
- allocates scene durations across the full narration audio;
- burns `subtitle/subtitle.srt` into the final video;
- outputs H.264/AAC MP4 at exactly 1920x1080 and 30 fps;
- regenerates timeline and video files when a session resumes, repairing files
  made by older versions.

FFmpeg and FFprobe must both be available on `PATH`.

## Media quality and Full HD normalization

The media stage now prioritizes Wikimedia candidates that are landscape,
close to a 16:9 aspect ratio, and near or above 1920x1080. It rejects common
non-video assets such as document covers, title pages, logos, seals, SVG/DjVu
files, HTML responses, and corrupted images.

Every downloaded or cached scene image is decoded with Pillow and normalized
to an exact 1920x1080 progressive JPEG before FFmpeg receives it. Existing
sessions can therefore be resumed safely: valid cached images are normalized,
while invalid cached images are deleted and downloaded again.

Source images smaller than Full HD may still be used when no better licensed
candidate exists, but they are ranked below larger 16:9 images. A generated
1920x1080 placeholder is used only after all search fallbacks fail.

## Resilient multi-source media retrieval

The media stage now uses Openverse and Wikimedia Commons instead of relying on
Wikimedia alone. It limits each scene to four meaningful searches, caches
repeated searches, spaces requests per host, honors HTTP `Retry-After`, and
uses exponential backoff for HTTP 429 and server errors.

When a saved session contains an old `Media unavailable` placeholder, resume
will automatically discard it and search again. If both online catalogs truly
have no usable result, the application creates a styled contextual finance
visual rather than an error screen. All downloaded and generated assets are
validated and normalized to exact 1920x1080 JPEG files.

## Sentence-level subtitles

Whisper now requests word timestamps and groups recognized words into complete
sentences. Each SRT cue contains exactly one sentence, and every cue is
normalized to end with a period. The next sentence replaces the previous one;
multiple sentences are never combined into the same subtitle cue.

## Fresher, non-repeating media

The media stage now checks the URLs listed in `research/research.json` before
searching Openverse or Wikimedia. It extracts each current article's Open Graph
hero image and ranks it against the scene query. Publisher image terms and
copyright still apply, so review media attribution before publication.

Across the full video, a 16x16 perceptual image hash is maintained. Images that
are visually near-identical to an earlier scene, or that reuse the same source
URL, are rejected and the next candidate is tried. Existing cached sessions are
also checked for duplicates when media is rebuilt.

## Modify and regenerate without deleting files

Completed sessions include a **Modify / Regenerate** screen. It supports:

- changing among several male and female Microsoft Edge voices;
- regenerating media, voice, subtitles, timeline, or only the final video;
- opening `subtitle.srt`, `script.json`, or the media folder for manual edits;
- automatic downstream dependency rebuilding.

Examples:

- Change speaker: choose a voice, select **Narration voice**, and regenerate.
  Voice, subtitles, timeline, and video are rebuilt.
- Edit subtitle text manually: open `subtitle.srt`, save the edit, select
  **Final video only**, and regenerate.
- Replace one image manually: overwrite its numbered JPG in the media folder,
  select **Final video only**, and regenerate.
- Refresh all visuals: select **Media images**. Media, timeline, and video are
  rebuilt while research, script, storyboard, and voice are preserved.

## Subtitle readability controls

The Modify / Regenerate screen now includes subtitle controls:

- Compact, Standard, or Large subtitle text;
- selectable Windows-safe fonts;
- configurable maximum words per subtitle cue.

Long spoken sentences are split into short timed cues. Every displayed cue ends
with a period, and only one cue is shown at a time. Subtitles are burned into
the bottom-center title-safe area of the 1920x1080 frame.

Changing the word limit automatically regenerates subtitles and the final video.
Changing only the text style automatically regenerates the final video.

## Honest chart policy

The storyboard prompt now requests a chart only when the script contains actual
numeric values, a period, units, and a named source. A real chart request must
also specify its title, x-axis, y-axis, units, period, and source in
`visual.notes`.

When no suitable online image is found, the local fallback is now a neutral
illustrative background. It does not draw fabricated data, axes, values, or a
`FINANCE DAILY | SCENE` label, and it is explicitly marked as not being a data
chart. Existing local fallbacks are retried whenever media is regenerated.

## Regional editions and languages

A new session now starts by selecting one of three editorial editions:

- **Taiwan** — Traditional Chinese narration and subtitles, Taiwan-focused market priorities, and Taiwan Mandarin Edge TTS voices. The research prompt leads with TAIEX, Taiwan-listed companies, semiconductors, the New Taiwan dollar, exports, rates, and policy, while still including material international events such as yen moves, U.S. rates, China demand, oil, shipping, and global AI/semiconductor demand.
- **Japan** — Japanese narration and subtitles, with priorities covering Nikkei 225, TOPIX, the yen, Bank of Japan, JGB yields, wages, inflation, exporters, autos, technology, and material global transmission channels.
- **Global** — English narration and subtitles for an international audience, with globally balanced cross-asset and cross-border story selection.

The edition is saved in `metadata.json`. It controls:

- research audience and event-ranking priorities;
- research and script output language;
- default Microsoft Edge TTS voice and selectable voice list;
- Whisper transcription language;
- subtitle punctuation, spacing, line length, and regional font;
- storyboard instructions, while keeping media search queries primarily in English for better international catalog retrieval.

The edition is shown in the Resume Session table and on completed projects. Existing projects created before this feature remain compatible and are treated as Global editions unless their metadata says otherwise.


## Exact-script regional subtitles

Subtitle text is now generated from the approved `script/script.json`, not from
speech recognition. This makes the displayed wording deterministic: names,
Traditional Chinese characters, and Arabic numbers such as `43682` and `0.16`
remain exactly as written in the script. Regenerating subtitles no longer
requires Whisper.

For Taiwan, `，` and `。` define subtitle boundaries but are not displayed.
Very short fragments are merged with a neighbor, long clauses are split to the
selected character target, and numeric/Latin tokens are never split in the
middle.

## Voice and live subtitle preview

The Modify screen supports edition-specific speakers, narration speed, pitch,
font, and Compact/Standard/Large subtitle presets. A live 16:9 preview shows
the selected typeface and size at the same bottom-safe placement used by the
video renderer.

## Topic-level visuals and market charts

The default media behavior is now **one precise visual per topic/section**. The
same image remains on screen while the narration stays on that topic and only
changes when the storyboard section changes. Users may switch back to one
visual per scene in the Modify screen.

Recognized market subjects—including the S&P 500, Dow Jones, Nasdaq, TAIEX,
Nikkei 225, TOPIX, USD/TWD, USD/JPY, gold, oil, and Bitcoin—prefer a current
six-month historical chart. Charts use downloaded market history and visibly
include the title, update date, x-axis, y-axis units, and source. If current
data cannot be retrieved, the normal news/open-media pipeline is used instead;
the project does not fabricate chart values.
