# ui/export_tab.py
"""
Export tab for Pentest Report - Ultra Corporate Edition
Fully compatible with:
- pdf_generator Ultra Corporate v3
- theme_hex color selector
- watermark toggle
- save/load JSON
"""

import streamlit as st
from datetime import datetime
import json
import base64
from io import BytesIO

from report import pdf_generator
from report import docx_generator


SAVE_FILE = "data/saved_report.json"


def save_json_file(report):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        st.error(f"Failed to save JSON: {e}")
        return False


def load_json_file():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load JSON: {e}")
        return None


def _generate_pdf(report):
    """
    PDF Generator wrapper.
    DO NOT send theme or watermark as parameters.
    pdf_generator uses them directly from report dict.
    """
    return pdf_generator.generate_pdf_bytes(report)


def _generate_docx(report):
    return docx_generator.generate_docx_bytes(report)


def render_export_tab(report_data: dict):

    st.header("📤 Export Final Report")

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
    # WATERMARK OPTION
    # -----------------------------------------------------------
    watermark = st.checkbox("Add watermark (CONFIDENTIAL)", value=report_data.get("watermark_enabled", False))
    report_data["watermark_enabled"] = watermark

    st.markdown("---")

    # -----------------------------------------------------------
    # BUTTONS (PDF / DOCX)
    # -----------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 Generate PDF Report"):
            with st.spinner("Generating PDF report..."):
                try:
                    pdf_bytes = _generate_pdf(report_data)
                    st.session_state["generated_pdf"] = pdf_bytes
                    st.success("PDF report generated successfully.")
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")

    with col2:
        if st.button("📝 Generate DOCX Report"):
            with st.spinner("Generating DOCX report..."):
                try:
                    docx_bytes = _generate_docx(report_data)
                    st.session_state["generated_docx"] = docx_bytes
                    st.success("DOCX report generated successfully.")
                except Exception as e:
                    st.error(f"Error generating DOCX: {e}")

    st.markdown("---")

    # -----------------------------------------------------------
    # DOWNLOAD GENERATED FILES
    # -----------------------------------------------------------
    pdf_data = st.session_state.get("generated_pdf")
    docx_data = st.session_state.get("generated_docx")

    if pdf_data or docx_data:
        st.subheader("⬇️ Download Files")

        fname = f"Pentest_Report_{report_data.get('client','Client')}_{datetime.now().strftime('%Y%m%d')}"

        if pdf_data:
            st.download_button(
                label="📥 Download PDF",
                data=pdf_data,
                file_name=f"{fname}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        if docx_data:
            st.download_button(
                label="📥 Download DOCX",
                data=docx_data,
                file_name=f"{fname}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
    else:
        st.info("Generate a PDF or DOCX first to enable downloads.")

    st.markdown("---")

    # -----------------------------------------------------------
    # SAVE / LOAD JSON
    # -----------------------------------------------------------
    st.subheader("💾 JSON Save / Load")

    colA, colB = st.columns(2)

    with colA:
        if st.button("💾 Save Report as JSON"):
            if save_json_file(report_data):
                st.success("Report saved to JSON.")

    with colB:
        if st.button("📂 Load JSON"):
            loaded = load_json_file()
            if loaded:
                st.session_state["report_data"] = loaded
                st.success("JSON loaded. Refreshing...")
                st.rerun()

    st.markdown("---")

    # -----------------------------------------------------------
    # EXPORT SUMMARY
    # -----------------------------------------------------------
    st.subheader("🧾 Export Summary")

    st.text(f"Client: {report_data.get('client','N/A')}")
    st.text(f"Project: {report_data.get('project','N/A')}")
    st.text(f"Tester: {report_data.get('tester','N/A')}")
    st.text(f"Findings: {len(report_data.get('findings', []))}")
    st.text(f"Additional Reports: {len(report_data.get('additional_reports', []))}")
    st.text(f"Date: {report_data.get('date','')}")

    st.caption("Export includes full corporate layout, TOC with findings and additional reports, heatmap, images, and badges.")
