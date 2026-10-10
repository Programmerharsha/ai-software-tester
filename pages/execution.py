"""Test Execution page — configure and run test cases via Playwright/API."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import json
import streamlit as st
import pandas as pd

import database.database as db
from ai.ai_service import generate_actions, generate_api_actions


def _require_project():
    pid = st.session_state.get("selected_project_id")
    if not pid:
        st.warning("Select a project first (Projects page).")
        return None
    return pid


def _result_badge(result: str) -> str:
    colors = {
        "Pass": ("#00e676", "rgba(0,230,118,0.12)"),
        "Fail": ("#ff5370", "rgba(255,83,112,0.12)"),
        "Blocked": ("#ffcc02", "rgba(255,204,2,0.12)"),
        "Skipped": ("#9ca3af", "rgba(156,163,175,0.12)"),
        "Not Executed": ("#6c63ff", "rgba(108,99,255,0.12)"),
    }
    c, bg = colors.get(result, ("#9ca3af", "rgba(156,163,175,0.12)"))
    return f'<span style="color:{c}; background:{bg}; border:1px solid {c}40; padding:2px 10px; border-radius:20px; font-size:0.8rem; font-weight:600;">{result}</span>'


def render():
    st.markdown("## Test Execution")

    pid = _require_project()
    if not pid:
        return

    project = db.get_project(pid)
    st.caption(f"Project: **{project['name']}** | Base URL: `{project.get('base_url','Not set')}`")

    tab_run, tab_history = st.tabs(["Run Tests", "Execution History"])

    # ── Run Tests ─────────────────────────────────────────────────────────────
    with tab_run:
        st.markdown("### Run Configuration")

        # Get test cases
        all_tcs = db.get_test_cases(pid)
        if not all_tcs:
            st.info("No test cases available. Go to AI Test Generator to create some.")
            return

        c1, c2 = st.columns(2)
        with c1:
            exec_name = st.text_input("Execution Name", value=f"Run_{int(time.time())}")
            browser = st.selectbox("Browser", ["chromium", "firefox", "webkit"])
        with c2:
            base_url = st.text_input("Base URL", value=project.get("base_url", "http://localhost:5000"))
            headless = st.checkbox("Headless Mode", value=True)

        # Test case selection
        st.markdown("#### Select Test Cases")
        col_select_all, _ = st.columns([1, 5])
        with col_select_all:
            select_all = st.checkbox("Select All", value=True)

        selected_ids = []
        # All Automated TCs (with or without pre-generated actions — missing ones are auto-generated at run time)
        automated_tcs = [tc for tc in all_tcs if tc.get("automation") in ("Automated", "Partial")]
        # Truly manual TCs (no automation planned at all)
        manual_tcs = [tc for tc in all_tcs if tc.get("automation") not in ("Automated", "Partial")]

        if automated_tcs:
            st.markdown("**Automated** (actions generated on demand if not already present)")
            for tc in automated_tcs:
                # show priority text instead of emoji
                p_icon = {"High": "[High]", "Medium": "[Med]", "Low": "[Low]"}.get(tc.get("priority", "Medium"), "[Med]")
                has_actions = bool(tc.get("actions_json"))
                label = f"{p_icon} `{tc['tc_id']}` — {tc['scenario']}" + (" (actions ready)" if has_actions else " (auto-generate)")
                checked = st.checkbox(
                    label,
                    value=select_all,
                    key=f"exec_check_{tc['id']}",
                )
                if checked:
                    selected_ids.append(tc["id"])

        if manual_tcs:
            st.markdown("**Manual** (skipped in automated runs)")
            for tc in manual_tcs:
                checked = st.checkbox(
                    f"`{tc['tc_id']}` — {tc['scenario']} *(manual only)*",
                    value=False,
                    key=f"exec_check_manual_{tc['id']}",
                )
                if checked:
                    selected_ids.append(tc["id"])

        if not selected_ids:
            st.info("Select at least one test case to run.")
        else:
            st.markdown(f"**{len(selected_ids)} test case(s) selected**")

            if st.button(f"Run {len(selected_ids)} Test(s)", use_container_width=True):
                # Create execution record
                exec_id = db.create_execution(pid, exec_name, browser, headless, base_url)
                tcs_to_run = [tc for tc in all_tcs if tc["id"] in selected_ids]

                # Progress container
                st.markdown(f"#### Running: {exec_name}")
                progress_bar = st.progress(0)
                status_placeholder = st.empty()
                results_placeholder = st.empty()

                all_results = []
                total = len(tcs_to_run)

                for i, tc in enumerate(tcs_to_run):
                    # ── Auto-generate actions if missing ──────────────────────
                    if not tc.get("actions_json"):
                        status_placeholder.markdown(
                            f"**Generating actions** for `{tc['tc_id']}` — {tc['scenario']} ({i+1}/{total})"
                        )
                        steps = db.get_test_steps(tc["id"])
                        step_texts = [s["action"] for s in steps]
                        try:
                            test_data = json.loads(tc.get("test_data", "{}") or "{}")
                        except Exception:
                            test_data = {}

                        is_api = tc.get("test_type", "").upper() == "API"
                        if is_api:
                            data, _, err = generate_api_actions(
                                tc["tc_id"], tc["scenario"],
                                step_texts, test_data,
                                tc.get("expected_result", ""), base_url,
                            )
                        else:
                            data, _, err = generate_actions(
                                tc["tc_id"], tc["scenario"],
                                step_texts, test_data,
                                tc.get("expected_result", ""), base_url,
                            )

                        if data:
                            actions_json = json.dumps(data)
                            db.update_test_case(tc["id"], actions_json=actions_json, automation="Automated")
                            tc["actions_json"] = actions_json  # update in-memory copy
                        else:
                            status_placeholder.warning(
                                f"⚠️ Could not auto-generate actions for `{tc['tc_id']}`: {err}"
                            )

                    status_placeholder.markdown(
                        f"**Running** `{tc['tc_id']}` — {tc['scenario']} ({i+1}/{total})"
                    )

                    from testing.test_executor import execute_test_case
                    result = execute_test_case(tc, exec_id, base_url, browser, headless)
                    all_results.append({"tc_id": tc["tc_id"], "scenario": tc["scenario"], **result})

                    progress_bar.progress((i + 1) / total)

                db.update_execution_status(exec_id, "Completed")
                status_placeholder.empty()

                # Results summary
                passed = sum(1 for r in all_results if r["result"] == "Pass")
                failed = sum(1 for r in all_results if r["result"] == "Fail")
                blocked = sum(1 for r in all_results if r["result"] == "Blocked")

                col_p, col_f, col_b, col_total = st.columns(4)
                with col_p:
                    st.metric("Passed", passed)
                with col_f:
                    st.metric("Failed", failed)
                with col_b:
                    st.metric("Blocked", blocked)
                with col_total:
                    rate = round(passed / total * 100) if total else 0
                    st.metric("Pass Rate", f"{rate}%")

                # Results table
                st.markdown("#### Results")
                for r in all_results:
                    icon = {"Pass": "[PASS]", "Fail": "[FAIL]", "Blocked": "[BLOCKED]"}.get(r["result"], "[NONE]")
                    duration = f"{r.get('duration_ms', 0)/1000:.2f}s"

                    with st.expander(f"{icon} `{r['tc_id']}` — {r['scenario']} | {r['result']} | {duration}",
                                     expanded=r["result"] == "Fail"):
                        if r["result"] == "Fail":
                            st.error(f"**Error:** {r.get('error_message', 'Unknown error')}")
                            if r.get("failed_step"):
                                st.markdown(f"**Failed Step:** `{r['failed_step']}`")
                            if r.get("url_at_failure"):
                                st.markdown(f"**URL at Failure:** {r['url_at_failure']}")
                            if r.get("screenshot_path"):
                                st.markdown(f"**Screenshot:** `{r['screenshot_path']}`")
                        else:
                            st.success(r.get("actual_result", "Completed"))
                        st.caption(f"Duration: {duration} | Browser: {r.get('browser_info', browser)}")

                # (balloons removed)
                st.session_state[f"last_exec_{pid}"] = exec_id

    # ── Execution History ──────────────────────────────────────────────────────
    with tab_history:
        st.markdown("### Past Executions")
        executions = db.get_executions(pid)

        if not executions:
            st.info("No executions yet. Run some tests first.")
            return

        for ex in executions:
            results = db.get_execution_results(ex["id"])
            total = len(results)
            passed = sum(1 for r in results if r["result"] == "Pass")
            failed = sum(1 for r in results if r["result"] == "Fail")
            rate = round(passed / total * 100) if total else 0

            with st.expander(
                f"{ex['name']} | {ex['status']} | {total} tests | {rate}% pass | {ex['browser']}",
                expanded=False,
            ):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Browser:** {ex['browser']} | **Headless:** {bool(ex['headless'])}")
                    st.markdown(f"**Base URL:** {ex.get('base_url','')}")
                    st.markdown(f"**Created:** {ex.get('created_at','')}")
                with col_b:
                    st.metric("Passed", passed)
                    st.metric("Failed", failed)

                if results:
                    st.markdown("**Results:**")
                    for r in results:
                        icon = {"Pass": "[PASS]", "Fail": "[FAIL]", "Blocked": "[BLOCKED]", "Skipped": "[SKIPPED]"}.get(
                            r["result"], "[NONE]"
                        )
                        dur = f"{r.get('duration_ms', 0)/1000:.2f}s"
                        st.markdown(f"{icon} `{r['tc_id']}` — {r['scenario']} — **{r['result']}** ({dur})")
                        if r["result"] == "Fail" and r.get("error_message"):
                            st.caption(f"   Error: {r['error_message'][:100]}")
