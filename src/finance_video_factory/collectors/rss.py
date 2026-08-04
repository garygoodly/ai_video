from __future__ import annotations
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
import feedparser
from finance_video_factory.models import Article

class RSSCollector:
    def collect(self, feeds: list[str], lookback_hours: int, limit: int) -> list[Article]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        articles: list[Article] = []
        seen: set[str] = set()
        for feed_url in feeds:
            parsed = feedparser.parse(feed_url)
            source = parsed.feed.get("title") or urlparse(feed_url).netloc
            for entry in parsed.entries:
                url = entry.get("link", "")
                title = entry.get("title", "").strip()
                if not url or not title or url in seen:
                    continue
                published = None
                struct = entry.get("published_parsed") or entry.get("updated_parsed")
                if struct:
                    published = datetime(*struct[:6], tzinfo=timezone.utc)
                    if published < cutoff:
                        continue
                seen.add(url)
                articles.append(Article(title=title, summary=entry.get("summary", ""), url=url, source=source, published_at=published))
        articles.sort(key=lambda x: x.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return articles[:limit]
