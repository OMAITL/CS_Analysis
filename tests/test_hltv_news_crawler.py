# -*- coding: utf-8 -*-
"""Offline tests for HLTV news parsing."""

from __future__ import annotations

from crawlers.hltv.news_crawler import (
    _parse_news_index,
    _parse_news_sitemap,
)


SAMPLE_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.hltv.org/news/12345/cs2-major-update</loc>
    <lastmod>2026-06-01</lastmod>
  </url>
  <url>
    <loc>https://www.hltv.org/news/99999/old-post</loc>
    <lastmod>2020-01-01</lastmod>
  </url>
</urlset>
"""

SAMPLE_INDEX = """
<a href="/news/55555/team-wins-event">Winner</a>
<a href="/news/55555/team-wins-event">dup</a>
"""


def test_parse_news_sitemap_filters_age():
    items = _parse_news_sitemap(SAMPLE_SITEMAP, max_items=10, max_age_days=30)
    assert len(items) == 1
    assert "12345" in items[0].url
    assert "major" in items[0].title.lower()


def test_parse_news_index_dedupes():
    items = _parse_news_index(SAMPLE_INDEX, max_items=5)
    assert len(items) == 1
    assert items[0].url.endswith("/team-wins-event")
