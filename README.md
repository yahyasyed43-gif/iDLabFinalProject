# iDLabFinalProject
import streamlit as st
import time

import streamlit as st 
import time

# ---------------- Page Setup ----------------
st.set_page_config(
    page_title="Innovative Dummies",
    page_icon="💰",
    layout="wide"
)

# ---------------- Styling ----------------
st.markdown("""
<style>

/* =========================
   GLOBAL APP BACKGROUND
========================= */
.stApp {
    background:
    radial-gradient(
        circle at top left,
        #534dbb,
        #2a1f67 45%,
        #010101 100%
    );
}

/* Remove Streamlit spacing */
.block-container {
    max-width: 1200px;
    padding-top: 1rem;
}

/* =========================
   REMOVE STREAMLIT UI BARS
========================= */
header[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
}

[data-testid="stToolbar"] {
    visibility: hidden;
    height: 0%;
}

[data-testid="stDecoration"] {
    display:none;
}

footer {
    background: transparent !important;
    visibility:hidden;
}

/* Bottom area (FIXED to match background) */
[data-testid="stBottom"],
[data-testid="stChatInputContainer"],
[data-testid="stChatInput"] {
    background: transparent !important;
    backdrop-filter: none !important;
    box-shadow: none !important;
}

/* Main container */
[data-testid="stAppViewContainer"] {
    background: transparent !important;
}

/* =========================
   HEADER
========================= */
.main-title {
    color:white;
    text-align:center;
    font-size:48px;
    font-weight:800;
    letter-spacing:1px;
}

.subtitle {
    color:#50d6a3;
    text-align:center;
    font-size:22px;
    font-weight:600;
    margin-bottom:30px;
}

/* =========================
   SIDEBAR
========================= */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #010101, #2a1f67);
    border-right: 2px solid #534dbb;
}

section[data-testid="stSidebar"] * {
    color:white;
}

section[data-testid="stSidebar"] h2 {
    color:#50d6a3;
}

/* =========================
   CHAT WINDOW (SOLID COLOR)
========================= */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #1a1447; /* solid dark panel */
    border: 2px solid #534dbb;
    border-radius: 30px;
    padding: 25px;
    box-shadow: 0px 20px 50px rgba(0,0,0,.45);
}

/* =========================
   USER MESSAGE
========================= */
.user-message {
    background: linear-gradient(135deg, #50d6a3, #1c866a);
    color:#010101;
    padding: 15px 20px;
    border-radius: 25px 25px 5px 25px;
    max-width: 60%;
    margin-left:auto;
    margin-bottom: 18px;
    font-size: 16px;
    font-weight: 600;
    box-shadow: 0px 10px 30px rgba(0,0,0,.35);
}

/* =========================
   AI MESSAGE
========================= */
.bot-message {
    background: rgba(255,255,255,.95);
    color:#010101;
    padding: 15px 20px;
    border-radius: 25px 25px 25px 5px;
    max-width: 60%;
    margin-right:auto;
    margin-bottom: 18px;
    font-size: 16px;
    box-shadow: 0px 10px 30px rgba(0,0,0,.35);
}

/* =========================
   INPUT BOX (MATCH BACKGROUND)
========================= */
div[data-testid="stChatInput"] textarea {
    color:#010101;
    font-size:16px;
}

/* Send button */
button {
    background: #534dbb !important;
    color:white !important;
    border-radius: 50% !important;
}

/* Alerts */
div[data-testid="stAlert"] {
    background: rgba(80,214,163,.15);
    border-radius: 15px;
}

</style>
""", unsafe_allow_html=True)

# ---------------- Header ----------------
st.markdown(
"""
<div class="main-title">
Innovative Dummies
</div>

<div class="subtitle">
AI-Powered Financial Intelligence
</div>
""",
unsafe_allow_html=True
)

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown("## 💰 Financial Assistant")
    st.write("""
Your AI assistant for:

• ETF research  
• Investment insights  
• Financial education  
• Market analysis  
• Portfolio analysis
""")

    with st.spinner("Connecting..."):
        time.sleep(2)

    st.success("System Ready")

# ---------------- Chat Memory ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- Chat Display ----------------
chat_container = st.container(height=430)

with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(
                f"""
                <div class="user-message">
                {message["content"]}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="bot-message">
                {message["content"]}
                </div>
                """,
                unsafe_allow_html=True
            )

# ---------------- Input ----------------
prompt = st.chat_input("Ask about ETFs, investing, or money...")

if prompt:
    st.session_state.messages.append({
        "role":"user",
        "content":prompt
    })

    # Placeholder bot response
    bot_response = prompt

    st.session_state.messages.append({
        "role":"assistant",
        "content":bot_response
    })

    st.rerun()
