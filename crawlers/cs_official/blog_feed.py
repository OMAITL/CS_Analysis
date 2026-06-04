# -*- coding: utf-8 -*-
"""
Fetch recent posts from Counter-Strike official blog RSS.

Default feed: updates category on blog.counter-strike.net
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from xml.etree import ElementTree

from crawlers.hltv.client import HLTVClient

logger = logging.getLogger(__name__)

DEFAULT_FEED_URL = "https://blog.counter-strike.net/index.php/category/updates/feed/"
_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class CSOfficialBlogItem:
    title: str
    url: str
    published_date: Optional[str] = None
    snippet: str = ""

    def to_event_dict(self) -> dict:
        return {
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "dimension": "official_crawl",
            "source": "blog.counter-strike.net",
            "published_date": self.published_date,
        }


def _strip_html(value: str) -> str:
    text = _TAG_RE.sub(" ", value or "")
    return " ".join(text.split())[:400]


def _parse_rss_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    raw = value.strip()
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _within_days(dt: Optional[datetime], days: int) -> bool:
    if dt is None:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, days))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= cutoff


def fetch_cs_official_blog(
    *,
    max_items: int = 5,
    max_age_days: int = 30,
    feed_url: Optional[str] = None,
    fail_soft: bool = True,
) -> List[CSOfficialBlogItem]:
    url = (feed_url or os.getenv("CS_OFFICIAL_FEED_URL", DEFAULT_FEED_URL)).strip()
    client = HLTVClient(min_interval_seconds=1.5, user_agent="DSA-CS-Research/1.0 (official blog RSS)")
    try:
        xml_text = client.get_text(url)
    except Exception as exc:
        logger.warning("CS official blog feed failed: %s", exc)
        if fail_soft:
            return []
        raise

    root = ElementTree.fromstring(xml_text)
    channel = root.find("channel")
    nodes = list(root.findall(".//item"))
    if channel is not None:
        nodes = list(channel.findall("item")) or nodes

    items: List[CSOfficialBlogItem] = []
    for node in nodes:
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        pub_raw = node.findtext("pubDate") or node.findtext("published") or ""
        desc = node.findtext("description") or node.findtext("{*}encoded") or ""
        pub_dt = _parse_rss_date(pub_raw)
        if not _within_days(pub_dt, max_age_days):
            continue
        if not title and not link:
            continue
        items.append(
            CSOfficialBlogItem(
                title=title or link,
                url=link,
                published_date=pub_dt.strftime("%Y-%m-%d") if pub_dt else pub_raw[:10] or None,
                snippet=_strip_html(desc) or "Valve CS 官方博客",
            )
        )
        if len(items) >= max_items:
            break

    logger.info("CS official blog RSS: %s items", len(items))
    return items
