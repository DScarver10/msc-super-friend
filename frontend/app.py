# frontend/app.py
from __future__ import annotations

import csv
import html
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
SEED_CSV_PATH = APP_ROOT / "content" / "afi41_seed.csv"

AFMS_MSC_URL = "https://www.airforcemedicine.af.mil/About-Us/Medical-Branches/Medical-Service-Corps/"
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")
BACKEND_URL_CONFIGURED = "BACKEND_URL" in st.secrets

# ----------------------------
# Streamlit page config
# ----------------------------
st.set_page_config(
    page_title="MSC Super Friend",
    page_icon=str(MSC_BADGE_PATH) if MSC_BADGE_PATH.exists() else "📘",
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
    st.caption("Public sources only. Do not enter PHI/PII.")


def render_welcome_panel():
    icon = f"<img src='{BOT_ICON_URI}' alt='Bot'/>" if BOT_ICON_URI else "🤖"
    st.markdown(
        f"""
        <div class="sf-welcome">
          <div class="sf-avatar">{icon}</div>
          <div>
            <h3>Hi! I’m MSC Super Friend.</h3>
            <p>Ask me to find guidance, summarize references, or point you to the right AFI or DHA publication.</p>
            <div class="muted">Public sources only. Do not enter PHI/PII.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_links_as_buttons(links: list[dict]):
    # Cleaner than raw markdown link list, still “trust-first”
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
    # stable enough within this run; we’ll re-map each rerun from JSON
    return f"{kind}:{idx}"


def render_feedback_controls(question: str, answer: str, citations: list[dict] | None):
    """
    Renders 👍 / 👎 feedback controls under an answer.
    Stores feedback via POST /feedback.
    """
    citations = citations or []

    # Stable per-question/answer key
    q_id = _hash_text(question.strip())
    a_id = _hash_text(answer.strip())
    key_prefix = f"fb_{q_id}_{a_id}"

    if key_prefix not in st.session_state:
        st.session_state[key_prefix] = {"vote": None}

    vote = st.session_state[key_prefix]["vote"]

    # Wrapper for CSS pill styling
    st.markdown('<div class="sf-feedback">', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 6], vertical_alignment="center")

    with c1:
        st.markdown('<div class="is-selected">' if vote == "up" else "<div>", unsafe_allow_html=True)
        up = st.button("👍", key=f"{key_prefix}_up")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="is-selected">' if vote == "down" else "<div>", unsafe_allow_html=True)
        down = st.button("👎", key=f"{key_prefix}_down")
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        if vote == "up":
            st.caption("Recorded: Helpful")
        elif vote == "down":
            st.caption("Recorded: Not helpful")

    st.markdown("</div>", unsafe_allow_html=True)

    # Handle clicks
    if up:
        payload = {
            "vote": "up",
            "question_id": q_id,
            "answer_id": a_id,
            "question": question,
            "answer": answer,
            "citations": citations,
        }
        submit_feedback(payload)
        st.session_state[key_prefix]["vote"] = "up"
        st.toast("Thanks — feedback recorded", icon="✅")

    if down:
        payload = {
            "vote": "down",
            "question_id": q_id,
            "answer_id": a_id,
            "question": question,
            "answer": answer,
            "citations": citations,
        }
        submit_feedback(payload)
        st.session_state[key_prefix]["vote"] = "down"
        st.toast("Thanks — feedback recorded", icon="✅")


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
                f"Indexed: {result.get('indexed_as_of')} • Chunks: {result.get('num_chunks')} • Skipped: {result.get('skipped_items')}"
            )
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Ingest failed: {e}")

st.sidebar.divider()
st.sidebar.caption("Tip: Prefer direct official PDFs for maximum trust and speed.")

debug_enabled = st.sidebar.checkbox("DEBUG")
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
tab1, tab2, tab3 = st.tabs(["📚 Doctrine Library", "🧰 MSC Toolkit", "💬 Ask Super Friend"])

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
        st.error("Missing or empty file: frontend/content/afi41_seed.csv")
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

    # If open token points to afi detail, render detail
    if st.session_state.open_kind == "afi" and st.session_state.open_idx is not None:
        idx = st.session_state.open_idx
        if 0 <= idx < len(afi):
            a = afi[idx]
            pub = clean_text(a.get("pub"))
            title = to_sentence_case(a.get("title") or "")
            st.markdown(f"### {pub} — {title}" if pub else f"### {title}")

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

            if st.button("← Back to list", use_container_width=True):
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
            display_title = f"{pub} — {title}" if pub else title
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
        placeholder="Search toolkit documents by title, tags, or summary…",
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

            if st.button("← Back to toolkit", use_container_width=True):
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
# Tab 3: Ask Super Friend
# ----------------------------
with tab3:
    st.subheader("Ask Super Friend")
    st.caption("Citations are always shown.")

    # Welcome panel (visual polish + guidance)
    st.markdown('<div class="sf-chat-wrap">', unsafe_allow_html=True)
    render_welcome_panel()
    st.markdown('<div class="sf-chat-label">Ask a question</div>', unsafe_allow_html=True)

    with st.form("ask_form"):
        question = st.text_area(
            "Question",
            placeholder="Ask a question (e.g., 'Where can I find DHA policy on …?')",
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

                left, right = st.columns([2, 1], gap="large")

                with left:
                    st.markdown("### Answer")
                    st.write(resp.get("answer", ""))

                    grounded = resp.get("grounded", False)
                    st.markdown(
                        f"**Grounded:** {'✅ Yes' if grounded else '⚠️ Insufficient evidence'}  \n"
                        f"**Indexed as of:** {resp.get('indexed_as_of', 'unknown')}"
                    )

                with right:
                    st.markdown("### Evidence & Citations")
                    citations = resp.get("citations", [])
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
st.caption("Built for MSCs | Version 1.0")
