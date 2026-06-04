"""Probe CSQAQ goods page K-line API when switching to daily chart."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

GOOD_ID = 769
URL = f"https://csqaq.com/goods/{GOOD_ID}"


def main() -> None:
    hits: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1600, "height": 1000})

        def on_request(req):
            u = req.url
            if any(x in u for x in ("chart", "kline", "Chart")):
                hits.append({"phase": "req", "url": u, "method": req.method, "post": req.post_data})

        def on_response(resp):
            u = resp.url
            if resp.status != 200:
                return
            if not any(x in u for x in ("chart", "kline", "Chart")):
                return
            try:
                body = resp.json()
            except Exception:
                return
            data = body.get("data")
            summary = {"phase": "resp", "url": u, "code": body.get("code")}
            if isinstance(data, list) and data and isinstance(data[0], dict) and "v" in data[0]:
                summary["rows"] = len(data)
                summary["nz_v"] = sum(1 for x in data if int(x.get("v") or 0) > 0)
                summary["tail"] = data[-3:]
            elif isinstance(data, dict):
                summary["keys"] = list(data.keys())
                md = data.get("main_data")
                if isinstance(md, list) and md:
                    summary["main_len"] = len(md)
                    summary["main_tail"] = md[-2:]
            hits.append(summary)

        page.on("request", on_request)
        page.on("response", on_response)
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(5000)

        # try click 日线
        for sel in [
            "text=日线",
            "button:has-text('日线')",
            "[class*='day']",
        ]:
            loc = page.locator(sel)
            if loc.count() > 0:
                try:
                    loc.first.click(timeout=3000)
                    page.wait_for_timeout(5000)
                    print("clicked", sel)
                    break
                except Exception as exc:
                    print("click fail", sel, exc)

        # try 切换常规图 / K线 related buttons
        for text in ("K线", "切换", "常规"):
            loc = page.get_by_text(text, exact=False)
            if loc.count() > 0:
                try:
                    loc.first.click(timeout=2000)
                    page.wait_for_timeout(3000)
                    print("clicked text", text)
                except Exception:
                    pass

        page.wait_for_timeout(5000)
        browser.close()

    out = ROOT / "data" / "_probe_goods_kline_hits.json"
    out.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", out, "hits", len(hits))
    for h in hits:
        print(json.dumps(h, ensure_ascii=False)[:500])


if __name__ == "__main__":
    main()
