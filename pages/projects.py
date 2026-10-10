"""Projects page — create, view, edit, delete projects."""

import streamlit as st
import database.database as db


def render():
    st.markdown("## Projects")

    tab_list, tab_new = st.tabs(["All Projects", "New Project"])

    # ── New Project ──────────────────────────────────────────────────────────
    with tab_new:
        st.markdown("### Create New Project")
        with st.form("new_project_form", clear_on_submit=True):
            name = st.text_input("Project Name *", placeholder="e.g. E-commerce Platform")
            description = st.text_area("Description", placeholder="Brief description of the project...", height=100)
            base_url = st.text_input("Application Base URL", placeholder="http://localhost:3000")

            submitted = st.form_submit_button("Create Project", use_container_width=True)
            if submitted:
                if not name:
                    st.error("Project name is required.")
                else:
                    pid = db.create_project(name, description, base_url)
                    st.session_state.selected_project_id = pid
                st.success(f"Project '{name}' created (ID: {pid})")
                st.rerun()

    # ── Project List ─────────────────────────────────────────────────────────
    with tab_list:
        projects = db.get_projects()
        if not projects:
            st.info("No projects yet. Create one in the 'New Project' tab.")
            return

        for p in projects:
            metrics = db.get_project_metrics(p["id"])
            selected = st.session_state.get("selected_project_id") == p["id"]
            border_color = "#6c63ff" if selected else "rgba(255,255,255,0.08)"

            st.markdown(f"""
            <div style="border:1px solid {border_color}; border-radius:14px; padding:18px 22px;
                        background:{'rgba(108,99,255,0.08)' if selected else '#1e2130'};
                        margin-bottom:12px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                  <span style="font-size:1.1rem; font-weight:700; color:#a78bfa;">#{p['id']}</span>
                  <span style="font-size:1.2rem; font-weight:700; margin-left:8px;">{p['name']}</span>
                  <span style="font-size:0.75rem; color:#9ca3af; margin-left:12px;">
                    {p.get('base_url','') or 'No URL set'}
                  </span>
                </div>
                <span style="font-size:0.75rem; color:#9ca3af;">{p.get('created_at','')[:10]}</span>
              </div>
              <div style="color:#9ca3af; margin-top:6px; font-size:0.9rem;">
                {p.get('description','') or 'No description'}
              </div>
              <div style="margin-top:10px; display:flex; gap:20px; font-size:0.85rem;">
                <span>{metrics['total_requirements']} Requirements</span>
                <span>{metrics['total_test_cases']} Tests</span>
                <span>{metrics['pass_rate']}% Pass Rate</span>
                <span>{metrics['open_bugs']} Open Bugs</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, _ = st.columns([1, 1, 1, 5])
            with c1:
                if st.button("Select", key=f"sel_{p['id']}", use_container_width=True):
                    st.session_state.selected_project_id = p["id"]
                    st.rerun()
            with c2:
                if st.button("Edit", key=f"edit_{p['id']}", use_container_width=True):
                    st.session_state[f"editing_{p['id']}"] = True
            with c3:
                if st.button("Delete", key=f"del_{p['id']}", use_container_width=True):
                    db.delete_project(p["id"])
                    if st.session_state.get("selected_project_id") == p["id"]:
                        st.session_state.selected_project_id = None
                    st.rerun()

            if st.session_state.get(f"editing_{p['id']}"):
                with st.form(f"edit_form_{p['id']}"):
                    new_name = st.text_input("Name", value=p["name"])
                    new_desc = st.text_area("Description", value=p.get("description", ""))
                    new_url = st.text_input("Base URL", value=p.get("base_url", ""))
                    if st.form_submit_button("Save"):
                        db.update_project(p["id"], name=new_name, description=new_desc, base_url=new_url)
                        st.session_state.pop(f"editing_{p['id']}", None)
                        st.rerun()
