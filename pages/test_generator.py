"""AI Test Generator page — generate test cases and automation actions with Qwen."""

import json
import streamlit as st
import database.database as db
from ai.ai_service import generate_test_cases, generate_actions, generate_api_actions


def _require_project():
    pid = st.session_state.get("selected_project_id")
    if not pid:
        st.warning("⚠️ Select a project first.")
        return None
    return pid


def render():
    st.markdown("## AI Test Generator")

    pid = _require_project()
    if not pid:
        return

    project = db.get_project(pid)
    st.caption(f"Project: **{project['name']}**")

    reqs = db.get_requirements(pid)
    if not reqs:
        st.info("Add requirements first (Requirements page).")
        return

    # Requirement selector
    req_options = {f"{r['req_id']} — {r['title']}": r for r in reqs}
    chosen_label = st.selectbox("Select Requirement", list(req_options.keys()))
    req = req_options[chosen_label]

    analysis = None
    if req.get("analysis"):
        try:
            analysis = json.loads(req["analysis"])
        except Exception:
            pass

    if not analysis:
        st.info("Tip: Analyze this requirement first (Requirements page) for better test generation.")

    st.divider()

    # ── Generate Test Cases ──────────────────────────────────────────────────
    st.markdown("### Step 1: Generate Test Cases")
    col_btn, col_info = st.columns([2, 4])
    with col_btn:
        gen_btn = st.button("Generate Test Cases with Qwen", use_container_width=True)

    if gen_btn:
        with st.spinner("Qwen is generating comprehensive test cases... (this may take a minute)"):
            data, raw, err = generate_test_cases(
                req["req_id"], req["title"], req["description"], req["priority"], analysis
            )

        if data and "test_cases" in data:
            st.session_state[f"gen_tcs_{req['id']}"] = data["test_cases"]
            st.success(f"Generated {len(data['test_cases'])} test cases!")
        else:
            st.error(f"Generation failed: {err}")
            with st.expander("Raw AI response"):
                st.code(raw[:3000])

    # Show generated test cases
    gen_tcs = st.session_state.get(f"gen_tcs_{req['id']}", [])
    if gen_tcs:
        st.markdown(f"#### Generated Test Cases ({len(gen_tcs)})")
        approved = []
        for i, tc in enumerate(gen_tcs):
            tc_type = tc.get("type", "Functional")
            priority = tc.get("priority", "Medium")
            priority_icon = {"High": "[High]", "Medium": "[Med]", "Low": "[Low]"}.get(priority, "[Med]")

            with st.expander(f"{priority_icon} {tc['id']} — {tc['scenario']}", expanded=i == 0):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Type:** {tc_type}")
                    st.markdown(f"**Priority:** {priority}")
                    st.markdown(f"**Severity:** {tc.get('severity','Medium')}")
                    st.markdown("**Preconditions:**")
                    for pre in tc.get("preconditions", []):
                        st.markdown(f"- {pre}")
                with col2:
                    st.markdown("**Steps:**")
                    for j, step in enumerate(tc.get("steps", []), 1):
                        st.markdown(f"{j}. {step}")
                    if tc.get("test_data"):
                        st.markdown(f"**Test Data:** `{json.dumps(tc['test_data'])}`")

                st.markdown(f"**Expected Result:** {tc.get('expected_result','')}")
                approve = st.checkbox(f"Approve & Save TC {tc['id']}", key=f"approve_{req['id']}_{i}",
                                      value=True)
                if approve:
                    approved.append(tc)

        if st.button("Save Approved Test Cases to Database", use_container_width=True):
            existing_tcs = db.get_test_cases(pid, req["id"])
            existing_ids = {tc["tc_id"] for tc in existing_tcs}
            saved = 0
            for tc in approved:
                if tc["id"] in existing_ids:
                    continue  # skip duplicates
                steps = tc.get("steps", [])
                tc_db_id = db.create_test_case(
                    project_id=pid,
                    requirement_id=req["id"],
                    tc_id=tc["id"],
                    scenario=tc["scenario"],
                    description=tc.get("description", ""),
                    test_type=tc.get("type", "Functional"),
                    preconditions="\n".join(tc.get("preconditions", [])),
                    test_data=json.dumps(tc.get("test_data", {})),
                    expected_result=tc.get("expected_result", ""),
                    priority=tc.get("priority", "Medium"),
                    severity=tc.get("severity", "Medium"),
                    automation="Automated" if tc.get("automation_feasible", False) else "Manual",
                )
                db.add_test_steps(tc_db_id, [{"action": s, "expected": ""} for s in steps])
                saved += 1
            st.success(f"Saved {saved} test cases to database!")
            st.session_state.pop(f"gen_tcs_{req['id']}", None)
            st.rerun()

    st.divider()

    # ── Generate Automation Actions ──────────────────────────────────────────
    st.markdown("### Step 2: Generate Automation Actions")
    base_url = project.get("base_url", "http://localhost:5000")
    base_url = st.text_input("Application Base URL", value=base_url)

    tcs_in_db = db.get_test_cases(pid, req["id"])
    automated_tcs = [tc for tc in tcs_in_db if tc.get("automation") in ("Automated", "Partial")]

    if not automated_tcs:
        st.info("No automated test cases in DB yet. Save test cases first.")
        return

    tc_options = {f"{tc['tc_id']} — {tc['scenario']}": tc for tc in automated_tcs}
    chosen_tc_label = st.selectbox("Select Test Case for Action Generation", list(tc_options.keys()))
    chosen_tc = tc_options[chosen_tc_label]

    is_api = chosen_tc.get("test_type", "").upper() == "API"
    test_mode = st.radio("Test Type", ["UI (Playwright)", "API (HTTP)"],
                         index=1 if is_api else 0, horizontal=True)

    if st.button("Generate Automation Actions with Qwen", use_container_width=True):
        steps = db.get_test_steps(chosen_tc["id"])
        step_texts = [s["action"] for s in steps]
        try:
            test_data = json.loads(chosen_tc.get("test_data", "{}") or "{}")
        except Exception:
            test_data = {}

        with st.spinner("Qwen is creating structured test actions..."):
            if "API" in test_mode:
                data, raw, err = generate_api_actions(
                    chosen_tc["tc_id"], chosen_tc["scenario"],
                    step_texts, test_data, chosen_tc.get("expected_result", ""), base_url,
                )
            else:
                data, raw, err = generate_actions(
                    chosen_tc["tc_id"], chosen_tc["scenario"],
                    step_texts, test_data, chosen_tc.get("expected_result", ""), base_url,
                )

        if data:
            actions_json = json.dumps(data, indent=2)
            st.session_state[f"actions_{chosen_tc['id']}"] = actions_json
            st.success("Actions generated and validated!")

            # Show actions
            from testing.action_validator import validate_actions
            if "actions" in data:
                valid, errors = validate_actions(data["actions"])
                if not valid:
                    st.error("Action validation failed:\n" + "\n".join(errors))
                else:
                    st.success(f"{len(data['actions'])} actions validated")

            with st.expander("View Generated Actions JSON"):
                st.code(actions_json, language="json")

            if st.button("Save Actions to Test Case"):
                db.update_test_case(chosen_tc["id"], actions_json=actions_json, automation="Automated")
                st.success("Actions saved!")
                st.rerun()
        else:
            st.error(f"Action generation failed: {err}")
            with st.expander("Raw AI response"):
                st.code(raw[:3000])

    # Show existing actions
    elif chosen_tc.get("actions_json"):
        with st.expander("Existing Actions (already generated)"):
            st.code(chosen_tc["actions_json"], language="json")
