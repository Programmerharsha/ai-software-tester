"""Bug Management page — create, view, edit bugs and AI-generated bug reports."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import streamlit as st
import pandas as pd

import database.database as db


def _require_project():
    pid = st.session_state.get("selected_project_id")
    if not pid:
        st.warning("Select a project first.")
        return None
    return pid


def render():
    st.markdown("## Bug Management")

    pid = _require_project()
    if not pid:
        return

    project = db.get_project(pid)
    st.caption(f"Project: **{project['name']}**")

    tab_list, tab_report, tab_ai = st.tabs(["All Bugs", "Report Bug", "AI Bug Report"])

    # ── All Bugs ──────────────────────────────────────────────────────────────
    with tab_list:
        bugs = db.get_bugs(pid)

        # Filters
        if bugs:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                sev_filter = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low"])
            with col_f2:
                pri_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
            with col_f3:
                sta_filter = st.selectbox("Status", ["All", "Open", "In Progress", "Resolved", "Closed", "Wont Fix"])

            filtered = bugs
            if sev_filter != "All":
                filtered = [b for b in filtered if b.get("severity") == sev_filter]
            if pri_filter != "All":
                filtered = [b for b in filtered if b.get("priority") == pri_filter]
            if sta_filter != "All":
                filtered = [b for b in filtered if b.get("status") == sta_filter]

            # Summary metrics
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total", len(bugs))
            with c2:
                st.metric("Critical/High", sum(1 for b in bugs if b.get("severity") in ("Critical", "High")))
            with c3:
                st.metric("Open", sum(1 for b in bugs if b.get("status") == "Open"))
            with c4:
                st.metric("Resolved", sum(1 for b in bugs if b.get("status") in ("Resolved", "Closed")))

            st.divider()

            if not filtered:
                st.info("No bugs match the current filters.")
            else:
                for bug in filtered:
                    sev = bug.get("severity", "Medium")
                    status = bug.get("status", "Open")
                    sev_color = {"Critical": "#ff1744", "High": "#ff5370", "Medium": "#ffcc02", "Low": "#00e676"}.get(sev, "#9ca3af")
                    sta_color = {"Open": "#ff5370", "In Progress": "#ffcc02", "Resolved": "#00e676", "Closed": "#9ca3af", "Wont Fix": "#6c63ff"}.get(status, "#9ca3af")

                    with st.expander(
                        f"{bug['bug_id']} — {bug['title']}",
                        expanded=False,
                    ):
                        col_info, col_actions = st.columns([3, 1])
                        with col_info:
                            st.markdown(f"""
                            <div style="display:flex; gap:12px; margin-bottom:10px;">
                              <span style="color:{sev_color}; border:1px solid {sev_color}40; background:{sev_color}15; padding:2px 10px; border-radius:20px; font-size:0.8rem; font-weight:600;">{sev}</span>
                              <span style="color:{sta_color}; border:1px solid {sta_color}40; background:{sta_color}15; padding:2px 10px; border-radius:20px; font-size:0.8rem; font-weight:600;">{status}</span>
                              <span style="color:#9ca3af; font-size:0.8rem;">Priority: {bug.get('priority','Medium')}</span>
                            </div>
                            """, unsafe_allow_html=True)

                            if bug.get("description"):
                                st.markdown(f"**Description:** {bug['description']}")
                            if bug.get("environment"):
                                st.markdown(f"**Environment:** `{bug['environment']}`")
                            if bug.get("steps_to_repro"):
                                st.markdown("**Steps to Reproduce:**")
                                for step in bug["steps_to_repro"].split("\n"):
                                    if step.strip():
                                        st.markdown(f"  {step}")
                            if bug.get("expected_result"):
                                st.markdown(f"**Expected:** {bug['expected_result']}")
                            if bug.get("actual_result"):
                                st.markdown(f"**Actual:** {bug['actual_result']}")
                            if bug.get("error_message"):
                                st.code(bug["error_message"], language=None)
                            if bug.get("possible_cause"):
                                st.markdown(f"**Possible Cause:** {bug['possible_cause']}")

                            st.caption(f"Created: {bug.get('created_at','')[:16]} | Assigned: {bug.get('assigned_to','Unassigned')}")

                        with col_actions:
                            new_status = st.selectbox(
                                "Update Status",
                                ["Open", "In Progress", "Resolved", "Closed", "Wont Fix"],
                                index=["Open", "In Progress", "Resolved", "Closed", "Wont Fix"].index(status) if status in ["Open", "In Progress", "Resolved", "Closed", "Wont Fix"] else 0,
                                key=f"bug_status_{bug['id']}",
                            )
                            if new_status != status:
                                if st.button("Update", key=f"upd_bug_{bug['id']}"):
                                    db.update_bug(bug["id"], status=new_status)
                                    st.rerun()

                            if st.button("Delete", key=f"del_bug_{bug['id']}", use_container_width=True):
                                db.delete_bug(bug["id"])
                                st.rerun()
        else:
            st.info("No bugs reported yet. Use the 'Report Bug' or 'AI Bug Report' tabs.")

    # ── Report Bug ────────────────────────────────────────────────────────────
    with tab_report:
        st.markdown("### Manual Bug Report")
        next_id = db.get_next_bug_id(pid)

        with st.form("bug_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                bug_id = st.text_input("Bug ID", value=next_id)
                title = st.text_input("Title *", placeholder="Brief description of the bug")
                severity = st.selectbox("Severity", ["Critical", "High", "Medium", "Low"])
                priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            with c2:
                environment = st.text_input("Environment", placeholder="e.g. Local Development")
                assigned_to = st.text_input("Assigned To", placeholder="developer@team.com")
                error_message = st.text_input("Error Message", placeholder="Exception or error text")

            description = st.text_area("Description", placeholder="Detailed bug description", height=80)
            steps_to_repro = st.text_area("Steps to Reproduce", placeholder="1. Navigate to...\n2. Click...\n3. Observe...", height=100)
            c3, c4 = st.columns(2)
            with c3:
                expected_result = st.text_area("Expected Result", height=80)
            with c4:
                actual_result = st.text_area("Actual Result", height=80)
            possible_cause = st.text_area("Possible Cause", height=60)

            if st.form_submit_button("Submit Bug Report", use_container_width=True):
                if not title:
                    st.error("Title is required.")
                else:
                    db.create_bug(
                        pid, bug_id, title,
                        description=description,
                        severity=severity,
                        priority=priority,
                        environment=environment,
                        steps_to_repro=steps_to_repro,
                        expected_result=expected_result,
                        actual_result=actual_result,
                        error_message=error_message,
                        possible_cause=possible_cause,
                        assigned_to=assigned_to,
                    )
                    st.success(f"Bug {bug_id} reported!")
                    st.rerun()

    # ── AI Bug Report ─────────────────────────────────────────────────────────
    with tab_ai:
        st.markdown("### AI-Generated Bug Report")
        st.markdown("Select a failed test execution result and let Qwen generate a professional bug report.")

        # Get all failed results for this project
        executions = db.get_executions(pid)
        all_failed_results = []
        for ex in executions:
            results = db.get_execution_results(ex["id"])
            for r in results:
                if r["result"] == "Fail":
                    r["execution_name"] = ex["name"]
                    all_failed_results.append(r)

        if not all_failed_results:
            st.info("No failed test results found. Run tests first to see failures here.")
            return

        result_options = {
            f"{r['execution_name']} | {r['tc_id']} — {r['scenario']}": r
            for r in all_failed_results
        }
        chosen_label = st.selectbox("Select Failed Test Result", list(result_options.keys()))
        chosen_result = result_options[chosen_label]

        # Show failure context
        with st.expander("Failure Details", expanded=True):
            st.markdown(f"**Test Case:** {chosen_result['tc_id']} — {chosen_result['scenario']}")
            st.markdown(f"**Error:** {chosen_result.get('error_message','')}")
            st.markdown(f"**Failed Step:** {chosen_result.get('failed_step','')}")
            st.markdown(f"**URL:** {chosen_result.get('url_at_failure','')}")
            st.markdown(f"**Browser:** {chosen_result.get('browser_info','')}")

        if st.button("Generate Bug Report with Qwen", use_container_width=True):
            from ai.ai_service import generate_bug_report
            with st.spinner("Qwen is generating a professional bug report..."):
                data, raw, err = generate_bug_report(
                    tc_id=chosen_result["tc_id"],
                    scenario=chosen_result["scenario"],
                    expected=chosen_result.get("expected_result", ""),
                    actual=chosen_result.get("actual_result", ""),
                    error=chosen_result.get("error_message", ""),
                    failed_step=chosen_result.get("failed_step", ""),
                    url=chosen_result.get("url_at_failure", ""),
                    browser=chosen_result.get("browser_info", ""),
                )

            if data:
                st.success("Bug report generated!")
                st.session_state["ai_bug_draft"] = data
                st.session_state["ai_bug_result_id"] = chosen_result["id"]
            else:
                st.error(f"Generation failed: {err}")
                with st.expander("Raw response"):
                    st.code(raw[:2000])

        # Show editable draft
        if "ai_bug_draft" in st.session_state:
            draft = st.session_state["ai_bug_draft"]
            st.markdown("### Review & Edit Bug Report")
            st.info("Review the AI-generated report, edit as needed, then save.")

            with st.form("ai_bug_form"):
                next_id = db.get_next_bug_id(pid)
                c1, c2 = st.columns(2)
                with c1:
                    bug_id = st.text_input("Bug ID", value=next_id)
                    title = st.text_input("Title", value=draft.get("title", ""))
                    severity = st.selectbox("Severity",
                        ["Critical", "High", "Medium", "Low"],
                        index=["Critical", "High", "Medium", "Low"].index(draft.get("severity", "Medium")),
                    )
                with c2:
                    priority = st.selectbox("Priority",
                        ["High", "Medium", "Low"],
                        index=["High", "Medium", "Low"].index(draft.get("priority", "Medium")),
                    )
                    environment = st.text_input("Environment", value=draft.get("environment", "Local Development"))

                description = st.text_area("Description", value=draft.get("description", ""), height=80)
                steps_str = "\n".join(draft.get("steps_to_repro", []))
                steps_to_repro = st.text_area("Steps to Reproduce", value=steps_str, height=120)
                c3, c4 = st.columns(2)
                with c3:
                    expected_result = st.text_area("Expected", value=draft.get("expected_result", ""), height=80)
                with c4:
                    actual_result = st.text_area("Actual", value=draft.get("actual_result", ""), height=80)
                error_message = st.text_input("Error", value=draft.get("error_message", ""))
                possible_cause = st.text_area("Possible Cause", value=draft.get("possible_cause", ""), height=60)

                if st.form_submit_button("Save Bug Report", use_container_width=True):
                    db.create_bug(
                        pid, bug_id, title,
                        result_id=st.session_state.get("ai_bug_result_id"),
                        description=description,
                        severity=severity,
                        priority=priority,
                        environment=environment,
                        steps_to_repro=steps_to_repro,
                        expected_result=expected_result,
                        actual_result=actual_result,
                        error_message=error_message,
                        possible_cause=possible_cause,
                    )
                    st.success(f"Bug {bug_id} saved!")
                    del st.session_state["ai_bug_draft"]
                    st.rerun()
