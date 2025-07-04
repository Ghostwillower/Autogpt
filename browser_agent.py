"""Browser automation helpers using Playwright."""

from typing import Dict, List

from logger import log


def run_browser_task(task: Dict) -> str:
    """Execute a list of browser actions using Playwright.

    ``task`` should contain a ``steps`` list with dictionaries describing
    each action.
    """
    log("Starting browser task", "WEB")
    steps = task.get("steps", [])
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as exc:
        log(f"Playwright not available: {exc}", "ERROR")
        return "Browser automation unavailable"

    actions_log: List[str] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for step in steps:
                action = step.get("action")
                if action == "go_to":
                    url = step.get("url", "")
                    page.goto(url, timeout=30000)
                    actions_log.append(f"Visited {url}")
                elif action == "click":
                    page.click(step.get("selector"), timeout=30000)
                    actions_log.append(f"Clicked {step.get('selector')}")
                elif action == "fill":
                    page.fill(step.get("selector"), step.get("value", ""), timeout=30000)
                    actions_log.append(f"Filled {step.get('selector')}")
                else:
                    actions_log.append(f"Unknown action {action}")
            browser.close()
        log("Browser task complete", "WEB")
        return "; ".join(actions_log)
    except Exception as exc:
        log(f"Browser task failed: {exc}", "ERROR")
        return "Browser task failed"
