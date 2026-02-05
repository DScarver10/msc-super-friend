# frontend/app.py
from __future__ import annotations

import json
from pathlib import Path

import requests
import streamlit as st

# ----------------------------
# Paths / constants
# ----------------------------
APP_ROOT = Path(__file__).resolve().parent
CONTENT_DIR = APP_ROOT / "content"
ASSETS_DIR = APP_ROOT / "assets"

MSC_BADGE_PATH = ASSETS_DIR / "msc.png"
AFMS_MSC_URL = "https://www.airforcemedicine.af.mil/About-Us/Medical-Branches/Medical-Service-Corps/"

BACKEND_URL = st.secrets.get("BACKEND_URL", "http://127.0.0.1:8000")


# ----------------------------
# Streamlit page config
# ----------------------------
st.set_page_config(
    page_title="MSC Super Friend",
    page_icon=str(MSC_BADGE_PATH) if MSC_BADGE_PATH.exists() else "📘",
    layout="wide",
)

# Optional UI polish (keeps it professional, not playful)
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 2.2rem; }
      h1, h2, h3 { letter-spacing: 0.2px; }
      .stButton button { border-radius: 6px; font-weight: 600; }
      section[data-testid="stSidebar"] h2 { letter-spacing: 0.3px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------
# Helpers
# ----------------------------
def load_json(filename: str):
    path = CONTENT_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


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


def render_links(links: list[dict]):
    if not links:
        st.markdown("**Links:** _None_")
        return
    st.markdown("**Links:**")
    for link in links:
        label = link.get("label", "Link")
        url = link.get("url", "")
        st.markdown(f"- [{label}]({url})")


def render_card_header(title: str, tags: list[str] | None, last_reviewed: str | None):
    st.markdown(f"### {title}")
    cols = st.columns([3, 1])
    with cols[0]:
        if tags:
            st.markdown(" • ".join([f"`{t}`" for t in tags]))
    with cols[1]:
        if last_reviewed:
            st.caption(f"Last reviewed: {last_reviewed}")


# ----------------------------
# Header (trust-first)
# ----------------------------
col_logo, col_title = st.columns([1, 6], vertical_alignment="center")
with col_logo:
    if MSC_BADGE_PATH.exists():
        st.image(str(MSC_BADGE_PATH), width=80)
with col_title:
    st.title("MSC Super Friend")
    st.caption("Curated MSC references + evidence-grounded retrieval. Public sources only. Do not enter PHI/PII.")

# Status strip (backend reachable?)
try:
    health = get_health()
    sources_list = health.get("sources", [])
    st.success(
        f"Backend OK • Indexed: {health.get('indexed_as_of')} • "
        f"Chunks: {health.get('num_chunks')} • "
        f"Sources: {', '.join(sources_list) if sources_list else 'None'}"
    )
except Exception as e:
    st.warning(f"Backend not reachable (RAG disabled): {e}")
    health = {"sources": [], "indexed_as_of": "unknown", "num_chunks": 0}
    sources_list = []

# Sidebar controls (RAG only)
st.sidebar.header("RAG Controls")
top_k = st.sidebar.slider("Evidence to retrieve (Top-K)", min_value=1, max_value=12, value=5)
allowed = st.sidebar.multiselect("Limit sources (optional)", options=sources_list, default=[])

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

# Tabs (no emoji / no kiddy icons)
tab1, tab2, tab3 = st.tabs(["Doctrine Library", "MSC Toolkit", "RAG Q&A"])


# ----------------------------
# Tab 1: Doctrine Library
# ----------------------------
with tab1:
    st.subheader("Doctrine Library")
    st.caption("A verified, searchable library of DHA and AFI Health Services publications.")

    try:
        afi = load_json("doctrine_afi41.json")
    except FileNotFoundError:
        st.error("Missing file: frontend/content/doctrine_afi41.json")
        st.stop()

    q = st.text_input("Search AFI 41-series", placeholder="Search by AFI number, title, tags, or use case...")
    if q:
        ql = q.lower()
        afi = [
            a for a in afi
            if ql in a.get("pub", "").lower()
            or ql in a.get("title", "").lower()
            or ql in a.get("why_it_matters", "").lower()
            or any(ql in t.lower() for t in a.get("tags", []))
            or any(ql in uc.lower() for uc in a.get("use_cases", []))
        ]

    for a in afi:
        pub = a.get("pub", "").strip()
        title = a.get("title", "").strip()
        display_title = f"{pub} — {title}" if pub else title

        with st.container(border=True):
            render_card_header(display_title, a.get("tags", []), a.get("last_reviewed"))
            st.write(a.get("why_it_matters", ""))

            use_cases = a.get("use_cases", [])
            if use_cases:
                st.markdown("**Use cases:**")
                for uc in use_cases:
                    st.markdown(f"- {uc}")

            render_links(a.get("official_links", []))

            notes = (a.get("notes") or "").strip()
            if notes:
                st.markdown("**Notes:**")
                st.write(notes)


# ----------------------------
# Tab 2: MSC Toolkit
# ----------------------------
with tab2:
    st.subheader("MSC Toolkit")
    st.caption("Helpful documents at your fingertips.")

    # 1) Direct link to AFMS MSC landing page (prominent)
    st.markdown("### Official MSC Landing Page")
    st.markdown(f"**[Open AFMS Medical Service Corps Page]({AFMS_MSC_URL})**")

    st.divider()

    # 2) Helpful documents from toolkit.json
    try:
        toolkit = load_json("toolkit.json")
    except FileNotFoundError:
        st.error("Missing file: frontend/content/toolkit.json")
        st.stop()

    q = st.text_input("Search toolkit documents", placeholder="Search by title, tags, or summary...")
    if q:
        ql = q.lower()
        toolkit = [
            t for t in toolkit
            if ql in t.get("title", "").lower()
            or ql in t.get("summary", "").lower()
            or any(ql in tag.lower() for tag in t.get("tags", []))
        ]

    for t in toolkit:
        with st.container(border=True):
            render_card_header(t.get("title", ""), t.get("tags", []), t.get("last_reviewed"))
            doc_type = (t.get("type") or "").strip()
            if doc_type:
                st.markdown(f"`{doc_type}`")
            st.write(t.get("summary", ""))
            render_links(t.get("official_links", []))


# ----------------------------
# Tab 3: RAG Q&A
# ----------------------------
with tab3:
    st.subheader("Ask Super Friend")
    st.caption("Answers are generated only from indexed sources. Citations are always shown.")

    if health.get("num_chunks", 0) == 0 or health.get("indexed_as_of") in ("not indexed", "unknown"):
        st.warning("Index not built yet. Run 'Rebuild Index (Ingest)' in the sidebar.")

    question = st.text_area(
        "Question",
        placeholder="Example: Summarize what is available on the DHA Policies page and where to find it.",
        height=90,
    )

    colA, colB = st.columns([1, 1])
    with colA:
        run = st.button("Get Answer", type="primary", use_container_width=True)
    with colB:
        st.markdown("**Trust rules:** citations always shown • refusal if evidence is weak • no PHI/PII")

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
                        st.info("No citations returned.")
                    else:
                        for i, c in enumerate(citations, start=1):
                            title = c.get("title", "Untitled")
                            url = c.get("url", "")
                            score = float(c.get("score", 0.0))
                            source = c.get("source", "")
                            st.markdown(
                                f"**[{i}] {title}**  \n"
                                f"Source: `{source}`  \n"
                                f"Score: `{score:.3f}`  \n"
                                f"[Open]({url})"
                            )

            except requests.HTTPError as e:
                try:
                    st.error(e.response.json())
                except Exception:
                    st.error(f"Request failed: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
