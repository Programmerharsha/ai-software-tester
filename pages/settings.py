"""
Settings page — configure Online AI Providers (Gemini, Groq, OpenAI, Ollama, Demo Mode),
Playwright browser automation, demo server, and cloud deployment diagnostics.
"""

import os
import platform
import sys
import time
from typing import Dict

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ai import providers
from ai.ollama_client import get_ai_status
import config
import database.database as db
from demo_app.server import is_demo_server_running, start_demo_server_background
from testing.playwright_engine import check_browser_status, install_browser_binary


def render():
    st.markdown("## System & Cloud Deployment Settings")
    st.caption("Configure cloud AI services, browser runners, and online hosting options.")

    settings = db.get_all_settings()
    current_provider = providers.get_active_provider()

    tab_ai, tab_cloud, tab_runner, tab_guide = st.tabs([
        "AI Providers (Cloud & Local)",
        "Browser & Target Server",
        "Execution Preferences",
        "Deploy to Streamlit Cloud Guide"
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: AI Providers
    # ─────────────────────────────────────────────────────────────────────────
    with tab_ai:
        st.markdown("### AI Engine Configuration")
        st.caption(
            "Select an online or local AI provider. When hosting on Streamlit Community Cloud, "
            "Google Gemini, Groq, or the built-in Smart Demo Engine are recommended."
        )

        provider_keys = ["gemini", "groq", "demo", "openai", "ollama"]
        provider_labels = [providers.PROVIDER_DISPLAY_NAMES.get(k, k) for k in provider_keys]
        default_idx = provider_keys.index(current_provider) if current_provider in provider_keys else 0

        selected_label = st.selectbox(
            "Active AI Engine",
            provider_labels,
            index=default_idx,
            help="Choose which AI service powers requirement analysis, test case generation, and bug reports."
        )
        selected_provider = provider_keys[provider_labels.index(selected_label)]

        # Live status check banner
        status = get_ai_status()
        if status.get("ready"):
            st.markdown(
                f"""
                <div style="background:rgba(0,230,118,0.08); border:1px solid rgba(0,230,118,0.3);
                            border-radius:12px; padding:14px 18px; margin: 12px 0 20px 0;">
                  <div style="font-weight:700; color:#00e676; display:flex; align-items:center;">
                    <span style="font-size:1.1rem; margin-right:8px;">✅</span>
                    {status.get('provider_display', 'AI Engine')}: READY
                  </div>
                  <div style="color:#e8eaf6; font-size:0.9rem; margin-top:4px;">
                    {status.get('model_msg', '')} &bull; {status.get('ollama_msg', '')}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background:rgba(255,83,112,0.08); border:1px solid rgba(255,83,112,0.3);
                            border-radius:12px; padding:14px 18px; margin: 12px 0 20px 0;">
                  <div style="font-weight:700; color:#ff5370; display:flex; align-items:center;">
                    <span style="font-size:1.1rem; margin-right:8px;">⚠️</span>
                    {status.get('provider_display', 'AI Engine')}: ACTION REQUIRED
                  </div>
                  <div style="color:#e8eaf6; font-size:0.9rem; margin-top:4px;">
                    {status.get('ollama_msg', '')} {status.get('model_msg', '')}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()

        # Dynamic Provider Settings Form
        with st.form("ai_provider_form"):
            st.markdown(f"#### Configure {providers.PROVIDER_DISPLAY_NAMES.get(selected_provider)}")

            if selected_provider == "gemini":
                st.info(
                    "Google Gemini offers a generous free tier with high quality and zero credit card required. "
                    "Get your free API key at [Google AI Studio](https://aistudio.google.com/app/apikey)."
                )
                current_key = providers.get_provider_api_key("gemini")
                gemini_key = st.text_input(
                    "Google Gemini API Key",
                    value=current_key,
                    type="password",
                    help="Loaded from Streamlit Secrets or environment variable if configured.",
                )
                gemini_model = st.selectbox(
                    "Model",
                    ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
                    index=["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"].index(
                        providers.get_provider_model("gemini") if providers.get_provider_model("gemini") in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"] else "gemini-1.5-flash"
                    ),
                    help="gemini-1.5-flash is fast, accurate, and has high free-tier rate limits.",
                )

            elif selected_provider == "groq":
                st.info(
                    "Groq Cloud provides lightning-fast inference for open models. "
                    "Get a free API key at [Groq Console](https://console.groq.com/keys)."
                )
                current_key = providers.get_provider_api_key("groq")
                groq_key = st.text_input(
                    "Groq API Key",
                    value=current_key,
                    type="password",
                    help="Starts with gsk_...",
                )
                groq_model = st.selectbox(
                    "Model",
                    ["llama-3.3-70b-versatile", "qwen-2.5-coder-32b", "llama-3.1-8b-instant"],
                    index=["llama-3.3-70b-versatile", "qwen-2.5-coder-32b", "llama-3.1-8b-instant"].index(
                        providers.get_provider_model("groq") if providers.get_provider_model("groq") in ["llama-3.3-70b-versatile", "qwen-2.5-coder-32b", "llama-3.1-8b-instant"] else "llama-3.3-70b-versatile"
                    ),
                )

            elif selected_provider == "demo":
                st.success(
                    "Smart Demo Engine is built-in and runs entirely in memory without external API keys or network traffic. "
                    "It dynamically analyzes your requirement inputs to synthesize complete, schema-compliant test suites, "
                    "actions, root cause diagnoses, and professional defect reports. Ideal for instant public demonstrations!"
                )
                st.caption("Engine: Smart Heuristic Synthesizer v1.0 (Zero latency, 100% uptime)")

            elif selected_provider == "openai":
                st.info("Connect to OpenAI, OpenRouter, DeepSeek, or any OpenAI-compatible API endpoint.")
                openai_key = st.text_input(
                    "API Key",
                    value=providers.get_provider_api_key("openai"),
                    type="password",
                )
                openai_base_url = st.text_input(
                    "API Base URL",
                    value=providers.get_provider_base_url("openai"),
                    help="Default: https://api.openai.com/v1 (or https://openrouter.ai/api/v1, https://api.deepseek.com/v1)",
                )
                openai_model = st.text_input(
                    "Model Name",
                    value=providers.get_provider_model("openai"),
                    help="e.g. gpt-4o-mini, deepseek-chat",
                )

            elif selected_provider == "ollama":
                st.warning(
                    "Ollama runs models locally on your workstation. When deploying to Streamlit Community Cloud, "
                    "localhost is not accessible unless you provide a public endpoint (e.g. via Ngrok or a remote VPS)."
                )
                ollama_url = st.text_input(
                    "Ollama Server URL",
                    value=providers.get_provider_base_url("ollama"),
                    help="Default: http://localhost:11434 (or your public ngrok URL)",
                )
                ollama_model = st.text_input(
                    "Model Tag",
                    value=providers.get_provider_model("ollama"),
                    help="Default: qwen2.5-coder:7b",
                )

            save_btn = st.form_submit_button("Save AI Settings", use_container_width=True)

        if save_btn:
            db.set_setting("ai_provider", selected_provider)
            st.session_state["active_ai_provider"] = selected_provider

            if selected_provider == "gemini":
                db.set_setting("gemini_api_key", gemini_key)
                db.set_setting("gemini_model", gemini_model)
                st.session_state["gemini_api_key"] = gemini_key
                st.session_state["gemini_model"] = gemini_model
            elif selected_provider == "groq":
                db.set_setting("groq_api_key", groq_key)
                db.set_setting("groq_model", groq_model)
                st.session_state["groq_api_key"] = groq_key
                st.session_state["groq_model"] = groq_model
            elif selected_provider == "openai":
                db.set_setting("openai_api_key", openai_key)
                db.set_setting("openai_base_url", openai_base_url)
                db.set_setting("openai_model", openai_model)
                st.session_state["openai_api_key"] = openai_key
                st.session_state["openai_base_url"] = openai_base_url
                st.session_state["openai_model"] = openai_model
            elif selected_provider == "ollama":
                db.set_setting("ollama_url", ollama_url)
                db.set_setting("ai_model", ollama_model)
                st.session_state["ollama_url"] = ollama_url
                st.session_state["ai_model"] = ollama_model

            st.session_state["ai_status_checked"] = False
            st.success("AI Settings updated successfully!")
            st.rerun()

        # Connection Test Tool
        st.markdown("#### Test Live Connection")
        col_test_btn, col_test_result = st.columns([1, 2])
        with col_test_btn:
            do_test = st.button("Ping Active AI Provider", use_container_width=True)

        if do_test:
            with st.spinner(f"Testing {selected_label}..."):
                ok, test_msg = providers.test_provider_connection(selected_provider)
                with col_test_result:
                    if ok:
                        st.success(test_msg)
                    else:
                        st.error(test_msg)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: Browser & Target Server
    # ─────────────────────────────────────────────────────────────────────────
    with tab_cloud:
        st.markdown("### Browser & Demonstration Server Diagnostics")
        st.caption("Inspect and manage automation prerequisites for running tests online.")

        col_b1, col_b2 = st.columns(2)

        with col_b1:
            st.markdown("#### Playwright Browser Status")
            installed, b_msg = check_browser_status("chromium")
            if installed:
                st.markdown("""
                <div style="background:rgba(0,230,118,0.08); border:1px solid rgba(0,230,118,0.25);
                            border-radius:10px; padding:12px; margin-bottom:12px;">
                  <b style="color:#00e676;">✅ Chromium Browser: READY</b><br>
                  <span style="font-size:0.85rem; color:#9ca3af;">Headless automation binaries are present.</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:rgba(255,83,112,0.08); border:1px solid rgba(255,83,112,0.25);
                            border-radius:10px; padding:12px; margin-bottom:12px;">
                  <b style="color:#ff5370;">⚠️ Chromium Binary Missing</b><br>
                  <span style="font-size:0.85rem; color:#9ca3af;">{b_msg}</span>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Install Chromium Binaries Now", use_container_width=True):
                    with st.spinner("Downloading and installing Chromium binaries via Playwright..."):
                        ok_inst, msg_inst = install_browser_binary("chromium")
                        if ok_inst:
                            st.success(msg_inst)
                            st.rerun()
                        else:
                            st.error(msg_inst)

        with col_b2:
            st.markdown("#### Built-in Demo Target Server")
            demo_running = is_demo_server_running("http://127.0.0.1:5000")
            if demo_running:
                st.markdown("""
                <div style="background:rgba(0,230,118,0.08); border:1px solid rgba(0,230,118,0.25);
                            border-radius:10px; padding:12px; margin-bottom:12px;">
                  <b style="color:#00e676;">✅ Demo Flask App: RUNNING (Port 5000)</b><br>
                  <span style="font-size:0.85rem; color:#9ca3af;">Responding at http://127.0.0.1:5000</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:rgba(255,204,2,0.08); border:1px solid rgba(255,204,2,0.25);
                            border-radius:10px; padding:12px; margin-bottom:12px;">
                  <b style="color:#ffcc02;">⚪ Demo Flask App: STOPPED</b><br>
                  <span style="font-size:0.85rem; color:#9ca3af;">Start in background to run tests against local demo app.</span>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Start Demo App on Port 5000", use_container_width=True):
                    with st.spinner("Starting Flask demo target in daemon thread..."):
                        ok_start, msg_start = start_demo_server_background()
                        if ok_start:
                            st.success(msg_start)
                            st.rerun()
                        else:
                            st.error(msg_start)

        st.divider()

        st.markdown("#### Sample Demo Data Management")
        st.caption("Re-seed the initial starter project, requirements, and test cases.")
        if st.button("Reload Starter Demo Data", use_container_width=False):
            pid = db.seed_demo_data(force=True)
            st.success("Starter Demo project and test cases have been reloaded!")
            st.rerun()

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: Execution Preferences
    # ─────────────────────────────────────────────────────────────────────────
    with tab_runner:
        st.markdown("### Test Runner Options")
        with st.form("runner_prefs_form"):
            c1, c2 = st.columns(2)
            with c1:
                browser = st.selectbox(
                    "Default Browser",
                    ["chromium", "firefox", "webkit"],
                    index=["chromium", "firefox", "webkit"].index(settings.get("browser", "chromium")),
                    help="Chromium is recommended for fastest headless execution.",
                )
                test_timeout = st.number_input(
                    "Test Timeout (ms)",
                    value=int(settings.get("test_timeout", "30000")),
                    min_value=1000,
                    max_value=120000,
                    step=1000,
                )
            with c2:
                headless = st.checkbox(
                    "Headless Mode",
                    value=settings.get("headless", "1") == "1",
                    help="Always required on Streamlit Cloud (containers have no display window).",
                )
                screenshot_on_failure = st.checkbox(
                    "Screenshot on Failure",
                    value=settings.get("screenshot_on_failure", "1") == "1",
                    help="Auto-capture screenshot evidence when test steps fail.",
                )

            if st.form_submit_button("Save Execution Preferences", use_container_width=True):
                db.set_setting("browser", browser)
                db.set_setting("headless", "1" if headless else "0")
                db.set_setting("test_timeout", str(int(test_timeout)))
                db.set_setting("screenshot_on_failure", "1" if screenshot_on_failure else "0")
                st.success("Execution preferences saved!")
                st.rerun()

        st.divider()

        # System details
        st.markdown("### Host Runtime Information")
        col_sys1, col_sys2 = st.columns(2)
        with col_sys1:
            st.markdown(f"**Operating System:** {platform.system()} {platform.release()} ({platform.machine()})")
            st.markdown(f"**Python Runtime:** {platform.python_version()}")
            try:
                import streamlit
                st.markdown(f"**Streamlit Version:** {streamlit.__version__}")
            except Exception:
                pass
        with col_sys2:
            try:
                import playwright
                st.markdown(f"**Playwright Library:** {playwright.__version__}")
            except Exception:
                st.markdown("**Playwright Library:** Not installed")
            st.markdown(f"**Database Storage:** `{config.DB_PATH.name}`")
            st.markdown(f"**Evidence Directory:** `{config.SCREENSHOTS_DIR.name}/`")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4: Streamlit Cloud Deployment Guide
    # ─────────────────────────────────────────────────────────────────────────
    with tab_guide:
        st.markdown("### How to Deploy this Project to Streamlit Community Cloud")
        st.markdown("""
        Deploying this AI Software Tester to the web is completely free and takes under 3 minutes:

        #### Step 1: Push to GitHub
        Ensure your project is pushed to a GitHub repository:
        ```bash
        git add .
        git commit -m "Add online support for Streamlit deployment"
        git push origin main
        ```

        #### Step 2: Create Streamlit Cloud App
        1. Visit **[share.streamlit.io](https://share.streamlit.io/)** and sign in with your GitHub account.
        2. Click **New App** and select your repository: `ai-software-tester`.
        3. Set the **Main file path** to: `app.py`.

        #### Step 3: Configure Cloud Secrets (Optional for Live AI)
        1. In the app settings on Streamlit Cloud, click on **Secrets**.
        2. Paste your free Gemini or Groq API key:
        ```toml
        AI_PROVIDER = "gemini"
        GEMINI_API_KEY = "AIzaSy..."
        GEMINI_MODEL = "gemini-1.5-flash"
        ```
        *(If no secrets are added, the website automatically falls back to the built-in Smart Demo Engine so every feature works out of the box!)*

        #### Step 4: Click Deploy!
        - Streamlit Cloud will automatically install Linux dependencies from `packages.txt` and Python packages from `requirements.txt`.
        - Your project will be live at `https://<your-subdomain>.streamlit.app`!
        """)
