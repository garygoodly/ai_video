from __future__ import annotations

import io
import math
import re
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from kvf.models.media import MediaAsset, MediaProvider as MediaProviderType
from kvf.models.storyboard import StoryboardScene
from kvf.providers.media_provider import MediaProvider


class WikimediaProvider(MediaProvider):
    """Download and normalize scene images from Wikimedia Commons.

    Candidate selection favors large landscape images close to 16:9. Every
    accepted download is decoded with Pillow, converted to RGB, center-cropped,
    and saved as an exact 1920x1080 JPEG. Invalid files, HTML responses, PDFs,
    scans, logos, and document covers are rejected before they reach FFmpeg.
    """

    API = "https://commons.wikimedia.org/w/api.php"
    USER_AGENT = "AI-Video-Generator/1.3"
    TARGET_WIDTH = 1920
    TARGET_HEIGHT = 1080
    TARGET_RATIO = TARGET_WIDTH / TARGET_HEIGHT
    SEARCH_LIMIT = 30
    MIN_SOURCE_WIDTH = 960
    MIN_SOURCE_HEIGHT = 540

    REJECT_TITLE_TERMS = {
        "book cover",
        "cover page",
        "document",
        "investigation report",
        "logo",
        "seal",
        "signature",
        "symbol",
        "title page",
    }

    def download(self, scene: StoryboardScene, output_file: Path) -> MediaAsset:
        last_exception: Exception | None = None

        for query in self._build_queries(scene.visual.query):
            try:
                return self._download_best_match(query, scene, output_file)
            except Exception as exc:
                last_exception = exc
                print(f"No usable Wikimedia image for '{query}'; trying fallback.")

        reason = str(last_exception) if last_exception else "no usable result"
        print(
            f"Warning: using a generated placeholder for scene {scene.id}: "
            f"{scene.visual.query} ({reason})"
        )
        return self._create_placeholder(scene, output_file)

    def normalize_existing(self, image_file: Path) -> bool:
        """Validate and normalize an existing cached image in place."""
        try:
            with Image.open(image_file) as image:
                image.load()
                normalized = self._fit_to_full_hd(image)
            self._save_jpeg(normalized, image_file)
            return True
        except (OSError, ValueError, UnidentifiedImageError):
            return False

    def _build_queries(self, original: str) -> list[str]:
        normalized = self._normalize_query(original)

        removable_terms = {
            "aerial", "animation", "background", "chart", "cinematic",
            "closeup", "concept", "diagram", "footage", "graphic",
            "illustration", "infographic", "montage", "news", "route",
            "shipping", "showing", "stock", "video", "visual",
        }
        keywords = [
            token for token in normalized.split()
            if token not in removable_terms and len(token) > 2
        ]

        candidates = [
            original.strip(),
            f"{normalized} landscape",
            f"{normalized} map" if "map" in original.lower() else normalized,
            " ".join(keywords),
            " ".join(keywords[:5]),
            " ".join(keywords[:3]),
            " ".join(normalized.split()[:4]),
            " ".join(normalized.split()[:2]),
        ]

        lower = normalized.lower()
        if "strait of hormuz" in lower:
            candidates.extend([
                "Strait of Hormuz map",
                "Strait of Hormuz satellite image",
                "Strait of Hormuz landscape",
                "Persian Gulf map",
            ])
        if "persian gulf" in lower:
            candidates.extend(["Persian Gulf map", "Persian Gulf satellite"])

        unique: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            candidate = re.sub(r"\s+", " ", candidate).strip()
            key = candidate.casefold()
            if candidate and key not in seen:
                unique.append(candidate)
                seen.add(key)
        return unique

    def _search_images(self, query: str) -> list[dict]:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": self.SEARCH_LIMIT,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": self.TARGET_WIDTH,
            "format": "json",
            "formatversion": 2,
        }
        response = requests.get(
            self.API,
            params=params,
            timeout=30,
            headers={"User-Agent": self.USER_AGENT},
        )
        response.raise_for_status()

        pages = response.json().get("query", {}).get("pages", [])
        results: list[dict] = []
        for page in pages:
            imageinfo = page.get("imageinfo") or []
            if not imageinfo:
                continue
            info = dict(imageinfo[0])
            info["title"] = page.get("title", "")
            results.append(info)
        return results

    def _rank_images(self, images: list[dict]) -> list[dict]:
        ranked: list[tuple[float, dict]] = []

        for info in images:
            mime = str(info.get("mime", "")).lower()
            download_url = info.get("thumburl") or info.get("url", "")
            title = str(info.get("title", "")).lower()
            width = int(info.get("thumbwidth") or info.get("width") or 0)
            height = int(info.get("thumbheight") or info.get("height") or 0)

            if not mime.startswith("image/") or not download_url:
                continue
            if mime in {"image/svg+xml", "image/vnd.djvu"}:
                continue
            if any(term in title for term in self.REJECT_TITLE_TERMS):
                continue
            if width <= 0 or height <= 0:
                continue

            ratio = width / height
            ratio_error = abs(math.log(max(ratio, 0.01) / self.TARGET_RATIO))
            resolution_score = min(width / self.TARGET_WIDTH, 1.5) + min(
                height / self.TARGET_HEIGHT, 1.5
            )
            landscape_bonus = 1.5 if width >= height else -2.5
            full_hd_bonus = 2.0 if (
                width >= self.TARGET_WIDTH and height >= self.TARGET_HEIGHT
            ) else 0.0
            minimum_penalty = 3.0 if (
                width < self.MIN_SOURCE_WIDTH or height < self.MIN_SOURCE_HEIGHT
            ) else 0.0

            score = (
                resolution_score
                + landscape_bonus
                + full_hd_bonus
                - (ratio_error * 5.0)
                - minimum_penalty
            )
            candidate = dict(info)
            candidate["download_url"] = download_url
            candidate["candidate_width"] = width
            candidate["candidate_height"] = height
            ranked.append((score, candidate))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [candidate for _, candidate in ranked]

    def _download_best_match(
        self,
        query: str,
        scene: StoryboardScene,
        output_file: Path,
    ) -> MediaAsset:
        ranked = self._rank_images(self._search_images(query))
        if not ranked:
            raise RuntimeError(f"No usable image for '{query}'")

        errors: list[str] = []
        for candidate in ranked[:10]:
            try:
                source_width, source_height = self._download_and_normalize(
                    candidate["download_url"], output_file
                )
                metadata = candidate.get("extmetadata", {})
                print(
                    f"Scene {scene.id}: selected {source_width}x{source_height} "
                    f"source for '{query}', saved as 1920x1080."
                )
                return MediaAsset(
                    scene=scene.id,
                    provider=MediaProviderType.WIKIMEDIA,
                    query=query,
                    file=output_file.name,
                    width=self.TARGET_WIDTH,
                    height=self.TARGET_HEIGHT,
                    license=self._metadata_value(metadata, "LicenseShortName"),
                    author=self._metadata_value(metadata, "Artist"),
                    source_url=(
                        candidate.get("descriptionurl")
                        or candidate.get("url", "")
                    ),
                )
            except Exception as exc:
                errors.append(str(exc))

        raise RuntimeError(
            f"All candidate downloads failed for '{query}': "
            + "; ".join(errors[-3:])
        )

    def _download_and_normalize(
        self,
        url: str,
        output_file: Path,
    ) -> tuple[int, int]:
        response = requests.get(
            url,
            timeout=60,
            headers={"User-Agent": self.USER_AGENT},
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()
        if content_type and not content_type.startswith("image/"):
            raise ValueError(f"Non-image response: {content_type}")
        if len(response.content) < 1024:
            raise ValueError("Downloaded image is unexpectedly small")

        try:
            with Image.open(io.BytesIO(response.content)) as image:
                image.load()
                source_size = image.size
                normalized = self._fit_to_full_hd(image)
        except (OSError, UnidentifiedImageError) as exc:
            raise ValueError("Downloaded bytes are not a valid image") from exc

        output_file.parent.mkdir(parents=True, exist_ok=True)
        self._save_jpeg(normalized, output_file)
        return source_size

    def _fit_to_full_hd(self, image: Image.Image) -> Image.Image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        return ImageOps.fit(
            image,
            (self.TARGET_WIDTH, self.TARGET_HEIGHT),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

    @staticmethod
    def _save_jpeg(image: Image.Image, output_file: Path) -> None:
        temporary = output_file.with_suffix(".tmp.jpg")
        image.save(
            temporary,
            format="JPEG",
            quality=92,
            optimize=True,
            progressive=True,
            subsampling="4:2:0",
        )
        temporary.replace(output_file)

    @staticmethod
    def _metadata_value(metadata: dict, key: str) -> str | None:
        value = metadata.get(key, {}).get("value")
        if not value:
            return None
        return re.sub(r"<[^>]+>", "", str(value)).strip() or None

    def _create_placeholder(
        self,
        scene: StoryboardScene,
        output_file: Path,
    ) -> MediaAsset:
        width, height = self.TARGET_WIDTH, self.TARGET_HEIGHT
        image = Image.new("RGB", (width, height), (28, 32, 40))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=42)
        small_font = ImageFont.load_default(size=26)

        title = "Media unavailable"
        query = scene.visual.query.strip()
        wrapped = self._wrap_text(query, 46)

        title_box = draw.multiline_textbbox((0, 0), title, font=font)
        title_width = title_box[2] - title_box[0]
        draw.text(((width - title_width) / 2, 420), title, font=font, fill="white")

        query_box = draw.multiline_textbbox(
            (0, 0), wrapped, font=small_font, spacing=10, align="center"
        )
        query_width = query_box[2] - query_box[0]
        draw.multiline_text(
            ((width - query_width) / 2, 510),
            wrapped,
            font=small_font,
            fill=(205, 210, 220),
            spacing=10,
            align="center",
        )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        self._save_jpeg(image, output_file)

        return MediaAsset(
            scene=scene.id,
            provider=MediaProviderType.AI,
            query=query,
            file=output_file.name,
            width=width,
            height=height,
            license=None,
            author="Local placeholder",
            source_url="local://generated-placeholder",
        )

    @staticmethod
    def _wrap_text(text: str, width: int) -> str:
        words = text.split()
        lines: list[str] = []
        current: list[str] = []
        for word in words:
            candidate = " ".join([*current, word])
            if current and len(candidate) > width:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        return "\n".join(lines)

    @staticmethod
    def _normalize_query(query: str) -> str:
        stop_words = [
            "with", "and", "montage", "showing", "beautiful", "historic",
            "view", "scene",
        ]
        normalized = query.lower()
        for word in stop_words:
            normalized = re.sub(rf"\b{re.escape(word)}\b", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()
