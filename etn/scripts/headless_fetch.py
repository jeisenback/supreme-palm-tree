from playwright.sync_api import sync_playwright
from pathlib import Path

TARGETS = [
    ("https://easttennessee.iiba.org/events/annual-general-meeting-2025/", "annual-general-meeting-2025-headless.html"),
    ("https://web.membernova.com/400592/Events/babok-study-session-baccm-bapm", "babok-study-session-baccm-bapm-headless.html"),
    ("https://web.membernova.com/400592/Events/interviewing-skills-for-bas", "interviewing-skills-for-bas-headless.html"),
    ("https://easttennessee.iiba.org/events/the-project-manager%E2%80%93business-analyst-partners/", "project-manager-business-analyst-partnership-headless.html"),
    ("https://easttennessee.iiba.org/Events/testing", "requirements-life-cycle-management-headless.html"),
    ("https://web.membernova.com/400592/Events/study-session-agile-and-product-ownership-ana", "study-session-agile-product-ownership-headless.html"),
    ("https://web.membernova.com/400592/Events/study-session-elicitation-and-collaboration", "study-session-elicitation-and-collaboration-headless.html"),
]
OUT_DIR = Path(__file__).resolve().parents[1] / 'outputs' / 'event_pages'
OUT_DIR.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    for url, name in TARGETS:
        out = OUT_DIR / name
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state('networkidle', timeout=30000)
            # extra wait in case of JS
            page.wait_for_timeout(1500)
            html = page.content()
            out.write_text(html, encoding='utf-8')
            print('Saved', out)
        except Exception as e:
            out.write_text(f"ERROR: {e}", encoding='utf-8')
            print('Failed', url, e)
    browser.close()
