from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

import streamlit as st

from agent import friendly_error_message, run_chat_turn
from schemas import ChatTurnResponse, ETFComparisonResponse
from table_renderer import comparison_table_rows

APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "logo.png"


def render_bullets(title: str, items: list[str]) -> None:
    st.markdown(f"#### {title}")
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption("Not available")


def render_comparison(comparison: ETFComparisonResponse) -> None:
    """Render structured comparison data without turning it into Markdown."""

    st.markdown("### ETF comparison")
    rows = comparison_table_rows(comparison)
    if rows:
        st.dataframe(
            rows,
            hide_index=True,
            width="stretch",
            height=38 + (35 * len(rows)),
        )
    else:
        st.warning("No ETF rows were returned.")

    st.markdown("#### Holdings and explanations")
    for etf in comparison.compared_etfs:
        with st.expander(f"{etf.ticker} — {etf.name}"):
            st.markdown(f"**Simple explanation:** {etf.simple_explanation}")
            st.markdown("**Top holdings**")
            if etf.top_holdings:
                st.dataframe(
                    [{"Holding": holding} for holding in etf.top_holdings],
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.caption("Not available")

            if comparison.research_included:
                st.markdown("**Morningstar analyst summary**")
                st.write(etf.analyst_summary or "Not available")

    left, right = st.columns(2)
    with left:
        render_bullets("Similarities", comparison.similarities)
    with right:
        render_bullets("Differences", comparison.differences)

    st.info(comparison.beginner_takeaway, icon="💡")
    render_bullets("Data notes", comparison.data_notes)
    render_bullets("Try asking", comparison.follow_up_suggestions)


def render_assistant_response(response: ChatTurnResponse) -> None:
    if response.response_type == "comparison" and response.comparison:
        render_comparison(response.comparison)
    else:
        st.markdown(response.message or "No response was returned.")


def ask_backend(prompt: str) -> ChatTurnResponse:
    return asyncio.run(
        run_chat_turn(
            message=prompt,
            thread_id=st.session_state.thread_id,
            include_research=st.session_state.include_research,
            user_profile=st.session_state.user_profile,
        )
    )


def reset_conversation() -> None:
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid4())


