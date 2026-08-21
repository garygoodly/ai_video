from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageStat

from kvf.models.media import MediaAsset, MediaProvider


class SourceScreenshotProvider:
    """Capture *readable evidence*, not merely an authoritative webpage.

    A source is accepted only when the visible page content strongly matches the
    scene claim. X/Twitter posts are cropped to the post itself. News and
    official pages are cropped around the most relevant headline/data area.
    Generic home pages, calendars unrelated to the claim, loading screens,
    paywalls, and mostly blank captures are rejected.
    """

    TARGET = (1920, 1080)
    MIN_RELEVANCE = 3.0

    GENERIC_TITLES = {
        "calendar",
        "federal open market committee",
        "home",
        "market info",
        "news & events",
    }
    BAD_PAGE_TERMS = {
        "access denied",
        "request blocked",
        "just a moment",
        "sign in to continue",
        "subscribe to continue",
        "enable javascript",
        "captcha",
        "verify you are human",
    }

    CONCEPT_ALIASES = {
        "semiconductor": ("半導體", "費半", "sox", "chip", "memory", "晶片"),
        "treasury": ("美債", "公債", "treasury", "bond"),
        "yield": ("殖利率", "yield"),
        "federal reserve": ("聯準會", "fed", "fomc", "federal reserve"),
        "oil": ("原油", "油價", "brent", "wti", "荷莫茲", "hormuz"),
        "taiwan": ("台股", "台灣", "twse", "taiex", "新台幣"),
        "foreign investor": ("外資", "三大法人", "foreign investor"),
        "nikkei": ("日經", "nikkei"),
        "tsmc": ("台積電", "tsmc"),
        "nvidia": ("輝達", "nvidia", "nvda"),
        "micron": ("美光", "micron"),
        "nasdaq": ("nasdaq", "那斯達克", "納斯達克"),
        "s&p 500": ("s&p 500", "sp500", "標普"),
        "dow jones": ("dow jones", "道瓊"),
        "yen": ("日圓", "yen", "jpy"),
        "dollar": ("美元", "dollar", "usd"),
    }

    def __init__(self, source_urls: list[str] | None = None) -> None:
        self.source_urls = list(dict.fromkeys(
            url for raw in (source_urls or [])
            if (url := self._canonical_url(raw))
        ))
        self._cache: dict[str, dict] = {}
        self._playwright = None
        self._browser = None
        self._blocked_hosts: set[str] = set()

    def close(self) -> None:
        try:
            if self._browser is not None:
                self._browser.close()
        finally:
            self._browser = None
            if self._playwright is not None:
                self._playwright.stop()
                self._playwright = None

    def create(self, scene, output: Path) -> MediaAsset | None:
        candidates = [url for url in self.source_urls if self._is_supported(url)]
        if not candidates:
            return None
        try:
            self._ensure_browser()
        except Exception as exc:
            print(f"Source screenshot provider unavailable: {exc}")
            return None

        anchors = self._scene_anchors(scene)
        if not anchors["terms"] and not anchors["numbers"]:
            return None

        best: tuple[str, dict, float] | None = None
        for url in candidates[:30]:
            host = urlparse(url).netloc.lower()
            if host in self._blocked_hosts:
                continue
            try:
                info = self._inspect(url)
            except Exception as exc:
                print(f"Could not inspect source screenshot {url}: {exc}")
                continue
            if not self._page_is_usable(info):
                continue
            score = self._relevance(anchors, info, url)
            if best is None or score > best[2]:
                best = (url, info, score)

        if best is None or best[2] < self.MIN_RELEVANCE:
            return None

        url, info, score = best
        try:
            image_path = self._capture(url, info, anchors)
            if not self._capture_is_useful(image_path):
                image_path.unlink(missing_ok=True)
                return None
            self._fit_on_canvas(image_path, output, url)
        except Exception as exc:
            print(f"Could not capture source evidence {url}: {exc}")
            return None

        host = urlparse(url).netloc.lower()
        return MediaAsset(
            scene=scene.id,
            provider=MediaProvider.NEWS_ARTICLE,
            query=f"Readable source evidence ({score:.1f}): {scene.visual.query}",
            file=output.name,
            width=self.TARGET[0],
            height=self.TARGET[1],
            license="Source/platform terms apply",
            author=host,
            source_url=url,
        )

    def _ensure_browser(self) -> None:
        if self._browser is not None:
            return
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Install requirements-optional-screenshots.txt "
                "and run: playwright install chromium"
            ) from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)

    def _inspect(self, url: str) -> dict:
        if url in self._cache:
            return self._cache[url]
        page = self._browser.new_page(viewport={"width": 1440, "height": 1000})
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=25000)
            if response is not None and response.status in {401, 403, 429}:
                self._blocked_hosts.add(urlparse(url).netloc.lower())
                raise RuntimeError(f"HTTP {response.status}")
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            page.wait_for_timeout(1200)

            title = page.title().strip()
            text = page.locator("body").inner_text(timeout=5000)[:16000]
            spinner_visible = self._spinner_visible(page)
            info = {
                "title": title,
                "text": f"{title} {text}",
                "body": text,
                "spinner_visible": spinner_visible,
            }
            self._cache[url] = info
            return info
        finally:
            page.close()

    @staticmethod
    def _spinner_visible(page) -> bool:
        selectors = [
            ".spinner", ".loading", "[aria-busy='true']", "[class*='loading']",
            "[class*='spinner']", "text=/loading/i",
        ]
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if loc.count() and loc.is_visible(timeout=250):
                    return True
            except Exception:
                continue
        return False

    def _capture(self, url: str, info: dict, anchors: dict) -> Path:
        page = self._browser.new_page(
            viewport={"width": 1440, "height": 1000}, device_scale_factor=1.5
        )
        fd, tmp_name = tempfile.mkstemp(prefix="kvf-source-", suffix=".png")
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=25000)
            if response is not None and response.status in {401, 403, 429}:
                self._blocked_hosts.add(urlparse(url).netloc.lower())
                raise RuntimeError(f"HTTP {response.status}")
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            page.wait_for_timeout(1200)

            host = urlparse(url).netloc.lower()
            if host.endswith("x.com") or host.endswith("twitter.com"):
                tweet = page.locator('article[data-testid="tweet"]').first
                if tweet.count() == 0:
                    raise RuntimeError("No readable X post was found on the page")
                tweet_text = tweet.inner_text(timeout=3000).strip()
                if len(tweet_text) < 30:
                    raise RuntimeError("X post text is too short to be useful evidence")
                tweet.screenshot(path=str(tmp))
                return tmp

            # Prefer an element containing an exact number from the narration;
            # this is especially useful for official tables/data releases.
            element = self._find_evidence_element(page, anchors)
            if element is not None:
                try:
                    element.scroll_into_view_if_needed(timeout=2000)
                    page.wait_for_timeout(300)
                    element.screenshot(path=str(tmp))
                    return tmp
                except Exception:
                    pass

            # For news/official pages, the article/main content is much more
            # useful than a full browser viewport containing navigation chrome.
            for selector in ("article", "main", "[role='main']", "#content", ".content"):
                try:
                    loc = page.locator(selector).first
                    if loc.count() and loc.is_visible(timeout=300):
                        box = loc.bounding_box()
                        if box and box["width"] >= 500 and box["height"] >= 180:
                            # Avoid giant full-article captures that become unreadable.
                            clip_h = min(box["height"], 760)
                            page.screenshot(
                                path=str(tmp),
                                clip={
                                    "x": max(0, box["x"]),
                                    "y": max(0, box["y"]),
                                    "width": min(box["width"], 1400),
                                    "height": clip_h,
                                },
                            )
                            return tmp
                except Exception:
                    continue

            raise RuntimeError("No readable evidence region was found")
        finally:
            page.close()

    @staticmethod
    def _find_evidence_element(page, anchors: dict):
        # Exact numeric evidence is strongest. Try longer values first.
        for number in sorted(anchors["numbers"], key=len, reverse=True):
            try:
                loc = page.get_by_text(re.compile(re.escape(number))).first
                if loc.count() and loc.is_visible(timeout=250):
                    for xpath in ("xpath=ancestor::tr[1]", "xpath=ancestor::li[1]", "xpath=ancestor::p[1]", "xpath=ancestor::section[1]", "xpath=ancestor::div[1]"):
                        try:
                            parent = loc.locator(xpath)
                            if parent.count() and parent.is_visible(timeout=200):
                                box = parent.bounding_box()
                                if box and 250 <= box["width"] <= 1500 and 60 <= box["height"] <= 800:
                                    return parent
                        except Exception:
                            continue
                    return loc
            except Exception:
                continue

        for term in sorted(anchors["terms"], key=len, reverse=True)[:8]:
            if len(term) < 4:
                continue
            try:
                loc = page.get_by_text(re.compile(re.escape(term), re.I)).first
                if loc.count() and loc.is_visible(timeout=200):
                    return loc.locator("xpath=ancestor::*[self::section or self::article or self::div or self::p][1]")
            except Exception:
                continue
        return None

    @classmethod
    def _fit_on_canvas(cls, source: Path, output: Path, url: str) -> None:
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            # Keep the evidence large and readable, with a small source footer.
            max_w, max_h = 1780, 940
            image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", cls.TARGET, "black")
            x = (cls.TARGET[0] - image.width) // 2
            y = max(30, (1000 - image.height) // 2)
            canvas.paste(image, (x, y))

            draw = ImageDraw.Draw(canvas)
            host = urlparse(url).netloc.lower().replace("www.", "")
            try:
                font = ImageFont.truetype("arial.ttf", 25)
            except OSError:
                font = ImageFont.load_default()
            draw.text((70, 1020), f"Source: {host}", fill=(190, 190, 190), font=font)

            output.parent.mkdir(parents=True, exist_ok=True)
            canvas.save(output, "JPEG", quality=94, optimize=True)
        source.unlink(missing_ok=True)

    @classmethod
    def _page_is_usable(cls, info: dict) -> bool:
        title = str(info.get("title", "")).strip().casefold()
        body = str(info.get("body", "")).strip()
        combined = f"{title} {body}".casefold()
        if any(term in combined for term in cls.BAD_PAGE_TERMS):
            return False
        if len(body) < 180:
            return False
        if info.get("spinner_visible") and len(body) < 1200:
            return False
        return True

    @classmethod
    def _relevance(cls, anchors: dict, info: dict, url: str) -> float:
        source = str(info.get("text", "")).casefold()
        title = str(info.get("title", "")).strip().casefold()
        score = 0.0

        matched_numbers = [n for n in anchors["numbers"] if n in source]
        score += 2.25 * len(matched_numbers)

        matched_terms = [t for t in anchors["terms"] if t.casefold() in source]
        score += 1.0 * len(matched_terms)

        # Generic pages should need much stronger evidence to win.
        if title in cls.GENERIC_TITLES:
            score -= 2.5
        if any(part in urlparse(url).path.casefold() for part in ("calendar", "index.html", "home")):
            score -= 1.0

        host = urlparse(url).netloc.lower()
        if host.endswith("x.com") or host.endswith("twitter.com"):
            score += 0.75

        # If the narration contains precise numbers, a page that contains none
        # of them is usually not direct evidence for that claim.
        if anchors["numbers"] and not matched_numbers and len(matched_terms) < 2:
            score -= 3.0
        return score

    @classmethod
    def _scene_anchors(cls, scene) -> dict:
        text = f"{scene.visual.query} {scene.narration}".casefold()
        terms: set[str] = set()

        # ASCII entities/tickers/phrases survive across languages and are high-value.
        for token in re.findall(r"[a-z][a-z0-9&./-]{2,}", text):
            if token not in {"the", "and", "with", "from", "market", "financial", "video", "chart", "photo"}:
                terms.add(token.strip(".,/"))

        for canonical, aliases in cls.CONCEPT_ALIASES.items():
            if any(alias.casefold() in text for alias in aliases):
                terms.add(canonical)
                terms.update(alias.casefold() for alias in aliases if re.search(r"[a-z]", alias, re.I))

        # Keep exact numeric strings so a claim such as 5.6% / 4.70 / 12621
        # must match visible evidence when possible.
        numbers = set(re.findall(r"(?<!\w)\d+(?:[.,]\d+)*(?:%|％)?", text))
        normalized_numbers = set()
        for value in numbers:
            normalized_numbers.add(value)
            normalized_numbers.add(value.replace(",", ""))
        return {"terms": terms, "numbers": normalized_numbers}

    @staticmethod
    def _capture_is_useful(path: Path) -> bool:
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image).convert("L").resize((320, 180))
                entropy = image.entropy()
                stddev = ImageStat.Stat(image).stddev[0]
                return entropy >= 2.0 and stddev >= 20.0
        except Exception:
            return False

    @staticmethod
    def _canonical_url(raw: object) -> str | None:
        if raw is None:
            return None
        text = str(raw).strip().replace("\\/", "/").replace("\\(", "(").replace("\\)", ")")
        destinations = re.findall(r"\]\(\s*(https?://[^)\s]+)", text, flags=re.IGNORECASE)
        candidates = destinations + re.findall(r"https?://[^\s\]>)\"']+", text, flags=re.IGNORECASE)
        for candidate in candidates:
            candidate = candidate.strip().rstrip(".,;:").replace("\\", "")
            parsed = urlparse(candidate)
            if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
                return candidate
        return None

    @staticmethod
    def _is_supported(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in {"http", "https"}:
            return False
        host = parsed.netloc.lower().split(":", 1)[0]
        if host.endswith("x.com") or host.endswith("twitter.com"):
            return True
        if (
            host.endswith(".gov")
            or host.endswith(".gov.tw")
            or host.endswith(".go.jp")
            or host in {
                "federalreserve.gov", "www.federalreserve.gov",
                "twse.com.tw", "www.twse.com.tw",
                "taifex.com.tw", "www.taifex.com.tw",
            }
        ):
            return True
        # A small set of news sites where a headline/article-header capture is
        # useful and generally visible without a subscriber session.
        return host.endswith("apnews.com") or host.endswith("reuters.com")
