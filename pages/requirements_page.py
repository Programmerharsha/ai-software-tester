"""Requirements page — add/view/analyze requirements with Qwen."""

import json
import streamlit as st
import database.database as db
from ai.ai_service import analyze_requirement


def _require_project():
    pid = st.session_state.get("selected_project_id")
    if not pid:
        st.warning("⚠️ Please select a project first (go to Projects page).")
        return None
    return pid


def render():
    st.markdown("## Requirements")

    pid = _require_project()
    if not pid:
        return

    project = db.get_project(pid)
    st.caption(f"Project: **{project['name']}**")

    tab_list, tab_new = st.tabs(["Requirements", "Add Requirement"])

    # ── Add Requirement ──────────────────────────────────────────────────────
    with tab_new:
        st.markdown("### Add New Requirement")
        with st.form("req_form", clear_on_submit=True):
            req_id = st.text_input("Requirement ID *", placeholder="REQ001")
            title = st.text_input("Title *", placeholder="User Login")
            description = st.text_area("Requirement *",
                placeholder="The user should be able to log in using a valid email address and password.",
                height=150)
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            submitted = st.form_submit_button("Save Requirement", use_container_width=True)
            if submitted:
                if not req_id or not title or not description:
                    st.error("Please fill all required fields.")
                else:
                    rid = db.create_requirement(pid, req_id, title, description, priority)
                    st.success(f"Requirement '{req_id}' saved (DB ID: {rid})")
                    st.rerun()

    # ── Requirements List ────────────────────────────────────────────────────
    with tab_list:
        reqs = db.get_requirements(pid)
        if not reqs:
            st.info("No requirements yet. Add one in the 'Add Requirement' tab.")
            return

        for req in reqs:
            status_color = {"Draft": "#9ca3af", "Analysed": "#00e676", "Tested": "#6c63ff"}.get(
                req.get("status", "Draft"), "#9ca3af"
            )
            priority_icon = {"High": "[High]", "Medium": "[Med]", "Low": "[Low]"}.get(req.get("priority", "Medium"), "[Med]")

            with st.expander(
                f"{priority_icon} {req['req_id']} — {req['title']} | Status: {req.get('status','Draft')}",
                expanded=False,
            ):
                col_info, col_actions = st.columns([3, 1])

                with col_info:
                    st.markdown(f"**Description:**\n{req['description']}")
                    st.markdown(f"**Priority:** {req['priority']} | **Status:** {req.get('status','Draft')}")

                with col_actions:
                    if st.button("Analyze with Qwen", key=f"analyze_{req['id']}",
                                 use_container_width=True):
                        with st.spinner(f"Qwen is analyzing {req['req_id']}..."):
                            data, raw, err = analyze_requirement(
                                req["req_id"], req["title"], req["description"], req["priority"]
                            )
                        if data:
                            db.update_requirement_analysis(req["id"], json.dumps(data))
                            st.success("Analysis complete!")
                            st.rerun()
                        else:
                            st.error(f"Analysis failed: {err}")
                            with st.expander("Raw response"):
                                st.code(raw)

                    if st.button("Delete", key=f"del_req_{req['id']}", use_container_width=True):
                        db.delete_requirement(req["id"])
                        st.rerun()

                # Show analysis if available
                if req.get("analysis"):
                    try:
                        analysis = json.loads(req["analysis"])
                        st.divider()
                        st.markdown("#### AI Analysis")

                        a1, a2 = st.columns(2)
                        with a1:
                            st.markdown("**Functional Requirements**")
                            for item in analysis.get("functional_requirements", []):
                                st.markdown(f"- {item}")
                            st.markdown("**Inputs**")
                            for item in analysis.get("inputs", []):
                                st.markdown(f"- {item}")
                            st.markdown("**Outputs**")
                            for item in analysis.get("outputs", []):
                                st.markdown(f"- {item}")
                            st.markdown("**Preconditions**")
                            for item in analysis.get("preconditions", []):
                                st.markdown(f"- {item}")
                            st.markdown("**Validation Rules**")
                            for item in analysis.get("validation_rules", []):
                                st.markdown(f"- {item}")

                        with a2:
                            st.markdown("**Edge Cases**")
                            for item in analysis.get("edge_cases", []):
                                st.markdown(f"- {item}")
                            st.markdown("**Boundary Conditions**")
                            for item in analysis.get("boundary_conditions", []):
                                st.markdown(f"- {item}")
                            st.markdown("**Security Concerns**")
                            for item in analysis.get("security_concerns", []):
                                st.markdown(f"- {item}")
                            st.markdown("**Possible Risks**")
                            for item in analysis.get("possible_risks", []):
                                st.markdown(f"- {item}")
                            st.markdown("**Missing Requirements**")
                            for item in analysis.get("missing_requirements", []):
                                st.markdown(f"- {item}")

                        st.markdown("**Recommended Tests**")
                        for item in analysis.get("recommended_tests", []):
                            st.markdown(f"- {item}")

                    except json.JSONDecodeError:
                        st.warning("Could not parse analysis JSON.")
