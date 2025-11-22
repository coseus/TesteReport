# report/pdf_generator.py
"""
Advanced Corporate PDF Generator — ULTRA EDITION v5 (final)

Structură & paginare:
- Pagina 1: Cover (fără header)
- Pagina 2: Table of Contents
- Pagina 3: 1.x Confidentiality & Legal (1.0–1.3)
- Pagina 4: 2.x Assessment + 3.0 Finding Severity Ratings
- Pagina 5: 4.0 Executive Summary + 5.0 Vulnerability Summary
- Pagina 6+: 6.0 Technical Findings (6.x Findings, cu poze)
- După: 7.0 Additional Reports & Scans (7.x, cu poze)

Features:
- Header bar ~30px, logo stânga (RGB JPEG), Client – Project dreapta
- Footer cu număr de pagină
- Watermark opțional
- Imagini sigure (RGB JPEG, deduplicate) în Findings & Additional Reports
- Vulnerability Summary text + tabel (heatmap compact eliminat)
"""

from io import BytesIO
import base64
from collections import defaultdict

from PIL import Image as PILImage

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    Image as RLImage,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Preformatted

from util.helpers import format_multiline as _format_text
from util.helpers import preformat as _pre

# SECTION IMPORTS (1.x, 2.x, 3.0, 4.0, 5.0 text)
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
from report.sections.section_5_0_executive_summary import build_section as sec50
from report.sections.section_5_1_vulnerability_summary import build_section as sec51
from report.sections.section_7_0_remediation_summary import build_section as sec70
from report.sections.section_8_0_detailed_walkthrough import build_section as sec80


SEVERITIES_ORDER = ["Critical", "High", "Moderate", "Low", "Informational"]


# ---------- Helpers ----------
def _hex_to_color(hex_str):
    try:
        return colors.HexColor(hex_str)
    except Exception:
        return colors.HexColor("#2E3B4E")


def _truncate_title(title: str, max_words=7):
    if not title:
        return ""
    words = title.split()
    if len(words) <= max_words:
        return title
    return " ".join(words[:max_words]) + " ..."


def _compute_vuln_summary(report):
    """
    Calculează:
    - total pe severități (global)
    (by_host rămâne dacă vrei să-l folosești ulterior, dar nu e folosit în v5)
    """
    findings = report.get("findings", []) or []
    counts = {s: 0 for s in SEVERITIES_ORDER}
    by_host = defaultdict(lambda: {s: 0 for s in SEVERITIES_ORDER})

    for f in findings:
        sev = f.get("severity", "Informational")
        if sev not in SEVERITIES_ORDER:
            sev = "Informational"
        host = (f.get("host") or "Unknown").strip() or "Unknown"
        counts[sev] += 1
        by_host[host][sev] += 1

    total = sum(counts.values())
    report["vuln_summary_counts"] = counts
    report["vuln_summary_total"] = total
    report["vuln_by_host"] = by_host


# ---------- Styles ----------
def _build_styles(theme_hex):
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
            name="CenterTitle",
            fontName="Helvetica-Bold",
            fontSize=14,
            alignment=TA_CENTER,
            textColor=accent,
            spaceBefore=12,
            spaceAfter=12,  # mai mult spațiu sub titlu
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


