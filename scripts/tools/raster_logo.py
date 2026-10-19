"""Rastert assets/brand/logo.svg in Weiß und Slate (1200 px breit, transparent).

Aufruf: python3 scripts/tools/raster_logo.py
"""
import pathlib

from playwright.sync_api import sync_playwright

REPO = pathlib.Path(__file__).resolve().parents[2]
BRAND = REPO / "skill" / "flaesh-campus" / "assets" / "brand"
WIDTH = 1200
VARIANTS = {"logo-white.png": "#FFFFFF", "logo-slate.png": "#5D6C73"}


def main() -> None:
    svg = (BRAND / "logo.svg").read_text(encoding="utf-8")
    height = round(WIDTH * 252 / 595.3)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": height})
        for name, color in VARIANTS.items():
            colored = svg.replace("currentColor", color)
            html = (f"<!doctype html><html><body style='margin:0;background:transparent'>"
                    f"<div style='width:{WIDTH}px;height:{height}px'>{colored}</div></body></html>")
            page.set_content(html)
            page.locator("svg").evaluate(f"el => {{ el.setAttribute('width', {WIDTH}); el.setAttribute('height', {height}); }}")
            page.locator("div").screenshot(path=str(BRAND / name), omit_background=True)
        browser.close()


if __name__ == "__main__":
    main()
