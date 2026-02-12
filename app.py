"""
app.py – Streamlit chat UI for the AI Interviewer Chatbot.
Run with: streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv
from config import (
    COMPANY_NAME,
    ROLE_TITLE,
    MANDATORY_QUALIFICATIONS,
    PHASE_GREETING,
    PHASE_MANDATORY,
    PHASE_PREFERRED,
    PHASE_FOLLOWUP,
    PHASE_DECISION,
    PHASE_ENDED,
)
from agent import InterviewAgent, AVAILABLE_MODELS

# Load environment variables from .env
load_dotenv()

# ── Page Configuration ──────────────────────────────────────────────────────

st.set_page_config(
    page_title=f"AI Interviewer – {COMPANY_NAME}",
    page_icon="🚚",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Custom Styling ──────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Global font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5f8a 50%, #3a7cbd 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    }
    .main-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
    .main-header p { margin: 0.3rem 0 0 0; opacity: 0.85; font-size: 0.95rem; }

    /* Phase badge */
    .phase-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .phase-mandatory { background: #fee2e2; color: #991b1b; }
    .phase-preferred { background: #dbeafe; color: #1e40af; }
    .phase-decision { background: #d1fae5; color: #065f46; }
    .phase-greeting { background: #fef3c7; color: #92400e; }

    /* Progress card */
    .progress-card {
        background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        border-left: 4px solid #3a7cbd;
    }

    /* Score display */
    .score-display {
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
    }
    .score-good { background: #d1fae5; color: #065f46; }
    .score-medium { background: #fef3c7; color: #92400e; }
    .score-low { background: #fee2e2; color: #991b1b; }

    /* Quick option buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)


# ── Session State Initialization ────────────────────────────────────────────

def init_session():
    """Initialize all session state variables."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
        st.session_state.messages = []  # chat history for display
        st.session_state.agent = None
        # Priority: .env > session state
        st.session_state.api_key = os.getenv("GROQ_API_KEY", "")
        st.session_state.model_id = AVAILABLE_MODELS[0]
        st.session_state.interview_started = False

init_session()

# Re-check .env if session key is missing (for dynamic updates)
if not st.session_state.api_key:
    env_key = os.getenv("GROQ_API_KEY", "")
    if env_key and env_key != "your_groq_key_here":
        st.session_state.api_key = env_key

# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:

    api_key = os.getenv("GROQ_API_KEY")

    st.markdown("---")

    # Interview progress
    if st.session_state.agent:
        progress = st.session_state.agent.get_progress()

        st.markdown("### 📊 Interview Progress")

        # Phase indicator
        phase_map = {
            PHASE_GREETING: ("👋 Greeting", "phase-greeting"),
            PHASE_MANDATORY: ("🔴 Mandatory Questions", "phase-mandatory"),
            PHASE_PREFERRED: ("🔵 Preferred Questions", "phase-preferred"),
            PHASE_FOLLOWUP: ("🔵 Follow-up Question", "phase-preferred"),
            PHASE_DECISION: ("✅ Final Decision", "phase-decision"),
            PHASE_ENDED: ("✅ Interview Complete", "phase-decision"),
        }
        label, css_class = phase_map.get(
            progress["phase"], ("❓ Unknown", "phase-greeting")
        )
        st.markdown(
            f'<span class="phase-badge {css_class}">{label}</span>',
            unsafe_allow_html=True,
        )

        st.progress(progress["answered"] / max(progress["total"], 1))
        st.caption(f"Questions: {progress['answered']}/{progress['total']}")

        st.markdown(
            f"""
            <div class="progress-card">
                <b>Mandatory:</b> {progress['mandatory_done']}/{progress['mandatory_total']}<br>
                <b>Preferred:</b> {progress['preferred_done']}/{progress['preferred_total']}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if progress["is_disqualified"]:
            st.error("⚠️ Candidate disqualified")

        st.markdown("---")

        if progress["phase"] not in (PHASE_DECISION, PHASE_ENDED):
            if st.button("🛑 End Interview", use_container_width=True):
                with st.spinner("Generating final assessment..."):
                    response = st.session_state.agent.force_decision()
                    st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

        if st.button("🔄 Start New Interview", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    else:
        if st.session_state.api_key and st.session_state.api_key != "your_groq_key_here":
            st.success("✅ Groq API Key loaded from .env")
        else:
            st.info("Enter your Groq API key in the sidebar or .env file to begin.")


# ── Main Chat Area ──────────────────────────────────────────────────────────

st.markdown(
    f"""
    <div class="main-header">
        <h1>🚚 AI Hiring Interviewer</h1>
        <p>{ROLE_TITLE} • {COMPANY_NAME} (Groq Powered)</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.api_key or st.session_state.api_key == "your_groq_key_here":
    st.warning("👈 Please enter or update your **Groq API Key** in the sidebar to start.")
    st.stop()

if not st.session_state.interview_started:
    try:
        st.session_state.agent = InterviewAgent(
            api_key=st.session_state.api_key, 
            model_id=st.session_state.model_id
        )
        with st.spinner("Starting..."):
            greeting = st.session_state.agent.get_greeting()
            st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.interview_started = True
        st.rerun()
    except Exception as e:
        st.error(f"Initialization Error: {e}")
        st.stop()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

if st.session_state.agent:
    progress = st.session_state.agent.get_progress()
    if progress["phase"] == PHASE_MANDATORY:
        idx = st.session_state.agent.mandatory_index
        if idx < len(MANDATORY_QUALIFICATIONS):
            st.markdown("---")
            st.caption("⚡ Quick answer:")
            cols = st.columns([1, 1, 2])
            with cols[0]:
                if st.button("✅ Yes", key=f"yes_{idx}", use_container_width=True):
                    _input = "Yes"
                    st.session_state.messages.append({"role": "user", "content": _input})
                    with st.spinner("Processing..."):
                        response = st.session_state.agent.process_message(_input)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
            with cols[1]:
                if st.button("❌ No", key=f"no_{idx}", use_container_width=True):
                    _input = "No"
                    st.session_state.messages.append({"role": "user", "content": _input})
                    with st.spinner("Processing..."):
                        response = st.session_state.agent.process_message(_input)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()

if st.session_state.agent and st.session_state.agent.phase != PHASE_ENDED:
    if user_input := st.chat_input("Type your answer here..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                response = st.session_state.agent.process_message(user_input)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
elif st.session_state.agent and st.session_state.agent.phase == PHASE_ENDED:
    progress = st.session_state.agent.get_progress()
    score = progress["score"]
    css_class = "score-good" if score >= 80 else "score-medium" if score >= 50 else "score-low"
    st.markdown(f'<div class="score-display {css_class}">Match Score: {score}/100</div>', unsafe_allow_html=True)
    with st.expander("📋 Recruiter Summary (Internal)", expanded=False):
        st.text(st.session_state.agent.tracker.generate_summary())
    st.info("Interview complete.")