st.set_page_config(page_title="ETF Engine", page_icon="🤖", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: #ffffff; }
    section[data-testid="stSidebar"] { background: #aba7c2; }
    section[data-testid="stSidebar"] * { color: white; }
    div[data-testid="stChatInput"] {
        border: 2px solid #50d6a3;
        border-radius: 18px;
    }

    h3.quiz-heading {
        font-family: Georgia, serif;
        color: #2a1f67 !important;
        font-size: 32px;
        font-weight: 700;
    }

    div[data-testid="stForm"] label p {
        font-family: "Times New Roman", serif;
        color: #2a1f67;
        font-size: 20px;
    }

    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {
        background-color: #1c866a !important;
        color: white !important;
        border: 2px solid #1c866a !important;
    }

    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #2a1f67 !important;
        color: white !important;
        border-color: #2a1f67 !important;
    }

    .st-key-example_0 button,
    .st-key-example_1 button,
    .st-key-example_2 button {
        background-color: #aba7c2;
        color: #2a1f67;
        border: 2px solid #2a1f67;
        font-family: Georgia, serif;
        font-size: 18px;
    }

    .st-key-example_0 button:hover,
    .st-key-example_1 button:hover,
    .st-key-example_2 button:hover {
        background-color: #1c866a !important;
        color: white !important;
        border-color: #1c866a !important;
    }

    .st-key-example_0 button:hover p,
    .st-key-example_1 button:hover p,
    .st-key-example_2 button:hover p {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())
if "include_research" not in st.session_state:
    st.session_state.include_research = False
if "feedback_open" not in st.session_state:
    st.session_state.feedback_open = False
if "feedback_rating" not in st.session_state:
    st.session_state.feedback_rating = 0
if "user_profile" not in st.session_state:
    st.session_state.user_profile = None

if LOGO_PATH.exists():
    _, logo, _ = st.columns([1, 1, 1])
    with logo:
        st.image(str(LOGO_PATH), width=200)

st.markdown(
    """
<div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <h1 style="
                font-family: Georgia, serif;
                color: #2a1f67;
                font-size: 47px;
                line-height: 1.1;
                margin: 0;
                padding: 0;
            ">
                ETF Engine
            </h1>
            <p style="
                font-family: 'Times New Roman', serif;
                color: #534dbb;
                font-size: 25px;
                font-weight: 500;
                font-style: italic;
                letter-spacing: 0.5px;
                line-height: 1.4;
                margin: 8px 0 0 0;
                padding: 0;
            ">
                Powering Smarter Investment Decisions with the ETF Engine Vision
            </p>
        </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    header_col, logo_col = st.columns([0.75, 0.25], gap="small")
    with header_col:
        st.markdown(
            "<h1 style='font-family: Georgia; color: #2a1f67; font-size: 2.0rem; font-weight: 700; margin:0; white-space:nowrap;'>"
            "Engine Hub</h1>",
            unsafe_allow_html=True,
        )
    with logo_col:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=70)
    st. markdown("<hr style='border: 3px solid #ffffff; margin: 4px 0 8px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style = 'font-family: Times New Roman; font-size: 18px; color: #ffffff;'>" "Allowing investors to compare their Exchange Traded Funds (ETFs) and make smart decisions using real financial data from MorningStar</p>", unsafe_allow_html=True)


    st.markdown(
        """
        <style>
        div[data-testid="stCheckbox"] label {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            border: 2px solid #2a1f67;
            border-radius: 14px;
            padding: 8px 12px;
            background: #2a1f67;
            color: white;
        }
        div[data-testid="stCheckbox"] input[type="checkbox"] {
            transform: scale(1.2);
        }
        section[data-testid="stSidebar"] [class*="st-key-feedback_star_"] button,
        section[data-testid="stSidebar"] [class*="st-key-feedback_star_"] button:hover,
        section[data-testid="stSidebar"] [class*="st-key-feedback_star_"] button:focus,
        section[data-testid="stSidebar"] [class*="st-key-feedback_star_"] button:active {
            background: transparent !important;
            border-color: transparent !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
            min-height: 2.25rem !important;
        }
        section[data-testid="stSidebar"] [class*="st-key-feedback_star_"] button p {
            font-size: 28px !important;
            line-height: 1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.checkbox(
        "Include Morningstar analyst research",
        key="include_research",
        help="Research takes longer and is requested only when enabled.",
    )

    if st.button("Leave feedback", key="feedback_button"):
        st.session_state.feedback_open = True

    if st.session_state.feedback_open:
        st.markdown("#### Tell us how we did")
        st.markdown("_Click a star to rate us_", unsafe_allow_html=True)
        star_cols = st.columns([1, 1, 1, 1, 1, 2], gap=None)
        for star_index in range(1, 6):
            with star_cols[star_index - 1]:
                if st.button("⭐", key=f"feedback_star_{star_index}"):
                    st.session_state.feedback_rating = star_index
        if st.session_state.feedback_rating:
            st.success(f"Thanks! You selected {st.session_state.feedback_rating} star{'s' if st.session_state.feedback_rating > 1 else ''}.")
        close_col, _, _, _, _ = st.columns([1, 0.3, 0.3, 0.3, 0.3])
        with close_col:
            if st.button("Close", key="feedback_close"):
                st.session_state.feedback_open = False
                st.session_state.feedback_rating = 0

    st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] div[data-testid="stButton"] button {
        background-color: #1c866a;
        color: white;
        border: 2px solid #ffffff;
        border-radius: 14px;
        padding: 12px 16px;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
        background-color: #162f4f;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )

    st.button(
        "New Chat",
        on_click=reset_conversation,
        width="stretch",
    )


st.caption(f"Thread: {st.session_state.thread_id[:8]}")

if st.session_state.user_profile is None:
    st.markdown(
        """
        <h3 class="quiz-heading" style="
            font-family: Georgia, serif !important;
            color: #2a1f67 !important;
            font-size: 32px;
            font-weight: 700;
        ">
            Let’s personalize your ETF Engine experience
        </h3>
        """,
        unsafe_allow_html=True,
    )
    st.write("Answer four quick questions to get started!")

    with st.form("investor_profile_form"):
        Plan = st.radio(
            "What is your investment plan? ",
            ["Short-term investment", "Long-term investment"]
        )
        Sector = st.radio(
            "What is your primary sector of focus?",
            ["Technology", "Healthcare", "Finance", "Energy", "Communication"]
        )
        Risk = st.radio(
            "What is your risk interest?",
            ["Low", "Medium", "High"]
        )
        Experience = st.radio(
            "Experience in Investment",
            [
                "Beginner", "Advanced", "Expert"
            ],
        )
        profile_submitted = st.form_submit_button(
            "Start exploring ETFs", width="stretch", type="primary"
        )

    if profile_submitted:
        st.session_state.user_profile = {
            "investment_plan": Plan,
            "sector_focus": Sector,
            "risk_interest": Risk,
            "experience_level": Experience,
        }
        st.rerun()

    st.stop()

for message in st.session_state.messages:
    avatar = "🟦" if message["role"] == "user" else "🟪"
    with st.chat_message(message["role"], avatar=avatar):
        if message["role"] == "user":
            st.write(message["content"])
        elif "response" in message:
            render_assistant_response(ChatTurnResponse.model_validate(message["response"]))
        else:
            st.write(message.get("content", ""))

st.markdown(
    """
    <h4 style="
        font-family: Georgia, serif;
        color: #2a1f67;
        font-size: 30px;
    ">
        Try an example
    </h4>
    """,
    unsafe_allow_html=True,
)
example_columns = st.columns(3)
example_prompts = [
    "Compare VOO and QQQ",
    "Compare VOO, QQQ, and SCHD",
    "Which ETF has a lower expense ratio between VOO and SPY?",
]
selected_prompt = None
for index, (column, example) in enumerate(
    zip(example_columns, example_prompts, strict=True)
):
    with column:
        if st.button(example, key=f"example_{index}", width="stretch"):
            selected_prompt = example

typed_prompt = st.chat_input("Compare two or three ETFs...")
prompt = typed_prompt or selected_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🟦"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="🟪"):
        try:
            with st.spinner("Researching Morningstar data..."):
                response = ask_backend(prompt)
            render_assistant_response(response)
            st.session_state.messages.append(
                {"role": "assistant", "response": response.model_dump(mode="json")}
            )
        except Exception as error:
            error_message = f"Unable to complete the request: {friendly_error_message(error)}"
            st.error(error_message)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "response": ChatTurnResponse(
                        response_type="message", message=error_message
                    ).model_dump(mode="json"),
                }
            )
