#!/usr/bin/env python3
"""Optional headless-render fetch for JS/bot-walled sources.

Isolated on purpose. The main scanner and the validator's core logic never
import this module; it is loaded lazily and only by the headless code paths. If
Playwright is not installed, render() raises HeadlessUnavailable and every caller
treats that exactly like a failed fetch — so the absence of a browser can never
break the offline pipeline or the self-test.
"""

class HeadlessUnavailable(Exception):
    pass


def available():
    try:
        import playwright  # noqa: F401
        return True
    except Exception:
        return False


def render(url, timeout=45, wait="domcontentloaded", wait_selector=None,
           settle_ms=2500):
    """Return fully-rendered HTML for url, or raise HeadlessUnavailable / Exception.

    Hardened for the sources that failed a first pass:
      - HTTP/1.1 only (``--disable-http2``): several government / airline CDNs
        return net::ERR_HTTP2_PROTOCOL_ERROR to headless Chromium over h2 while
        serving fine over h1 (Smartraveller, Turkish Airlines).
      - Longer default timeout (45s) for slow gov origins.
      - After navigation, wait for network idle (best-effort) and a settle pause
        so client-rendered lists finish injecting before we read the DOM.
      - Optional ``wait_selector`` to block on a known list container.
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
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=8000)
                except Exception:
                    pass
            else:
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass
            try:
                page.wait_for_timeout(settle_ms)
            except Exception:
                pass
            return page.content()
        finally:
            browser.close()
