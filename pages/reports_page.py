"""Reports page — generate HTML/CSV/PDF reports with Plotly charts."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import time
from datetime import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import database.database as db
from config import REPORTS_DIR


def _require_project():
    pid = st.session_state.get("selected_project_id")
    if not pid:
        st.warning("⚠️ Select a project first.")
        return None
    return pid


def _generate_html_report(pid: int, exec_id=None) -> str:
    """Generate a complete HTML report string."""
    project = db.get_project(pid)
    metrics = db.get_project_metrics(pid)
    reqs = db.get_requirements(pid)
    tcs = db.get_test_cases(pid)
    bugs = db.get_bugs(pid)
    executions = db.get_executions(pid)

    # Gather results
    all_results = []
    for ex in (executions if exec_id is None else [db.get_execution(exec_id)]):
        if ex:
            results = db.get_execution_results(ex["id"])
            for r in results:
                r["execution_name"] = ex["name"]
                all_results.append(r)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def result_color(r):
        return {"Pass": "#00e676", "Fail": "#ff5370", "Blocked": "#ffcc02",
                "Skipped": "#9ca3af"}.get(r, "#9ca3af")

    def severity_color(s):
        return {"Critical": "#ff1744", "High": "#ff5370", "Medium": "#ffcc02",
                "Low": "#00e676"}.get(s, "#9ca3af")

    # Build HTML
    req_rows = "".join(
        f"<tr><td>{r['req_id']}</td><td>{r['title']}</td><td>{r['priority']}</td>"
        f"<td>{r['status']}</td></tr>"
        for r in reqs
    )

    tc_rows = "".join(
        f"<tr><td>{tc['tc_id']}</td><td>{tc.get('req_ref','-')}</td><td>{tc['scenario']}</td>"
        f"<td>{tc['test_type']}</td><td>{tc['priority']}</td>"
        f"<td style='color:{result_color(tc.get('status','Not Executed'))}'>"
        f"{tc.get('status','Not Executed')}</td></tr>"
        for tc in tcs
    )

    result_rows = "".join(
        f"<tr><td>{r['tc_id']}</td><td>{r['scenario']}</td>"
        f"<td style='color:{result_color(r['result'])};font-weight:bold'>{r['result']}</td>"
        f"<td>{r.get('duration_ms',0)/1000:.2f}s</td>"
        f"<td style='font-size:0.8rem;max-width:200px;word-break:break-all'>"
        f"{r.get('error_message','')[:100]}</td></tr>"
        for r in all_results
    )

    bug_rows = "".join(
        f"<tr><td>{b['bug_id']}</td><td>{b['title']}</td>"
        f"<td style='color:{severity_color(b.get('severity','Medium'))}'>{b.get('severity','Medium')}</td>"
        f"<td>{b.get('priority','Medium')}</td><td>{b.get('status','Open')}</td></tr>"
        for b in bugs
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Test Report — {project['name']}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: Inter, sans-serif; }}
    body {{ background: #0f1117; color: #e8eaf6; padding: 40px; }}
    h1 {{ font-size: 2rem; color: #a78bfa; margin-bottom: 8px; }}
    h2 {{ font-size: 1.3rem; color: #6c63ff; margin: 28px 0 12px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; }}
    .meta {{ color: #9ca3af; margin-bottom: 24px; font-size: 0.85rem; }}
    .kpis {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 28px; }}
    .kpi {{ background: #1e2130; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; text-align: center; }}
    .kpi-val {{ font-size: 1.8rem; font-weight: 700; color: #a78bfa; }}
    .kpi-label {{ font-size: 0.8rem; color: #9ca3af; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
    th {{ background: #252836; padding: 10px 14px; text-align: left; font-size: 0.85rem; color: #9ca3af; }}
    td {{ padding: 9px 14px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.85rem; }}
    tr:hover {{ background: rgba(108,99,255,0.05); }}
    .footer {{ text-align: center; color: #9ca3af; font-size: 0.8rem; margin-top: 40px; }}
  </style>
</head>
<body>
    <h1>Test Report — {project['name']}</h1>
  <p class="meta">Generated: {now} | AI Model: qwen2.5-coder:7b | Version: AI Software Tester v1.0</p>

  <div class="kpis">
    <div class="kpi"><div class="kpi-val">{metrics['total_requirements']}</div><div class="kpi-label">Requirements</div></div>
    <div class="kpi"><div class="kpi-val">{metrics['total_test_cases']}</div><div class="kpi-label">Test Cases</div></div>
    <div class="kpi"><div class="kpi-val" style="color:#00e676">{metrics['passes']}</div><div class="kpi-label">Passed</div></div>
    <div class="kpi"><div class="kpi-val" style="color:#ff5370">{metrics['fails']}</div><div class="kpi-label">Failed</div></div>
    <div class="kpi"><div class="kpi-val">{metrics['pass_rate']}%</div><div class="kpi-label">Pass Rate</div></div>
  </div>

    <h2>Requirements ({len(reqs)})</h2>
  <table>
    <tr><th>ID</th><th>Title</th><th>Priority</th><th>Status</th></tr>
    {req_rows or '<tr><td colspan="4">No requirements</td></tr>'}
  </table>

    <h2>Test Cases ({len(tcs)})</h2>
  <table>
    <tr><th>TC ID</th><th>Req</th><th>Scenario</th><th>Type</th><th>Priority</th><th>Status</th></tr>
    {tc_rows or '<tr><td colspan="6">No test cases</td></tr>'}
  </table>

    <h2>Execution Results ({len(all_results)})</h2>
  <table>
    <tr><th>TC ID</th><th>Scenario</th><th>Result</th><th>Duration</th><th>Error</th></tr>
    {result_rows or '<tr><td colspan="5">No results</td></tr>'}
  </table>

    <h2>Bugs ({len(bugs)})</h2>
  <table>
    <tr><th>Bug ID</th><th>Title</th><th>Severity</th><th>Priority</th><th>Status</th></tr>
    {bug_rows or '<tr><td colspan="5">No bugs reported</td></tr>'}
  </table>

  <div class="footer">AI Software Tester — Powered by Qwen2.5-Coder 7B via Ollama</div>
</body>
</html>"""
    return html


