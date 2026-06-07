# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import setup_env

setup_env()

from playwright.sync_api import sync_playwright

hits = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    def on_resp(r):
        u = r.url
        if any(k in u.lower() for k in ("good", "search", "suggest")):
            hits.append((r.status, u))

    page.on("response", on_resp)
    page.goto("https://csqaq.com/home", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    loc = page.locator("input").first
    if loc.count() > 0:
        loc.fill("M4A1 闪回", timeout=5000)
        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)
    browser.close()

print("hits", len(hits))
for status, url in hits[:20]:
    print(status, url)
