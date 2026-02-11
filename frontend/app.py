# frontend/app.py
from __future__ import annotations

import csv
import html
import hashlib
import json
import re
from base64 import b64encode
from pathlib import Path
from urllib.parse import quote

import requests
import streamlit as st

# ----------------------------
# Paths / constants
# ----------------------------
APP_ROOT = Path(__file__).resolve().parent
CONTENT_DIR = APP_ROOT / "content"
ASSETS_DIR = APP_ROOT / "assets"
STYLES_DIR = APP_ROOT / "styles"

MSC_BADGE_PATH = ASSETS_DIR / "msc.png"
BOT_ICON_PATH = ASSETS_DIR / "bot.png"
REPO_ROOT = APP_ROOT.parent
SEED_CSV_PATH = (
    REPO_ROOT / "web" / "public" / "data" / "afi41_seed.csv"
    if (REPO_ROOT / "web" / "public" / "data" / "afi41_seed.csv").exists()
    else APP_ROOT / "content" / "afi41_seed.csv"
)

AFMS_MSC_URL = "https://www.airforcemedicine.af.mil/About-Us/Medical-Branches/Medical-Service-Corps/"
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")
BACKEND_URL_CONFIGURED = "BACKEND_URL" in st.secrets
APP_VERSION = str(st.secrets.get("APP_VERSION", "1.0.0"))
SVG_FEEDBACK_DEFAULT = bool(st.secrets.get("SVG_FEEDBACK_DEFAULT", False))

# ----------------------------
# Streamlit page config
# ----------------------------
st.set_page_config(
    page_title="MSC Super Companion",
    page_icon=str(MSC_BADGE_PATH) if MSC_BADGE_PATH.exists() else "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒâ€¹Ã…â€œ",
    layout="wide",
)

# ----------------------------
# Load CSS theme
# ----------------------------
THEME_CSS_PATH = STYLES_DIR / "theme.css"
if THEME_CSS_PATH.exists():
    st.markdown(f"<style>{THEME_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Small extra CSS for full-row clickable anchors (keeps it non-linky)
st.markdown(
    """
    <style>
    /* Fix input text color (mobile + desktop) */
    .stTextInput input,
    .stTextArea textarea {
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
    }

    /* Placeholder text stays subtle */
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #9aa0a6 !important;
    }
      a.sf-rowlink { text-decoration: none !important; color: inherit !important; display:block; }
      a.sf-rowlink:visited { color: inherit !important; }
      a.sf-rowlink:active { color: inherit !important; }
      .stTabs [data-baseweb="tab"] { color: #1E2A32 !important; }
      .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #1E2A32 !important; }
      .stTabs [data-baseweb="tab"]:after { background: #1B3F72 !important; }
      .stTabs [data-baseweb="tab"][aria-selected="true"] { border-bottom: 2px solid #1B3F72 !important; }
      .sf-title, .sf-summary { display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden; }
      .sf-title { -webkit-line-clamp: 2; }
      .sf-summary { -webkit-line-clamp: 3; }
      .sf-card-link{ display:block; text-decoration:none !important; color: inherit !important; }
      .sf-card-title{ display:-webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; }
      .sf-card-desc{ display:-webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; overflow: hidden; }
      .sf-card-chevron{ color: rgba(30,42,50,0.65); font-size: 22px; line-height: 1; padding-top: 2px; margin-left:auto; }
      .sf-card-wrap{ margin: 6px 0; }
      .sf-card-wrap [data-testid="stDownloadButton"] > button,
      .sf-card-wrap [data-testid="stLinkButton"] > a{
        display: block;
        width: 100%;
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: var(--cardRadius);
        padding: 14px;
        text-align: left;
        white-space: normal;
        box-shadow: var(--cardShadow);
        color: #1E2A32 !important;
        text-decoration: none !important;
      }
      .sf-card-wrap [data-testid="stDownloadButton"] > button:hover,
      .sf-card-wrap [data-testid="stLinkButton"] > a:hover{
        background: rgba(27,63,114,.06);
        border-color: rgba(27,63,114,.35);
      }
      .sf-table{
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        overflow: hidden;
      }
      .sf-table-row{
        margin: 0;
        padding: 0;
        border-bottom: 1px solid #CBD5E1;
      }
      .sf-table-row:last-child{
        border-bottom: none;
      }
      .sf-table-row.even{
        background: #F2F4F6;
      }
      .sf-table-row.odd{
        background: #7A0019;
      }
      .sf-table-row.odd [data-testid="stLinkButton"] > a,
      .sf-table-row.odd [data-testid="stDownloadButton"] > button{
        color: #FFFFFF !important;
      }
      .sf-table-row [data-testid="stLinkButton"] > a,
      .sf-table-row [data-testid="stDownloadButton"] > button{
        border-radius: 0 !important;
        margin: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 10px 12px !important;
        text-align: left !important;
      }
      .sf-row-list{
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        overflow: hidden;
      }
      .sf-row-card{
        display: flex;
        gap: 10px;
        align-items: flex-start;
        padding: 10px 12px;
        border-bottom: 1px solid #CBD5E1;
      }
      .sf-row-card:last-child{ border-bottom: none; }
      .sf-row-card.even{ background: rgba(128, 0, 32, 0.06); }
      .sf-row-card.odd{ background: #F2F4F6; }
      .sf-row-link{ display:block; text-decoration:none !important; color: inherit !important; }
      .sf-tag{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 2px 8px;
        font-size: 12px;
        font-weight: 500;
        border-radius: 999px;
        background: rgba(0,0,0,0.08);
        color: #374151;
        white-space: nowrap;
      }
      .sf-title-text{
        font-weight: 600;
        color: #111827;
      }
      .sf-desc-text{
        font-size: 13px;
        color: #6b7280;
        margin-top: 4px;
      }
      .sf-table-tool_list [data-testid="stLinkButton"] > a,
      .sf-table-tool_list [data-testid="stDownloadButton"] > button{
        font-weight: 600;
      }
      .tool-card-desc{
        font-size: 13px;
        color: #6b7280;
        margin-top: 4px;
      }
      .sf-tag{
        display: inline-block;
        margin: 4px 12px 8px 12px;
        padding: 2px 8px;
        font-size: 12px;
        font-weight: 500;
        border-radius: 999px;
        background: rgba(0,0,0,0.08);
        color: #374151;
      }
      .sf-header{
        border: 2px solid #0B3C5D !important;
        border-radius: 14px !important;
      }
      .stTextInput input{
        color: #0B0F14 !important;
        background: #FFFFFF !important;
        border: 1px solid rgba(27,63,114,0.22) !important;
      }
      .stTextInput input::placeholder{
        color: rgba(11,15,20,0.45) !important;
      }
      .sf-chat-wrap{
        border: 1px solid rgba(27,63,114,0.28);
        background: #FFFFFF;
        border-radius: var(--cardRadius);
        box-shadow: var(--cardShadow);
        padding: 6px 12px 10px 12px;
        margin: 4px 0 12px 0;
      }
      .sf-chat-label{
        font-size: 12px;
        color: var(--muted);
        margin: 8px 0 6px 0;
      }
      .sf-chat-wrap .sf-welcome{
        margin: 0;
        box-shadow: none;
        border: none;
        background: transparent;
      }
      .sf-chat-wrap .stTextArea > div > div{
        border-color: #1B3F72;
        background: #FFFFFF;
        color: #111111;
      }
      .sf-chat-wrap textarea{
        color: #000000 !important;
        font-size: 15px !important;
      }
      .sf-chat-wrap textarea::placeholder{
        color: #6b7280 !important;
        font-size: 14px !important;
        opacity: 1 !important;
      }
      .sf-doclink{
        display: inline-block;
        margin-top: 6px;
        color: #1B3F72;
        text-decoration: none;
        font-weight: 600;
      }
      .sf-doclink:hover{
        text-decoration: underline;
      }
      .sf-chat-wrap [data-testid="stButton"]{
        margin-top: 6px;
      }
      .sf-svg-thumb {
        width: 22px;
        height: 22px;
        margin: 0 auto 4px auto;
        color: #1B3F72;
      }
      .sf-svg-thumb svg {
        width: 22px;
        height: 22px;
        display: block;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Helpers
# ----------------------------
@st.cache_data(show_spinner=False)
def load_json(filename: str):
    path = CONTENT_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_csv_rows(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return [row for row in reader]


def load_afi_seed() -> list[dict]:
    rows = load_csv_rows(SEED_CSV_PATH)
    if not rows:
        return []
    header = rows[0]
    items: list[dict] = []
    for row in rows[1:]:
        row_map = {header[i]: (row[i] if i < len(row) else "") for i in range(len(header))}
        title = (row_map.get("title") or "").strip()
        pub = (row_map.get("pub") or "").strip()
        url = (row_map.get("official_publication_pdf") or "").strip()
        tag = (row_map.get("msc_functional_area") or "").strip()
        items.append(
            {
                "pub": pub,
                "title": title,
                "why_it_matters": "",
                "tags": [tag] if tag else [],
                "use_cases": [],
                "notes": "",
                "official_links": [{"label": "Open publication", "url": url}] if url else [],
            }
        )
    return items


@st.cache_data(show_spinner=False)
def load_index_meta_rows() -> list[dict]:
    meta_path = REPO_ROOT / "backend" / "data" / "index" / "meta.json"
    if not meta_path.exists():
        return []
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _normalize_doc_ref(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    lower = raw.lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        return lower
    return Path(raw.replace("\\", "/")).name.lower()


def _chunk_belongs_to_doc(chunk: dict, doc_ref: str) -> bool:
    if not doc_ref:
        return False
    chunk_url = (chunk.get("url") or "").strip().lower()
    chunk_path = (chunk.get("local_path") or "").strip().replace("\\", "/")
    chunk_name = Path(chunk_path).name.lower() if chunk_path else ""
    if doc_ref.startswith("http://") or doc_ref.startswith("https://"):
        return doc_ref == chunk_url or doc_ref in chunk_url
    return doc_ref == chunk_name


def _make_match_snippet(text: str, terms: list[str], window: int = 180) -> str:
    cleaned = clean_text(text)
    if not cleaned:
        return ""
    lower = cleaned.lower()
    positions = [lower.find(t) for t in terms if t and lower.find(t) >= 0]
    anchor = min(positions) if positions else 0
    start = max(0, anchor - window)
    end = min(len(cleaned), anchor + window)
    snippet = cleaned[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(cleaned):
        snippet = snippet + "..."
    return snippet


def search_indexed_doc_content(doc_ref: str, query: str, max_hits: int = 6) -> list[dict]:
    terms = [t for t in re.findall(r"[a-z0-9][a-z0-9\-]+", (query or "").lower()) if len(t) >= 2]
    if not doc_ref or not terms:
        return []

    rows = load_index_meta_rows()
    ranked: list[tuple[int, dict]] = []
    for row in rows:
        if not _chunk_belongs_to_doc(row, doc_ref):
            continue
        text = row.get("text") or ""
        lower = text.lower()
        if not all(t in lower for t in terms):
            continue
        score = sum(lower.count(t) for t in terms)
        ranked.append((score, row))

    ranked.sort(key=lambda x: x[0], reverse=True)
    hits: list[dict] = []
    for score, row in ranked[:max_hits]:
        hits.append(
            {
                "score": score,
                "page": row.get("page"),
                "snippet": _make_match_snippet(row.get("text") or "", terms),
            }
        )
    return hits


def _to_viewer_page(page_value: object) -> int | None:
    try:
        raw = int(page_value)  # type: ignore[arg-type]
    except Exception:
        return None
    # Most PDF viewers are 1-based. If index data is 0-based, bump it.
    return raw + 1 if raw >= 0 else None


def _build_pdf_match_url(base_url: str, search_query: str, page_value: object) -> str:
    if not base_url:
        return ""
    root = base_url.split("#", 1)[0]
    parts: list[str] = []
    page = _to_viewer_page(page_value)
    if page is not None:
        parts.append(f"page={page}")
    if search_query.strip():
        parts.append(f"search={quote(search_query.strip())}")
    if not parts:
        return root
    return f"{root}#{'&'.join(parts)}"


def render_doc_find_panel(items: list[dict], panel_key: str) -> None:
    options: list[dict] = []
    seen: set[str] = set()
    for item in items:
        title = to_sentence_case(item.get("title") or "").strip() or "Untitled"
        pub = clean_text(item.get("pub") or "")
        label = f"{pub} - {title}" if pub else title
        links = item.get("official_links", []) or []
        if not links:
            continue
        raw_ref = (links[0].get("url") or "").strip()
        norm_ref = _normalize_doc_ref(raw_ref)
        if not norm_ref or norm_ref in seen:
            continue
        seen.add(norm_ref)
        options.append(
            {
                "label": label,
                "doc_ref": norm_ref,
                "open_url": build_doc_url(item),
            }
        )

    if not options:
        return

    st.markdown("#### Find In A Document")
    st.caption("Mobile-friendly in-document search over indexed text snippets.")

    doc_idx = st.selectbox(
        "Document",
        options=list(range(len(options))),
        format_func=lambda i: str(options[i].get("label") or ""),
        key=f"{panel_key}_doc_idx",
    )
    selected = options[doc_idx]
    selected_label = str(selected.get("label") or "")
    selected_ref = str(selected.get("doc_ref") or "")
    selected_open_url = str(selected.get("open_url") or "")

    query = st.text_input(
        "Find text",
        placeholder="Type a word or phrase to search within the selected document...",
        key=f"{panel_key}_query",
    )
    if not query.strip():
        return

    hits = search_indexed_doc_content(selected_ref, query.strip(), max_hits=6)
    if not hits:
        st.caption("No matches found in indexed content for this document.")
        return

    st.markdown(f"**Matches in:** {selected_label}")
    for i, hit in enumerate(hits, start=1):
        page = hit.get("page")
        page_num = _to_viewer_page(page)
        page_text = f"Page {page_num}" if page_num is not None else "Page not available"
        snippet = hit.get("snippet") or ""
        st.markdown(f"**{i}. {page_text}**")
        st.caption(snippet)

        open_url = _build_pdf_match_url(selected_open_url, query.strip(), page)
        if open_url:
            st.link_button(
                f"Open at match {i}",
                open_url,
                use_container_width=True,
                key=f"{panel_key}_open_{doc_idx}_{i}",
            )


def _data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    ext = path.suffix.lower().replace(".", "")
    mime = "png" if ext == "png" else "jpeg"
    return f"data:image/{mime};base64,{b64encode(path.read_bytes()).decode()}"


MSC_BADGE_URI = _data_uri(MSC_BADGE_PATH)
BOT_ICON_URI = _data_uri(BOT_ICON_PATH)


def get_health():
    r = requests.get(f"{BACKEND_URL}/health", timeout=10)
    r.raise_for_status()
    return r.json()


def run_ingest():
    r = requests.post(f"{BACKEND_URL}/ingest", timeout=300)
    r.raise_for_status()
    return r.json()


def ask(question: str, top_k: int, allowed_sources: list[str] | None):
    payload: dict = {"question": question, "top_k": top_k}
    if allowed_sources:
        payload["allowed_sources"] = allowed_sources
    r = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


def qp_get() -> dict:
    # Streamlit has two APIs depending on version
    try:
        return dict(st.query_params)  # type: ignore[attr-defined]
    except Exception:
        return st.experimental_get_query_params()


def qp_set(**kwargs):
    # Remove keys with None/"" to keep URL clean
    clean = {k: v for k, v in kwargs.items() if v not in (None, "", [])}
    try:
        st.query_params.clear()  # type: ignore[attr-defined]
        for k, v in clean.items():
            st.query_params[k] = v  # type: ignore[attr-defined]
    except Exception:
        st.experimental_set_query_params(**clean)


def render_app_header():
    logo_img = f"<img src='{MSC_BADGE_URI}' alt='MSC'/>" if MSC_BADGE_URI else ""
    st.markdown(
        f"""
        <div class="sf-header">
          <div class="sf-head-top">
            <div class="sf-brand">
              <div class="sf-mark">{logo_img}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("For official-use research support only. Do not enter PHI, PII, or operationally sensitive data.")


def render_welcome_panel():
    icon = f"<img src='{BOT_ICON_URI}' alt='Bot'/>" if BOT_ICON_URI else "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€šÃ‚Â¤ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“"
    st.markdown(
        f"""
        <div class="sf-welcome">
          <div class="sf-avatar">{icon}</div>
          <div>
            <h3>Welcome to MSC Super Companion.</h3>
            <p>Ask a question and I’ll help you find guidance, summarize sources, and point you to relevant publications.</p>
            <div class="muted">Citations are provided when supporting evidence is retrieved. Validate decisions against official publications and local command policy.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_links_as_buttons(links: list[dict]):
    # Cleaner than raw markdown link list, still ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“trust-firstÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â
    if not links:
        st.caption("Official links: none")
        return

    st.markdown("#### Official links")
    for link in links:
        label = link.get("label", "Open")
        url = link.get("url", "")
        if url:
            if is_url(url):
                st.markdown(
                    f'<a class="sf-doclink" href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>',
                    unsafe_allow_html=True,
                )
            else:
                local_path = resolve_local_path(url)
                if local_path and local_path.exists():
                    file_href = f"/docs/{quote(local_path.name)}"
                    st.markdown(
                        f'<a class="sf-doclink" href="{file_href}" target="_blank" rel="noopener noreferrer">{label}</a>',
                        unsafe_allow_html=True,
                    )


def render_tags(tags: list[str] | None):
    tags = tags or []
    if not tags:
        return ""
    safe = [f"<span class='sf-tag'>{html.escape(clean_text(t))}</span>" for t in tags[:6]]
    return f"<div class='sf-tags'>{''.join(safe)}</div>"


def safe_text(x: str | None) -> str:
    return html.escape((x or "").strip())


def clean_text(s: str | None) -> str:
    if s is None:
        return ""
    raw = html.unescape(str(s))
    no_tags = re.sub(r"<[^>]+>", "", raw)
    collapsed = " ".join(no_tags.split()).strip()
    if collapsed in ("/a", "/div", "/span", "a", "div", "span"):
        return ""
    return collapsed


def escape_html(x: str | None) -> str:
    return html.escape((x or "").strip(), quote=True)


def render_card_button(
    label: str,
    bg: str,
    border_color: str,
    key: str,
    url: str | None = None,
    data: bytes | None = None,
    file_name: str | None = None,
    mime: str | None = None,
) -> None:
    st.markdown(
        f"<div class='sf-card-wrap' style='--card-bg:{bg}; --card-border:{border_color};'>",
        unsafe_allow_html=True,
    )
    if data is not None and file_name and mime:
        st.download_button(
            label,
            data=data,
            file_name=file_name,
            mime=mime,
            use_container_width=True,
            key=key,
        )
    elif url:
        try:
            st.link_button(label, url, use_container_width=True, key=key)
        except TypeError:
            try:
                st.link_button(label, url, key=key)
            except TypeError:
                st.link_button(label, url)
    st.markdown("</div>", unsafe_allow_html=True)


def render_row_card(
    title: str,
    desc: str,
    tag: str,
    row_class: str,
    url: str | None = None,
    data: bytes | None = None,
    file_name: str | None = None,
    mime: str | None = None,
    key: str = "",
) -> None:
    safe_title = escape_html(clean_text(title))
    safe_desc = escape_html(clean_text(desc))
    safe_tag = escape_html(clean_text(tag))
    card_body = f"""
        <div class="sf-row-card {row_class}">
          {f"<div class='sf-tag'>{safe_tag}</div>" if safe_tag else ""}
          <div>
            <div class="sf-title-text">{safe_title}</div>
            {f"<div class='sf-desc-text'>{safe_desc}</div>" if safe_desc else ""}
          </div>
        </div>
    """
    if url:
        st.markdown(
            f'<a class="sf-row-link" href="{url}" target="_blank" rel="noopener noreferrer">{card_body}</a>',
            unsafe_allow_html=True,
        )
    elif data is not None and file_name and mime:
        b64 = b64encode(data).decode("ascii")
        href = f"data:{mime};base64,{b64}"
        st.markdown(
            f'<a class="sf-row-link" href="{href}" download="{escape_html(file_name)}">{card_body}</a>',
            unsafe_allow_html=True,
        )


def is_url(value: str | None) -> bool:
    if not value:
        return False
    return value.startswith("http://") or value.startswith("https://")


def resolve_local_path(value: str) -> Path | None:
    if is_url(value):
        return None
    # Treat relative paths as frontend-local
    return (APP_ROOT / value).resolve()

def is_local_doc(value: str | None) -> bool:
    if not value:
        return False
    v = value.strip()
    lower = v.lower()
    if "frontend/docs" in lower or "/docs/" in lower or "\\docs\\" in lower:
        return True
    if lower.endswith(".pdf"):
        candidate = (APP_ROOT / "docs" / Path(v).name)
        return candidate.exists()
    return False


def build_doc_url(item: dict) -> str:
    # Prefer official_links if present
    official_links = item.get("official_links", []) or []
    if official_links:
        raw = official_links[0].get("url", "") or ""
        if is_url(raw):
            return raw
        if raw:
            if BACKEND_URL_CONFIGURED:
                return f"{BACKEND_URL}/docs/{quote(Path(raw).name)}"
            return f"/docs/{quote(Path(raw).name)}"

    # Fallbacks for local file fields
    for key in ("path", "local_path", "file"):
        raw = item.get(key, "") or ""
        if raw:
            if is_url(raw):
                return raw
            if BACKEND_URL_CONFIGURED:
                return f"{BACKEND_URL}/docs/{quote(Path(raw).name)}"
            return f"/docs/{quote(Path(raw).name)}"

    return ""


def load_file_bytes(path: Path) -> bytes:
    return path.read_bytes()


def mime_for_path(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return "application/pdf"
    if ext == ".xlsx":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/octet-stream"


def to_sentence_case(text: str) -> str:
    cleaned = clean_text(text)
    letters = [c for c in cleaned if c.isalpha()]
    if not letters:
        return cleaned

    result = cleaned
    if all(c.isupper() for c in letters):
        lowered = cleaned.lower()
        result = lowered[:1].upper() + lowered[1:]

    # Preserve common acronyms
    acronyms = ["AFI", "DHA", "DOD", "AFMS", "MSC"]
    for ac in acronyms:
        result = re.sub(rf"\b{ac.lower()}\b", ac, result, flags=re.IGNORECASE)
    return result


def make_open_token(kind: str, idx: int) -> str:
    # stable enough within this run; weÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ll re-map each rerun from JSON
    return f"{kind}:{idx}"


def _hash_text(value: str) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()[:16]


def submit_feedback(payload: dict) -> None:
    r = requests.post(f"{BACKEND_URL}/feedback", json=payload, timeout=20)
    r.raise_for_status()


def _svg_thumb_up() -> str:
    return (
        '<div class="sf-svg-thumb" aria-hidden="true">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.64l1.38-9A2 2 0 0 0 19.69 9Z"></path>'
        '<path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>'
        '</svg></div>'
    )


def _svg_thumb_down() -> str:
    return (
        '<div class="sf-svg-thumb" aria-hidden="true">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.64l-1.38 9A2 2 0 0 0 4.31 15Z"></path>'
        '<path d="M17 2h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path>'
        '</svg></div>'
    )


def render_feedback_controls(
    question: str,
    answer: str,
    citations: list[dict] | None,
    use_svg_icons: bool = False,
):
    """Render feedback controls and POST votes to /feedback."""
    citations = citations or []

    q_id = _hash_text(question.strip())
    a_id = _hash_text(answer.strip())
    key_prefix = f"fb_{q_id}_{a_id}"

    if key_prefix not in st.session_state:
        st.session_state[key_prefix] = {"vote": None}

    vote = st.session_state[key_prefix]["vote"]

    st.markdown('<div class="sf-feedback">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 6], vertical_alignment="center")

    with c1:
        if use_svg_icons:
            st.markdown(_svg_thumb_up(), unsafe_allow_html=True)
        st.markdown('<div class="is-selected">' if vote == "up" else '<div>', unsafe_allow_html=True)
        up = st.button('Helpful', key=f"{key_prefix}_up", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        if use_svg_icons:
            st.markdown(_svg_thumb_down(), unsafe_allow_html=True)
        st.markdown('<div class="is-selected">' if vote == "down" else '<div>', unsafe_allow_html=True)
        down = st.button('Not helpful', key=f"{key_prefix}_down", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        if vote == 'up':
            st.caption('Recorded: Helpful')
        elif vote == 'down':
            st.caption('Recorded: Not helpful')

    st.markdown('</div>', unsafe_allow_html=True)

    if up:
        payload = {
            'vote': 'up',
            'question_id': q_id,
            'answer_id': a_id,
            'question': question,
            'answer': answer,
            'citations': citations,
        }
        submit_feedback(payload)
        st.session_state[key_prefix]['vote'] = 'up'
        st.toast('Thanks - feedback recorded')

    if down:
        payload = {
            'vote': 'down',
            'question_id': q_id,
            'answer_id': a_id,
            'question': question,
            'answer': answer,
            'citations': citations,
        }
        submit_feedback(payload)
        st.session_state[key_prefix]['vote'] = 'down'
        st.toast('Thanks - feedback recorded')


# ----------------------------
# Init session state
# ----------------------------
if "open_token" not in st.session_state:
    st.session_state.open_token = ""
if "open_kind" not in st.session_state:
    st.session_state.open_kind = ""
if "open_idx" not in st.session_state:
    st.session_state.open_idx = None

# ----------------------------
# Header
# ----------------------------
render_app_header()

# ----------------------------
# Backend status (calm)
# ----------------------------
try:
    health = get_health()
    BACKEND_OK = True
    sources_list = health.get("sources", [])
    # Backend status text intentionally hidden from UI.
except Exception:
    BACKEND_OK = False
    health = {"sources": [], "indexed_as_of": "unknown", "num_chunks": 0}
    sources_list = []
    # Backend status text intentionally hidden from UI.

# ----------------------------
# Sidebar (RAG controls)
# ----------------------------
st.sidebar.header("RAG Controls")
top_k = st.sidebar.slider("Evidence to retrieve (Top-K)", min_value=1, max_value=12, value=5)
allowed = st.sidebar.multiselect("Limit sources (optional)", options=sources_list, default=[])

if st.sidebar.button("Reload data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("Rebuild Index (Ingest)", use_container_width=True):
    with st.spinner("Ingesting sources and rebuilding index..."):
        try:
            result = run_ingest()
            st.sidebar.success(
                f"Indexed: {result.get('indexed_as_of')} ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ Chunks: {result.get('num_chunks')} ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ Skipped: {result.get('skipped_items')}"
            )
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Ingest failed: {e}")

st.sidebar.divider()
st.sidebar.caption("Tip: Prefer direct official PDFs for maximum trust and speed.")

debug_enabled = st.sidebar.checkbox("DEBUG")
use_svg_feedback = st.sidebar.checkbox(
    "SVG feedback icons",
    value=SVG_FEEDBACK_DEFAULT,
    help="Show optional SVG thumbs icons for answer feedback controls.",
)
if debug_enabled:
    st.sidebar.markdown("**CSV Debug**")
    st.sidebar.code(str(SEED_CSV_PATH))
    rows = load_csv_rows(SEED_CSV_PATH)
    st.sidebar.markdown(f"Rows: `{len(rows)}`")
    if rows:
        header = rows[0]
        title_idx = header.index("title") if "title" in header else -1
        tail = rows[-5:] if len(rows) >= 6 else rows[1:]
        titles = []
        for r in tail:
            if title_idx >= 0 and title_idx < len(r):
                titles.append(r[title_idx])
        if titles:
            st.sidebar.markdown("Last 5 titles:")
            for t in titles:
                st.sidebar.markdown(f"- {t}")

# ----------------------------
# Tabs
# ----------------------------
tab1, tab2, tab3 = st.tabs(["ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒâ€¦Ã‚Â¡ Doctrine Library", "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€šÃ‚Â§Ãƒâ€šÃ‚Â° MSC Toolkit", "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢Ãƒâ€šÃ‚Â¬ Ask Super Companion"])

# ----------------------------
# Query param routing (full-row clickable)
# ----------------------------
params = qp_get()
open_param = params.get("open")
# normalize (can be list in older API)
if isinstance(open_param, list):
    open_param = open_param[0] if open_param else ""

if open_param:
    # expected "afi:12" or "toolkit:3"
    token = str(open_param)
    parts = token.split(":")
    if len(parts) == 2 and parts[1].isdigit():
        st.session_state.open_token = token
        st.session_state.open_kind = parts[0]
        st.session_state.open_idx = int(parts[1])

# ----------------------------
# Tab 1: Doctrine Library
# ----------------------------
with tab1:
    st.subheader("Doctrine Library")
    st.caption("Quick access to trusted DHA and AFI health services guidance.")

    afi = load_afi_seed()
    if not afi:
        st.error(f"Missing or empty file: {SEED_CSV_PATH}")
        st.stop()

    # Search bar (clean)
    q = st.text_input(
        "",
        placeholder="Search AFI number, title, tags, or use case...",
        label_visibility="collapsed",
    )

    if q:
        ql = q.lower()
        afi = [
            a for a in afi
            if ql in (a.get("pub", "") or "").lower()
            or ql in (a.get("title", "") or "").lower()
            or ql in (a.get("why_it_matters", "") or "").lower()
            or any(ql in t.lower() for t in (a.get("tags", []) or []))
            or any(ql in uc.lower() for uc in (a.get("use_cases", []) or []))
        ]

    render_doc_find_panel(afi, panel_key="doctrine_find")

    # If open token points to afi detail, render detail
    if st.session_state.open_kind == "afi" and st.session_state.open_idx is not None:
        idx = st.session_state.open_idx
        if 0 <= idx < len(afi):
            a = afi[idx]
            pub = clean_text(a.get("pub"))
            title = to_sentence_case(a.get("title") or "")
            st.markdown(f"### {pub} ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â {title}" if pub else f"### {title}")

            why = (a.get("why_it_matters") or "").strip()
            if why:
                st.write(clean_text(why))

            use_cases = a.get("use_cases", []) or []
            if use_cases:
                st.markdown("#### Use cases")
                for uc in use_cases[:8]:
                    st.markdown(f"- {clean_text(uc)}")

            notes = (a.get("notes") or "").strip()
            if notes:
                st.markdown("#### Notes")
                st.write(clean_text(notes))

            render_links_as_buttons(a.get("official_links", []) or [])

            if st.button("ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Ãƒâ€šÃ‚Â Back to list", use_container_width=True):
                st.session_state.open_token = ""
                st.session_state.open_kind = ""
                st.session_state.open_idx = None
                qp_set()  # clear query params
                st.rerun()
        else:
            # bad index, clear
            st.session_state.open_token = ""
            st.session_state.open_kind = ""
            st.session_state.open_idx = None
            qp_set()
            st.rerun()

    else:
        # LIST VIEW (row cards)
        st.markdown('<div class="sf-row-list">', unsafe_allow_html=True)
        for i, a in enumerate(afi):
            row_class = "even" if i % 2 == 0 else "odd"
            pub = clean_text(a.get("pub"))
            title = to_sentence_case(a.get("title") or "")
            display_title = f"{pub} ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â {title}" if pub else title
            summary = clean_text(a.get("why_it_matters"))
            tag_label = clean_text((a.get("tags", []) or [""])[0]) if a.get("tags") else ""
            official_links = a.get("official_links", []) or []
            raw_link = official_links[0].get("url") if official_links else ""
            external_url = raw_link if is_url(raw_link) else ""
            local_path = (APP_ROOT / "docs" / Path(raw_link).name) if is_local_doc(raw_link) else None
            has_local_file = bool(local_path and local_path.exists())

            if external_url:
                render_row_card(
                    title=display_title,
                    desc=summary,
                    tag=tag_label,
                    row_class=row_class,
                    url=external_url,
                )
            elif has_local_file:
                render_row_card(
                    title=display_title,
                    desc=summary,
                    tag=tag_label,
                    row_class=row_class,
                    data=load_file_bytes(local_path),
                    file_name=local_path.name,
                    mime=mime_for_path(local_path),
                    key=f"doc_dl_{i}",
                )
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------
# Tab 2: MSC Toolkit
# ----------------------------
with tab2:
    st.subheader("MSC Toolkit")
    st.caption("Helpful resources, right when you need them.")

    try:
        toolkit = load_json("toolkit.json")
    except FileNotFoundError:
        st.error("Missing file: frontend/content/toolkit.json")
        st.stop()
    landing_card = {
        "title": "Official MSC Landing Page",
        "summary": "AFMS Medical Service Corps page",
        "type": "Official",
        "tags": ["AFMS", "MSC"],
        "official_links": [{"label": "Open page", "url": AFMS_MSC_URL}],
    }
    dha_strategy_card = {
        "title": "DHA Strategy",
        "summary": "Defense Health Agency strategy page",
        "type": "Official",
        "tags": ["DHA", "Strategy"],
        "official_links": [{"label": "Open page", "url": "https://www.dha.mil/About-DHA/DHA-Strategy"}],
    }
    toolkit = [landing_card, dha_strategy_card] + (toolkit or [])

    q2 = st.text_input(
        "",
        placeholder="Search toolkit documents by title, tags, or summaryÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦",
        label_visibility="collapsed",
        key="toolkit_search",
    )
    if q2:
        ql = q2.lower()
        toolkit = [
            t for t in toolkit
            if ql in (t.get("title", "") or "").lower()
            or ql in (t.get("summary", "") or "").lower()
            or any(ql in tag.lower() for tag in (t.get("tags", []) or []))
        ]

    render_doc_find_panel(toolkit, panel_key="toolkit_find")

    # Detail view
    if st.session_state.open_kind == "toolkit" and st.session_state.open_idx is not None:
        idx = st.session_state.open_idx
        if 0 <= idx < len(toolkit):
            t = toolkit[idx]
            title = to_sentence_case(t.get("title") or "")
            st.markdown(f"### {title}")

            doc_type = (t.get("type") or "").strip()
            if doc_type:
                st.caption(f"Type: {to_sentence_case(doc_type)}")

            summary = (t.get("summary") or "").strip()
            if summary:
                st.write(clean_text(summary))

            render_links_as_buttons(t.get("official_links", []) or [])

            if st.button("ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â Ãƒâ€šÃ‚Â Back to toolkit", use_container_width=True):
                st.session_state.open_token = ""
                st.session_state.open_kind = ""
                st.session_state.open_idx = None
                qp_set()
                st.rerun()
        else:
            st.session_state.open_token = ""
            st.session_state.open_kind = ""
            st.session_state.open_idx = None
            qp_set()
            st.rerun()

    else:
        # LIST VIEW
        st.markdown('<div class="sf-row-list">', unsafe_allow_html=True)
        for i, t in enumerate(toolkit):
            row_class = "even" if i % 2 == 0 else "odd"
            title = to_sentence_case(t.get("title") or "")
            summary = clean_text(t.get("summary"))
            doc_type = to_sentence_case(t.get("type") or "")

            official_links = t.get("official_links", []) or []
            primary_link = official_links[0].get("url") if official_links else ""
            external_url = primary_link if is_url(primary_link) else ""
            local_path = (APP_ROOT / "docs" / Path(primary_link).name) if is_local_doc(primary_link) else None
            has_local_file = bool(local_path and local_path.exists())

            if external_url:
                render_row_card(
                    title=title,
                    desc=summary,
                    tag=doc_type,
                    row_class=row_class,
                    url=external_url,
                )
            elif has_local_file:
                render_row_card(
                    title=title,
                    desc=summary,
                    tag=doc_type,
                    row_class=row_class,
                    data=load_file_bytes(local_path),
                    file_name=local_path.name,
                    mime=mime_for_path(local_path),
                    key=f"tool_dl_{i}",
                )
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------
# Tab 3: Ask Super Companion
# ----------------------------
with tab3:
    st.subheader("Ask Super Companion")
    st.caption("Citations are shown when supporting evidence is retrieved.")

    # Welcome panel (visual polish + guidance)
    st.markdown('<div class="sf-chat-wrap">', unsafe_allow_html=True)
    render_welcome_panel()
    st.markdown('<div class="sf-chat-label">Ask a question</div>', unsafe_allow_html=True)

    with st.form("ask_form"):
        question = st.text_area(
            "Question",
            placeholder="Ask a question (e.g., 'Where can I find DHA policy on ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦?')",
            height=90,
            label_visibility="collapsed",
        )

        colA, colB = st.columns([1, 1])
        with colA:
            run = st.form_submit_button("Get Answer", type="primary", use_container_width=True)
        with colB:
            pass
    st.markdown("</div>", unsafe_allow_html=True)

    if run and question.strip():
        with st.spinner("Retrieving evidence and generating a grounded response..."):
            try:
                resp = ask(question.strip(), top_k, allowed_sources=allowed or None)
                citations = resp.get("citations", [])

                left, right = st.columns([2, 1], gap="large")

                with left:
                    st.markdown("### Answer")
                    st.write(resp.get("answer", ""))

                    grounded = resp.get("grounded", False)
                    st.markdown(
                        f"**Grounded:** {'ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ Yes' if grounded else 'ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã‚Â¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â Insufficient evidence'}  \n"
                        f"**Indexed as of:** {resp.get('indexed_as_of', 'unknown')}"
                    )
                    render_feedback_controls(
                        question=question.strip(),
                        answer=str(resp.get("answer", "")),
                        citations=citations,
                        use_svg_icons=use_svg_feedback,
                    )

                with right:
                    st.markdown("### Evidence & Citations")
                    if not citations:
                        st.caption("No citations returned.")
                    else:
                        for i, c in enumerate(citations, start=1):
                            title = to_sentence_case(c.get("title", "Untitled") or "")
                            url = c.get("url", "")
                            score = float(c.get("score", 0.0))
                            source = c.get("source", "")
                            st.markdown(
                                f"**[{i}] {title}**  \n"
                                f"Source: `{source}`  \n"
                                f"Score: `{score:.3f}`"
                            )
                            if url:
                                st.link_button("Open source", url, use_container_width=True)

            except requests.HTTPError as e:
                st.caption("Something went wrong. The service may be temporarily unavailable.")
                print(f"Ask request failed: {e}")
            except Exception as e:
                st.caption("Something went wrong. The service may be temporarily unavailable.")
                print(f"Ask request failed: {e}")

# ----------------------------
# Footer
# ----------------------------
st.divider()
st.caption(f"{APP_VERSION}")