# ---------- Header / Footer / Watermark ----------
def _draw_header(canvas, doc, report, accent):
    page = canvas.getPageNumber()
    if page == 1:
        # Fără header pe copertă
        return

    canvas.saveState()
    w, h = A4

    # bară ~30px (aprox 24pt)
    bar_h = 24
    canvas.setFillColor(accent)
    canvas.rect(0, h - bar_h, w, bar_h, fill=1, stroke=0)

    # logo stânga (convertit la JPEG RGB)
    logo_b64 = report.get("logo_b64")
    if logo_b64:
        try:
            raw = base64.b64decode(logo_b64)
            img = PILImage.open(BytesIO(raw))
            if img.mode != "RGB":
                img = img.convert("RGB")
            bio = BytesIO()
            img.save(bio, format="JPEG")
            bio.seek(0)
            logo = ImageReader(bio)
            canvas.drawImage(
                logo,
                10 * mm,
                h - bar_h + 2,
                width=14 * mm,
                height=14 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            pass

    # Client – Project dreapta
    client = report.get("client", "")
    project = report.get("project", "")
    text = f"{client} – {project}" if (client or project) else "Penetration Test Report"
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawRightString(w - 15 * mm, h - bar_h + 8, text)

    canvas.restoreState()


def _draw_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(w - 20 * mm, 10 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def _add_watermark(canvas, text="CONFIDENTIAL"):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 60)
    canvas.setFillGray(0.9, 0.15)
    w, h = A4
    canvas.translate(w / 2, h / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, text)
    canvas.restoreState()

# ---------- Safe Image Helper (dedupe) ----------
def _pdf_safe_images(b64_list, max_w_mm: float = 140.0):
    """
    Primește o listă de B64, dedupe (elimină duplicate) și întoarce
    o listă de RLImage-uri sigure (RGB JPEG, resize).
    """
    images = []
    seen = set()

    for b64img in b64_list or []:
        if not b64img or b64img in seen:
            continue
        seen.add(b64img)

        try:
            raw = base64.b64decode(b64img)
            img = PILImage.open(BytesIO(raw))

            if img.mode != "RGB":
                img = img.convert("RGB")

            max_w_px = int(max_w_mm * 3.78)  # aproximare mm -> px
            if img.width > max_w_px:
                ratio = max_w_px / float(img.width)
                img = img.resize((max_w_px, int(img.height * ratio)))

            bio = BytesIO()
            img.save(bio, format="JPEG", quality=92)
            bio.seek(0)
            images.append(RLImage(bio, width=max_w_mm * mm))
        except Exception:
            continue

    return images


# ---------- Technical Findings (6.0 / 6.x) ----------
def _build_technical_findings(elements, styles, report):
    findings = report.get("findings", []) or []
    if not findings:
        return

    elements.append(Paragraph("6.0 Technical Findings", styles["HeadingModern"]))
    elements.append(Spacer(1, 6))

    # sortare după severitate ordonată
    def sev_key(f):
        try:
            return SEVERITIES_ORDER.index(f.get("severity", "Informational"))
        except ValueError:
            return len(SEVERITIES_ORDER)

    findings_sorted = sorted(findings, key=sev_key)

    for f in findings_sorted:
        fid = f.get("id") or "-"
        sev = f.get("severity", "Informational")
        title = f.get("title", "Untitled Finding")

        elements.append(
            Paragraph(f"6.{fid} [{sev}] {title}", styles["SubHeading"])
        )

        # meta info
        meta_lines = []
        host = f.get("host")
        if host:
            meta_lines.append(f"Host: {host}")
        port = f.get("port")
        proto = f.get("protocol")
        if port or proto:
            meta_lines.append(f"Port/Proto: {port or '-'} / {proto or '-'}")
        cvss = f.get("cvss")
        if cvss:
            meta_lines.append(f"CVSS: {cvss}")
        cve = f.get("cve")
        if cve:
            meta_lines.append(f"CVE: {cve}")

        if meta_lines:
            elements.append(
                Paragraph(" | ".join(meta_lines), styles["MetaSmall"])
            )
            elements.append(Spacer(1, 4))

        if f.get("description"):
            elements.append(Paragraph("<b>Description</b>", styles["NormalHelv"]))
            elements.append(
                Paragraph(f.get("description", "").replace("\n", "<br/>"), styles["NormalHelv"])
            )
            elements.append(Spacer(1, 4))

        if f.get("impact"):
            elements.append(Paragraph("<b>Impact</b>", styles["NormalHelv"]))
            elements.append(
                Paragraph(f.get("impact", "").replace("\n", "<br/>"), styles["NormalHelv"])
            )
            elements.append(Spacer(1, 4))

        if f.get("recommendation"):
            elements.append(Paragraph("<b>Recommendation</b>", styles["NormalHelv"]))
            elements.append(
                Paragraph(f.get("recommendation", "").replace("\n", "<br/>"), styles["NormalHelv"])
            )
            elements.append(Spacer(1, 4))

        if f.get("code"):
            elements.append(Paragraph("<b>Code / Output</b>", styles["NormalHelv"]))
            safe_code = (
                f.get("code", "")
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br/>")
            )
            elements.append(
                Paragraph(f"<font face='Courier'>{safe_code}</font>", styles["NormalHelv"])
            )
            elements.append(Spacer(1, 4))

        img_objs = _pdf_safe_images(f.get("images", []), max_w_mm=140)
        if img_objs:
            elements.append(Paragraph("<b>Evidence Images</b>", styles["NormalHelv"]))
            elements.append(Spacer(1, 2))
            for img in img_objs:
                elements.append(img)
                elements.append(Spacer(1, 6))

        elements.append(Spacer(1, 12))


# ---------- Additional Reports (9.0 / 9.x) ----------
def _build_additional_reports(elements, styles, report):
    additional = report.get("additional_reports", []) or []
    if not additional:
        return

    elements.append(Paragraph("7.0 Additional Reports & Scans", styles["HeadingModern"]))
    elements.append(Spacer(1, 6))

    for idx, r in enumerate(additional, start=1):
        title = r.get("name", f"Item {idx}")
        desc = r.get("description", "")
        code = r.get("code", "")
        images = r.get("images", []) or []

        elements.append(
            Paragraph(f"7.{idx} {title}", styles["SubHeading"])
        )
        elements.append(Spacer(1, 2))

        if desc:
            elements.append(
                Paragraph(desc.replace("\n", "<br/>"), styles["NormalHelv"])
            )
            elements.append(Spacer(1, 4))

        if code:
            elements.append(Paragraph("<b>Code / Output</b>", styles["NormalHelv"]))
            safe_code = (
                code.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br/>")
            )
            elements.append(
                Paragraph(f"<font face='Courier'>{safe_code}</font>", styles["NormalHelv"])
            )
            elements.append(Spacer(1, 4))

        img_objs = _pdf_safe_images(images, max_w_mm=140)
        if img_objs:
            elements.append(Paragraph("<b>Evidence Images</b>", styles["NormalHelv"]))
            elements.append(Spacer(1, 2))
            for img in img_objs:
                elements.append(img)
                elements.append(Spacer(1, 6))

        elements.append(Spacer(1, 10))
        
def _build_remediation_summary(elements, styles, report):
    """
    Section 7.0 – Remediation Summary
    Fields inside report:
        report["remediation_short"]
        report["remediation_medium"]
        report["remediation_long"]
    """

    elements.append(Paragraph("7.0 Remediation Summary", styles["HeadingModern"]))
    elements.append(Spacer(1, 6))

    # -------- SHORT TERM --------
    short = report.get("remediation_short", [])
    elements.append(Paragraph("<b>7.1 Short Term</b>", styles["SubHeading"]))
    if not short:
        elements.append(Paragraph("No short-term remediation items provided.", styles["NormalHelv"]))
    else:
        for item in short:
            line = item.replace("\n", "<br/>")
            elements.append(Paragraph(f"• {line}", styles["NormalHelv"]))
    elements.append(Spacer(1, 10))

    # -------- MEDIUM TERM --------
    medium = report.get("remediation_medium", [])
    elements.append(Paragraph("<b>7.2 Medium Term</b>", styles["SubHeading"]))
    if not medium:
        elements.append(Paragraph("No medium-term remediation items provided.", styles["NormalHelv"]))
    else:
        for item in medium:
            line = item.replace("\n", "<br/>")
            elements.append(Paragraph(f"• {line}", styles["NormalHelv"]))
    elements.append(Spacer(1, 10))

    # -------- LONG TERM --------
    long = report.get("remediation_long", [])
    elements.append(Paragraph("<b>7.3 Long Term</b>", styles["SubHeading"]))
    if not long:
        elements.append(Paragraph("No long-term remediation items provided.", styles["NormalHelv"]))
    else:
        for item in long:
            line = item.replace("\n", "<br/>")
            elements.append(Paragraph(f"• {line}", styles["NormalHelv"]))
    elements.append(Spacer(1, 10))



def _build_detailed_walkthrough(elements, styles, report):
    """
    Section 8.0 – Detailed Walkthrough
    Uses report["detailed_walkthrough"] = [
        {
            "name": "...",
            "description": "...",
            "code": "...",
            "images": [b64, b64, ...]
        }
    ]
    """
    from util.helpers import pdf_safe_image
    import base64

    elements.append(Paragraph("8.0 Detailed Walkthrough", styles["HeadingModern"]))
    elements.append(Spacer(1, 8))

    steps = report.get("detailed_walkthrough", [])

    if not steps:
        elements.append(Paragraph("No walkthrough steps provided.", styles["NormalHelv"]))
        elements.append(Spacer(1, 10))
        return

    for idx, step in enumerate(steps, start=1):
        title = step.get("name", f"Step {idx}")
        desc = step.get("description", "").replace("\n", "<br/>")
        code = step.get("code", "")
        imgs = step.get("images", [])

        # ---- title ----
        elements.append(Paragraph(f"<b>8.{idx} – {title}</b>", styles["SubHeading"]))
        elements.append(Spacer(1, 4))

        # ---- description ----
        if desc:
            elements.append(Paragraph(desc, styles["NormalHelv"]))
            elements.append(Spacer(1, 6))

        # ---- code block ----
        if code:
            code_html = code.replace(" ", "&nbsp;").replace("\n", "<br/>")
            elements.append(Paragraph(f"<font face='Courier'>{code_html}</font>", styles["CodeBlock"]))
            elements.append(Spacer(1, 6))

        # ---- images ----
        for b64 in imgs:
            try:
                stream, w, h = pdf_safe_image(b64, max_width_mm=150)
                if stream:
                    elements.append(RLImage(stream, width=w, height=h))
                    elements.append(Spacer(1, 8))
            except:
                continue

        elements.append(Spacer(1, 10))





# ---------- MAIN ----------
def generate_pdf_bytes(report: dict) -> bytes:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=25 * mm,
        bottomMargin=20 * mm,
    )

    theme_hex = report.get("theme_hex", "#2E3B4E")
    accent = _hex_to_color(theme_hex)
    watermark_enabled = bool(report.get("watermark_enabled", False))

    styles = _build_styles(theme_hex)
    elements = []

    # Vulnerability summary pre-calc (folosit de section_5_1)
    _compute_vuln_summary(report)

    # ==========================================================
    # PAGINA 1: COVER
    # ==========================================================
    elements.append(Paragraph("PENETRATION TESTING REPORT", styles["ReportTitle"]))
    elements.append(Spacer(1, 20))

    info = [
        ["Client:", report.get("client", "")],
        ["Project:", report.get("project", "")],
        ["Date:", str(report.get("date", ""))],
        ["Version:", report.get("version", "")],
        ["Tester:", report.get("tester", "")],
        ["Contact:", report.get("contact", "")],
    ]
    info_table = Table(info, colWidths=[40 * mm, None])
    info_table.setStyle(
        TableStyle(
            [
                ("TEXTCOLOR", (0, 0), (0, -1), accent),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(info_table)

    if report.get("logo_b64"):
        try:
            img_data = base64.b64decode(report["logo_b64"])
            img = PILImage.open(BytesIO(img_data))
            if img.mode != "RGB":
                img = img.convert("RGB")
            bio = BytesIO()
            img.save(bio, format="JPEG")
            bio.seek(0)
            elements.append(Spacer(1, 20))
            elements.append(RLImage(bio, width=45 * mm, height=45 * mm))
        except Exception:
            pass

    elements.append(Spacer(1, 30))
    elements.append(
        Paragraph(
            "This report contains confidential security assessment information. "
            "Unauthorized disclosure is prohibited.",
            styles["NormalHelv"],
        )
    )
    elements.append(PageBreak())

# ==========================================================
# TABLE OF CONTENTS (pagina 2)
# ==========================================================

    elements.append(Paragraph("Table of Contents", styles["HeadingModern"]))
    elements.append(Spacer(1, 8))

    toc_entries = []

    # ---------- 1.x Confidentiality ----------
    toc_entries += [
        ("1.0", "Confidentiality & Legal"),
        ("1.1", "Confidentiality Statement"),
        ("1.2", "Disclaimer"),
        ("1.3", "Contact Information"),
    ]

    # ---------- 2.x Finding Severity Ratings ----------
    toc_entries.append(("2.0", "Finding Severity Ratings"))

    # ---------- 3.x Executive Summary ----------
    toc_entries.append(("3.0", "Executive Summary"))

    # ---------- 4.x Vulnerability Summary ----------
    toc_entries.append(("4.0", "Vulnerability Summary"))

    # ---------- 5.x Assessment Overview ----------
    toc_entries += [
        ("5.0", "Assessment Overview"),
        ("5.1", "Assessment Details"),
        ("5.2", "Scope"),
        ("5.3", "Scope Exclusions"),
        ("5.4", "Client Allowances"),
    ]

    # ---------- 6.x Technical Findings ----------
    toc_entries.append(("6.0", "Technical Findings"))

    # Preluăm findings 6.x.x
    for f in report.get("findings", []):
        fid = f.get("id")
        if not fid:
            continue
        severity = f.get("severity", "Informational")
        title = _truncate_title(f.get("title", "Untitled Finding"))
        toc_entries.append((f"6.{fid}", f"{severity} – {title}"))

    # ---------- 7.x Remediation Summary ----------
    toc_entries.append(("7.0", "Remediation Summary"))
    toc_entries.append(("7.1", "Short Term"))
    toc_entries.append(("7.2", "Medium Term"))
    toc_entries.append(("7.3", "Long Term"))

    # ---------- 8.x Detailed Walkthrough ----------
    toc_entries.append(("8.0", "Detailed Walkthrough"))

    # preluăm steps 8.x
    for idx, step in enumerate(report.get("detailed_walkthrough", []), start=1):
        name = _truncate_title(step.get("name", "Untitled Step"))
        toc_entries.append((f"8.{idx}", name))

    # ---------- 9.x Additional Reports ----------
    toc_entries.append(("9.0", "Additional Reports & Scans"))

    for idx, r in enumerate(report.get("additional_reports", []), start=1):
        name = _truncate_title(r.get("name", "Untitled Report"))
        toc_entries.append((f"9.{idx}", name))

    # ---------- Build TOC table ----------
    toc_rows = [
        [Paragraph(num, styles["TOCEntry"]), Paragraph(text, styles["TOCEntry"])]
        for num, text in toc_entries
    ]

    toc_table = Table(toc_rows, colWidths=[25 * mm, None])
    toc_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("WORDWRAP", (0, 0), (-1, -1), True),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    elements.append(toc_table)
    elements.append(PageBreak())


    # ==========================================================
    # PAGINA 3: 1.x
    # ==========================================================
    sec10(elements, styles, report)
    sec11(elements, styles, report)
    sec12(elements, styles, report)
    sec13(elements, styles, report)
    elements.append(PageBreak())

    # ==========================================================
    # PAGINA 4: 2.x + 3.0
    # ==========================================================
    sec20(elements, styles, report)
    sec21(elements, styles, report)
    sec22(elements, styles, report)
    sec23(elements, styles, report)
    sec24(elements, styles, report)
    sec30(elements, styles, report)
    elements.append(PageBreak())

    # ==========================================================
    # PAGINA 5: 4.0 Exec Summary + 5.0 Vulnerability Summary
    # ==========================================================
    sec50(elements, styles, report)
    sec51(elements, styles, report)
    elements.append(PageBreak())

    # ==========================================================
    # PAGINA 6+: 6.0 Technical Findings
    # ==========================================================
    _build_technical_findings(elements, styles, report)
    elements.append(PageBreak())

    # ==========================================================
    # 7.0 Additional Reports
    # ==========================================================
    _build_additional_reports(elements, styles, report)

    # ==========================================================
    # BUILD PDF WITH HEADER/FOOTER/WATERMARK
    # ==========================================================
    def all_pages(canvas, doc):
        _draw_header(canvas, doc, report, accent)
        if watermark_enabled:
            _add_watermark(canvas, "CONFIDENTIAL")
        _draw_footer(canvas, doc)

    doc.build(elements, onFirstPage=all_pages, onLaterPages=all_pages)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf
