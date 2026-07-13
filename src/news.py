"""News helpers for AlphaOS."""

from __future__ import annotations

from datetime import timezone
from html import unescape
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .cache import get_cached_value

DEFAULT_NEWS_QUERY = "日経平均"
_NEWS_CACHE_TTL_SECONDS = 300
_NEWS_URL = "https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP:ja"


def fetch_latest_market_news(query: str = DEFAULT_NEWS_QUERY) -> dict[str, str] | None:
    """Fetch a single market-related news item from Google News RSS."""
    cache_key = f"news.{query}"
    return get_cached_value(
        cache_key,
        lambda: _fetch_latest_market_news_uncached(query),
        _NEWS_CACHE_TTL_SECONDS,
    )


def _fetch_latest_market_news_uncached(query: str) -> dict[str, str] | None:
    url = _NEWS_URL.format(query=quote_plus(query))

    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=5) as response:
            feed = response.read()
    except Exception:
        return None

    try:
        root = ElementTree.fromstring(feed)
    except Exception:
        return None

    channel = root.find("channel")
    if channel is None:
        return None

    item = channel.find("item")
    if item is None:
        return None

    title = _find_text(item, "title")
    if not title:
        return None

    source = ""
    source_element = item.find("source")
    if source_element is not None and source_element.text:
        source = unescape(source_element.text.strip())

    published_at = _find_text(item, "pubDate")
    if published_at:
        published_at = _normalize_rss_datetime(published_at)

    return {
        "title": unescape(title.strip()),
        "source": source,
        "url": _find_text(item, "link"),
        "published_at": published_at,
    }


def _find_text(element: ElementTree.Element, tag: str) -> str:
    child = element.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _normalize_rss_datetime(value: str) -> str:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return value

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()
