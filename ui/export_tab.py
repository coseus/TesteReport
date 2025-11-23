# ui/export_tab.py
"""
Export tab for Pentest Report - Ultra Corporate Edition
Fully compatible with:
- Advanced Corporate pdf_generator
- theme_hex color selector
- watermark toggle
- save/load JSON fully
"""

import streamlit as st
from datetime import datetime
import json

from report import pdf_generator
from report import docx_generator


SAVE_FILE = "data/saved_report.json"


# -------------------------------------------------------
# JSON SAVE
# -------------------------------------------------------
def save_json_file(report):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        st.error(f"Failed to save JSON: {e}")
        return False


# -------------------------------------------------------
# JSON LOAD
# -------------------------------------------------------
def _load_json_from_disk():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load JSON: {e}")
        return None


# -------------------------------------------------------
# PDF / DOCX WRAPPERS
# -------------------------------------------------------
def _generate_pdf(report):
    return pdf_generator.generate_pdf_bytes(report)


def _generate_docx(report):
    return docx_generator.generate_docx_bytes(report)


# -------------------------------------------------------
# MAIN EXPORT TAB
# -------------------------------------------------------
def render_export_tab(report_data: dict):

    st.header("ðŸ“¤ Export Final Report")

    # -----------------------------------------------------------
    # THEME COLOR
    # -----------------------------------------------------------
    theme = st.color_picker(
        "Accent Color (theme)",
        value=report_data.get("theme_hex", "#ED863D"),
        key="theme_hex_picker"
    )
    report_data["theme_hex"] = theme

    # -----------------------------------------------------------
    # WATERMARK
    # -----------------------------------------------------------
    watermark = st.checkbox(
        "Add watermark (CONFIDENTIAL)",
        value=report_data.get("watermark_enabled", False)
    )
    report_data["watermark_enabled"] = watermark

    st.markdown("---")

    # -----------------------------------------------------------
    # GENERATE PDF / DOCX
    # -----------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        if st.button("ðŸ“„ Generate PDF Report"):
            with st.spinner("Generating PDF report..."):
                try:
                    pdf_bytes = _generate_pdf(report_data)
                    st.session_state["generated_pdf"] = pdf_bytes
                    st.success("PDF report generated successfully.")
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")

    with col2:
        if st.button("ðŸ“ Generate DOCX Report"):
            with st.spinner("Generating DOCX report..."):
                try:
                    docx_bytes = _generate_docx(report_data)
                    st.session_state["generated_docx"] = docx_bytes
                    st.success("DOCX report generated successfully.")
                except Exception as e:
                    st.error(f"Error generating DOCX: {e}")

    st.markdown("---")

    # -----------------------------------------------------------
    # DOWNLOADS
    # -----------------------------------------------------------
    pdf_data = st.session_state.get("generated_pdf")
    docx_data = st.session_state.get("generated_docx")

    if pdf_data or docx_data:
        st.subheader("â¬‡ï¸ Download Files")

        fname = f"Pentest_Report_{report_data.get('client','Client')}_{datetime.now().strftime('%Y%m%d')}"

        if pdf_data:
            st.download_button(
                label="ðŸ“¥ Download PDF",
                data=pdf_data,
                file_name=f"{fname}.pdf",
                mime="application/pdf",
                width="stretch"
            )

        if docx_data:
            st.download_button(
                label="ðŸ“¥ Download DOCX",
                data=docx_data,
                file_name=f"{fname}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                width="stretch"
            )
    else:
        st.info("Generate a PDF or DOCX first to enable downloads.")

    st.markdown("---")

