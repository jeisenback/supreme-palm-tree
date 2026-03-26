Run Playwright UI tests (requires Playwright installed in venv)

1. Install packages into the project venv:

```bash
c:/tools/nonprofit_tool/.venv/Scripts/python.exe -m pip install -r requirements-playwright.txt
c:/tools/nonprofit_tool/.venv/Scripts/python.exe -m playwright install
```

2. Run tests:

```bash
Ensure the Streamlit app is running (e.g. `streamlit run apps/facilitator_ui.py --server.port 8502`), then run:

```bash
pytest tests/test_facilitator_playwright.py -q
```
```

Notes:
- The test script starts a Streamlit process and then runs a simple Playwright browser check. Adjust timeouts as needed.
- On CI, prefer running the app separately and point `FACILITATOR_APP_URL` to the app URL instead of letting the test start a process.