def _generate_csv_report(pid: int) -> bytes:
    """Generate CSV bytes of execution results."""
    executions = db.get_executions(pid)
    all_results = []
    for ex in executions:
        results = db.get_execution_results(ex["id"])
        for r in results:
            r["execution_name"] = ex["name"]
            all_results.append(r)

    if not all_results:
        df = pd.DataFrame(columns=["tc_id", "scenario", "result", "duration_ms"])
    else:
        df = pd.DataFrame(all_results)[
            [c for c in ["tc_id", "scenario", "result", "duration_ms",
                          "error_message", "failed_step", "execution_name"] if c in pd.DataFrame(all_results).columns]
        ]
    return df.to_csv(index=False).encode("utf-8")


def render():
    st.markdown("## Reports")

    pid = _require_project()
    if not pid:
        return

    project = db.get_project(pid)
    st.caption(f"Project: **{project['name']}**")

    tab_gen, tab_past = st.tabs(["Generate Report", "Past Reports"])

    # ── Generate Report ───────────────────────────────────────────────────────
    with tab_gen:
        st.markdown("### Generate New Report")

        executions = db.get_executions(pid)
        exec_options = {"All Executions": None}
        exec_options.update({f"#{ex['id']} — {ex['name']}": ex["id"] for ex in executions})

        c1, c2, c3 = st.columns(3)
        with c1:
            exec_label = st.selectbox("Execution Scope", list(exec_options.keys()))
            exec_id = exec_options[exec_label]
        with c2:
            report_name = st.text_input("Report Name", value=f"{project['name']}_Report_{datetime.now().strftime('%Y%m%d_%H%M')}")
        with c3:
            fmt = st.selectbox("Format", ["HTML", "CSV", "PDF"])

        metrics = db.get_project_metrics(pid)

        # Live preview stats
        st.markdown("#### Report Preview")
        c_a, c_b, c_c, c_d, c_e = st.columns(5)
        with c_a: st.metric("Requirements", metrics["total_requirements"])
        with c_b: st.metric("Test Cases", metrics["total_test_cases"])
        with c_c: st.metric("Passed", metrics["passes"])
        with c_d: st.metric("Failed", metrics["fails"])
        with c_e: st.metric("Pass Rate", f"{metrics['pass_rate']}%")

        if st.button(f"Generate {fmt} Report", use_container_width=True):
            with st.spinner(f"Generating {fmt} report..."):
                timestamp = int(time.time())
                filename = f"{report_name}_{timestamp}"

                if fmt == "HTML":
                    content = _generate_html_report(pid, exec_id)
                    filepath = str(REPORTS_DIR / f"{filename}.html")
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    db.save_report(pid, exec_id, report_name, "HTML", filepath)
                    st.success(f"HTML report saved: `{filepath}`")
                    st.download_button(
                        "Download HTML Report",
                        data=content.encode("utf-8"),
                        file_name=f"{filename}.html",
                        mime="text/html",
                        use_container_width=True,
                    )

                elif fmt == "CSV":
                    csv_bytes = _generate_csv_report(pid)
                    filepath = str(REPORTS_DIR / f"{filename}.csv")
                    with open(filepath, "wb") as f:
                        f.write(csv_bytes)
                    db.save_report(pid, exec_id, report_name, "CSV", filepath)
                    st.success(f"CSV report saved.")
                    st.download_button(
                        "Download CSV Report",
                        data=csv_bytes,
                        file_name=f"{filename}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

                elif fmt == "PDF":
                    try:
                        from fpdf import FPDF
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Helvetica", "B", 18)
                        pdf.cell(0, 12, f"Test Report: {project['name']}", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("Helvetica", "", 10)
                        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                                 new_x="LMARGIN", new_y="NEXT")
                        pdf.ln(4)

                        # KPIs
                        pdf.set_font("Helvetica", "B", 12)
                        pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_font("Helvetica", "", 10)
                        kpis = [
                            f"Requirements: {metrics['total_requirements']}",
                            f"Test Cases: {metrics['total_test_cases']}",
                            f"Passed: {metrics['passes']}",
                            f"Failed: {metrics['fails']}",
                            f"Pass Rate: {metrics['pass_rate']}%",
                            f"Open Bugs: {metrics['open_bugs']}",
                        ]
                        for kpi in kpis:
                            pdf.cell(0, 7, kpi, new_x="LMARGIN", new_y="NEXT")

                        filepath = str(REPORTS_DIR / f"{filename}.pdf")
                        pdf.output(filepath)
                        db.save_report(pid, exec_id, report_name, "PDF", filepath)

                        with open(filepath, "rb") as f:
                            pdf_bytes = f.read()
                        st.success(f"✅ PDF report saved.")
                        st.download_button(
                            "⬇️ Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"{filename}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except ImportError:
                        st.error("fpdf2 not installed. Run: `pip install fpdf2`")

    # ── Past Reports ──────────────────────────────────────────────────────────
    with tab_past:
        st.markdown("### 📋 Generated Reports")
        reports = db.get_reports(pid)

        if not reports:
            st.info("No reports generated yet.")
            return

        for r in reports:
            exists = Path(r.get("file_path", "")).exists()
            icon = "📄" if r.get("format") == "HTML" else "📊" if r.get("format") == "CSV" else "📑"
            status = "✅" if exists else "❌ (file missing)"

            with st.expander(f"{icon} {r['name']} | {r['format']} | {r.get('created_at','')[:16]} | {status}"):
                st.markdown(f"**File:** `{r.get('file_path','')}`")
                if exists:
                    with open(r["file_path"], "rb") as f:
                        content = f.read()
                    mime = {"HTML": "text/html", "CSV": "text/csv", "PDF": "application/pdf"}.get(r["format"], "text/plain")
                    st.download_button(
                        f"⬇️ Download {r['format']}",
                        data=content,
                        file_name=Path(r["file_path"]).name,
                        mime=mime,
                        key=f"dl_report_{r['id']}",
                    )
