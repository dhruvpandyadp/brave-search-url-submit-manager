from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from services.brave_links import domain_search_url, site_search_url, submit_url
from services.brave_submitter import (
    DEFAULT_CHROME_PATH,
    chrome_path_available,
    playwright_available,
    submit_urls_in_one_browser,
)
from services.sitemap_parser import load_sitemap
from services.url_tools import normalize_url, parse_url_lines


SUBMIT_STATUSES = ["pending", "submitted", "failed", "skipped"]
INDEX_STATUSES = ["unknown", "indexed", "not indexed"]
QUEUE_COLUMNS = [
    "id",
    "url",
    "domain",
    "source",
    "submit_status",
    "index_status",
    "created_at",
    "last_submitted_at",
    "last_checked_at",
    "notes",
]
WORKFLOW_STEPS = ["Import URLs", "URL Queue", "Submit", "Report"]


st.set_page_config(
    page_title="Brave Search URL Submit Manager",
    page_icon="B",
    layout="wide",
)


st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetric"] {
        border: 1px solid #d8dee8;
        border-radius: 8px;
        padding: 12px 14px;
        background: #fbfcfe;
    }
    .small-note {
        color: #5f6b7a;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_queue() -> None:
    if "urls" not in st.session_state:
        st.session_state.urls = []
    if "next_id" not in st.session_state:
        st.session_state.next_id = 1
    if "current_step" not in st.session_state:
        st.session_state.current_step = "Import URLs"


def queue_df() -> pd.DataFrame:
    init_queue()
    return pd.DataFrame(st.session_state.urls, columns=QUEUE_COLUMNS)


def add_urls(items: list[dict[str, str]]) -> tuple[int, int]:
    init_queue()
    existing = {item["url"] for item in st.session_state.urls}
    inserted = 0
    duplicates = 0

    for item in items:
        if item["url"] in existing:
            duplicates += 1
            continue

        st.session_state.urls.append(
            {
                "id": st.session_state.next_id,
                "url": item["url"],
                "domain": item["domain"],
                "source": item.get("source", "manual"),
                "submit_status": "pending",
                "index_status": "unknown",
                "created_at": now_stamp(),
                "last_submitted_at": "",
                "last_checked_at": "",
                "notes": item.get("notes", ""),
            }
        )
        st.session_state.next_id += 1
        existing.add(item["url"])
        inserted += 1

    return inserted, duplicates


def get_urls(
    submit_status: str | None = None,
    index_status: str | None = None,
    search: str | None = None,
) -> pd.DataFrame:
    df = queue_df()
    if df.empty:
        return df

    if submit_status and submit_status != "all":
        df = df[df["submit_status"] == submit_status]
    if index_status and index_status != "all":
        df = df[df["index_status"] == index_status]
    if search:
        term = search.lower()
        df = df[
            df["url"].str.lower().str.contains(term, na=False)
            | df["domain"].str.lower().str.contains(term, na=False)
            | df["notes"].str.lower().str.contains(term, na=False)
        ]

    return df.sort_values(["created_at", "id"], ascending=[False, False]).reset_index(drop=True)


def update_url(row_id: int, submit_status: str, index_status: str, notes: str) -> None:
    init_queue()
    for item in st.session_state.urls:
        if item["id"] != row_id:
            continue
        item["submit_status"] = submit_status
        item["index_status"] = index_status
        item["notes"] = notes
        if submit_status == "submitted":
            item["last_submitted_at"] = now_stamp()
        if index_status in {"indexed", "not indexed"}:
            item["last_checked_at"] = now_stamp()
        break


def update_submit_result(row_id: int, submit_status: str, message: str) -> None:
    init_queue()
    for item in st.session_state.urls:
        if item["id"] != row_id:
            continue
        item["submit_status"] = submit_status
        item["notes"] = message if not item["notes"] else f"{item['notes']}\n{message}"
        if submit_status == "submitted":
            item["last_submitted_at"] = now_stamp()
        break


def reset_failed_urls() -> int:
    init_queue()
    count = 0
    for item in st.session_state.urls:
        if item["submit_status"] == "failed":
            item["submit_status"] = "pending"
            item["notes"] = item["notes"] + "\nReset failed URLs to pending." if item["notes"] else "Reset failed URLs to pending."
            count += 1
    return count


def delete_url(row_id: int) -> None:
    init_queue()
    st.session_state.urls = [item for item in st.session_state.urls if item["id"] != row_id]


def stats() -> dict[str, int]:
    df = queue_df()
    if df.empty:
        return {"total": 0, "pending": 0, "submitted": 0, "indexed": 0}
    return {
        "total": len(df),
        "pending": int((df["submit_status"] == "pending").sum()),
        "submitted": int((df["submit_status"] == "submitted").sum()),
        "indexed": int((df["index_status"] == "indexed").sum()),
    }


def build_items(raw_urls: list[str], source: str) -> tuple[list[dict[str, str]], list[str]]:
    items: list[dict[str, str]] = []
    errors: list[str] = []
    seen: set[str] = set()

    for raw_url in raw_urls:
        result = normalize_url(raw_url)
        if not result.is_valid:
            errors.append(f"{result.original}: {result.error}")
            continue
        if result.url in seen:
            continue
        seen.add(result.url)
        items.append({"url": result.url, "domain": result.domain, "source": source})

    return items, errors


def add_url_batch(raw_urls: list[str], source: str) -> None:
    items, errors = build_items(raw_urls, source)
    inserted, duplicates = add_urls(items)

    if inserted:
        st.success(f"Added {inserted} URLs.")
    if duplicates:
        st.info(f"Skipped {duplicates} existing URLs.")
    if errors:
        with st.expander(f"{len(errors)} invalid URLs"):
            st.write("\n".join(errors))
    if not inserted and not duplicates and not errors:
        st.warning("No URLs found.")


def go_to_step(step: str) -> None:
    st.session_state.current_step = step
    st.rerun()


def render_stepper() -> None:
    current_index = WORKFLOW_STEPS.index(st.session_state.current_step)
    cols = st.columns(len(WORKFLOW_STEPS))
    for index, step in enumerate(WORKFLOW_STEPS):
        label = f"{index + 1}. {step}"
        if index == current_index:
            cols[index].button(label, type="primary", disabled=True, width="stretch")
        else:
            if cols[index].button(label, disabled=index > current_index + 1, width="stretch"):
                go_to_step(step)


def render_import_step() -> None:
    st.subheader("Add URLs Or Import Sitemap")
    st.markdown(
        '<p class="small-note">Start by adding URLs manually, uploading CSV, or importing sitemap.xml.</p>',
        unsafe_allow_html=True,
    )

    manual_tab, csv_tab, sitemap_tab = st.tabs(["Manual URLs", "CSV Upload", "Sitemap"])

    with manual_tab:
        manual = st.text_area("One URL per line", height=180, placeholder="https://example.com/page")
        if st.button("Add Manual URLs", type="primary"):
            add_url_batch(parse_url_lines(manual), "manual")

    with csv_tab:
        upload = st.file_uploader("Upload CSV", type=["csv"])
        if upload is not None:
            frame = pd.read_csv(upload)
            st.dataframe(frame.head(20), width="stretch", hide_index=True)
            url_column = st.selectbox("URL column", frame.columns)
            if st.button("Import CSV URLs"):
                add_url_batch(frame[url_column].dropna().astype(str).tolist(), "csv")

    with sitemap_tab:
        sitemap = st.text_input("Sitemap URL or local XML path", placeholder="https://example.com/sitemap.xml")
        if st.button("Import Sitemap", type="primary"):
            try:
                urls = load_sitemap(sitemap)
                add_url_batch(urls, "sitemap")
            except Exception as exc:
                st.error(f"Sitemap import failed: {exc}")

    df = get_urls()
    if not df.empty:
        st.divider()
        st.success(f"{len(df)} URLs ready for review.")
        if st.button("Review URL Queue", type="primary", width="stretch", key="review_queue_bottom"):
            go_to_step("URL Queue")


def status_editor(row: pd.Series) -> None:
    with st.form(f"edit-{row['id']}"):
        submit_status = st.selectbox(
            "Submit status",
            SUBMIT_STATUSES,
            index=SUBMIT_STATUSES.index(row["submit_status"]),
        )
        index_status = st.selectbox(
            "Index status",
            INDEX_STATUSES,
            index=INDEX_STATUSES.index(row["index_status"]),
        )
        notes = st.text_area("Notes", value=row["notes"] or "", height=90)
        col_a, col_b = st.columns(2)
        saved = col_a.form_submit_button("Save", width='stretch')
        removed = col_b.form_submit_button("Delete", width='stretch')

    if saved:
        update_url(int(row["id"]), submit_status, index_status, notes)
        st.success("Saved.")
        st.rerun()
    if removed:
        delete_url(int(row["id"]))
        st.warning("Deleted.")
        st.rerun()


def render_dashboard() -> None:
    current = stats()
    col_1, col_2, col_3, col_4 = st.columns(4)
    col_1.metric("Total URLs", current["total"])
    col_2.metric("Pending", current["pending"])
    col_3.metric("Submitted", current["submitted"])
    col_4.metric("Indexed", current["indexed"])

    st.subheader("Recent Queue")
    df = get_urls()
    if df.empty:
        st.info("Add URLs to start queue.")
        return
    st.dataframe(
        df[["url", "domain", "source", "submit_status", "index_status", "created_at"]],
        width='stretch',
        hide_index=True,
    )


def render_add_urls() -> None:
    st.subheader("Add URLs")
    manual = st.text_area("One URL per line", height=180, placeholder="https://example.com/page")
    if st.button("Add Manual URLs", type="primary"):
        add_url_batch(parse_url_lines(manual), "manual")

    st.divider()
    upload = st.file_uploader("Upload CSV", type=["csv"])
    if upload is not None:
        frame = pd.read_csv(upload)
        st.dataframe(frame.head(20), width='stretch', hide_index=True)
        url_column = st.selectbox("URL column", frame.columns)
        if st.button("Import CSV URLs"):
            add_url_batch(frame[url_column].dropna().astype(str).tolist(), "csv")


def render_sitemap() -> None:
    st.subheader("Import Sitemap")
    sitemap = st.text_input("Sitemap URL or local XML path", placeholder="https://example.com/sitemap.xml")
    if st.button("Import Sitemap", type="primary"):
        try:
            urls = load_sitemap(sitemap)
            add_url_batch(urls, "sitemap")
        except Exception as exc:
            st.error(f"Sitemap import failed: {exc}")


def render_queue() -> None:
    st.subheader("URL Queue")
    filters = st.columns([1, 1, 2])
    submit_filter = filters[0].selectbox("Submit status", ["all", *SUBMIT_STATUSES])
    index_filter = filters[1].selectbox("Index status", ["all", *INDEX_STATUSES])
    search = filters[2].text_input("Search")

    df = get_urls(submit_filter, index_filter, search)
    if df.empty:
        st.info("No URLs yet. Add URLs or import sitemap first.")
        if st.button("Go To Import", width="stretch"):
            go_to_step("Import URLs")
        return

    st.dataframe(
        df[["id", "url", "domain", "source", "submit_status", "index_status", "last_submitted_at", "last_checked_at"]],
        width='stretch',
        hide_index=True,
    )

    selected_id = st.selectbox("Edit URL", df["id"].tolist(), format_func=lambda row_id: df[df["id"] == row_id]["url"].iloc[0])
    row = df[df["id"] == selected_id].iloc[0]

    col_1, col_2, col_3 = st.columns(3)
    col_1.link_button("Open Brave Submit", submit_url(), width='stretch')
    col_2.link_button("Check URL Index", site_search_url(row["url"]), width='stretch')
    col_3.link_button("Check Domain Index", domain_search_url(row["domain"]), width='stretch')

    status_editor(row)

    st.divider()
    col_a, col_b = st.columns(2)
    if col_a.button("Add More URLs", width="stretch", key="queue_add_more"):
        go_to_step("Import URLs")
    if col_b.button("Choose Submission Method", type="primary", width="stretch", key="queue_choose_submission"):
        go_to_step("Submit")


def render_submission_helper() -> None:
    st.subheader("Submission Helper")
    st.markdown(
        '<p class="small-note">Assisted flow only. Open Brave, submit URL manually, then mark status here.</p>',
        unsafe_allow_html=True,
    )

    df = get_urls(submit_status="pending")
    if df.empty:
        st.info("No pending URLs.")
        return

    row = df.iloc[0]
    st.code(row["url"], language="text")
    col_1, col_2, col_3 = st.columns(3)
    col_1.link_button("Open Brave Submit", submit_url(), width='stretch')
    col_2.link_button("Check URL Index", site_search_url(row["url"]), width='stretch')
    col_3.link_button("Check Domain Index", domain_search_url(row["domain"]), width='stretch')
    status_editor(row)


def render_auto_submit() -> None:
    st.subheader("Auto Submit")
    st.markdown(
        '<p class="small-note">Visible browser automation. Stops on CAPTCHA, verification, missing fields, or blocked access.</p>',
        unsafe_allow_html=True,
    )

    if not playwright_available():
        st.error("Playwright is not installed in current Python environment.")
        st.code("pip install -r requirements.txt", language="bash")
        return

    chrome_path = st.text_input("Chrome executable path", value=DEFAULT_CHROME_PATH)
    if chrome_path and not chrome_path_available(chrome_path):
        st.warning("Chrome path not found. Playwright bundled browser will be used if installed.")

    col_a, col_b, col_c = st.columns(3)
    limit = col_a.number_input("Max URLs", min_value=1, max_value=50, value=5, step=1)
    delay = col_b.number_input("Delay seconds", min_value=1.0, max_value=60.0, value=5.0, step=1.0)
    headless_default = not DEFAULT_CHROME_PATH.startswith("/Applications/")
    headless = col_c.toggle("Headless", value=headless_default)

    pending = get_urls(submit_status="pending")
    failed_count = len(get_urls(submit_status="failed"))
    if failed_count:
        if st.button(f"Reset {failed_count} Failed URLs To Pending"):
            reset_failed_urls()
            st.rerun()

    if pending.empty:
        st.info("No pending URLs.")
        return

    st.dataframe(
        pending[["id", "url", "domain", "submit_status", "created_at"]].head(int(limit)),
        width="stretch",
        hide_index=True,
    )

    consent = st.checkbox("I understand this may be rate-limited or blocked by Brave, and automation will not bypass challenges.")
    if st.button("Auto Submit Pending URLs", type="primary", disabled=not consent):
        progress = st.progress(0)
        results = []
        batch = pending.head(int(limit))
        id_by_url = {row.url: int(row.id) for row in batch.itertuples(index=False)}
        urls = [row.url for row in batch.itertuples(index=False)]
        with st.spinner("Opening Chrome once and submitting queued URLs"):
            batch_results = submit_urls_in_one_browser(
                urls,
                chrome_path=chrome_path,
                headless=headless,
                pause_seconds=float(delay),
            )
            for index, result in enumerate(batch_results, start=1):
                results.append({"url": result.url, "status": result.status, "message": result.message})

                mapped_status = "submitted" if result.status == "submitted" else "failed"
                update_submit_result(id_by_url[result.url], mapped_status, f"Auto submit: {result.status} - {result.message}")
                progress.progress(index / len(batch))

                if result.status == "blocked":
                    st.error("Stopped: Brave showed challenge or access-control text.")
                    break

        st.dataframe(pd.DataFrame(results), width="stretch", hide_index=True)
        st.rerun()


def render_submit_step() -> None:
    st.subheader("Choose Submission Method")
    pending = get_urls(submit_status="pending")
    if pending.empty:
        st.info("No pending URLs. You can review report now.")
        if st.button("Go To Report", type="primary", width="stretch", key="submit_empty_report"):
            go_to_step("Report")
        return

    st.markdown(
        '<p class="small-note">Pick manual submission for full control, or auto submit for visible browser automation.</p>',
        unsafe_allow_html=True,
    )
    manual_tab, auto_tab = st.tabs(["Manual Submission", "Auto Submit"])

    with manual_tab:
        render_submission_helper()
        if st.button("Go To Report After Manual Updates", width="stretch", key="manual_go_report"):
            go_to_step("Report")

    with auto_tab:
        render_auto_submit()
        if st.button("Go To Report", width="stretch", key="auto_go_report"):
            go_to_step("Report")


def render_reports() -> None:
    st.subheader("Reports")
    df = get_urls()
    if df.empty:
        st.info("No data to export.")
        return

    st.dataframe(df, width='stretch', hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV Report",
        data=csv,
        file_name="brave-url-submit-report.csv",
        mime="text/csv",
        width='stretch',
    )

    st.divider()
    col_a, col_b = st.columns(2)
    if col_a.button("Back To Queue", width="stretch"):
        go_to_step("URL Queue")
    if col_b.button("Start New Session", width="stretch"):
        st.session_state.urls = []
        st.session_state.next_id = 1
        go_to_step("Import URLs")


st.title("Brave Search URL Submit Manager")
st.markdown(
    '<p class="small-note">Import URLs, review your submission queue, submit to Brave Search, and export a clean status report.</p>',
    unsafe_allow_html=True,
)

init_queue()
render_stepper()
st.divider()

with st.sidebar:
    st.header("Submission Progress")
    st.caption(f"Current step: {st.session_state.current_step}")
    current = stats()
    st.metric("URLs", current["total"])
    st.metric("Pending", current["pending"])
    st.metric("Submitted", current["submitted"])
    st.divider()
    with st.expander("How To Use It", expanded=True):
        st.markdown(
            """
            1. Add URLs manually, upload CSV, or import sitemap.
            2. Review URLs in URL Queue.
            3. Choose Manual Submission or Auto Submit.
            4. Download CSV report.
            """
        )
    with st.expander("About Brave Search URL Submit Manager"):
        st.markdown(
            """
            Queue URLs in session memory and submit them to Brave Search with a guided workflow.

            Auto Submit uses a visible Chrome browser, keeps a delay between URLs, and stops if Brave shows a challenge or access block.
            """
        )

if st.session_state.current_step == "Import URLs":
    render_import_step()
elif st.session_state.current_step == "URL Queue":
    render_queue()
elif st.session_state.current_step == "Submit":
    render_submit_step()
else:
    render_reports()

st.divider()
st.markdown(
    "<p style='text-align:center; color:#5f6b7a; font-size:0.9rem;'>Built with ❤️ by Dhruv Pandya | Brave Search URL Submit Manager</p>",
    unsafe_allow_html=True,
)
