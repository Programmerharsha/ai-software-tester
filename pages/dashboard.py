"""Dashboard page — project metrics, charts, summary."""

import json
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

import database.database as db


def _donut(labels, values, colors, title):
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.65, marker_colors=colors,
        textinfo="none",
        hovertemplate="%{label}: %{value}<extra></extra>",
    ))
    fig.update_layout(
        title_text=title, title_x=0.5, title_font_color="#e8eaf6",
        showlegend=True, legend_font_color="#9ca3af",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=280, margin=dict(t=40, b=20, l=20, r=20),
    )
    return fig


def render():
    st.markdown("## Dashboard")

    proj_id = st.session_state.get("selected_project_id")
    projects = db.get_projects()

    if not projects:
        st.markdown("""
        <div style="text-align:center; padding:60px; background:rgba(108,99,255,0.05);
                    border:1px solid rgba(108,99,255,0.2); border-radius:20px;">
          <div style="font-size:3rem;"></div>
          <h2 style="color:#a78bfa;">Welcome to AI Software Tester</h2>
          <p style="color:#9ca3af;">Create your first project to get started.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Create Project", use_container_width=False):
            st.session_state.current_page = "Projects"
            st.rerun()
        return

    # Project selector
    proj_names = [p["name"] for p in projects]
    proj_ids = [p["id"] for p in projects]
    sel_idx = 0
    if proj_id in proj_ids:
        sel_idx = proj_ids.index(proj_id)

    col_sel, _ = st.columns([2, 4])
    with col_sel:
        chosen = st.selectbox("Project", proj_names, index=sel_idx, label_visibility="collapsed")
        proj_id = proj_ids[proj_names.index(chosen)]
        st.session_state.selected_project_id = proj_id

    project = db.get_project(proj_id)
    metrics = db.get_project_metrics(proj_id)

    # ── KPI Row ──────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Requirements", metrics["total_requirements"])
    with c2:
        st.metric("Test Cases", metrics["total_test_cases"])
    with c3:
        st.metric("Passed", metrics["passes"], delta=None)
    with c4:
        st.metric("Failed", metrics["fails"])
    with c5:
        st.metric("Pass Rate", f"{metrics['pass_rate']}%")
    with c6:
        st.metric("Open Bugs", metrics["open_bugs"])

    st.divider()

    # ── Charts row ──────────────────────────────────────────────────────────
    ch1, ch2, ch3 = st.columns(3)

    with ch1:
        rc = metrics["result_counts"]
        if sum(rc.values()) > 0:
            labels = list(rc.keys())
            vals = list(rc.values())
            colors = {"Pass": "#00e676", "Fail": "#ff5370", "Blocked": "#ffcc02",
                      "Skipped": "#9ca3af", "Not Executed": "#3d4a6b"}
            c_list = [colors.get(l, "#6c63ff") for l in labels]
            st.plotly_chart(_donut(labels, vals, c_list, "Test Results"), use_container_width=True)
        else:
            st.info("No execution results yet.")

    with ch2:
        bs = metrics["bug_severity"]
        if sum(bs.values()) > 0:
            labels = list(bs.keys())
            vals = list(bs.values())
            colors = {"Critical": "#ff1744", "High": "#ff5370", "Medium": "#ffcc02",
                      "Low": "#00e676"}
            c_list = [colors.get(l, "#6c63ff") for l in labels]
            st.plotly_chart(_donut(labels, vals, c_list, "Bug Severity"), use_container_width=True)
        else:
            st.info("No bugs recorded yet.")

    with ch3:
        # Automation coverage
        tcs = db.get_test_cases(proj_id)
        auto_counts = {"Automated": 0, "Manual": 0, "Partial": 0}
        for tc in tcs:
            k = tc.get("automation", "Manual")
            auto_counts[k] = auto_counts.get(k, 0) + 1
        if sum(auto_counts.values()) > 0:
            labels = list(auto_counts.keys())
            vals = list(auto_counts.values())
            colors = ["#6c63ff", "#40c4ff", "#ff5370"]
            st.plotly_chart(_donut(labels, vals, colors, "Automation Coverage"), use_container_width=True)
        else:
            st.info("No test cases yet.")

    # ── Traceability Matrix ──────────────────────────────────────────────────
    st.markdown("### Traceability Matrix")
    reqs = db.get_requirements(proj_id)
    if reqs:
        for req in reqs:
            tcs = db.get_test_cases(proj_id, req["id"])
            total = len(tcs)
            passed = sum(1 for tc in tcs if tc.get("status") == "Pass")
            failed = sum(1 for tc in tcs if tc.get("status") == "Fail")
            bugs = db.get_bugs(proj_id)
            related_bugs = [b for b in bugs if any(tc["id"] == b.get("result_id") for tc in tcs)]

            with st.expander(f"{req['req_id']} — {req['title']} ({total} tests)", expanded=False):
                if tcs:
                    for tc in tcs:
                        status = tc.get("status", "Not Executed")
                    icon = {"Pass": "[PASS]", "Fail": "[FAIL]", "Blocked": "[BLOCKED]",
                        "Skipped": "[SKIPPED]"}.get(status, "[NONE]")
                    st.markdown(f"  {icon} `{tc['tc_id']}` — {tc['scenario']} — **{status}**")
                else:
                    st.caption("No test cases linked to this requirement.")
    else:
        st.info("Add requirements to see the traceability matrix.")

    # ── Recent Bugs ──────────────────────────────────────────────────────────
    st.markdown("### 🐛 Recent Bugs")
    bugs = db.get_bugs(proj_id)[:5]
    if bugs:
        cols = ["bug_id", "title", "severity", "priority", "status"]
        import pandas as pd
        df = pd.DataFrame(bugs)[cols]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No bugs reported yet.")
