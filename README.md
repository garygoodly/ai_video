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
