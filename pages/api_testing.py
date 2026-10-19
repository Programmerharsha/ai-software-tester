"""API Testing page — manual HTTP test builder and AI-powered API test cases."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import time
import streamlit as st

import database.database as db
from testing.api_engine import APIEngine


def _require_project():
    pid = st.session_state.get("selected_project_id")
    if not pid:
        st.warning("Select a project first.")
        return None
    return pid


def render():
    st.markdown("## API Testing")

    pid = _require_project()
    if not pid:
        return

    project = db.get_project(pid)
    st.caption(f"Project: **{project['name']}** | Base URL: `{project.get('base_url','Not set')}`")

    tab_manual, tab_ai_tests = st.tabs(["Manual API Builder", "AI API Test Cases"])

    # ── Manual API Builder ────────────────────────────────────────────────────
    with tab_manual:
        st.markdown("### Manual API Test Builder")

        base_url = st.text_input("Base URL", value=project.get("base_url") or "http://localhost:5000",
                                  key="api_base_url")

        col_method, col_endpoint = st.columns([1, 3])
        with col_method:
            method = st.selectbox("Method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
        with col_endpoint:
            endpoint = st.text_input("Endpoint", placeholder="/api/login", value="/api/health")

        col_h, col_b = st.columns(2)
        with col_h:
            headers_str = st.text_area("Headers (JSON)", value='{"Content-Type": "application/json"}', height=100)
        with col_b:
            body_str = st.text_area("Body (JSON)", value="{}", height=100)

        st.markdown("**Assertions**")
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            expected_status = st.number_input("Expected Status Code", value=200, min_value=100, max_value=599)
        with col_a2:
            max_response_time = st.number_input("Max Response Time (ms)", value=2000, min_value=100)
        with col_a3:
            json_field = st.text_input("JSON Field Path", placeholder="data.token", help="Optional: check a JSON field")
        json_field_expected = st.text_input("JSON Field Expected Value", placeholder="expected value", help="Optional")

        if st.button("Run API Test", use_container_width=True):
            try:
                headers_dict = json.loads(headers_str) if headers_str.strip() else {}
            except json.JSONDecodeError:
                st.error("Invalid Headers JSON.")
                return
            try:
                body_dict = json.loads(body_str) if body_str.strip() and body_str.strip() != "{}" else {}
            except json.JSONDecodeError:
                st.error("Invalid Body JSON.")
                return

            assertions = [
                {"type": "status", "operator": "eq", "expected": expected_status},
                {"type": "response_time", "max_ms": max_response_time},
            ]
            if json_field.strip():
                assertions.append({
                    "type": "json_field",
                    "path": json_field.strip(),
                    "operator": "eq",
                    "expected": json_field_expected.strip(),
                })

            api_test = {
                "method": method,
                "endpoint": endpoint,
                "headers": headers_dict,
                "body": body_dict,
                "assertions": assertions,
            }

            eff_base = (base_url or "").strip() or project.get("base_url") or "http://localhost:5000"
            engine = APIEngine(base_url=eff_base)
            with st.spinner(f"Running {method} {endpoint}..."):
                result = engine.run_api_test(api_test)

            # Display results
            overall = result["result"]
            st.markdown("---")
            if overall == "Pass":
                st.success(f"PASS — All assertions passed")
            else:
                st.error(f"FAIL — Some assertions failed")

            c1, c2, c3 = st.columns(3)
            with c1:
                status_color = "#00e676" if result["status_code"] == expected_status else "#ff5370"
                st.markdown(f"**Status Code:** <span style='color:{status_color}'>{result['status_code']}</span>",
                            unsafe_allow_html=True)
            with c2:
                dur_color = "#00e676" if result["duration_ms"] <= max_response_time else "#ff5370"
                st.markdown(f"**Duration:** <span style='color:{dur_color}'>{result['duration_ms']}ms</span>",
                            unsafe_allow_html=True)
            with c3:
                st.markdown(f"**Method:** `{method}`")

            if result["assertions_passed"]:
                st.markdown("**Passed Assertions:**")
                for a in result["assertions_passed"]:
                    st.markdown(f"  - {a}")

            if result["assertions_failed"]:
                st.markdown("**Failed Assertions:**")
                for a in result["assertions_failed"]:
                    st.markdown(f"  - {a}")

            with st.expander("Response Body"):
                body = result.get("response_body", "")
                try:
                    st.json(json.loads(body))
                except Exception:
                    st.code(body)

    # ── AI API Test Cases ──────────────────────────────────────────────────────
    with tab_ai_tests:
        st.markdown("### AI-Generated API Tests")

        tcs = db.get_test_cases(pid)
        api_tcs = [tc for tc in tcs if tc.get("test_type", "").upper() == "API" and tc.get("actions_json")]

        if not api_tcs:
            st.info("""
            No API test cases with actions found.

            **To create API tests:**
            1. Go to Requirements page — add an API requirement
            2. Go to AI Test Generator — generate API test cases
            3. Set test type to "API" when generating actions
            4. Come back here to run them
            """)
            return

        base_url = st.text_input("API Base URL", value=project.get("base_url", "http://localhost:5000"),
                                  key="ai_api_base_url")

        tc_options = {f"{tc['tc_id']} — {tc['scenario']}": tc for tc in api_tcs}
        selected_labels = st.multiselect("Select API Test Cases to Run", list(tc_options.keys()))

        if selected_labels and st.button("Run Selected API Tests", use_container_width=True):
            engine = APIEngine(base_url=base_url)
            all_results = []

            for label in selected_labels:
                tc = tc_options[label]
                try:
                    actions_data = json.loads(tc["actions_json"])
                    api_tests = actions_data.get("api_tests", [])
                except Exception:
                    st.error(f"Invalid actions JSON for {tc['tc_id']}")
                    continue

                with st.spinner(f"Running {tc['tc_id']}..."):
                    results = engine.run_all(api_tests)
                    all_pass = all(r["result"] == "Pass" for r in results)
                    all_results.append({
                        "tc_id": tc["tc_id"],
                        "scenario": tc["scenario"],
                        "result": "Pass" if all_pass else "Fail",
                        "sub_results": results,
                    })

            # Show results
            st.markdown("### Results")
            for r in all_results:
                icon = "[PASS]" if r["result"] == "Pass" else "[FAIL]"
                with st.expander(f"{icon} {r['tc_id']} — {r['scenario']} — {r['result']}"):
                    for sub in r["sub_results"]:
                        sub_icon = "[PASS]" if sub["result"] == "Pass" else "[FAIL]"
                        st.markdown(f"{sub_icon} `{sub['method']} {sub['endpoint']}` — {sub['result']} — {sub['duration_ms']}ms")
                        if sub.get("assertions_failed"):
                            for af in sub["assertions_failed"]:
                                st.caption(f"  {af}")
                        if sub.get("assertions_passed"):
                            for ap in sub["assertions_passed"]:
                                st.caption(f"  {ap}")
