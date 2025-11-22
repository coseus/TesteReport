# report/pdf_generator.py
"""
Corporate Extended PDF Generator - Reordered Sections
New structure:
1.0 Confidentiality & Legal
  1.1 Confidentiality Statement
  1.2 Disclaimer
  1.3 Contact Information
2.0 Finding Severity Ratings
3.0 Executive Summary
4.0 Vulnerability Summary
5.0 Assessment Overview
  5.1 Assessment Details
  5.2 Scope
  5.3 Scope Exclusions
  5.4 Client Allowances
6.0 Technical Findings
7.0 Remediation Summary
8.0 Detailed Walkthrough
9.0 Additional Reports & Scans
"""

from io import BytesIO
import io
import base64
from datetime import datetime
from PIL import Image as PILImage
import matplotlib.pyplot as plt

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage,
    Table, TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas

from report.sections.section_1_0_confidentiality_and_legal import build_section as sec10
from report.sections.section_1_1_confidentiality_statement import build_section as sec11
from report.sections.section_1_2_disclaimer import build_section as sec12
from report.sections.section_1_3_contact_information import build_section as sec13

from report.sections.section_2_0_assessment_overview import build_section as sec20
from report.sections.section_2_1_assessment_details import build_section as sec21
from report.sections.section_2_2_scope import build_section as sec22
from report.sections.section_2_3_scope_exclusions import build_section as sec23
from report.sections.section_2_4_client_allowances import build_section as sec24

from report.sections.section_3_0_finding_severity_ratings import build_section as sec30

from report.sections.section_4_0_technical_findings import build_section as sec40
from report.sections.section_4_1_additional_reports import build_section as sec41

from report.sections.section_5_0_executive_summary import build_section as sec50
from report.sections.section_5_1_vulnerability_summary import build_section as sec51

from report.sections.section_7_0_remediation_summary import build_section as sec70
from report.sections.section_8_0_detailed_walkthrough import build_section as sec80


# --------------------------------------------------------------------
# WATERMARK
# --------------------------------------------------------------------
def _add_watermark(canvas_obj, doc, text="CONFIDENTIAL"):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica-Bold", 60)
    canvas_obj.setFillGray(0.9, 0.5)
    width, height = A4
    canvas_obj.translate(width / 2.0, height / 2.0)
    canvas_obj.rotate(45)
    canvas_obj.drawCentredString(0, 0, text)
    canvas_obj.restoreState()


# --------------------------------------------------------------------
# STYLES
# --------------------------------------------------------------------
def _get_styles():
    accent = _hex_to_color(theme_hex)
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=28,
            alignment=TA_CENTER,
            textColor=accent,
            spaceAfter=24,
        )
    )

    styles.add(
        ParagraphStyle(
            name="HeadingModern",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=accent,
            spaceBefore=12,
            spaceAfter=18,  # mai mult spațiu sub titlu
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubHeading",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=accent,
            spaceBefore=10,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="NormalHelv",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TOCEntry",
            fontName="Helvetica",
            fontSize=10,
            leading=13,
        )
    )
    styles.add(
        ParagraphStyle(
            name="PreText",
            fontName="Helvetica",
            fontSize=10,
            leading=13,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=12,
            allowHTML=True
        )
    )

    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            fontName="Courier",
            fontSize=8,
            leading=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="MetaSmall",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.grey,
        )
    )

    return styles
    return styles


# --------------------------------------------------------------------
# DONUT CHART (used by Vulnerability Summary if needed)
# --------------------------------------------------------------------
def _build_vulnerability_donut(data: dict | None):
    if not data:
        return None

    labels = list(data.keys())
    values = list(data.values())
    if not values or sum(values) == 0:
        return None

    colors_map = {
        "Critical": "#e74c3c",
        "High": "#e67e22",
        "Moderate": "#f1c40f",
        "Low": "#3498db",
        "Informational": "#95a5a6",
    }

    fig, ax = plt.subplots(figsize=(3.2, 3.2))
    wedges, _, autotexts = ax.pie(
        values,
        labels=None,
        autopct="%1.0f%%",
        startangle=90,
        pctdistance=0.85,
        colors=[colors_map.get(k, "#95a5a6") for k in labels],
        wedgeprops=dict(width=0.35)
    )

    centre_circle = plt.Circle((0, 0), 0.60, fc="white")
    fig.gca().add_artist(centre_circle)
    ax.axis("equal")

    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0.5))
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="PNG", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


