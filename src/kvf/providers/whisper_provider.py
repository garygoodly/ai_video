from pathlib import Path

import whisper

from kvf.providers.subtitle_provider import SubtitleProvider


class WhisperProvider(SubtitleProvider):

    def __init__(
        self,
        model: str = "tiny",
    ):
        self.model = whisper.load_model(
            model
        )

    def generate(
        self,
        audio: Path,
        output_dir: Path,
    ):

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        result = self.model.transcribe(
            str(audio)
        )

        srt_path = (
            output_dir
            / "subtitle.srt"
        )

        with open(
            srt_path,
            "w",
            encoding="utf-8",
        ) as f:

            for i, segment in enumerate(
                result["segments"],
                start=1,
            ):

                f.write(f"{i}\n")
                f.write(
                    f"{self._format(segment['start'])} --> {self._format(segment['end'])}\n"
                )
                f.write(
                    segment["text"].strip()
                )
                f.write("\n\n")

    def _format(
        self,
        seconds: float,
    ) -> str:

        h = int(seconds // 3600)

        m = int(
            (seconds % 3600) // 60
        )

        s = int(seconds % 60)

        ms = int(
            (seconds - int(seconds))
            * 1000
        )

        return (
            f"{h:02}:{m:02}:{s:02},{ms:03}"
        )