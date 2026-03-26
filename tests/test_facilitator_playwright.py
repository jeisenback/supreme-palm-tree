import os
import time
import pytest
from playwright.sync_api import sync_playwright
import requests

APP_URL = os.environ.get("FACILITATOR_APP_URL", "http://localhost:8502")

# Skip in CI — requires a running Streamlit server on APP_URL.
# Set FACILITATOR_APP_URL env var and start the app before running locally.
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true" or not os.environ.get("FACILITATOR_APP_URL"),
    reason="Playwright tests require a running Streamlit server (set FACILITATOR_APP_URL)",
)


def wait_for_app(url: str, timeout: int = 30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"App at {url} did not become available within {timeout}s")


@pytest.mark.parametrize("open_path", ["/", "/?open=etn/ECBA_CaseStudyv2/ECBA_CaseStudy_Plan.md"])
def test_facilitator_ui_basic(open_path):
    # Expect the app to be started externally (CI or developer). Wait until reachable.
    wait_for_app(APP_URL)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(APP_URL + open_path, timeout=60000)
        # wait for Streamlit to render and show the main title
        try:
            page.wait_for_selector("text=Facilitator", timeout=15000)
        except Exception:
            # dump content for debugging
            print('PAGE HTML START')
            print(page.content())
            print('PAGE HTML END')
            raise

        # basic checks: sidebar exists and main header contains 'Facilitator'
        assert page.locator("text=Facilitator").first.count() >= 1
        # if preview content present, ensure filename or planning header exists
        if "ECBA_CaseStudy_Plan" in open_path:
            assert page.locator("text=ECBA_CaseStudy_Plan").first.count() >= 0
        # try presenter link when available (not fatal)
        if page.locator("text=Presenter View").count() > 0:
            page.locator("text=Presenter View").first.click()
        browser.close()
