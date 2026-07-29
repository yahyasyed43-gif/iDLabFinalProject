import streamlit as st
import time

# ---------------- Page Setup ----------------
st.set_page_config(page_title="ETF Engine", page_icon="🤖")

# ---------------- Title ----------------
title_col1, title_col2 = st.columns([0.8, 0.2])

with title_col1:
    st.title("ETF Engine")
    st.subheader("Need help with extra cash?", anchor=None, help=None, divider="blue", width="stretch")

with title_col2:
    st.image("uploaded_image.png", width=120) 

# ---------------- Sidebar ----------------
with st.sidebar:
  # Smaller version of the image at top of sidebar
    st.image("uploaded_image.png", width=60)    # 🔥 Smaller sidebar image

    st.markdown("## 💰 Financial Assistant")

    st.write("""
Your AI assistant for:

• ETF research  
• Investment insights  
• Financial education  
• Market analysis  
• Portfolio analysis
""")

    with st.spinner("Loading..."):
        time.sleep(1)

    st.success("Ready!")

# ---------------- CSS ----------------
st.markdown("""
<style>

/* =========================
   GLOBAL BACKGROUND (WHITE)
========================= */
.stApp {
    background: #ffffff !important;
}

/* =========================
   SIDEBAR (YOUR UPDATED COLORS)
========================= */
section[data-testid="stSidebar"] {
    background: #1c866a !important;
    border-right: 2px solid #1c866a;
}

section[data-testid="stSidebar"] * {
    color: #010101 !important;
}

/* Fix white echo code block */
div[data-testid="stCodeBlock"] {
    background: #50d6a3 !important;
    color: #1c866a !important;
    border: 1px solid #1c866a !important;
    border-radius: 10px !important;
}
            /* =========================
   FORCE ALL SIDEBAR BOXES TO ELM GREEN
========================= */

section[data-testid="stSidebar"] div[data-testid="stMarkdown"],
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"],
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"],
section[data-testid="stSidebar"] div[data-testid="stExpander"],
section[data-testid="stSidebar"] div[data-testid="stAlert"],
section[data-testid="stSidebar"] div[data-testid="stContainer"] {
    background-color: #1c866a !important;   /* elm green */
    color: #ffffff !important;              /* white text */
    border-radius: 8px !important;
    padding: 6px !important;
}

div[data-testid="stCodeBlock"] pre {
    background: #1c866a !important;
    color: #1c866a !important;
}

/* =========================
   TOP & BOTTOM BARS (WHITE)
========================= */
header[data-testid="stHeader"],
[data-testid="stBottomBlockContainer"],
[data-testid="stBottom"],
[data-testid="stChatMessageInput"],
[data-testid="stChatInputContainer"],
[data-testid="stElementContainer"] {
    background: #ffffff !important;
    color: #010101 !important;
    border: none !important;
    box-shadow: none !important;
}

/* =========================
   TEXT COLOR SYSTEM
========================= */
html, body, .stApp, .block-container {
    color: #010101 !important;
}

h2, h3 {
    color: #1c866a !important;
}

p, span, label {
    color: #534dbb !important;
}

h1 {
    color: #010101 !important;
}

/* =========================
   CHAT BUBBLES
========================= */
.user-message {
    background-color: #1c866a;
    color: white;
    padding: 12px 16px;
    border-radius: 18px;
    max-width: 70%;
    margin-left: auto;
    margin-bottom: 10px;
    word-wrap: break-word;
}

.bot-message {
    background-color: #E5E5EA;
    color: black;
    padding: 12px 16px;
    border-radius: 18px;
    max-width: 70%;
    margin-right: auto;
    margin-bottom: 10px;
    word-wrap: break-word;
}

/* =========================
   BUTTON STYLING (#aba7c2)
========================= */
.stButton > button {
    background-color: #aba7c2 !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 8px 14px !important;
    font-size: 14px !important;
}

.stButton > button:hover {
    background-color: #c3c0d8 !important;
    color: white !important;
}

/* =========================
   PROMPTER (WHITE INPUT BOX)
========================= */
div[data-testid="stChatInput"] {
    background: white !important;
    border: 3px solid #50d6a3 !important;
    border-radius: 30px !important;
    box-shadow: 0px 10px 30px rgba(0,0,0,.2) !important;
}

div[data-testid="stChatInput"] textarea {
    color: #010101 !important;
    font-size: 16px !important;
}

div[data-testid="stChatInput"] textarea::placeholder {
    color: #534dbb !important;
}

</style>
""", unsafe_allow_html=True)


# ---------------- Chat History ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- Flags ----------------
if "config_completed" not in st.session_state:
    st.session_state.config_completed = False

if "show_config" not in st.session_state:
    st.session_state.show_config = False


# ---------------- Output Area ----------------
chat_container = st.container(height=280)

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


# ---------------- Example Prompt Buttons ----------------
st.markdown("### Try an example prompt:")

colA, colB, colC = st.columns(3)

with colA:
    if st.button("Compare tech ETFs", key="ex1"):
        st.session_state.user_prompt = "Compare tech ETFs"
        st.session_state.messages.append({"role": "user", "content": st.session_state.user_prompt})

        if not st.session_state.config_completed:
            st.session_state.show_config = True
        else:
            st.session_state.messages.append({"role": "assistant", "content": f"You said: {st.session_state.user_prompt}"})

        st.rerun()

with colB:
    if st.button("Find low-risk ETFs", key="ex2"):
        st.session_state.user_prompt = "Find low-risk ETFs"
        st.session_state.messages.append({"role": "user", "content": st.session_state.user_prompt})

        if not st.session_state.config_completed:
            st.session_state.show_config = True
        else:
            st.session_state.messages.append({"role": "assistant", "content": f"You said: {st.session_state.user_prompt}"})

        st.rerun()

with colC:
    if st.button("Best ETFs for beginners", key="ex3"):
        st.session_state.user_prompt = "Best ETFs for beginners"
        st.session_state.messages.append({"role": "user", "content": st.session_state.user_prompt})

        if not st.session_state.config_completed:
            st.session_state.show_config = True
        else:
            st.session_state.messages.append({"role": "assistant", "content": f"You said: {st.session_state.user_prompt}"})

        st.rerun()


# ---------------- Prompt Input ----------------
prompt = st.chat_input("Type your message...")

if prompt:
    st.session_state.user_prompt = prompt
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not st.session_state.config_completed:
        st.session_state.show_config = True
    else:
        st.session_state.messages.append({"role": "assistant", "content": f"You said: {prompt}"})

    st.rerun()


# ---------------- Configuration Settings ----------------
if st.session_state.show_config and not st.session_state.config_completed:

    # Chatbot-style message
    with st.container():
        st.markdown(
            """
            <div style="
                background-color:#E5E5EA;
                color:black;
                padding:12px 16px;
                border-radius:18px;
                max-width:70%;
                margin-right:auto;
                margin-bottom:15px;
                font-size:16px;">
                Please specify configuration settings for a more accurate response.
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### 📊 Compare ETF — Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("#### ⏳ Duration")
            st.session_state.duration_choice = st.radio(
                "",
                ["Long Term", "Short Term"],
                key="duration_radio",
                horizontal=True
            )

    with col2:
        with st.container(border=True):
            st.markdown("#### 🏭 Sector")
            st.session_state.sector_choice = st.radio(
                "",
                ["Tech", "Finance", "Medical", "Manufacturing"],
                key="sector_radio",
                horizontal=True
            )

    with col3:
        with st.container(border=True):
            st.markdown("#### ⚠️ Risk")
            st.session_state.risk_choice = st.radio(
                "",
                ["Low", "Medium", "High"],
                key="risk_radio",
                horizontal=True
            )

    if st.button("Done"):
        st.session_state.show_config = False
        st.session_state.config_completed = True

        bot_response = (
            f"Your ETF preferences:\n\n"
            f"• Duration: {st.session_state.duration_choice}\n"
            f"• Sector: {st.session_state.sector_choice}\n"
            f"• Risk Level: {st.session_state.risk_choice}\n\n"
            f"Based on your prompt:\n\n"
            f"\"{st.session_state.user_prompt}\""
        )

        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        st.rerun()
