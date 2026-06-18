# 🔎 Brave Search URL Submit Manager

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Community%20Cloud-red)](https://streamlit.io/)
[![Playwright](https://img.shields.io/badge/Playwright-Auto%20Submit-green)](https://playwright.dev/python/)
[![License](https://img.shields.io/badge/License-MIT-green)](https://opensource.org/license/mit/)
[![Live App](https://img.shields.io/badge/Live%20App-Open-brightgreen)](https://brave-search-url-submit-manager.streamlit.app/)

**Brave Search URL Submit Manager** is a guided web app for importing, reviewing, submitting, and tracking URLs for Brave Search. Add URLs manually, upload CSV files, import a sitemap, review your queue, choose manual or automated submission, and export a clean CSV report.

🔗 **Live App:** [https://brave-search-url-submit-manager.streamlit.app/](https://brave-search-url-submit-manager.streamlit.app/)

![URL Queue](https://img.shields.io/badge/URL%20Queue-Session%20Based-blue)
![Sitemap Import](https://img.shields.io/badge/Sitemap-Import-orange)
![CSV Reports](https://img.shields.io/badge/Reports-CSV-brightgreen)

## ✨ Key Features

### 🚀 **Guided Submission Workflow**
- 📥 **Import URLs** - Add URLs manually, upload CSV files, or import `sitemap.xml`
- 📋 **Review Queue** - See every normalized URL before submitting
- 🧹 **Clean URLs** - Validate, normalize, and remove duplicates automatically
- 🧭 **Step-by-step Flow** - Import URLs → URL Queue → Submit → Report
- 📊 **Progress Summary** - Track total, pending, and submitted URLs in the sidebar

### 🔍 **Brave Search Submission Tools**
- 🖱️ **Manual Submission** - Open Brave's submit page and manage status yourself
- ⚙️ **Auto Submit** - Use Playwright automation to submit queued URLs
- 🛑 **Challenge Safety** - Stops if Brave shows CAPTCHA, verification, or access blocks
- ⏱️ **Delay Controls** - Add time between submissions to reduce aggressive behavior
- 🌐 **Index Check Links** - Open Brave `site:` search checks for each URL or domain

### 📄 **Reporting**
- ✅ **Submission Status** - Track pending, submitted, failed, skipped, indexed, or not indexed
- 📝 **Notes Field** - Store messages, errors, or manual review notes
- 📥 **CSV Export** - Download final status report for client or internal records
- 🧠 **Session Memory** - No local database required; export before closing or reset

### ☁️ **Cloud-ready**
- 🚀 **Streamlit Community Cloud Ready** - Includes `runtime.txt`, `packages.txt`, and `.streamlit/config.toml`
- 🐧 **Linux Chromium Support** - Uses `/usr/bin/chromium` in cloud deployments
- 💻 **Local Chrome Support** - Uses Google Chrome on macOS when available
- 🔐 **No Secrets Required** - No API keys or credentials needed

## 🚀 Quick Start

### Prerequisites
- Python 3.12
- pip package manager
- Google Chrome for local visible-browser auto-submit

> Python 3.14 can break Streamlit/protobuf imports on macOS. Use Python 3.12 locally.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dhruvpandyadp/brave-search-url-submit-manager.git
   ```
   ```bash
   cd brave-search-url-submit-manager
   ```

2. **Create a virtual environment:**
   ```bash
   python3.12 -m venv .venv
   ```
   ```bash
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   python -m pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** and go to `http://localhost:8501`

## 💻 Usage

1. **Add URLs**
   - Paste URLs manually
   - Upload a CSV file
   - Import a sitemap URL such as `https://example.com/sitemap.xml`

2. **Review URL Queue**
   - Confirm all URLs were imported correctly
   - Search or filter the queue
   - Edit submission/index status if needed

3. **Choose Submission Method**
   - Use **Manual Submission** for full control
   - Use **Auto Submit** for Playwright-powered browser automation

4. **Export Report**
   - Review final status table
   - Download CSV report
   - Start a new session when finished

## 📊 Workflow Overview

| Step | Screen | Purpose |
|------|--------|---------|
| 1 | Import URLs | Add manual URLs, CSV URLs, or sitemap URLs |
| 2 | URL Queue | Review, filter, and edit collected URLs |
| 3 | Submit | Choose manual submission or auto-submit |
| 4 | Report | Export final CSV status report |

## ⚙️ Auto Submit Behavior

Auto Submit uses Playwright to control a browser session.

### Local Runs
- Uses local Google Chrome when available
- Can run with visible browser window
- Opens Chrome once per batch
- Submits URLs one by one with delay

### Streamlit Community Cloud
- Uses Linux Chromium from `packages.txt`
- Runs in headless mode
- Cannot show a visible browser window
- May be blocked if Brave detects automated server-side traffic

### Safety Rules
- Does not bypass CAPTCHA
- Does not bypass verification challenges
- Stops if Brave shows access-control text
- Stores debug HTML/screenshot files only when failures happen


## 🛠️ Technical Details

### Built With
- **[Streamlit](https://streamlit.io/)** - Web app framework
- **[Playwright](https://playwright.dev/python/)** - Browser automation for auto-submit
- **[pandas](https://pandas.pydata.org/)** - CSV import/export and table handling
- **[requests](https://requests.readthedocs.io/)** - Sitemap fetching
- **[Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)** - HTML/XML support
- **Python 3.12** - Runtime for local and cloud deployment

### Architecture
- **Session State Queue** - Stores URLs in browser session memory
- **URL Tools** - Normalizes URLs, removes fragments, filters tracking parameters
- **Sitemap Parser** - Extracts URLs from XML sitemap files
- **Brave Link Helpers** - Generates submit and `site:` search URLs
- **Brave Submitter** - Handles Playwright-based auto-submit logic

### Project Structure

```text
brave-search-url-submit-manager/
  app.py
  requirements.txt
  packages.txt
  runtime.txt
  README.md
  services/
    __init__.py
    brave_links.py
    brave_submitter.py
    sitemap_parser.py
    url_tools.py
```

## 📱 Browser Support

| Browser | Manual Workflow | CSV Export | Auto Submit Local |
|---------|-----------------|------------|-------------------|
| Chrome | ✅ Full | ✅ Full | ✅ Full |
| Firefox | ✅ Full | ✅ Full | Browser automation still uses Chrome/Chromium |
| Safari | ✅ Full | ✅ Full | Browser automation still uses Chrome/Chromium |
| Edge | ✅ Full | ✅ Full | Browser automation still uses Chrome/Chromium |
| Mobile Browser | ✅ Responsive | ✅ Full | Not recommended |

## 🎯 Use Cases

### **New Website Launch**
```text
Scenario: New site or redesigned site needs URL discovery support
Action: Import sitemap and submit important URLs
Result: Track which URLs were submitted
Benefit: Cleaner launch checklist for search visibility
```

### **Client SEO Workflow**
```text
Scenario: Agency needs proof of submitted pages
Action: Queue URLs, submit them, export CSV report
Result: Share status report with client
Benefit: Transparent submission workflow
```

### **Index Monitoring**
```text
Scenario: Check whether URLs appear in Brave Search
Action: Use generated Brave site-search links
Result: Mark indexed or not indexed manually
Benefit: Lightweight tracking without database overhead
```

## ⚠️ Important Notes

- Brave may limit, block, or challenge automated submissions.
- Auto Submit is best-effort automation, not guaranteed indexing.
- This app does not provide a Brave API or indexing guarantee.
- No local database is used; export CSV before closing the session.
- Community Cloud sessions can reset at any time.

## 📜 License

This project is licensed under the MIT License.

## 👨‍💻 Author

**Created by Dhruv Pandya**

- GitHub: [@dhruvpandyadp](https://github.com/dhruvpandyadp)
- LinkedIn: [Dhruv Pandya](https://linkedin.com/in/dhruvpandyadp)

## 🙏 Acknowledgments

- Streamlit team for the web app framework
- Playwright team for browser automation tooling
- Brave Search for providing a public URL submission page
- Open source community for feedback and inspiration

---

## 🚀 Ready To Submit URLs?

Use the live app:

[https://brave-search-url-submit-manager.streamlit.app/](https://brave-search-url-submit-manager.streamlit.app/)

```bash
# Run locally
git clone https://github.com/dhruvpandyadp/brave-search-url-submit-manager.git
cd brave-search-url-submit-manager
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

### What You Get
- ⚡ **Fast URL Imports** from manual input, CSV, and sitemap
- 📋 **Clear Queue Review** before submission
- ⚙️ **Manual or Auto Submit** options
- 📊 **Downloadable Reports** for submission tracking
