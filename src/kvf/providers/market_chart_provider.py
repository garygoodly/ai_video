from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFont

from kvf.models.media import MediaAsset, MediaProvider
from kvf.models.storyboard import StoryboardScene


class MarketChartProvider:
    """Generate precise, source-labelled historical charts from Yahoo data."""

    SYMBOLS = {
        "s&p 500": ("^GSPC", "S&P 500", "Index points"),
        "sp500": ("^GSPC", "S&P 500", "Index points"),
        "s&p500": ("^GSPC", "S&P 500", "Index points"),
        "dow jones": ("^DJI", "Dow Jones Industrial Average", "Index points"),
        "dow": ("^DJI", "Dow Jones Industrial Average", "Index points"),
        "nasdaq": ("^IXIC", "Nasdaq Composite", "Index points"),
        "taiex": ("^TWII", "TAIEX", "Index points"),
        "taiwan weighted": ("^TWII", "TAIEX", "Index points"),
        "nikkei": ("^N225", "Nikkei 225", "Index points"),
        "topix": ("^TOPX", "TOPIX", "Index points"),
        "usd/twd": ("TWD=X", "USD/TWD", "TWD per USD"),
        "usd/jpy": ("JPY=X", "USD/JPY", "JPY per USD"),
        "yen": ("JPY=X", "USD/JPY", "JPY per USD"),
        "bitcoin": ("BTC-USD", "Bitcoin", "USD"),
        "gold": ("GC=F", "Gold futures", "USD per troy ounce"),
        "crude oil": ("CL=F", "WTI crude oil futures", "USD per barrel"),
    }

    API = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 FinanceVideoFactory/3.0"})

    def match(self, scene: StoryboardScene) -> tuple[str, str, str] | None:
        haystack = f"{scene.section} {scene.visual.query} {scene.narration}".casefold()
        for key, value in sorted(self.SYMBOLS.items(), key=lambda item: -len(item[0])):
            if key in haystack:
                return value
        return None

    def create(self, scene: StoryboardScene, output: Path) -> MediaAsset | None:
        matched = self.match(scene)
        if not matched:
            return None
        symbol, title, unit = matched
        try:
            timestamps, values = self._fetch(symbol)
            if len(values) < 10:
                return None
            self._draw(output, title, unit, timestamps, values)
        except Exception as exc:
            print(f"Could not build market chart for {title}: {exc}")
            return None
        return MediaAsset(
            scene=scene.id,
            provider=MediaProvider.LOCAL,
            query=f"{title} latest 6-month historical chart",
            file=output.name,
            width=1920,
            height=1080,
            license="Data source terms apply",
            author="Yahoo Finance historical market data",
            source_url=f"https://finance.yahoo.com/quote/{quote(symbol, safe='')}",
        )

    def _fetch(self, symbol: str) -> tuple[list[datetime], list[float]]:
        response = self.session.get(
            self.API.format(symbol=quote(symbol, safe="")),
            params={"range": "6mo", "interval": "1d", "events": "history"},
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()["chart"]["result"][0]
        timestamps = [datetime.fromtimestamp(value) for value in result["timestamp"]]
        closes = result["indicators"]["quote"][0]["close"]
        pairs = [(t, float(v)) for t, v in zip(timestamps, closes) if v is not None]
        return [p[0] for p in pairs], [p[1] for p in pairs]

    def _draw(
        self, output: Path, title: str, unit: str,
        timestamps: list[datetime], values: list[float]
    ) -> None:
        image = Image.new("RGB", (1920, 1080), (18, 25, 36))
        draw = ImageDraw.Draw(image)
        title_font = self._font(54)
        label_font = self._font(28)
        small_font = self._font(23)
        left, top, right, bottom = 150, 170, 1810, 900
        draw.text((left, 55), f"{title} — latest 6 months", fill="white", font=title_font)
        draw.text((left, 120), f"Daily close • Updated {timestamps[-1].date().isoformat()}", fill=(180, 195, 215), font=small_font)

        minimum, maximum = min(values), max(values)
        padding = (maximum - minimum) * 0.08 or 1.0
        minimum -= padding
        maximum += padding
        for row in range(6):
            y = top + (bottom - top) * row / 5
            value = maximum - (maximum - minimum) * row / 5
            draw.line((left, y, right, y), fill=(54, 66, 82), width=2)
            draw.text((30, y - 16), f"{value:,.2f}", fill=(205, 215, 230), font=small_font)
        points = []
        for index, value in enumerate(values):
            x = left + (right - left) * index / max(1, len(values) - 1)
            y = bottom - (bottom - top) * (value - minimum) / (maximum - minimum)
            points.append((x, y))
        draw.line(points, fill=(82, 214, 180), width=7, joint="curve")
        for index in range(0, len(timestamps), max(1, len(timestamps) // 5)):
            x = left + (right - left) * index / max(1, len(values) - 1)
            draw.text((x - 35, bottom + 25), timestamps[index].strftime("%b %Y"), fill=(205, 215, 230), font=small_font)
        draw.text((left, 970), "X-axis: Date", fill=(205, 215, 230), font=label_font)
        draw.text((620, 970), f"Y-axis: {unit}", fill=(205, 215, 230), font=label_font)
        draw.text((1300, 970), "Source: Yahoo Finance", fill=(205, 215, 230), font=label_font)
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output, "JPEG", quality=94, optimize=True)

    @staticmethod
    def _font(size: int):
        candidates = [
            "C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for path in candidates:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        return ImageFont.load_default()
