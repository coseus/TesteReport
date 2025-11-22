# report/sections/section_5_0_executive_summary.py
from reportlab.platypus import Paragraph, Spacer, Preformatted
from util.helpers import format_multiline, preformat
from reportlab.lib.units import mm

def build_section(elements, styles, report):
    elements.append(Paragraph("3.0 Executive Summary", styles["HeadingModern"]))

    text = report.get("executive_summary", "")

    # EXACT formatting preserved
    elements.append(Preformatted(preformat(text), styles["PreText"]))
    elements.append(Spacer(1, 14))
