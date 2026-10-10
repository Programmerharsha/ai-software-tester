"""AI Failure Analysis page — send failures to Qwen for classification and root cause analysis."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from datetime import datetime
import streamlit as st

import database.database as db


def _require_project():
    pid = st.session_state.get("selected_project_id")
    if not pid:
        st.warning("Select a project first.")
        return None
    return pid


def _classification_badge(classification: str) -> str:
    colors = {
        "Application Bug": ("#ff5370", "rgba(255,83,112,0.12)"),
        "Test Automation Bug": ("#ffcc02", "rgba(255,204,2,0.12)"),
        "Selector Problem": ("#40c4ff", "rgba(64,196,255,0.12)"),
        "Network Problem": ("#ff9800", "rgba(255,152,0,0.12)"),
        "Authentication Problem": ("#ff1744", "rgba(255,23,68,0.12)"),
        "Environment Problem": ("#ab47bc", "rgba(171,71,188,0.12)"),
        "Data Problem": ("#26c6da", "rgba(38,198,218,0.12)"),
        "Unknown": ("#9ca3af", "rgba(156,163,175,0.12)"),
    }
    c, bg = colors.get(classification, ("#9ca3af", "rgba(156,163,175,0.12)"))
    return f"""<span style="color:{c}; background:{bg}; border:1px solid {c}40;
        padding:4px 14px; border-radius:20px; font-size:0.85rem; font-weight:700;">
        {classification}
    </span>"""


def render():
    st.markdown("## AI Failure Analysis")

    pid = _require_project()
    if not pid:
        return

    project = db.get_project(pid)
    st.caption(f"Project: **{project['name']}**")

    # Get all failed results
    executions = db.get_executions(pid)
    all_failed = []
    for ex in executions:
        results = db.get_execution_results(ex["id"])
        for r in results:
            if r["result"] == "Fail":
                r["execution_name"] = ex["name"]
                r["browser_name"] = ex.get("browser", "chromium")
                all_failed.append(r)

    if not all_failed:
        st.info("""
        No failed test results found for this project.

        **To see failures here:**
        1. Create and run test cases (Test Execution page)
        2. Any FAIL results will appear here for AI analysis
        """)
        return

    st.markdown(f"### {len(all_failed)} Failed Test(s) Found")
    st.markdown("Select any failure to send it to **Qwen2.5-Coder 7B** for deep analysis.")

    st.divider()

    for i, failure in enumerate(all_failed):
        # Check if already analyzed
        existing_analysis = failure.get("ai_analysis")
        analyzed = bool(existing_analysis)
        icon = "[ANALYZED]" if analyzed else "[UNANALYZED]"

        with st.expander(
            f"{icon} [{failure['execution_name']}] `{failure['tc_id']}` — {failure['scenario']}",
            expanded=(i == 0 and not analyzed),
        ):
            # Failure context
            col_ctx, col_actions = st.columns([3, 1])

            with col_ctx:
                st.markdown(f"""
                <div style="background:#1e2130; border:1px solid rgba(255,83,112,0.3);
                            border-radius:12px; padding:16px; margin-bottom:12px;">
                  <div style="color:#ff5370; font-weight:700; margin-bottom:8px;">Failure Context</div>
                  <div><b>Expected:</b> {failure.get('expected_result', 'N/A')}</div>
                  <div><b>Actual:</b> {failure.get('actual_result', 'N/A')}</div>
                  <div><b>Error:</b> <code>{failure.get('error_message','N/A')[:200]}</code></div>
                  <div><b>Failed Step:</b> {failure.get('failed_step','N/A')}</div>
                  <div><b>URL:</b> {failure.get('url_at_failure','N/A')}</div>
                  <div><b>Browser:</b> {failure.get('browser_name','N/A')}</div>
                  <div><b>Time:</b> {failure.get('executed_at','N/A')}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_actions:
                if st.button("Analyze with Qwen",
                             key=f"analyze_fail_{failure['id']}",
                             use_container_width=True):
                    from ai.ai_service import analyze_failure
                    with st.spinner("Qwen2.5-Coder 7B is analyzing the failure..."):
                        data, raw, err = analyze_failure(
                            tc_id=failure["tc_id"],
                            scenario=failure["scenario"],
                            expected=failure.get("expected_result", ""),
                            actual=failure.get("actual_result", ""),
                            error=failure.get("error_message", ""),
                            failed_step=failure.get("failed_step", ""),
                            url=failure.get("url_at_failure", ""),
                            browser=failure.get("browser_name", ""),
                            timestamp=failure.get("executed_at", datetime.now().isoformat()),
                        )

                    if data:
                        db.update_result_analysis(failure["id"], json.dumps(data))
                        st.success("Analysis saved!")
                        st.rerun()
                    else:
                        st.error(f"Analysis failed: {err}")
                        with st.expander("Raw response"):
                            st.code(raw[:2000])

                if analyzed:
                    if st.button("Create Bug", key=f"bug_from_{failure['id']}", use_container_width=True):
                        st.session_state.current_page = "Bug Management"
                        st.session_state["ai_bug_prefill_result"] = failure["id"]
                        st.rerun()

            # Show existing analysis
            if existing_analysis:
                try:
                    analysis = json.loads(existing_analysis)

                    st.markdown("#### AI Analysis Result")

                    # Classification + confidence
                    classification = analysis.get("classification", "Unknown")
                    confidence = analysis.get("confidence", "Low")
                    confidence_color = {"High": "#00e676", "Medium": "#ffcc02", "Low": "#ff5370"}.get(confidence, "#9ca3af")
                    retry_note = (
                        '<div style="color:#00e676; font-size:0.85rem;">Should Retry: Yes</div>'
                        if analysis.get("should_retry")
                        else ""
                    )
                    environment_note = (
                        '<div style="color:#ffcc02; font-size:0.85rem;">Environment Issue</div>'
                        if analysis.get("is_environment_issue")
                        else ""
                    )

                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:16px; margin-bottom:16px; flex-wrap:wrap;">
                        <div>{_classification_badge(classification)}</div>
                        <div style="color:{confidence_color}; font-weight:600; font-size:0.9rem;">
                            Confidence: {confidence}
                        </div>
                        {retry_note}
                        {environment_note}
                    </div>
                    """, unsafe_allow_html=True)

                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.markdown("**Failure Explanation**")
                        st.info(analysis.get("failure_explanation", "N/A"))

                        st.markdown("**Likely Root Cause**")
                        st.warning(analysis.get("likely_root_cause", "N/A"))

                    with col_b:
                        st.markdown("**Evidence**")
                        for ev in analysis.get("evidence", []):
                            st.markdown(f"• {ev}")

                        st.markdown("**Suggested Fix**")
                        st.success(analysis.get("suggested_fix", "N/A"))

                    st.markdown("**Recommended Investigation**")
                    for step in analysis.get("recommended_investigation", []):
                        st.markdown(f"→ {step}")

                except json.JSONDecodeError:
                    st.warning("Could not parse stored analysis.")
