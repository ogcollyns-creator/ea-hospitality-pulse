#!/usr/bin/env python3
"""Optional headless-render fetch for JS/bot-walled sources.

Isolated on purpose. The main scanner and the validator's core logic never
import this module; it is loaded lazily and only by the --probe-headless
diagnostic. If Playwright is not installed, render() raises HeadlessUnavailable
and every caller treats that exactly like a failed fetch — so the absence of a
browser can never break the offline pipeline or the self-test.

This exists to answer one question honestly, on a live-network runner: *would* a
rendered fetch of a JS-walled source yield real items? It does NOT write to the
registry. Promoting a headless source into production requires the production
scanner to render it too, which is a separate, deliberate change.
"""

class HeadlessUnavailable(Exception):
    pass


def available():
    try:
        import playwright  # noqa: F401
        return True
    except Exception:
        return False


def render(url, timeout=30, wait="domcontentloaded"):
    """Return fully-rendered HTML for url, or raise HeadlessUnavailable / Exception.

    Uses a real Chromium so client-rendered pages and soft bot walls resolve the
    same way they do for a human. Polite: single navigation, no crawling here.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        raise HeadlessUnavailable(str(e))
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        try:
            ctx = browser.new_context(user_agent=ua, locale="en-GB")
            page = ctx.new_page()
            page.goto(url, timeout=timeout * 1000, wait_until=wait)
            try:
                page.wait_for_timeout(1500)  # let late XHR content settle
            except Exception:
                pass
            return page.content()
        finally:
            browser.close()