# --------------------------------------------------------------------
# COVER PAGE
# --------------------------------------------------------------------
def _build_cover(elements, styles, report: dict):
    elements.append(Paragraph(f"<b>Client:</b> {report.get('client', '')}", styles["CenterTitle"]))
    elements.append(Paragraph(f"<b>Project:</b> {report.get('project', '')}", styles["NormalHelv"]))
    elements.append(Paragraph(f"<b>Date:</b> {report.get('date', '')}", styles["NormalHelv"]))
    elements.append(Paragraph(f"<b>Version:</b> {report.get('version', '')}", styles["NormalHelv"]))
    elements.append(Paragraph(f"<b>Tester:</b> {report.get('tester', '')}", styles["NormalHelv"]))
    elements.append(Paragraph(f"<b>Contact:</b> {report.get('contact', '')}", styles["NormalHelv"]))

    # Optional logo (B64 from UI)
    logo_b64 = report.get("logo_b64")
    if logo_b64:
        try:
            img_data = base64.b64decode(logo_b64)
            img = PILImage.open(BytesIO(img_data))
            bio = BytesIO()
            img.save(bio, format="PNG")
            bio.seek(0)
            elements.append(Spacer(1, 12))
            elements.append(RLImage(bio, width=60 * mm, height=60 * mm))
        except Exception:
            pass

    elements.append(PageBreak())


# --------------------------------------------------------------------
# TABLE OF CONTENTS
# --------------------------------------------------------------------
def _build_toc(elements, styles):
    toc_data = [
        ["Section", "Title"],
        ["1.0", "Confidentiality & Legal"],
        ["1.1", "Confidentiality Statement"],
        ["1.2", "Disclaimer"],
        ["1.3", "Contact Information"],
        ["2.0", "Finding Severity Ratings"],
        ["3.0", "Executive Summary"],
        ["4.0", "Vulnerability Summary"],
        ["5.0", "Assessment Overview"],
        ["5.1", "Assessment Details"],
        ["5.2", "Scope"],
        ["5.3", "Scope Exclusions"],
        ["5.4", "Client Allowances"],
        ["6.0", "Technical Findings"],
        ["7.0", "Remediation Summary"],
        ["8.0", "Detailed Walkthrough"],
        ["9.0", "Additional Reports & Scans"],
    ]

    table = Table(toc_data, colWidths=[40 * mm, 120 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))

    elements.append(Paragraph("<b>Table of Contents</b>", styles["HeadingModern"]))
    elements.append(Spacer(1, 4))
    elements.append(table)
    elements.append(PageBreak())


# --------------------------------------------------------------------
# PDF GENERATOR
# --------------------------------------------------------------------
def generate_pdf_bytes(report: dict, watermark=None, theme_hex: str = "#2E3B4E") -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=25 * mm,
        rightMargin=25 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = _get_styles()
    elements = []

    # Resolve watermark text
    if isinstance(watermark, bool):
        watermark_text = "CONFIDENTIAL" if watermark else None
    elif isinstance(watermark, str) and watermark.strip():
        watermark_text = watermark
    else:
        watermark_text = "CONFIDENTIAL" if report.get("watermark_enabled") else None

    # 1) Cover
    _build_cover(elements, styles, report)

    # 2) TOC
    _build_toc(elements, styles)

    # 3) Sections in NEW ORDER

    # 1.x Confidentiality & Legal
    sec10(elements, styles, report)
    sec11(elements, styles, report)
    sec12(elements, styles, report)
    sec13(elements, styles, report)

    # 2.0 Finding Severity Ratings
    sec30(elements, styles, report)

    # 3.0 Executive Summary
    sec50(elements, styles, report)

    # 4.0 Vulnerability Summary (text + table etc.)
    sec51(elements, styles, report)

    # Optional donut chart under Vulnerability Summary (visual only, no new section number)
    if report.get("vuln_summary"):
        buf = _build_vulnerability_donut(report.get("vuln_summary", {}))
        if buf:
            elements.append(Spacer(1, 8))
            elements.append(Paragraph("Vulnerability Summary – Visual Overview", styles["SubHeading"]))
            elements.append(Spacer(1, 4))
            elements.append(RLImage(buf, width=110 * mm, height=110 * mm))
            elements.append(Spacer(1, 12))

    # 5.x Assessment & Scope
    sec20(elements, styles, report)   # 5.0 Assessment Overview
    sec21(elements, styles, report)   # 5.1 Assessment Details
    sec22(elements, styles, report)   # 5.2 Scope
    sec23(elements, styles, report)   # 5.3 Scope Exclusions
    sec24(elements, styles, report)   # 5.4 Client Allowances

    # 6.0 Technical Findings
    sec40(elements, styles, report)

    # 7.0 Remediation Summary
    sec70(elements, styles, report)

    # 8.0 Detailed Walkthrough
    sec80(elements, styles, report)

    # 9.0 Additional Reports & Scans
    sec41(elements, styles, report)

    # BUILD
    if watermark_text:
        doc.build(
            elements,
            onFirstPage=lambda c, d: _add_watermark(c, d, watermark_text),
            onLaterPages=lambda c, d: _add_watermark(c, d, watermark_text),
        )
    else:
        doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf
