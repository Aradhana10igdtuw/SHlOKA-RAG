import os
import requests
import streamlit as st
import base64
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = os.getenv("DATA_DIR", "data")

try:
    from ingest import ingest_documents
    LOCAL_FALLBACK_AVAILABLE = True
except Exception:
    LOCAL_FALLBACK_AVAILABLE = False

st.set_page_config(
    page_title="Shloka-AFI | Ayurvedic Scripture Analyzer",
    page_icon="🪷",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 1. API Health Check & Discovery (Run first to determine status badges)
api_url = "http://localhost:8000"
api_connected = False
groq_enabled = False
gemini_enabled = False

try:
    r = requests.get(f"{api_url}/health", timeout=2)
    if r.status_code == 200:
        api_connected = True
        health = r.json()
        groq_enabled = health.get("groq_configured", False)
        gemini_enabled = health.get("gemini_configured", False)
except Exception:
    pass

server_class = "online" if api_connected else "offline"
server_text = "Server Online" if api_connected else "Server Offline"
llm_class = "active" if (groq_enabled or gemini_enabled) else "offline"
llm_text = "Groq" if groq_enabled else ("Gemini" if gemini_enabled else "No LLM")

# 2. Sidebar Configuration & Theme Setup
with st.sidebar:
    st.markdown('<div class="sidebar-title">🪷 SHLOKA — AFI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">Scripture Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    
    # Theme Selector
    theme = st.selectbox(
        "Manuscript Style",
        ["Parchment (Light)", "Vellum (Dark)"],
        index=0
    )
    
    # Language Selector
    target_language = st.selectbox(
        "Analysis Language",
        ["English", "Hindi", "Sanskrit", "Spanish", "German", "French"],
        index=0
    )
    
    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    
    # Status badges
    st.markdown('<div class="sidebar-section-title">System Status</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sidebar-status-box">
        <div class="sidebar-status-item">
            <span>FastAPI Server</span>
            <span class="status-badge {server_class}">{server_text}</span>
        </div>
        <div class="sidebar-status-item">
            <span>LLM Provider</span>
            <span class="status-badge {llm_class}">{llm_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    
    # Retrieval Configuration (Top-K Slider)
    st.markdown('<div class="sidebar-section-title">Retrieval Depth</div>', unsafe_allow_html=True)
    top_k = st.slider(
        "Context Chunks Count",
        min_value=1,
        max_value=8,
        value=3,
        help="Number of document context chunks to retrieve from knowledge base for LLM analysis."
    )
    
    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    
    # Scripture Library Management
    st.markdown('<div class="sidebar-section-title">Scripture Library</div>', unsafe_allow_html=True)
    uploaded_txt = st.file_uploader("Add reference text (.txt)", type=["txt"], key="txt_upload")
    if uploaded_txt:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        with open(os.path.join(DATA_DIR, uploaded_txt.name), "wb") as f:
            f.write(uploaded_txt.getbuffer())
        st.success(f"Uploaded {uploaded_txt.name}")

    if st.button("Rebuild Vector DB"):
        if api_connected:
            with st.spinner("Ingesting new documents..."):
                try:
                    r = requests.post(f"{api_url}/ingest", timeout=60)
                    d = r.json()
                    if d.get("status") == "success":
                        st.success(d.get("message"))
                    else:
                        st.warning(d.get("message"))
                except Exception as e:
                    st.error(str(e))
        else:
            st.error("Server offline.")

    # Ingested Files List
    if os.path.exists(DATA_DIR):
        files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f)) and not f.endswith(".gitkeep")]
        if files:
            st.markdown('<div class="sidebar-sub-title">Ingested Scripts:</div>', unsafe_allow_html=True)
            for f in files:
                kb = os.path.getsize(os.path.join(DATA_DIR, f)) / 1024
                st.caption(f"📜 {f} ({kb:.1f} KB)")


# 3. Dynamic Stylesheet Variables based on selected theme
if theme == "Parchment (Light)":
    main_bg = """
        linear-gradient(rgba(244, 237, 211, 0.94), rgba(244, 237, 211, 0.94)),
        url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.08'/%3E%3C/svg%3E"),
        radial-gradient(circle at center, #fbf8eb 0%, #ded0a5 100%)
    """
    sidebar_bg = """
        linear-gradient(rgba(238, 231, 207, 0.96), rgba(238, 231, 207, 0.96)),
        url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.08'/%3E%3C/svg%3E"),
        radial-gradient(circle at center, #f2ead0 0%, #d4c597 100%)
    """
    text_color = "#3a2c1a"
    muted_text = "#705b45"
    accent_color = "#8b6208"
    card_bg = "rgba(252, 249, 239, 0.85)"
    border_color = "rgba(139, 98, 8, 0.25)"
    input_bg = "rgba(255, 255, 255, 0.45)"
    input_text = "#3a2c1a"
    input_border = "rgba(139, 98, 8, 0.3)"
    tag_bg = "rgba(139, 98, 8, 0.06)"
    tag_border = "rgba(139, 98, 8, 0.3)"
    tag_text = "#8b6208"
    button_bg = "transparent"
    button_hover_bg = "rgba(139, 98, 8, 0.08)"
    button_text = "#8b6208"
    shadow_color = "rgba(139, 98, 8, 0.1)"
    online_color = "#2e7d32"
    online_bg = "rgba(46, 125, 50, 0.1)"
    online_border = "rgba(46, 125, 50, 0.25)"
    offline_color = "#c62828"
    offline_bg = "rgba(198, 40, 40, 0.1)"
    offline_border = "rgba(198, 40, 40, 0.25)"
    active_color = "#8b6208"
    active_bg = "rgba(139, 98, 8, 0.1)"
    active_border = "rgba(139, 98, 8, 0.25)"
    vata_color = "#4c7d9a"
    pitta_color = "#c65f33"
    kapha_color = "#588157"
    dosha_bg = "rgba(0, 0, 0, 0.02)"
else: # Vellum (Dark)
    main_bg = """
        linear-gradient(rgba(22, 19, 15, 0.96), rgba(22, 19, 15, 0.96)),
        url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.16'/%3E%3C/svg%3E"),
        radial-gradient(circle at center, #2e261e 0%, #0c0a07 100%)
    """
    sidebar_bg = """
        linear-gradient(rgba(17, 14, 11, 0.97), rgba(17, 14, 11, 0.97)),
        url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.16'/%3E%3C/svg%3E"),
        radial-gradient(circle at center, #241e17 0%, #070504 100%)
    """
    text_color = "#e6ddc6"
    muted_text = "#8f836f"
    accent_color = "#d9b356"
    card_bg = "rgba(28, 24, 18, 0.85)"
    border_color = "rgba(217, 179, 86, 0.25)"
    input_bg = "rgba(0, 0, 0, 0.3)"
    input_text = "#e6ddc6"
    input_border = "rgba(217, 179, 86, 0.3)"
    tag_bg = "rgba(217, 179, 86, 0.05)"
    tag_border = "rgba(217, 179, 86, 0.3)"
    tag_text = "#d9b356"
    button_bg = "transparent"
    button_hover_bg = "rgba(217, 179, 86, 0.08)"
    button_text = "#d9b356"
    shadow_color = "rgba(0, 0, 0, 0.3)"
    online_color = "#a5d6a7"
    online_bg = "rgba(165, 214, 167, 0.08)"
    online_border = "rgba(165, 214, 167, 0.25)"
    offline_color = "#ef9a9a"
    offline_bg = "rgba(239, 154, 154, 0.08)"
    offline_border = "rgba(239, 154, 154, 0.25)"
    active_color = "#d9b356"
    active_bg = "rgba(217, 179, 86, 0.08)"
    active_border = "rgba(217, 179, 86, 0.25)"
    vata_color = "#81b1d3"
    pitta_color = "#ff8a5c"
    kapha_color = "#8cb38a"
    dosha_bg = "rgba(255, 255, 255, 0.02)"

# Inject custom HTML Stylesheet
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Cinzel:wght@400;500;700&family=Kalam:wght@300;400;700&family=Inter:wght@300;400;500&display=swap');

[data-testid="collapsedControl"] {{ display: none; }}
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header {{ visibility: hidden; }}

.stApp {{ 
    background: {main_bg} !important; 
    color: {text_color} !important;
}}

[data-testid="stSidebar"] {{
    background: {sidebar_bg} !important;
    border-right: 1px solid {border_color} !important;
}}

.main .block-container {{ 
    padding-top: 2.5rem; 
    padding-bottom: 4rem; 
    max-width: 860px; 
}}

/* Typography */
.page-title {{
    font-family: 'Cinzel', serif;
    font-weight: 500; 
    font-size: 3.2rem; 
    color: {accent_color};
    text-align: center; 
    letter-spacing: 0.15em; 
    margin-bottom: 0.1rem;
    text-shadow: 1px 1px 2px {shadow_color};
}}

.page-subtitle {{
    font-family: 'Cormorant Garamond', serif; 
    font-weight: 400; 
    font-size: 1.15rem;
    font-style: italic;
    color: {muted_text}; 
    text-align: center; 
    letter-spacing: 0.2em;
    text-transform: uppercase; 
    margin-bottom: 2.5rem;
}}

.sidebar-title {{
    font-family: 'Cinzel', serif;
    font-weight: 500;
    font-size: 1.4rem;
    color: {accent_color};
    text-align: center;
    letter-spacing: 0.1em;
    margin-top: 1rem;
}}

.sidebar-subtitle {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 0.95rem;
    font-style: italic;
    color: {muted_text};
    text-align: center;
    margin-bottom: 0.5rem;
}}

.sidebar-section-title {{
    font-family: 'Cinzel', serif;
    font-size: 0.85rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    color: {accent_color};
    margin: 1.2rem 0 0.6rem 0;
    text-transform: uppercase;
}}

.sidebar-sub-title {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 0.85rem;
    font-style: italic;
    color: {muted_text};
    margin-top: 0.8rem;
    margin-bottom: 0.4rem;
}}

.sidebar-divider {{
    border: none;
    border-top: 1px solid {border_color};
    margin: 1rem 0;
}}

/* Sidebar Status styling */
.sidebar-status-box {{
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin-bottom: 0.5rem;
}}

.sidebar-status-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.35rem 0.6rem;
    border-radius: 6px;
    border: 1px dashed {border_color};
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: {text_color};
}}

.status-badge {{
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.status-badge.online {{
    background: {online_bg};
    color: {online_color};
    border: 1px solid {online_border};
}}

.status-badge.offline {{
    background: {offline_bg};
    color: {offline_color};
    border: 1px solid {offline_border};
}}

.status-badge.active {{
    background: {active_bg};
    color: {active_color};
    border: 1px solid {active_border};
}}

/* Form elements & Inputs */
.stTextArea textarea {{
    background: {input_bg} !important;
    border: 1px solid {input_border} !important;
    border-radius: 8px !important; 
    color: {input_text} !important;
    font-family: 'Kalam', cursive !important;
    font-size: 1.25rem !important; 
    line-height: 1.8 !important;
    box-shadow: inset 1px 1px 3px rgba(0,0,0,0.05) !important;
}}

.stTextArea textarea:focus {{
    border-color: {accent_color} !important;
    box-shadow: 0 0 0 1px {accent_color} !important;
}}

div.stButton > button {{
    background: {button_bg} !important;
    border: 1px solid {accent_color} !important;
    color: {button_text} !important; 
    font-family: 'Cinzel', serif !important;
    font-weight: 500 !important; 
    font-size: 0.9rem !important;
    letter-spacing: 0.2em !important; 
    text-transform: uppercase !important;
    border-radius: 6px !important; 
    padding: 0.6rem 2.5rem !important;
    transition: all 0.3s ease !important; 
    width: 100% !important;
    box-shadow: 0 4px 6px {shadow_color} !important;
}}

div.stButton > button:hover {{
    background: {button_hover_bg} !important;
    border-color: {accent_color} !important;
    box-shadow: 0 0 15px rgba(201, 168, 76, 0.15) !important;
}}

/* Result Panel */
.result-panel {{
    background: {card_bg}; 
    border: 3px double {border_color};
    border-radius: 12px; 
    padding: 2.5rem; 
    margin-top: 2rem;
    box-shadow: 0 10px 30px {shadow_color};
}}

.sanskrit-text {{
    font-family: 'Kalam', cursive; 
    font-size: 1.8rem;
    font-weight: 400;
    color: {accent_color}; 
    text-align: center; 
    padding: 1.8rem;
    border-top: 1px solid {border_color};
    border-bottom: 1px solid {border_color};
    line-height: 2; 
    margin: 1rem 0 1.5rem 0; 
    letter-spacing: 0.02em;
    text-shadow: 0.5px 0.5px 1px rgba(0,0,0,0.1);
}}

.translation-text {{
    font-family: 'Cormorant Garamond', serif; 
    font-weight: 400; 
    font-size: 1.3rem;
    color: {text_color}; 
    line-height: 1.8; 
    padding: 1.2rem 0;
    border-bottom: 1px solid {border_color}; 
    margin-bottom: 1.5rem;
    font-style: italic;
}}

.result-label {{
    font-family: 'Cinzel', serif; 
    font-size: 0.75rem; 
    font-weight: 500;
    letter-spacing: 0.15em; 
    text-transform: uppercase; 
    color: {muted_text}; 
    margin-bottom: 0.6rem;
}}

.tag {{
    display: inline-block; 
    background: {tag_bg};
    border: 1px solid {tag_border}; 
    color: {tag_text};
    border-radius: 4px; 
    padding: 0.2rem 0.8rem; 
    font-size: 0.85rem;
    margin: 0.25rem; 
    font-family: 'Cormorant Garamond', serif; 
    font-weight: 500; 
    letter-spacing: 0.05em;
}}

.confidence-num {{
    font-family: 'Cormorant Garamond', serif; 
    font-size: 2.8rem;
    font-weight: 300; 
    color: {accent_color}; 
    line-height: 1;
}}

.modern-box {{
    background: rgba(0, 0, 0, 0.02); 
    border-left: 2px solid {accent_color};
    padding: 1.2rem 1.4rem; 
    margin-top: 0.5rem; 
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.15rem; 
    color: {text_color}; 
    line-height: 1.7;
    border-radius: 0 6px 6px 0;
    border-top: 1px solid {border_color};
    border-right: 1px solid {border_color};
    border-bottom: 1px solid {border_color};
}}

.section-title {{
    font-family: 'Cinzel', serif; 
    font-size: 1.15rem;
    font-weight: 500; 
    color: {accent_color}; 
    letter-spacing: 0.12em; 
    margin: 2.2rem 0 0.8rem 0;
    text-transform: uppercase;
}}

.formulation-box {{
    background: rgba(201,168,76,0.03); 
    border: 1px solid {border_color};
    border-radius: 8px; 
    padding: 1.2rem 1.4rem; 
    margin-bottom: 1.5rem;
}}

.formulation-name {{
    font-family: 'Cinzel', serif; 
    font-size: 1.5rem;
    color: {accent_color}; 
    font-weight: 500; 
    margin-bottom: 0.4rem;
}}

.formulation-meta {{
    font-family: 'Cormorant Garamond', serif; 
    font-size: 0.95rem;
    font-style: italic;
    color: {muted_text}; 
    letter-spacing: 0.05em;
}}

.dosage-box {{
    background: rgba(0,0,0,0.02); 
    border: 1px solid {border_color};
    border-radius: 8px; 
    padding: 1.2rem; 
    margin-top: 0.5rem;
    display: flex; 
    gap: 2.5rem; 
    flex-wrap: wrap;
}}

.dosage-item {{ 
    font-family: 'Cormorant Garamond', serif; 
}}

.dosage-label {{ 
    font-family: 'Cinzel', serif;
    font-size: 0.7rem; 
    color: {muted_text}; 
    text-transform: uppercase; 
    letter-spacing: 0.12em; 
}}

.dosage-value {{ 
    font-size: 1.05rem; 
    color: {text_color}; 
    font-weight: 500; 
    margin-top: 0.2rem; 
}}

.rasa-row {{ 
    display: flex; 
    gap: 2.2rem; 
    flex-wrap: wrap; 
    margin-top: 0.5rem; 
    border: 1px solid {border_color};
    border-radius: 8px;
    padding: 1.2rem;
    background: rgba(0,0,0,0.02);
}}

.rasa-item {{ 
    text-align: center; 
}}

.rasa-label {{ 
    font-family: 'Cinzel', serif;
    font-size: 0.65rem; 
    color: {muted_text}; 
    text-transform: uppercase; 
    letter-spacing: 0.1em; 
}}

.rasa-value {{ 
    font-size: 1.1rem; 
    color: {accent_color}; 
    font-family: 'Cormorant Garamond', serif; 
    font-style: italic; 
    margin-top: 0.2rem;
}}

/* Fix markdown paragraphs inside custom layout */
.stMarkdown p {{
    color: {text_color} !important;
}}

/* Dosha balance meters */
.dosha-container {{
    background: {dosha_bg};
    border: 1px solid {border_color};
    border-radius: 8px;
    padding: 1.2rem;
    margin-top: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}}

.dosha-row-item {{
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
}}

.dosha-info-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'Cinzel', serif;
    font-size: 0.75rem;
    color: {text_color};
    letter-spacing: 0.05em;
}}

.dosha-name-val {{
    font-weight: 500;
}}

.dosha-percent-val {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 0.95rem;
    font-style: italic;
    color: {accent_color};
}}

.dosha-bar-outer {{
    background: rgba(0, 0, 0, 0.08);
    border-radius: 4px;
    height: 8px;
    width: 100%;
    overflow: hidden;
}}

.dosha-bar-inner {{
    height: 100%;
    border-radius: 4px;
}}

.dosha-bar-inner.vata {{
    background: {vata_color};
}}
.dosha-bar-inner.pitta {{
    background: {pitta_color};
}}
.dosha-bar-inner.kapha {{
    background: {kapha_color};
}}
</style>
""", unsafe_allow_html=True)

# 4. Main Title Section
st.markdown('<div class="page-title">Shloka — AFI</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Ayurvedic Scripture Intelligence</div>', unsafe_allow_html=True)

# 5. Core Interface Input Elements
shloka_input = st.text_area(
    "", placeholder="Enter Sanskrit shloka or formulation text here...",
    height=140, label_visibility="collapsed"
)
uploaded_image = st.file_uploader("or upload a scripture image", type=["png", "jpg", "jpeg"])
if uploaded_image:
    st.image(uploaded_image, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# 6. Action Execution (Analyze & Translate)
if st.button("Analyze & Translate"):
    has_text = bool(shloka_input.strip())
    has_image = uploaded_image is not None

    if not has_text and not has_image:
        st.warning("Please provide a shloka or upload an image.")
    elif not api_connected:
        st.error("Server offline — run uvicorn first.")
    elif not (groq_enabled or gemini_enabled):
        st.error("No LLM API key configured in .env")
    else:
        with st.spinner("Analyzing manuscript scripture..."):
            try:
                payload = {"top_k": top_k, "target_language": target_language}
                if has_image:
                    payload["image_base64"] = base64.b64encode(uploaded_image.read()).decode("utf-8")
                else:
                    payload["shloka"] = shloka_input.strip()

                res = requests.post(f"{api_url}/analyze", json=payload, timeout=120)

                if res.status_code == 200:
                    data = res.json()
                    st.markdown('<div class="result-panel">', unsafe_allow_html=True)

                    # Sanskrit text (transcribed or input)
                    transcribed = data.get("transcribed_text", "")
                    if transcribed:
                        st.markdown(f'<div class="sanskrit-text">{transcribed}</div>', unsafe_allow_html=True)

                    # Formulation info card
                    fname = data.get("formulation_name", "")
                    ftype = data.get("formulation_type", "")
                    fref  = data.get("source_reference", "")
                    if fname or ftype:
                        st.markdown(f"""
                        <div class="formulation-box">
                            <div class="formulation-name">{fname or "—"}</div>
                            <div class="formulation-meta">{ftype}{' · ' + fref if fref else ''}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Scripture Translation
                    st.markdown(f'<div class="translation-text">{data.get("translation", "—")}</div>', unsafe_allow_html=True)

                    # Metadata Grid (Herbs, Doshas, and AI Confidence)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        herbs = data.get("herbs", [])
                        herbs_html = "".join([f'<span class="tag">{h}</span>' for h in herbs]) if herbs else "<span class='tag' style='opacity:0.4'>—</span>"
                        st.markdown(f'<div class="result-label">Herbs</div>{herbs_html}', unsafe_allow_html=True)
                    with col2:
                        doshas = data.get("doshas", [])
                        doshas_html = "".join([f'<span class="tag">{d}</span>' for d in doshas]) if doshas else "<span class='tag' style='opacity:0.4'>—</span>"
                        st.markdown(f'<div class="result-label">Doshas</div>{doshas_html}', unsafe_allow_html=True)
                    with col3:
                        confidence = data.get("confidence", 0.0)
                        st.markdown(f'<div class="result-label">Confidence</div><div class="confidence-num">{int(confidence*100)}%</div>', unsafe_allow_html=True)

                    # Dosha Balance Meter section
                    dosha_influence = data.get("dosha_influence", {"vata": 0, "pitta": 0, "kapha": 0})
                    if any(dosha_influence.values()):
                        st.markdown('<div class="section-title">Dosha Balance Analysis</div>', unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="dosha-container">
                            <div class="dosha-row-item">
                                <div class="dosha-info-header">
                                    <span class="dosha-name-val">Vata (Air & Ether)</span>
                                    <span class="dosha-percent-val">{dosha_influence.get('vata', 0)}%</span>
                                </div>
                                <div class="dosha-bar-outer">
                                    <div class="dosha-bar-inner vata" style="width: {dosha_influence.get('vata', 0)}%;"></div>
                                </div>
                            </div>
                            <div class="dosha-row-item">
                                <div class="dosha-info-header">
                                    <span class="dosha-name-val">Pitta (Fire & Water)</span>
                                    <span class="dosha-percent-val">{dosha_influence.get('pitta', 0)}%</span>
                                </div>
                                <div class="dosha-bar-outer">
                                    <div class="dosha-bar-inner pitta" style="width: {dosha_influence.get('pitta', 0)}%;"></div>
                                </div>
                            </div>
                            <div class="dosha-row-item">
                                <div class="dosha-info-header">
                                    <span class="dosha-name-val">Kapha (Water & Earth)</span>
                                    <span class="dosha-percent-val">{dosha_influence.get('kapha', 0)}%</span>
                                </div>
                                <div class="dosha-bar-outer">
                                    <div class="dosha-bar-inner kapha" style="width: {dosha_influence.get('kapha', 0)}%;"></div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Rasa Panchaka Attributes
                    rasa = data.get("rasa", [])
                    virya = data.get("virya", "")
                    vipaka = data.get("vipaka", "")
                    guna = data.get("guna", [])
                    if rasa or virya or vipaka:
                        st.markdown('<div class="section-title">Rasa Panchaka</div>', unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="rasa-row">
                            <div class="rasa-item"><div class="rasa-label">Rasa</div><div class="rasa-value">{', '.join(rasa) if rasa else '—'}</div></div>
                            <div class="rasa-item"><div class="rasa-label">Virya</div><div class="rasa-value">{virya or '—'}</div></div>
                            <div class="rasa-item"><div class="rasa-label">Vipaka</div><div class="rasa-value">{vipaka or '—'}</div></div>
                            <div class="rasa-item"><div class="rasa-label">Guna</div><div class="rasa-value">{', '.join(guna) if guna else '—'}</div></div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Ingredients breakdown table
                    ingredients = data.get("ingredients", [])
                    if ingredients:
                        st.markdown('<div class="section-title">Ingredients</div>', unsafe_allow_html=True)
                        import pandas as pd
                        df_ing = pd.DataFrame(ingredients)
                        df_ing.columns = [c.replace("_", " ").title() for c in df_ing.columns]
                        st.dataframe(df_ing, use_container_width=True, hide_index=True)

                    # Dosage instruction
                    dosage = data.get("dosage", {})
                    if dosage and any(dosage.values()):
                        st.markdown('<div class="section-title">Dosage</div>', unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="dosage-box">
                            <div class="dosage-item"><div class="dosage-label">Amount</div><div class="dosage-value">{dosage.get('amount') or '—'}</div></div>
                            <div class="dosage-item"><div class="dosage-label">Frequency</div><div class="dosage-value">{dosage.get('frequency') or '—'}</div></div>
                            <div class="dosage-item"><div class="dosage-label">Anupana</div><div class="dosage-value">{dosage.get('anupana') or '—'}</div></div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Actions tag section
                    actions = data.get("actions", [])
                    if actions:
                        st.markdown('<div class="section-title">Therapeutic Actions</div>', unsafe_allow_html=True)
                        st.markdown("".join([f'<span class="tag">{a}</span>' for a in actions]), unsafe_allow_html=True)

                    # Targeted Diseases
                    diseases = data.get("diseases", [])
                    if diseases:
                        st.markdown('<div class="section-title">Addressed Conditions</div>', unsafe_allow_html=True)
                        st.markdown("".join([f'<span class="tag">{d}</span>' for d in diseases]), unsafe_allow_html=True)

                    # Body Systems
                    body_systems = data.get("body_systems", [])
                    if body_systems:
                        st.markdown('<div class="section-title">Body Systems</div>', unsafe_allow_html=True)
                        st.markdown("".join([f'<span class="tag">{b}</span>' for b in body_systems]), unsafe_allow_html=True)

                    # Contraindications
                    contra = data.get("contraindications", [])
                    if contra:
                        st.markdown('<div class="section-title">Contraindications</div>', unsafe_allow_html=True)
                        st.markdown("".join([f'<span class="tag">{c}</span>' for c in contra]), unsafe_allow_html=True)

                    # Modern Interpretation box
                    modern = data.get("modern_interpretation", "")
                    if modern:
                        st.markdown('<div class="section-title">Modern Interpretation</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="modern-box">{modern}</div>', unsafe_allow_html=True)

                    # Word Meanings Table
                    word_meanings = data.get("word_meanings", [])
                    if word_meanings:
                        st.markdown('<div class="section-title">Word Meanings</div>', unsafe_allow_html=True)
                        import pandas as pd
                        st.dataframe(pd.DataFrame(word_meanings), use_container_width=True, hide_index=True)

                    st.markdown('</div>', unsafe_allow_html=True)

                    # Raw API response debugging expander
                    with st.expander("Raw analysis payload (JSON)"):
                        st.json(data)
                else:
                    st.error(f"Analysis failed: {res.json().get('detail', res.text)}")

            except Exception as e:
                st.error(f"Error executing analysis: {e}")

st.markdown("<br><br>", unsafe_allow_html=True)