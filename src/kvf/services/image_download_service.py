from pathlib import Path

import requests


class ImageDownloadService:

    def download(
        self,
        url: str,
        output: Path,
    ) -> None:

        response = requests.get(
            url,
            timeout=60,
        )

        response.raise_for_status()

        output.write_bytes(
            response.content
        )