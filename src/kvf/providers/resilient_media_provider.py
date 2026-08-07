from __future__ import annotations

import io
import math
import random
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from kvf.models.media import MediaAsset, MediaProvider as MediaProviderType
from kvf.models.storyboard import StoryboardScene
from kvf.providers.media_provider import MediaProvider


class ResilientMediaProvider(MediaProvider):
    """Find, validate, and normalize scene images from multiple open sources.

    The old pipeline could issue hundreds of Wikimedia requests. Once Commons
    returned HTTP 429, every remaining scene became a placeholder. This
    provider limits query fan-out, caches searches, spaces requests, honors
    Retry-After, and falls back to Openverse before creating a local visual.
    """

    WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
    OPENVERSE_API = "https://api.openverse.org/v1/images/"
    USER_AGENT = "FinanceVideoFactory/2.0 (desktop video generator)"

    TARGET_WIDTH = 1920
    TARGET_HEIGHT = 1080
    TARGET_RATIO = TARGET_WIDTH / TARGET_HEIGHT
    MIN_SOURCE_WIDTH = 800
    MIN_SOURCE_HEIGHT = 450
    SEARCH_LIMIT = 15
    MAX_QUERIES = 4
    MAX_DOWNLOAD_CANDIDATES = 8
    REQUEST_INTERVAL_SECONDS = 1.0
    MAX_RETRIES = 3
    RATE_LIMIT_COOLDOWN_SECONDS = 120.0

    REJECT_TITLE_TERMS = {
        "book cover", "cover page", "document", "investigation report",
        "seal", "signature", "title page", "scanned page", "pdf page",
        "letterhead", "certificate",
    }

    def __init__(self, news_source_urls: list[str] | None = None) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})
        self._last_request_at: dict[str, float] = {}
        self._search_cache: dict[tuple[str, str], list[dict]] = {}
        self._blocked_until: dict[str, float] = {}
        self.news_source_urls = list(dict.fromkeys(news_source_urls or []))
        self._news_candidates: list[dict] | None = None
        self._used_hashes: list[int] = []
        self._used_source_urls: set[str] = set()

    def download(self, scene: StoryboardScene, output_file: Path) -> MediaAsset:
        queries = self._build_queries(scene.visual.query)[: self.MAX_QUERIES]
        errors: list[str] = []

        # Current article hero images are preferred because they are usually
        # closest to the newest news event described by the research sources.
        try:
            result = self._download_best_match(
                source="news_article",
                query=scene.visual.query,
                scene=scene,
                output_file=output_file,
            )
            return result
        except Exception as exc:
            errors.append(f"news_article/{scene.visual.query}: {exc}")

        # Openverse is intentionally first: it aggregates multiple open media
        # catalogs and avoids concentrating all requests on Wikimedia Commons.
        for source in ("openverse", "wikimedia"):
            for query in queries:
                try:
                    result = self._download_best_match(
                        source=source,
                        query=query,
                        scene=scene,
                        output_file=output_file,
                    )
                    return result
                except Exception as exc:
                    errors.append(f"{source}/{query}: {exc}")
                    print(f"No usable {source.title()} image for '{query}'.")

        print(
            f"Warning: no online image found for scene {scene.id}; "
            "creating a contextual 1920x1080 visual instead of an "
            f"'unavailable' screen. Last error: {errors[-1] if errors else 'none'}"
        )
        return self._create_context_visual(scene, output_file)

    def normalize_existing(self, image_file: Path) -> bool:
        try:
            with Image.open(image_file) as image:
                image.load()
                normalized = self._fit_to_full_hd(image)
            self._save_jpeg(normalized, image_file)
            return True
        except (OSError, ValueError, UnidentifiedImageError):
            return False

    @staticmethod
    def is_generated_fallback(asset: MediaAsset) -> bool:
        return (
            asset.source_url in {"local://generated-placeholder", "local://context-visual"}
            or asset.author in {"Local placeholder", "Local contextual visual"}
        )

    def _download_best_match(
        self,
        source: str,
        query: str,
        scene: StoryboardScene,
        output_file: Path,
    ) -> MediaAsset:
        candidates = self._search(source, query)
        ranked = self._rank_images(candidates, query)
        if not ranked:
            raise RuntimeError("search returned no acceptable candidates")

        failures: list[str] = []
        for candidate in ranked[: self.MAX_DOWNLOAD_CANDIDATES]:
            candidate_urls = [candidate["download_url"]]
            thumbnail_url = candidate.get("thumbnail_url")
            if thumbnail_url and thumbnail_url not in candidate_urls:
                candidate_urls.append(thumbnail_url)

            source_width = source_height = 0
            selected_url = ""
            for candidate_url in candidate_urls:
                try:
                    source_width, source_height = self._download_and_normalize(
                        candidate_url, output_file
                    )
                    selected_url = candidate_url
                    break
                except Exception as exc:
                    failures.append(str(exc))
            if selected_url:
                print(
                    f"Scene {scene.id}: {source} selected "
                    f"{source_width}x{source_height} for '{query}', "
                    "saved as 1920x1080."
                )
                if self._is_duplicate(output_file, candidate.get("source_url") or selected_url):
                    output_file.unlink(missing_ok=True)
                    failures.append("candidate duplicates an image already used in this video")
                    continue
                provider = {
                    "news_article": MediaProviderType.NEWS_ARTICLE,
                    "openverse": MediaProviderType.OPENVERSE,
                    "wikimedia": MediaProviderType.WIKIMEDIA,
                }[source]
                return MediaAsset(
                    scene=scene.id,
                    provider=provider,
                    query=query,
                    file=output_file.name,
                    width=self.TARGET_WIDTH,
                    height=self.TARGET_HEIGHT,
                    license=candidate.get("license"),
                    author=candidate.get("author"),
                    source_url=candidate.get("source_url") or selected_url,
                )
        raise RuntimeError("candidate downloads failed: " + "; ".join(failures[-3:]))

    def _search(self, source: str, query: str) -> list[dict]:
        key = (source, query.casefold())
        if key in self._search_cache:
            return self._search_cache[key]

        if source == "news_article":
            results = self._search_news_articles(query)
        elif source == "openverse":
            results = self._search_openverse(query)
        elif source == "wikimedia":
            results = self._search_wikimedia(query)
        else:
            raise ValueError(f"Unsupported media source: {source}")

        self._search_cache[key] = results
        return results

    def _search_news_articles(self, query: str) -> list[dict]:
        if self._news_candidates is None:
            self._news_candidates = []
            for source_url in self.news_source_urls[:30]:
                try:
                    response = self._request(source_url)
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "html" not in content_type:
                        continue
                    html = response.text[:1_500_000]
                    title = self._html_meta(html, "og:title") or self._html_title(html)
                    image_url = (
                        self._html_meta(html, "og:image")
                        or self._html_meta(html, "twitter:image")
                    )
                    if not image_url:
                        continue
                    image_url = urljoin(source_url, image_url)
                    self._news_candidates.append({
                        "title": title,
                        "mime": "image/jpeg",
                        "width": 0,
                        "height": 0,
                        "download_url": image_url,
                        "thumbnail_url": None,
                        "license": "Publisher/source terms apply",
                        "author": urlparse(source_url).netloc,
                        "source_url": source_url,
                    })
                except Exception as exc:
                    print(f"Could not inspect news source {source_url}: {exc}")
        return list(self._news_candidates)

    @staticmethod
    def _html_meta(html: str, property_name: str) -> str | None:
        escaped = re.escape(property_name)
        patterns = [
            rf'<meta[^>]+(?:property|name)=["\']{escaped}["\'][^>]+content=["\']([^"\']+)',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{escaped}["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).replace("&amp;", "&").strip()
        return None

    @staticmethod
    def _html_title(html: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return re.sub(r"<[^>]+>", "", match.group(1)).strip() if match else ""

    def _search_openverse(self, query: str) -> list[dict]:
        response = self._request(
            self.OPENVERSE_API,
            params={"q": query, "page_size": self.SEARCH_LIMIT, "mature": "false"},
        )
        results: list[dict] = []
        for item in response.json().get("results", []):
            url = item.get("url") or item.get("thumbnail")
            if not url:
                continue
            results.append({
                "title": item.get("title", ""),
                "mime": item.get("filetype") or "image/jpeg",
                "width": item.get("width") or 0,
                "height": item.get("height") or 0,
                "download_url": url,
                "thumbnail_url": item.get("thumbnail"),
                "license": item.get("license"),
                "author": item.get("creator"),
                "source_url": item.get("foreign_landing_url") or url,
            })
        return results

    def _search_wikimedia(self, query: str) -> list[dict]:
        response = self._request(
            self.WIKIMEDIA_API,
            params={
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
            },
        )
        results: list[dict] = []
        for page in response.json().get("query", {}).get("pages", []):
            imageinfo = page.get("imageinfo") or []
            if not imageinfo:
                continue
            info = imageinfo[0]
            metadata = info.get("extmetadata", {})
            results.append({
                "title": page.get("title", ""),
                "mime": info.get("mime", ""),
                "width": info.get("thumbwidth") or info.get("width") or 0,
                "height": info.get("thumbheight") or info.get("height") or 0,
                "download_url": info.get("thumburl") or info.get("url"),
                "license": self._metadata_value(metadata, "LicenseShortName"),
                "author": self._metadata_value(metadata, "Artist"),
                "source_url": info.get("descriptionurl") or info.get("url"),
            })
        return results

    def _request(self, url: str, params: dict | None = None) -> requests.Response:
        host = urlparse(url).netloc
        last_error: Exception | None = None

        blocked_until = self._blocked_until.get(host, 0.0)
        if blocked_until > time.monotonic():
            remaining = blocked_until - time.monotonic()
            raise RuntimeError(
                f"{host} is temporarily paused after rate limiting "
                f"({remaining:.0f}s remaining)"
            )

        for attempt in range(self.MAX_RETRIES):
            elapsed = time.monotonic() - self._last_request_at.get(host, 0.0)
            if elapsed < self.REQUEST_INTERVAL_SECONDS:
                time.sleep(self.REQUEST_INTERVAL_SECONDS - elapsed)

            try:
                response = self.session.get(url, params=params, timeout=45)
                self._last_request_at[host] = time.monotonic()

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        delay = float(retry_after) if retry_after else 0.0
                    except ValueError:
                        delay = 0.0
                    delay = max(delay, min(8.0, 2.0 ** attempt + random.random()))
                    if attempt + 1 >= 2:
                        cooldown = max(delay, self.RATE_LIMIT_COOLDOWN_SECONDS)
                        self._blocked_until[host] = time.monotonic() + cooldown
                        raise RuntimeError(
                            f"{host} returned HTTP 429; source paused for "
                            f"{cooldown:.0f}s"
                        )
                    print(
                        f"{host} rate limited the request; waiting "
                        f"{delay:.1f}s before one retry."
                    )
                    time.sleep(delay)
                    continue

                if 500 <= response.status_code < 600:
                    delay = min(20.0, 2.0 ** attempt + random.random())
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                if attempt + 1 < self.MAX_RETRIES:
                    time.sleep(min(20.0, 2.0 ** attempt + random.random()))

        raise RuntimeError(f"request failed after retries: {last_error or 'HTTP 429/5xx'}")

    def _rank_images(self, images: list[dict], query: str) -> list[dict]:
        ranked: list[tuple[float, dict]] = []
        query_terms = {term for term in self._normalize_query(query).split() if len(term) > 2}

        for info in images:
            title = str(info.get("title", "")).lower()
            mime = str(info.get("mime", "")).lower()
            url = str(info.get("download_url") or "")
            width = self._safe_int(info.get("width"))
            height = self._safe_int(info.get("height"))

            if not url:
                continue
            if mime and not (mime.startswith("image/") or mime in {"jpg", "jpeg", "png", "webp"}):
                continue
            if any(term in title for term in self.REJECT_TITLE_TERMS):
                continue
            if width <= 0 or height <= 0:
                # Unknown dimensions remain eligible but are ranked lower.
                width, height = 640, 360

            ratio = width / max(height, 1)
            ratio_error = abs(math.log(max(ratio, 0.01) / self.TARGET_RATIO))
            resolution_score = min(width / self.TARGET_WIDTH, 1.5) + min(height / self.TARGET_HEIGHT, 1.5)
            landscape_bonus = 1.5 if width >= height else -2.5
            full_hd_bonus = 2.0 if width >= self.TARGET_WIDTH and height >= self.TARGET_HEIGHT else 0.0
            low_res_penalty = 2.0 if width < self.MIN_SOURCE_WIDTH or height < self.MIN_SOURCE_HEIGHT else 0.0
            title_terms = set(re.findall(r"[a-z0-9]+", title))
            relevance_bonus = min(3.0, len(query_terms & title_terms) * 0.75)

            score = (
                resolution_score + landscape_bonus + full_hd_bonus + relevance_bonus
                - ratio_error * 5.0 - low_res_penalty
            )
            ranked.append((score, info))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in ranked]

    def _download_and_normalize(self, url: str, output_file: Path) -> tuple[int, int]:
        response = self._request(url)
        content_type = response.headers.get("Content-Type", "").lower()
        if content_type and not content_type.startswith("image/"):
            raise ValueError(f"non-image response: {content_type}")
        if len(response.content) < 2048:
            raise ValueError("image response is unexpectedly small")

        try:
            with Image.open(io.BytesIO(response.content)) as image:
                image.load()
                source_size = image.size
                normalized = self._fit_to_full_hd(image)
        except (OSError, UnidentifiedImageError) as exc:
            raise ValueError("downloaded bytes are not a valid image") from exc

        output_file.parent.mkdir(parents=True, exist_ok=True)
        self._save_jpeg(normalized, output_file)
        return source_size

    def register_existing(self, image_file: Path, source_url: str = "") -> bool:
        """Register a cached image; return False when it duplicates prior media."""
        try:
            image_hash = self._average_hash(image_file)
        except Exception:
            return False
        if source_url in self._used_source_urls or any(
            self._hash_distance(image_hash, known) <= 5 for known in self._used_hashes
        ):
            return False
        self._used_hashes.append(image_hash)
        if source_url:
            self._used_source_urls.add(source_url)
        return True

    def _is_duplicate(self, image_file: Path, source_url: str) -> bool:
        return not self.register_existing(image_file, source_url)

    @staticmethod
    def _average_hash(image_file: Path) -> int:
        with Image.open(image_file) as image:
            grayscale = ImageOps.grayscale(image).resize((16, 16), Image.Resampling.LANCZOS)
            pixels = list(grayscale.getdata())
        average = sum(pixels) / len(pixels)
        value = 0
        for pixel in pixels:
            value = (value << 1) | int(pixel >= average)
        return value

    @staticmethod
    def _hash_distance(left: int, right: int) -> int:
        return (left ^ right).bit_count()

    def _build_queries(self, original: str) -> list[str]:
        normalized = self._normalize_query(original)
        lower = normalized.lower()

        # Complex finance sentences rarely exist as literal image titles. A
        # semantic category fallback gives image catalogs realistic queries.
        category = self._category_fallback(lower)
        compact = " ".join(normalized.split()[:6])
        entity = " ".join(normalized.split()[:3])

        candidates = [original.strip(), compact, category, entity]
        unique: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            candidate = re.sub(r"\s+", " ", candidate).strip()
            key = candidate.casefold()
            if candidate and key not in seen:
                unique.append(candidate)
                seen.add(key)
        return unique

    @staticmethod
    def _category_fallback(text: str) -> str:
        rules = [
            (("hormuz", "persian gulf"), "Strait of Hormuz oil tanker"),
            (("oil", "crude", "tanker"), "oil tanker at sea"),
            (("factory", "manufacturing", "pmi"), "modern manufacturing factory"),
            (("job", "employment", "payroll", "worker"), "workers in modern workplace"),
            (("palantir",), "Palantir headquarters"),
            (("amazon",), "Amazon headquarters"),
            (("astrazeneca", "bristol", "pharmaceutical"), "pharmaceutical laboratory scientists"),
            (("merger", "acquisition"), "business executives meeting"),
            (("federal reserve", "inflation", "treasury", "yield"), "Federal Reserve building"),
            (("stock", "revenue", "cash flow", "earnings", "market"), "financial market trading screens"),
            (("ai", "artificial intelligence", "software"), "artificial intelligence data center"),
            (("port", "cargo", "container", "supply chain"), "container port aerial"),
            (("press conference", "officials", "ministry"), "government press conference"),
        ]
        for keywords, fallback in rules:
            if any(keyword in text for keyword in keywords):
                return fallback
        return "global finance business city"

    def _create_context_visual(self, scene: StoryboardScene, output_file: Path) -> MediaAsset:
        """Create an honest non-chart fallback when no real image is available.

        This visual intentionally contains no plotted line, axes, values, scene
        number, or implied statistics. Data charts must come from a real source
        or from structured data supplied by the project.
        """
        width, height = self.TARGET_WIDTH, self.TARGET_HEIGHT
        image = Image.new("RGB", (width, height), (17, 27, 44))
        draw = ImageDraw.Draw(image)

        for y in range(height):
            shade = int(22 + 34 * y / height)
            draw.line((0, y, width, y), fill=(14, shade, 58))

        rng = random.Random(scene.id)
        for _ in range(18):
            x = rng.randint(-120, width - 80)
            y = rng.randint(-120, height - 80)
            size = rng.randint(90, 260)
            color = (24 + rng.randint(0, 18), 65 + rng.randint(0, 30), 88 + rng.randint(0, 30))
            draw.rounded_rectangle((x, y, x + size, y + size), radius=30, fill=color)

        panel = (120, 180, 1800, 820)
        draw.rounded_rectangle(panel, radius=40, fill=(20, 34, 55), outline=(55, 100, 135), width=3)
        title_font = self._font(54)
        note_font = self._font(28)
        wrapped = self._wrap_text(scene.visual.query.strip(), 48)
        draw.multiline_text((170, 285), wrapped, font=title_font, fill="white", spacing=16)
        draw.text(
            (170, 720),
            "Illustrative background — not a data chart",
            font=note_font,
            fill=(165, 185, 205),
        )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        self._save_jpeg(image, output_file)
        return MediaAsset(
            scene=scene.id,
            provider=MediaProviderType.AI,
            query=scene.visual.query.strip(),
            file=output_file.name,
            width=width,
            height=height,
            license=None,
            author="Local contextual visual",
            source_url="local://context-visual",
        )

    @staticmethod
    def _font(size: int) -> ImageFont.ImageFont:
        candidates = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
        return ImageFont.load_default()

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
        image.save(temporary, format="JPEG", quality=92, optimize=True, progressive=True, subsampling="4:2:0")
        temporary.replace(output_file)

    @staticmethod
    def _metadata_value(metadata: dict, key: str) -> str | None:
        value = metadata.get(key, {}).get("value")
        if not value:
            return None
        return re.sub(r"<[^>]+>", "", str(value)).strip() or None

    @staticmethod
    def _safe_int(value: object) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

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
        return "\n".join(lines[:4])

    @staticmethod
    def _normalize_query(query: str) -> str:
        normalized = query.lower()
        normalized = re.sub(r"\b(202[0-9]|q[1-4]|percent|billion|million)\b", " ", normalized)
        normalized = re.sub(r"[^a-z0-9. ]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()
