
import base64
import streamlit as st
from datetime import datetime
from scrape import scrape_multiple
from search import get_search_results
from llm_utils import BufferedStreamingHandler, get_model_choices
from llm import get_llm, refine_query, filter_results, generate_summary, PRESET_PROMPTS
from config import OLLAMA_BASE_URL
from health import check_llm_health, check_search_engines, check_tor_proxy


def _render_pipeline_error(stage: str, err: Exception) -> None:
    message = str(err).strip() or err.__class__.__name__
    lower_msg = message.lower()
    hints = [
        f"- Confirm Ollama is running and reachable at `{OLLAMA_BASE_URL}`.",
        "- Check available models with `ollama list`.",
        "- If needed, pull a model first (example: `ollama pull llama3.2:latest`).",
        "- Restart the app after updating environment variables so the new values are picked up.",
    ]

    if "model" in lower_msg and "not found" in lower_msg:
        hints.insert(0, "- The selected Ollama model is not installed locally.")

    st.error(
        "❌ Failed to {}.\n\nError: {}\n\n{}".format(
            stage,
            message,
            "\n".join(hints),
        )
    )
    st.stop()


# Cache expensive backend calls
@st.cache_data(ttl=200, show_spinner=False)
def cached_search_results(refined_query: str, threads: int):
    return get_search_results(refined_query.replace(" ", "+"), max_workers=threads)


@st.cache_data(ttl=200, show_spinner=False)
def cached_scrape_multiple(filtered: list, threads: int):
    return scrape_multiple(filtered, max_workers=threads)


