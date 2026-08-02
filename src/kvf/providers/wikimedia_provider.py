from pathlib import Path
import requests

from kvf.models.media import (
    MediaAsset,
    MediaProvider as MediaProviderType,
)
from kvf.models.storyboard import StoryboardScene
from kvf.providers.media_provider import MediaProvider

import re

class WikimediaProvider(MediaProvider):

    API = "https://commons.wikimedia.org/w/api.php"

    def download(
            self,
            scene: StoryboardScene,
            output_file: Path,
    ) -> MediaAsset:

        # Get the normalized query
        normalized_query = self._normalize_query(scene.visual.query)

        # Create a broader fallback query using just the first 2 words
        # (e.g., "mount fuji shinkansen..." becomes "mount fuji")
        fallback_query = " ".join(normalized_query.split()[:2])

        queries = [
            scene.visual.query,
            normalized_query,
            fallback_query,  # Add the new fallback to the list
        ]

        last_exception = None

        for query in queries:
            try:
                # If the query is empty, skip it
                if not query:
                    continue

                return self._download_best_match(
                    query,
                    scene,
                    output_file,
                )
            except Exception as e:
                last_exception = e
                print(f"Retrying with next query... ({query})")

        raise RuntimeError(
            f"No Wikimedia result for '{scene.visual.query}'"
        ) from last_exception

    def _search_images(self, query: str) -> list:
        """Fetches a list of raw image metadata from the Wikimedia API."""
        headers = {
            'User-Agent': 'MyAIVideoBot/1.0 (e1350662@u.nus.edu)'
        }
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": 10,
            "prop": "imageinfo",
            "iiprop": "url|size",
            "format": "json",
        }

        response = requests.get(
            self.API,
            params=params,
            timeout=30,
            headers=headers
        )
        response.raise_for_status()

        pages = (
            response.json()
            .get("query", {})
            .get("pages", {})
        )

        # Extract just the imageinfo blocks into a list
        results = []
        for page in pages.values():
            if "imageinfo" in page:
                results.append(page["imageinfo"][0])

        return results

    def _select_best_image(self, images: list) -> dict:
        """Filters for valid formats and selects the highest resolution image."""
        valid_images = []
        for info in images:
            url = info.get("url", "").lower()

            # Keep only standard image formats
            if url.endswith(('.jpg', '.jpeg', '.png')):
                valid_images.append(info)

        if not valid_images:
            return {}

        # Calculate best resolution (width * height)
        best_image = max(valid_images, key=lambda x: x.get("width", 0) * x.get("height", 0))
        return best_image

    def _download_best_match(
            self,
            query: str,
            scene: StoryboardScene,
            output_file: Path,
    ) -> MediaAsset:
        """Orchestrates the search, selection, and saving of the media asset."""

        # 1. Search for a batch of images
        raw_images = self._search_images(query)
        if not raw_images:
            raise RuntimeError(f"No result for '{query}'")

        # 2. Filter and find the best one
        best_image = self._select_best_image(raw_images)
        if not best_image:
            raise RuntimeError(f"No valid JPG or PNG found for '{query}'")

        # 3. Download the actual image file
        headers = {
            'User-Agent': 'MyAIVideoBot/1.0 (e1350662@u.nus.edu)'
        }

        image = requests.get(
            best_image["url"],
            timeout=60,
            headers=headers
        )
        image.raise_for_status()

        output_file.write_bytes(image.content)

        return MediaAsset(
            scene=scene.id,
            provider=MediaProviderType.WIKIMEDIA,
            query=query,
            file=output_file.name,
            width=best_image.get("width", 0),
            height=best_image.get("height", 0),
            license=None,
            author=None,
            source_url=best_image["url"],
        )

    def _normalize_query(
            self,
            query: str,
    ) -> str:

        stop_words = [
            "with",
            "and",
            "montage",
            "showing",
            "beautiful",
            "historic",
            "view",
            "scene",
        ]

        query = query.lower()

        for word in stop_words:
            query = query.replace(word, " ")

        query = re.sub(r"\s+", " ", query)

        return query.strip()