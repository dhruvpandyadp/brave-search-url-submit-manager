from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import time

from services.brave_links import submit_url


CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
]
DEFAULT_CHROME_PATH = next((path for path in CHROME_PATHS if Path(path).exists()), CHROME_PATHS[0])
DEBUG_DIR = Path(__file__).resolve().parents[1] / "data" / "debug"
CHALLENGE_PATTERN = re.compile(
    r"captcha|robot|verify|verification|challenge|unusual traffic|blocked|access denied",
    re.IGNORECASE,
)
SUCCESS_PATTERN = re.compile(r"submitted|success|received|thank", re.IGNORECASE)


@dataclass(frozen=True)
class SubmitResult:
    url: str
    status: str
    message: str


def playwright_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
    except Exception:
        return False
    return True


def chrome_path_available(path: str = DEFAULT_CHROME_PATH) -> bool:
    return Path(path).exists()


def chrome_launch_kwargs(chrome_path: str, headless: bool) -> dict[str, object]:
    launch_kwargs: dict[str, object] = {
        "headless": headless,
        "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    }
    if chrome_path and Path(chrome_path).exists():
        launch_kwargs["executable_path"] = chrome_path
    return launch_kwargs


def submit_one_url(
    url: str,
    chrome_path: str = DEFAULT_CHROME_PATH,
    headless: bool = False,
    timeout_ms: int = 30000,
    pause_seconds: float = 1.5,
) -> SubmitResult:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return SubmitResult(url, "failed", f"Playwright not installed: {exc}")

    launch_kwargs = chrome_launch_kwargs(chrome_path, headless)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            result = _submit_with_page(page, url, timeout_ms, pause_seconds)
            browser.close()
            return result
    except PlaywrightTimeoutError as exc:
        return SubmitResult(url, "failed", f"Timeout: {exc}")
    except Exception as exc:
        return SubmitResult(url, "failed", str(exc))


def submit_urls_in_one_browser(
    urls: list[str],
    chrome_path: str = DEFAULT_CHROME_PATH,
    headless: bool = False,
    timeout_ms: int = 30000,
    pause_seconds: float = 1.5,
) -> list[SubmitResult]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return [SubmitResult(url, "failed", f"Playwright not installed: {exc}") for url in urls]

    launch_kwargs = chrome_launch_kwargs(chrome_path, headless)

    results: list[SubmitResult] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            for url in urls:
                try:
                    result = _submit_with_page(page, url, timeout_ms, pause_seconds)
                except PlaywrightTimeoutError as exc:
                    result = SubmitResult(url, "failed", f"Timeout: {exc}")
                except Exception as exc:
                    result = SubmitResult(url, "failed", str(exc))
                results.append(result)
                if result.status == "blocked":
                    break
                if pause_seconds:
                    time.sleep(pause_seconds)
        finally:
            try:
                browser.close()
            except Exception:
                pass
    return results


def _submit_with_page(page, url: str, timeout_ms: int, pause_seconds: float) -> SubmitResult:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    page.goto(submit_url(), wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(3000)

    body_text = page.locator("body").inner_text(timeout=timeout_ms)
    if CHALLENGE_PATTERN.search(body_text):
        _save_debug(page, "blocked-before")
        return SubmitResult(url, "blocked", "Challenge or access-control text detected before submit.")

    field_selector = (
        'input[type="url"], '
        'input[name*="url" i], '
        'input[id*="url" i], '
        'input[placeholder*="url" i], '
        'input[aria-label*="url" i], '
        'textarea[name*="url" i], '
        'textarea[id*="url" i], '
        'textarea[placeholder*="url" i], '
        'textarea[aria-label*="url" i], '
        'input[type="text"], '
        "textarea"
    )
    try:
        page.wait_for_selector(field_selector, timeout=timeout_ms)
    except PlaywrightTimeoutError:
        debug_path = _save_debug(page, "field-missing")
        return SubmitResult(url, "failed", f"URL field not found on Brave submit page. Debug: {debug_path}")

    field = page.locator(field_selector).first
    field.fill(url, timeout=timeout_ms)
    time.sleep(pause_seconds)

    button = page.get_by_role("button", name=re.compile(r"submit|send|add", re.IGNORECASE)).first
    if button.count() == 0:
        button = page.locator('button[type="submit"], input[type="submit"]').first
    if button.count() == 0:
        debug_path = _save_debug(page, "button-missing")
        return SubmitResult(url, "failed", f"Submit button not found on Brave submit page. Debug: {debug_path}")

    button.click(timeout=timeout_ms)
    page.wait_for_timeout(int(pause_seconds * 1000))

    body_text = page.locator("body").inner_text(timeout=timeout_ms)
    if CHALLENGE_PATTERN.search(body_text):
        _save_debug(page, "blocked-after")
        return SubmitResult(url, "blocked", "Challenge or access-control text detected after submit.")
    if SUCCESS_PATTERN.search(body_text):
        return SubmitResult(url, "submitted", "Brave page showed success/submitted text.")
    return SubmitResult(url, "submitted", "Submit button clicked. No challenge detected.")


def _save_debug(page, label: str) -> str:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = DEBUG_DIR / f"{stamp}-{label}"
    html_path = base.with_suffix(".html")
    png_path = base.with_suffix(".png")
    try:
        html_path.write_text(page.content(), encoding="utf-8")
    except Exception:
        pass
    try:
        page.screenshot(path=str(png_path), full_page=True)
    except Exception:
        pass
    return str(html_path)
