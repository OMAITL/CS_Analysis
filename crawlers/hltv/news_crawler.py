# -*- coding: utf-8 -*-
"""
Fetch recent HLTV news via official news sitemap (preferred) or /news index fallback.

HLTV has no public API. This module only reads public listing metadata (title, URL, date).
Respect robots.txt, keep request rate low, and use for personal research only.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from xml.etree import ElementTree

from crawlers.hltv.client import HLTVClient

logger = logging.getLogger(__name__)

NEWS_SITEMAP_PATH = "/news-sitemap.xml"
NEWS_INDEX_PATH = "/news"
_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
_HREF_NEWS_RE = re.compile(
    r'href="((?:https://www\.hltv\.org)?/news/\d+/[^"]+)"',
    re.IGNORECASE,
)
_TITLE_RE = re.compile(r"<title[^>]*>([^<]+)</title>", re.IGNORECASE)


@dataclass
class HLTVNewsItem:
    title: str
    url: str
    published_date: Optional[str] = None
    snippet: str = ""

    def to_event_dict(self) -> dict:
        return {
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "dimension": "hltv_crawl",
            "source": "hltv.org",
            "published_date": self.published_date,
        }


def _normalize_url(href: str, base: str = "https://www.hltv.org") -> str:
    if href.startswith("http"):
        return href.split("?")[0].rstrip("/")
    return f"{base}{href}".split("?")[0].rstrip("/")


def _title_from_slug(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1]
    slug = re.sub(r"^\d+-", "", slug)
    return slug.replace("-", " ").strip() or url


def _parse_iso_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if "T" in raw:
            return datetime.fromisoformat(raw)
        return datetime.strptime(raw[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _within_days(dt: Optional[datetime], days: int) -> bool:
    if dt is None:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, days))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= cutoff


def _parse_news_sitemap(xml_text: str, *, max_items: int, max_age_days: int) -> List[HLTVNewsItem]:
    root = ElementTree.fromstring(xml_text)
    items: List[HLTVNewsItem] = []
    for url_node in root.findall(".//sm:url", _SITEMAP_NS) or root.findall(".//{*}url"):
        loc = url_node.findtext("sm:loc", default="", namespaces=_SITEMAP_NS)
        if not loc and url_node.find("{*}loc") is not None:
            loc = url_node.find("{*}loc").text or ""
        loc = (loc or "").strip()
        if "/news/" not in loc:
            continue
        lastmod = url_node.findtext("sm:lastmod", default="", namespaces=_SITEMAP_NS)
        if not lastmod and url_node.find("{*}lastmod") is not None:
            lastmod = url_node.find("{*}lastmod").text or ""
        pub_dt = _parse_iso_date(lastmod)
        if not _within_days(pub_dt, max_age_days):
            continue
        norm = _normalize_url(loc)
        items.append(
            HLTVNewsItem(
                title=_title_from_slug(norm),
                url=norm,
                published_date=lastmod[:10] if lastmod else None,
                snippet="HLTV news (sitemap)",
            )
        )
        if len(items) >= max_items:
            break
    return items


def _parse_news_index(html: str, *, max_items: int) -> List[HLTVNewsItem]:
    seen = set()
    items: List[HLTVNewsItem] = []
    for match in _HREF_NEWS_RE.finditer(html):
        url = _normalize_url(match.group(1))
        if url in seen:
            continue
        seen.add(url)
        items.append(
            HLTVNewsItem(
                title=_title_from_slug(url),
                url=url,
                snippet="HLTV news (index)",
            )
        )
        if len(items) >= max_items:
            break
    return items


def fetch_hltv_news(
    *,
    max_items: int = 8,
    max_age_days: int = 14,
    client: Optional[HLTVClient] = None,
    fail_soft: bool = True,
) -> List[HLTVNewsItem]:
    """
    Return recent HLTV news entries (newest first, up to ``max_items``).

    Tries ``/news-sitemap.xml`` first; falls back to parsing ``/news`` links.
    """
    api = client or HLTVClient()
    errors: List[str] = []

    try:
        xml_text = api.get_text(NEWS_SITEMAP_PATH)
        items = _parse_news_sitemap(xml_text, max_items=max_items, max_age_days=max_age_days)
        if items:
            logger.info("HLTV sitemap: %s items", len(items))
            return items
    except Exception as exc:
        errors.append(f"sitemap: {exc}")
        logger.warning("HLTV news sitemap failed: %s", exc)

    try:
        html = api.get_text(NEWS_INDEX_PATH)
        items = _parse_news_index(html, max_items=max_items)
        if items:
            logger.info("HLTV /news index: %s items", len(items))
            return items
    except Exception as exc:
        errors.append(f"index: {exc}")
        logger.warning("HLTV /news index failed: %s", exc)

    if fail_soft:
        return []
    raise RuntimeError("; ".join(errors) or "HLTV news fetch failed")