# -----------------------------------------------------------
# JSON IMPORT / EXPORT (Enhanced with Auto-Validate & Selective Import)
# -----------------------------------------------------------
    st.subheader("💾 JSON Save / Load")
    
    # --- Save JSON to server ---
    if st.button("💾 Save JSON to Server"):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            st.success("JSON saved on server.")
        except Exception as e:
            st.error(f"Error saving JSON: {e}")
    
    # --- Download JSON directly ---
    json_bytes = json.dumps(report_data, indent=2, ensure_ascii=False, default=str).encode("utf-8")
    
    st.download_button(
        label="📥 Download JSON",
        data=json_bytes,
        file_name=f"Pentest_Report_{report_data.get('client','Client')}.json",
        mime="application/json",
        use_container_width=True
    )
    
    st.markdown("---")
    
    # --- Import JSON ---
    
    uploaded_json = st.file_uploader(
        "📂 Import JSON Report",
        type=["json"],
        key="json_importer"
    )
    
    # ---------------------------------------------
    # AUTO-VALIDATOR for JSON structure
    # ---------------------------------------------
    def _validate_json_structure(data: dict) -> dict:
        """Auto-repair missing fields in imported JSON."""
        TEMPLATE = {
            "client": "",
            "project": "",
            "tester": "",
            "contact": "",
            "date": "",
            "version": "1.0",
            "theme_hex": "#ED863D",
            "watermark_enabled": False,
    
            "executive_summary": "",
            "assessment_overview": "",
            "assessment_details": "",
            "scope": "",
            "scope_exclusions": "",
            "client_allowances": "",
    
            "findings": [],
            "additional_reports": [],
            "detailed_walkthrough": [],
    
            "remediation_short": [],
            "remediation_medium": [],
            "remediation_long": [],
    
            "vuln_summary_counts": {},
            "vuln_summary_total": 0,
            "vuln_by_host": {},
    
            "logo_b64": "",
        }
    
        repaired = TEMPLATE.copy()
    
        # merge keys safely
        for k, v in data.items():
            if k in repaired:
                repaired[k] = v  # overwrite allowed
            else:
                # unknown key -> keep it so user data is not lost
                repaired[k] = v
    
        return repaired
    
    
    # ---------------------------------------------
    # SELECTIVE IMPORT
    # ---------------------------------------------
    if uploaded_json:
        try:
            imported = json.loads(uploaded_json.read().decode("utf-8"))
            imported = _validate_json_structure(imported)
    
            st.success("JSON loaded. Choose what to import:")
    
            with st.expander("🧩 Selective Import Options", expanded=True):
    
                import_all = st.checkbox("Import EVERYTHING", value=False)
    
                colA, colB, colC = st.columns(3)
    
                with colA:
                    imp_client = st.checkbox("Client Information")
                    imp_scope = st.checkbox("Assessment & Scope")
                    imp_exec = st.checkbox("Executive Summary")
    
                with colB:
                    imp_findings = st.checkbox("Findings")
                    imp_reports = st.checkbox("Additional Reports")
                    imp_walk = st.checkbox("Detailed Walkthrough")
    
                with colC:
                    imp_remed = st.checkbox("Remediation Summary")
                    imp_theme = st.checkbox("Theme & Watermark")
    
            if st.button("⬆️ Apply Import"):
    
                if import_all:
                    st.session_state["report_data"] = imported
                    st.success("Imported ALL data.")
                    st.rerun()
                
                # otherwise, partial import
                rd = st.session_state["report_data"]
    
                if imp_client:
                    for key in ["client", "project", "tester", "contact", "date", "version"]:
                        rd[key] = imported[key]
    
                if imp_scope:
                    for key in ["assessment_overview", "assessment_details", "scope", "scope_exclusions", "client_allowances"]:
                        rd[key] = imported[key]
    
                if imp_exec:
                    rd["executive_summary"] = imported["executive_summary"]
    
                if imp_findings:
                    rd["findings"] = imported["findings"]
    
                if imp_reports:
                    rd["additional_reports"] = imported["additional_reports"]
    
                if imp_walk:
                    rd["detailed_walkthrough"] = imported["detailed_walkthrough"]
    
                if imp_remed:
                    for k in ["remediation_short", "remediation_medium", "remediation_long"]:
                        rd[k] = imported[k]
    
                if imp_theme:
                    rd["theme_hex"] = imported["theme_hex"]
                    rd["watermark_enabled"] = imported["watermark_enabled"]
                    rd["logo_b64"] = imported["logo_b64"]
    
                st.success("Selected data imported successfully.")
                st.rerun()
    
        except Exception as e:
            st.error(f"JSON Import Error: {e}")

    # -----------------------------------------------------------
    # EXPORT SUMMARY
    # -----------------------------------------------------------
    st.subheader("ðŸ§¾ Export Summary")
    st.text(f"Client: {report_data.get('client','N/A')}")
    st.text(f"Project: {report_data.get('project','N/A')}")
    st.text(f"Tester: {report_data.get('tester','N/A')}")
    st.text(f"Findings: {len(report_data.get('findings', []))}")
    st.text(f"Additional Reports: {len(report_data.get('additional_reports', []))}")
    st.text(f"Detailed Walkthrough: {len(report_data.get('detailed_walkthrough', []))}")
    st.text(f"Remediation Items: "
            f"{len(report_data.get('remediation_short', [])) + len(report_data.get('remediation_medium', [])) + len(report_data.get('remediation_long', []))}")
    st.text(f"Date: {report_data.get('date','')}")

    st.caption("Export includes all corporate sections: cover, TOC, sections 1â€“9, images, walkthrough, remediation summary.")
