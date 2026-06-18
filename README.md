# Brave Search URL Submit Manager

Streamlit app for collecting, validating, queueing, and tracking URLs for Brave Search submission.

This app uses an assisted workflow. It opens Brave submission and `site:` search links, then lets you record status in Streamlit session memory. It does not bypass CAPTCHA, automate hidden browser sessions, or mass-submit URLs.

## Features

- Add URLs manually.
- Upload CSV files.
- Import `sitemap.xml`.
- Guided workflow: import URLs, review queue, choose submission method, export report.
- Normalize, validate, and deduplicate URLs.
- Track submit status and index status.
- Open Brave submit and index-check links.
- Optional auto-submit with Playwright. Local runs can show Chrome; Community Cloud runs headless.
- Export CSV reports.
- No local database. URL queue lives in current Streamlit browser session memory.

## Run

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Use Python 3.12 locally. Python 3.14 can break Streamlit/protobuf imports on macOS.

Auto-submit uses Playwright with a visible browser and stops on CAPTCHA, verification, blocked access, or missing form fields. If Playwright browsers are not installed, the app can use local Google Chrome at:

```text
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

On Streamlit Community Cloud, `packages.txt` installs Linux Chromium and the app uses `/usr/bin/chromium` in headless mode.

## Deploy To Streamlit Community Cloud

1. Push this folder to GitHub.
2. In Streamlit Community Cloud, create a new app from the GitHub repo.
3. Set main file path to:

```text
app.py
```

4. Keep these files in repo root:

```text
requirements.txt
packages.txt
runtime.txt
.streamlit/config.toml
```

5. Deploy.

Community Cloud notes:

- Session memory resets when the app restarts.
- Auto Submit runs server-side in headless Chromium.
- Brave may block automated submission or show challenges; the app stops instead of bypassing them.

## Data

No local database is used. URLs live in Streamlit session state and disappear when the app session resets. Export CSV before closing if you need a report.

## Workflow

1. Add URLs manually, upload CSV, or import sitemap.
2. Review all collected URLs in URL Queue.
3. Choose Manual Submission or Auto Submit.
4. Export final CSV report.

## Project Structure

```text
brave-url-submit-manager/
  app.py
  requirements.txt
  README.md
  data/
    .gitkeep
  services/
    __init__.py
    brave_links.py
    sitemap_parser.py
    url_tools.py
```
