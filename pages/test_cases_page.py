"""Test Cases Management page — view, add, edit test cases and steps."""

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
        st.warning("⚠️ Select a project first.")
        return None
    return pid


def render():
    st.markdown("## Test Cases")

    pid = _require_project()
    if not pid:
        return

    project = db.get_project(pid)
    st.caption(f"Project: **{project['name']}**")

    tab_list, tab_add, tab_steps = st.tabs(["All Test Cases", "Add Manual Test Case", "Manage Steps"])

    # ── All Test Cases ────────────────────────────────────────────────────────
    with tab_list:
        tcs = db.get_test_cases(pid)

        if not tcs:
            st.info("No test cases yet. Use the AI Test Generator or 'Add Manual Test Case' tab.")
            return

        # Filters
        reqs = db.get_requirements(pid)
        req_options = {"All": None}
        req_options.update({r["req_id"]: r["id"] for r in reqs})

        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            req_filter = st.selectbox("Requirement", list(req_options.keys()))
        with col_f2:
            type_filter = st.selectbox("Type", ["All", "Functional", "Negative", "Boundary", "Validation",
                                                  "Security", "API", "UI", "Regression"])
        with col_f3:
            pri_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
        with col_f4:
            auto_filter = st.selectbox("Automation", ["All", "Automated", "Manual", "Partial"])

        # Apply filters
        filtered = tcs
        if req_filter != "All":
            req_id = req_options[req_filter]
            filtered = [tc for tc in filtered if tc.get("requirement_id") == req_id]
        if type_filter != "All":
            filtered = [tc for tc in filtered if tc.get("test_type") == type_filter]
        if pri_filter != "All":
            filtered = [tc for tc in filtered if tc.get("priority") == pri_filter]
        if auto_filter != "All":
            filtered = [tc for tc in filtered if tc.get("automation") == auto_filter]

        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total", len(filtered))
        with c2: st.metric("High Priority", sum(1 for tc in filtered if tc.get("priority") == "High"))
        with c3: st.metric("Automated", sum(1 for tc in filtered if tc.get("automation") == "Automated"))
        with c4: st.metric("Passed", sum(1 for tc in filtered if tc.get("status") == "Pass"))

        st.divider()

        for tc in filtered:
            p_icon = {"High": "[High]", "Medium": "[Med]", "Low": "[Low]"}.get(tc.get("priority", "Medium"), "[Med]")
            status = tc.get("status", "Not Executed")
            s_icon = {"Pass": "[PASS]", "Fail": "[FAIL]", "Blocked": "[BLOCKED]", "Skipped": "[SKIPPED]", "Not Executed": "[NONE]"}.get(status, "[NONE]")
            auto = tc.get("automation", "Manual")
            has_actions = bool(tc.get("actions_json"))

            with st.expander(
                f"{p_icon} {s_icon} `{tc['tc_id']}` — {tc['scenario']} | {tc['test_type']} | {auto}",
                expanded=False,
            ):
                col_info, col_act = st.columns([3, 1])

                with col_info:
                    st.markdown(f"**Type:** {tc['test_type']} | **Priority:** {tc['priority']} | **Severity:** {tc.get('severity','Medium')}")
                    if tc.get("req_ref"):
                        st.markdown(f"**Requirement:** `{tc['req_ref']}`")
                    if tc.get("description"):
                        st.markdown(f"**Description:** {tc['description']}")
                    if tc.get("preconditions"):
                        st.markdown(f"**Preconditions:**\n{tc['preconditions']}")
                    if tc.get("expected_result"):
                        st.markdown(f"**Expected Result:** {tc['expected_result']}")
                    if tc.get("test_data") and tc["test_data"] not in ("{}", "null", ""):
                        try:
                            td = json.loads(tc["test_data"])
                            if td:
                                st.markdown(f"**Test Data:** `{json.dumps(td)}`")
                        except Exception:
                            pass
                    st.markdown(f"**Automation:** {auto} | {'Actions ready' if has_actions else 'No actions yet'}")
                    st.caption(f"Created by: {tc.get('created_by','AI')} | {tc.get('created_at','')[:16]}")

                    # Show steps
                    steps = db.get_test_steps(tc["id"])
                    if steps:
                        st.markdown("**Steps:**")
                        for s in steps:
                            st.markdown(f"  {s['step_number']}. {s['action']}")

                with col_act:
                    if st.button("Delete", key=f"del_tc_{tc['id']}", use_container_width=True):
                        db.delete_test_case(tc["id"])
                        st.rerun()

                    if has_actions:
                        with st.expander("Actions JSON"):
                            st.code(tc["actions_json"], language="json")

    # ── Add Manual Test Case ───────────────────────────────────────────────────
    with tab_add:
        st.markdown("### Add Manual Test Case")

        reqs = db.get_requirements(pid)
        req_map = {r["req_id"]: r["id"] for r in reqs}
        req_options_list = ["(No requirement)"] + list(req_map.keys())

        with st.form("manual_tc_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                tc_id = st.text_input("Test Case ID *", placeholder="TC001")
                scenario = st.text_input("Scenario *", placeholder="Login with valid credentials")
                test_type = st.selectbox("Test Type", [
                    "Functional", "Negative", "Boundary", "Validation",
                    "Security", "API", "UI", "Regression",
                ])
                priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            with c2:
                severity = st.selectbox("Severity", ["Critical", "High", "Medium", "Low"])
                automation = st.selectbox("Automation", ["Manual", "Automated", "Partial"])
                req_label = st.selectbox("Linked Requirement", req_options_list)

            description = st.text_area("Description", height=80)
            preconditions = st.text_area("Preconditions", height=60,
                                         placeholder="User account exists; Application is accessible")
            expected_result = st.text_area("Expected Result *", height=80)
            test_data_str = st.text_area("Test Data (JSON)", value="{}", height=60)

            if st.form_submit_button("Add Test Case", use_container_width=True):
                if not tc_id or not scenario or not expected_result:
                    st.error("TC ID, Scenario, and Expected Result are required.")
                else:
                    req_id = req_map.get(req_label) if req_label != "(No requirement)" else None
                    try:
                        test_data = json.loads(test_data_str) if test_data_str.strip() else {}
                    except Exception:
                        test_data = {}

                    # Check for existing test cases in this project for auto-numbering
                    existing = db.get_test_cases(pid)
                    existing_ids = {tc["tc_id"] for tc in existing}
                    if tc_id in existing_ids:
                        st.error(f"Test Case ID '{tc_id}' already exists in this project.")
                    else:
                        tc_db_id = db.create_test_case(
                            project_id=pid,
                            requirement_id=req_id,
                            tc_id=tc_id,
                            scenario=scenario,
                            description=description,
                            test_type=test_type,
                            preconditions=preconditions,
                            expected_result=expected_result,
                            priority=priority,
                            severity=severity,
                            automation=automation,
                            test_data=json.dumps(test_data),
                            created_by="Manual",
                        )
                        st.success(f"Test Case '{tc_id}' added!")
                        st.rerun()

    # ── Manage Steps ───────────────────────────────────────────────────────────
    with tab_steps:
        st.markdown("### Manage Test Steps")

        tcs = db.get_test_cases(pid)
        if not tcs:
            st.info("No test cases yet.")
            return

        tc_options = {f"{tc['tc_id']} — {tc['scenario']}": tc for tc in tcs}
        chosen_label = st.selectbox("Select Test Case", list(tc_options.keys()))
        chosen_tc = tc_options[chosen_label]

        current_steps = db.get_test_steps(chosen_tc["id"])

        st.markdown(f"#### Steps for `{chosen_tc['tc_id']}`")
        if current_steps:
            for step in current_steps:
                st.markdown(f"**{step['step_number']}.** {step['action']}")
        else:
            st.caption("No steps defined yet.")

        st.divider()
        st.markdown("**Edit Steps**")
        st.caption("Enter one step per line. Save will replace all existing steps.")

        steps_text = st.text_area(
            "Steps (one per line)",
            value="\n".join(s["action"] for s in current_steps),
            height=180,
            key=f"steps_{chosen_tc['id']}",
        )

        if st.button("Save Steps", use_container_width=True):
            lines = [l.strip() for l in steps_text.split("\n") if l.strip()]
            db.add_test_steps(chosen_tc["id"], [{"action": l, "expected": ""} for l in lines])
            st.success(f"{len(lines)} steps saved for {chosen_tc['tc_id']}")
            st.rerun()
