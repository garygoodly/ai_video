Storyboard validation patch

Replace:
- gui.py
- src/kvf/models/storyboard.py

Changes:
1. Short non-empty storyboard narration is valid (min_length=1 instead of 10).
2. GUI shows useful Pydantic validation details instead of only the first line/error count.
3. Existing non-blocking duration behavior is preserved.