# Streamlit page configuration
st.set_page_config(
    page_title="Sherlocky: AI-Powered Dark Web OSINT Tool",
    page_icon="🕵️‍♂️",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown(
    """
    <style>
            .colHeight {
                max-height: 40vh;
                overflow-y: auto;
                text-align: center;
            }
            .pTitle {
                font-weight: bold;
                color: #FF4B4B;
                margin-bottom: 0.5em;
            }
            .aStyle {
                font-size: 18px;
                font-weight: bold;
                padding: 5px;
                padding-left: 0px;
                text-align: center;
            }
    </style>""",
    unsafe_allow_html=True,
)


# Sidebar
st.sidebar.title("Sherlocky")
st.sidebar.text("AI-Powered Dark Web OSINT Tool")
st.sidebar.subheader("Settings")

model_options = get_model_choices()
default_model_index = (
    next(
        (
            idx
            for idx, name in enumerate(model_options)
            if name.lower() in {"llama3.2:latest", "llama3.1:latest"}
        ),
        0,
    )
    if model_options
    else 0
)

if not model_options:
    st.sidebar.error(
        "⛔ **No LLM models available.**\n\n"
        "No Ollama model was detected.\n\n"
        "Confirm Ollama is running, then pull at least one model (example: `ollama pull llama3.2:latest`)."
    )
    st.stop()

model = st.sidebar.selectbox(
    "Select LLM Model",
    model_options,
    index=default_model_index,
    key="model_select",
)
st.sidebar.caption("Modelos instalados no Ollama são detetados automaticamente.")
threads = st.sidebar.slider("Scraping Threads", 1, 16, 4, key="thread_slider")

st.sidebar.divider()
st.sidebar.subheader("Ollama Configuration")
st.sidebar.markdown(f"&ensp;✅ **Ollama URL** — `{OLLAMA_BASE_URL}`")

with st.sidebar.expander("⚙️ Prompt Settings"):
    preset_options = {
        "🔍 Dark Web Threat Intel": "threat_intel",
        "🦠 Ransomware / Malware Focus": "ransomware_malware",
        "👤 Personal / Identity Investigation": "personal_identity",
        "🏢 Corporate Espionage / Data Leaks": "corporate_espionage",
    }
    preset_placeholders = {
        "threat_intel": "e.g. Pay extra attention to cryptocurrency wallet addresses and exchange names.",
        "ransomware_malware": "e.g. Highlight any references to double-extortion tactics or known ransomware-as-a-service affiliates.",
        "personal_identity": "e.g. Flag any passport or government ID numbers and note which country they appear to be from.",
        "corporate_espionage": "e.g. Prioritize any mentions of source code repositories, API keys, or internal Slack/email dumps.",
    }
    selected_preset_label = st.selectbox(
        "Research Domain",
        list(preset_options.keys()),
        key="preset_select",
    )
    selected_preset = preset_options[selected_preset_label]
    st.text_area(
        "System Prompt",
        value=PRESET_PROMPTS[selected_preset].strip(),
        height=200,
        disabled=True,
        key="system_prompt_display",
    )
    custom_instructions = st.text_area(
        "Custom Instructions (optional)",
        placeholder=preset_placeholders[selected_preset],
        height=100,
        key="custom_instructions",
    )

# --- Health Checks ---
st.sidebar.divider()
st.sidebar.subheader("Health Checks")

# LLM Health Check
if st.sidebar.button("🔌 Check LLM Connection", use_container_width=True):
    with st.sidebar:
        with st.spinner(f"Testing {model}..."):
            result = check_llm_health(model)
        if result["status"] == "up":
            st.sidebar.success(
                f"✅ **{result['provider']}** — Connected ({result['latency_ms']}ms)"
            )
        else:
            st.sidebar.error(
                f"❌ **{result['provider']}** — Failed\n\n{result['error']}"
            )

# Search Engine Health Check
if st.sidebar.button("🔍 Check Search Engines", use_container_width=True):
    with st.sidebar:
        with st.spinner("Checking Tor proxy..."):
            tor_result = check_tor_proxy()
        if tor_result["status"] == "down":
            st.sidebar.error(
                f"❌ **Tor Proxy** — Not reachable\n\n{tor_result['error']}\n\n"
                "Ensure Tor is running: `sudo systemctl start tor`"
            )
        else:
            st.sidebar.success(
                f"✅ **Tor Proxy** — Connected ({tor_result['latency_ms']}ms)"
            )
            with st.spinner("Pinging 16 search engines via Tor..."):
                engine_results = check_search_engines()
            up_count = sum(1 for r in engine_results if r["status"] == "up")
            total = len(engine_results)
            if up_count == total:
                st.sidebar.success(f"✅ **All {total} engines reachable**")
            elif up_count > 0:
                st.sidebar.warning(f"⚠️ **{up_count}/{total} engines reachable**")
            else:
                st.sidebar.error(f"❌ **0/{total} engines reachable**")

            for r in engine_results:
                if r["status"] == "up":
                    st.sidebar.markdown(
                        f"&ensp;🟢 **{r['name']}** — {r['latency_ms']}ms"
                    )
                else:
                    st.sidebar.markdown(
                        f"&ensp;🔴 **{r['name']}** — {r['error']}"
                    )


# Main UI - logo and input
_, logo_col, _ = st.columns(3)
with logo_col:
    st.image(".github/assets/robin_logo.png", width=200)

# Display text box and button
with st.form("search_form", clear_on_submit=True):
    col_input, col_button = st.columns([10, 1])
    query = col_input.text_input(
        "Enter Dark Web Search Query",
        placeholder="Enter Dark Web Search Query",
        label_visibility="collapsed",
        key="query_input",
    )
    run_button = col_button.form_submit_button("Run")

# Display a status message
status_slot = st.empty()
# Pre-allocate three placeholders-one per card
cols = st.columns(3)
p1, p2, p3 = [col.empty() for col in cols]
# Summary placeholders
summary_container_placeholder = st.empty()


# Process the query
if run_button and query:
    # clear old state
    for k in ["refined", "results", "filtered", "scraped", "streamed_summary"]:
        st.session_state.pop(k, None)

    # Stage 1 - Load LLM
    with status_slot.container():
        with st.spinner("🔄 Loading LLM..."):
            try:
                llm = get_llm(model)
            except Exception as e:
                _render_pipeline_error("load the selected LLM", e)

    # Stage 2 - Refine query
    with status_slot.container():
        with st.spinner("🔄 Refining query..."):
            try:
                st.session_state.refined = refine_query(llm, query)
            except Exception as e:
                _render_pipeline_error("refine the query", e)
    p1.container(border=True).markdown(
        f"<div class='colHeight'><p class='pTitle'>Refined Query</p><p>{st.session_state.refined}</p></div>",
        unsafe_allow_html=True,
    )

    # Stage 3 - Search dark web
    with status_slot.container():
        with st.spinner("🔍 Searching dark web..."):
            st.session_state.results = cached_search_results(
                st.session_state.refined, threads
            )
    p2.container(border=True).markdown(
        f"<div class='colHeight'><p class='pTitle'>Search Results</p><p>{len(st.session_state.results)}</p></div>",
        unsafe_allow_html=True,
    )

    # Stage 4 - Filter results
    with status_slot.container():
        with st.spinner("🗂️ Filtering results..."):
            st.session_state.filtered = filter_results(
                llm, st.session_state.refined, st.session_state.results
            )
    p3.container(border=True).markdown(
        f"<div class='colHeight'><p class='pTitle'>Filtered Results</p><p>{len(st.session_state.filtered)}</p></div>",
        unsafe_allow_html=True,
    )

    # Stage 5 - Scrape content
    with status_slot.container():
        with st.spinner("📜 Scraping content..."):
            st.session_state.scraped = cached_scrape_multiple(
                st.session_state.filtered, threads
            )

    # Stage 6 - Summarize
    # 6a) Prepare session state for streaming text
    st.session_state.streamed_summary = ""

    # 6c) UI callback for each chunk
    def ui_emit(chunk: str):
        st.session_state.streamed_summary += chunk
        summary_slot.markdown(st.session_state.streamed_summary)

    with summary_container_placeholder.container():  # border=True, height=450):
        hdr_col, btn_col = st.columns([4, 1], vertical_alignment="center")
        with hdr_col:
            st.subheader(":red[Investigation Summary]", anchor=None, divider="gray")
        summary_slot = st.empty()

    # 6d) Inject your two callbacks and invoke exactly as before
    with status_slot.container():
        with st.spinner("✍️ Generating summary..."):
            stream_handler = BufferedStreamingHandler(ui_callback=ui_emit)
            llm.callbacks = [stream_handler]
            _ = generate_summary(llm, query, st.session_state.scraped, preset=selected_preset, custom_instructions=custom_instructions)

    with btn_col:
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        fname = f"summary_{now}.md"
        b64 = base64.b64encode(st.session_state.streamed_summary.encode()).decode()
        href = f'<div class="aStyle">📥 <a href="data:file/markdown;base64,{b64}" download="{fname}">Download</a></div>'
        st.markdown(href, unsafe_allow_html=True)
    status_slot.success("✔️ Pipeline completed successfully!")
