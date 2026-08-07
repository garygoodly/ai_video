from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFont

from kvf.models.media import MediaAsset, MediaProvider
from kvf.models.storyboard import StoryboardScene


class MarketChartProvider:
    """Generate latest source-labelled market charts from real observations.

    This provider deliberately prefers a precise chart over a generic stock
    photo. It tries two Yahoo chart hosts and then Stooq where a symbol mapping
    is known. It never invents data points.
    """

    SYMBOLS = {
        "s&p 500": ("^GSPC", "^spx", "S&P 500", "Index points"),
        "sp500": ("^GSPC", "^spx", "S&P 500", "Index points"),
        "s&p500": ("^GSPC", "^spx", "S&P 500", "Index points"),
        "dow jones": ("^DJI", "^dji", "Dow Jones Industrial Average", "Index points"),
        "dow": ("^DJI", "^dji", "Dow Jones Industrial Average", "Index points"),
        "nasdaq": ("^IXIC", "^ndq", "Nasdaq Composite", "Index points"),
        "taiex": ("^TWII", None, "TAIEX", "Index points"),
        "taiwan weighted": ("^TWII", None, "TAIEX", "Index points"),
        "加權指數": ("^TWII", None, "TAIEX", "Index points"),
        "nikkei": ("^N225", "^nkx", "Nikkei 225", "Index points"),
        "topix": ("^TOPX", None, "TOPIX", "Index points"),
        "usd/twd": ("TWD=X", None, "USD/TWD", "TWD per USD"),
        "usd/jpy": ("JPY=X", None, "USD/JPY", "JPY per USD"),
        "日圓": ("JPY=X", None, "USD/JPY", "JPY per USD"),
        "yen": ("JPY=X", None, "USD/JPY", "JPY per USD"),
        "bitcoin": ("BTC-USD", None, "Bitcoin", "USD"),
        "gold": ("GC=F", None, "Gold futures", "USD per troy ounce"),
        "crude oil": ("CL=F", None, "WTI crude oil futures", "USD per barrel"),
        "wti": ("CL=F", None, "WTI crude oil futures", "USD per barrel"),
        "tsmc": ("TSM", "tsm.us", "TSMC ADR", "USD"),
        "台積電": ("2330.TW", None, "TSMC (2330.TW)", "TWD"),
        "nvidia": ("NVDA", "nvda.us", "NVIDIA", "USD"),
        "nvda": ("NVDA", "nvda.us", "NVIDIA", "USD"),
        "palantir": ("PLTR", "pltr.us", "Palantir", "USD"),
        "amazon": ("AMZN", "amzn.us", "Amazon", "USD"),
        "apple": ("AAPL", "aapl.us", "Apple", "USD"),
    }

    YAHOO_APIS = (
        "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        "https://query2.finance.yahoo.com/v8/finance/chart/{symbol}",
    )
    STOOQ_API = "https://stooq.com/q/d/l/"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 FinanceVideoFactory/4.0"})

    def match(self, scene: StoryboardScene):
        haystack = f"{scene.section} {scene.visual.query} {scene.narration}".casefold()
        for key, value in sorted(self.SYMBOLS.items(), key=lambda item: -len(item[0])):
            if key.casefold() in haystack:
                return value
        return None

    def create(self, scene: StoryboardScene, output: Path) -> MediaAsset | None:
        matched = self.match(scene)
        if not matched:
            return None
        yahoo_symbol, stooq_symbol, title, unit = matched
        try:
            timestamps, values, source_name, source_url = self._fetch(yahoo_symbol, stooq_symbol)
            if len(values) < 10:
                return None
            self._draw(output, title, unit, timestamps, values, source_name)
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
            license="Market-data provider terms apply",
            author=f"Chart generated locally from {source_name} observations",
            source_url=source_url,
        )

    def _fetch(self, yahoo_symbol: str, stooq_symbol: str | None):
        errors = []
        for api in self.YAHOO_APIS:
            try:
                response = self.session.get(
                    api.format(symbol=quote(yahoo_symbol, safe="")),
                    params={"range": "6mo", "interval": "1d", "events": "history"},
                    timeout=20,
                )
                response.raise_for_status()
                result = response.json()["chart"]["result"][0]
                timestamps = [datetime.fromtimestamp(value) for value in result["timestamp"]]
                closes = result["indicators"]["quote"][0]["close"]
                pairs = [(t, float(v)) for t, v in zip(timestamps, closes) if v is not None]
                if len(pairs) >= 10:
                    return (
                        [p[0] for p in pairs], [p[1] for p in pairs],
                        "Yahoo Finance", f"https://finance.yahoo.com/quote/{quote(yahoo_symbol, safe='')}",
                    )
            except Exception as exc:
                errors.append(str(exc))

        if stooq_symbol:
            try:
                response = self.session.get(
                    self.STOOQ_API,
                    params={"s": stooq_symbol, "i": "d"},
                    timeout=20,
                )
                response.raise_for_status()
                rows = list(csv.DictReader(io.StringIO(response.text)))
                pairs = []
                for row in rows[-160:]:
                    try:
                        pairs.append((datetime.strptime(row["Date"], "%Y-%m-%d"), float(row["Close"])))
                    except (KeyError, ValueError, TypeError):
                        continue
                if len(pairs) >= 10:
                    return (
                        [p[0] for p in pairs], [p[1] for p in pairs],
                        "Stooq", f"https://stooq.com/q/?s={quote(stooq_symbol)}",
                    )
            except Exception as exc:
                errors.append(str(exc))
        raise RuntimeError("; ".join(errors[-3:]) or "market data unavailable")

    def _draw(self, output, title, unit, timestamps, values, source_name):
        image = Image.new("RGB", (1920, 1080), (18, 25, 36))
        draw = ImageDraw.Draw(image)
        title_font = self._font(54)
        label_font = self._font(28)
        small_font = self._font(23)
        left, top, right, bottom = 150, 170, 1810, 900
        draw.text((left, 55), f"{title} — latest 6 months", fill="white", font=title_font)
        draw.text(
            (left, 120),
            f"Daily close • Updated {timestamps[-1].date().isoformat()} • Latest {values[-1]:,.2f}",
            fill=(180, 195, 215), font=small_font,
        )

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
        draw.text((1300, 970), f"Source: {source_name}", fill=(205, 215, 230), font=label_font)
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
