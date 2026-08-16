Content / visual / subtitle patch

Replace these files in the project:
- gui.py
- src/kvf/services/exact_subtitle_service.py
- src/kvf/services/forced_alignment_service.py   (new)
- src/kvf/steps/generate_subtitle_step.py
- src/kvf/steps/download_media_step.py
- src/kvf/steps/generate_timeline_step.py

What changes
1. Continuous narration + exact subtitles
   - TTS speaks the approved article continuously.
   - Subtitle text comes only from the approved script.
   - Whisper, when installed, is used only for timing anchors; its recognized text is never displayed.
   - If Whisper is unavailable, the system falls back to timing over the actual narration duration.

2. Better visual relevance
   - Fixes the old bug where visual_persistence=topic actually keyed by the whole section.
   - Recognizes S&P 500, Nasdaq, Dow, SOX, TAIEX, TSMC, Nikkei, TOPIX, USD/JPY, USD/TWD, DXY, US 10Y, oil, gold and Bitcoin as separate topics.
   - A visual persists only while that actual topic remains active.
   - Existing MarketChartProvider remains first priority for recognized instruments.

3. Section cards
   - Generates 1920x1080 section cards in assets/rendered/section_XX.jpg.
   - Timeline shows each card for up to ~3 seconds at the beginning of a new section.
   - The card uses the first seconds of existing narration; it does NOT add silence or extend the final video.

Recommended regeneration after installing
- Media images
- Subtitles
- Timeline
- Final video

If using Continuous narration and the narration audio itself has not changed, Voice does not need regeneration.
