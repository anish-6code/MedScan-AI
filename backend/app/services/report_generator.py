"""
app/services/report_generator.py

Generates a doctor-facing PDF report for a scan using ReportLab.

Template sections:
  1. Header   — hospital logo + title + generation timestamp
  2. Patient  — name, DOB, assigned doctor
  3. Scan     — scan ID, modality, upload date, status
  4. AI       — confidence score, findings summary, bboxes table
  5. Overlay  — embedded scan+mask overlay image
  6. Notes    — blank doctor's notes / correction section
"""
import io
import os
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Colour palette (clinical dark-blue theme) ──────────────────────────────────
PRIMARY   = colors.HexColor("#0A2540")
ACCENT    = colors.HexColor("#00A8E8")
LIGHT_BG  = colors.HexColor("#F4F7FB")
TEXT      = colors.HexColor("#1A1A2E")
MUTED     = colors.HexColor("#6B7280")

REPORTS_DIR = os.environ.get("REPORTS_DIR", "/api/reports")


# ── Style helpers ──────────────────────────────────────────────────────────────

def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"],
            fontSize=22, textColor=PRIMARY, spaceAfter=4,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"],
            fontSize=11, textColor=ACCENT, spaceAfter=2,
            fontName="Helvetica", alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "section", parent=base["Heading2"],
            fontSize=13, textColor=PRIMARY, spaceBefore=14, spaceAfter=4,
            fontName="Helvetica-Bold", borderPad=2,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontSize=10, textColor=TEXT, leading=16,
            fontName="Helvetica",
        ),
        "muted": ParagraphStyle(
            "muted", parent=base["Normal"],
            fontSize=9, textColor=MUTED, leading=13,
            fontName="Helvetica-Oblique",
        ),
        "finding": ParagraphStyle(
            "finding", parent=base["Normal"],
            fontSize=11, textColor=PRIMARY, leading=16,
            fontName="Helvetica-Bold",
        ),
    }


def _severity_color(confidence: float | None) -> colors.Color:
    if confidence is None:
        return MUTED
    if confidence >= 0.7:
        return colors.HexColor("#DC2626")   # red — high
    if confidence >= 0.4:
        return colors.HexColor("#D97706")   # amber — moderate
    return colors.HexColor("#16A34A")       # green — low


# ── Main builder ───────────────────────────────────────────────────────────────

def generate_report(
    *,
    scan_id: str,
    patient: dict[str, Any],
    scan: dict[str, Any],
    result: dict[str, Any] | None,
    overlay_path: str | None = None,
) -> str:
    """
    Build a PDF report and save it to REPORTS_DIR/{scan_id}.pdf.

    Args:
        scan_id:      UUID string
        patient:      {name, date_of_birth, assigned_doctor}
        scan:         {modality, upload_time, status, original_filename}
        result:       {confidence_score, findings_json} or None
        overlay_path: absolute path to overlay .png (embedded in PDF)

    Returns:
        Absolute path to the saved PDF file.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, f"{scan_id}.pdf")

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
        title=f"MedScan AI Report — {scan_id[:8]}",
        author="MedScan AI Platform",
    )

    S      = _styles()
    story  = []
    W, _H  = A4

    # ── 1. Header ─────────────────────────────────────────────────────────────
    story.append(Paragraph("MedScan AI", S["title"]))
    story.append(Paragraph("AI-Assisted DICOM Analysis Report", S["subtitle"]))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        S["muted"],
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=10))

    # ── 2. Patient Info ───────────────────────────────────────────────────────
    story.append(Paragraph("Patient Information", S["section"]))
    patient_data = [
        ["Full Name",        patient.get("name", "—")],
        ["Date of Birth",    patient.get("date_of_birth", "—")],
        ["Assigned Doctor",  patient.get("assigned_doctor", "—")],
        ["Patient ID",       patient.get("id", "—")],
    ]
    story.append(_info_table(patient_data))
    story.append(Spacer(1, 0.4*cm))

    # ── 3. Scan Metadata ──────────────────────────────────────────────────────
    story.append(Paragraph("Scan Information", S["section"]))
    scan_data = [
        ["Scan ID",          str(scan_id)],
        ["Filename",         scan.get("original_filename", "—")],
        ["Modality",         scan.get("modality", "—")],
        ["Upload Time",      str(scan.get("upload_time", "—"))],
        ["Processing Status", scan.get("status", "—").upper()],
    ]
    story.append(_info_table(scan_data))
    story.append(Spacer(1, 0.4*cm))

    # ── 4. AI Findings ────────────────────────────────────────────────────────
    story.append(Paragraph("AI Analysis Results", S["section"]))

    if result:
        conf          = result.get("confidence_score")
        findings_json = result.get("findings_json") or {}
        conf_color    = _severity_color(conf)
        severity      = (
            "HIGH" if (conf or 0) >= 0.7
            else "MODERATE" if (conf or 0) >= 0.4
            else "LOW"
        )

        story.append(Paragraph(
            f"Overall Confidence Score: "
            f'<font color="#{conf_color.hexval()[2:] if hasattr(conf_color, "hexval") else "000000"}">'
            f"<b>{conf:.1%} ({severity})</b></font>"
            if conf is not None else "Confidence Score: N/A",
            S["finding"],
        ))
        story.append(Spacer(1, 0.2*cm))

        summary = findings_json.get("summary", "No summary available.")
        story.append(Paragraph(summary, S["body"]))
        story.append(Spacer(1, 0.3*cm))

        # BBox table
        bboxes = findings_json.get("bboxes", [])
        if bboxes:
            story.append(Paragraph(f"Detected Regions ({len(bboxes)})", S["section"]))
            bbox_rows = [["#", "X", "Y", "Width", "Height", "Confidence", "Area (px)"]]
            for i, b in enumerate(bboxes[:10], 1):  # cap at 10 rows
                bbox_rows.append([
                    str(i), b["x"], b["y"], b["w"], b["h"],
                    f"{b['confidence']:.1%}", b["area_px"],
                ])
            story.append(_bbox_table(bbox_rows))

    else:
        story.append(Paragraph(
            "AI analysis not yet available. Scan may still be processing.",
            S["muted"],
        ))

    story.append(Spacer(1, 0.5*cm))

    # ── 5. Overlay Image ─────────────────────────────────────────────────────
    if overlay_path and os.path.exists(overlay_path):
        story.append(Paragraph("Scan Overlay (AI Segmentation Mask)", S["section"]))
        story.append(Spacer(1, 0.2*cm))
        max_img_w = W - 4*cm
        img = Image(overlay_path, width=min(max_img_w, 12*cm), height=12*cm,
                    kind="proportional")
        story.append(img)
        story.append(Paragraph(
            "Red overlay indicates detected region(s) of interest.",
            S["muted"],
        ))
    story.append(Spacer(1, 0.6*cm))

    # ── 6. Doctor's Notes ─────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=MUTED, spaceAfter=8))
    story.append(Paragraph("Doctor's Notes & Corrections", S["section"]))
    story.append(Paragraph(
        "Use this section to record any manual corrections or additional clinical observations.",
        S["muted"],
    ))
    # Blank lines for handwriting
    for _ in range(6):
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.HexColor("#D1D5DB"), spaceAfter=2))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return out_path


# ── Table helpers ──────────────────────────────────────────────────────────────

def _info_table(rows: list) -> Table:
    t = Table(rows, colWidths=[4.5*cm, None])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), LIGHT_BG),
        ("TEXTCOLOR",   (0, 0), (0, -1), PRIMARY),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT_BG]),
        ("GRID",        (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
        ("PADDING",     (0, 0), (-1, -1), 6),
    ]))
    return t


def _bbox_table(rows: list) -> Table:
    t = Table(rows, colWidths=[0.6*cm, 1.5*cm, 1.5*cm, 1.7*cm, 1.7*cm, 2.2*cm, 2.2*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("GRID",        (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
        ("PADDING",     (0, 0), (-1, -1), 5),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
    ]))
    return t


# ── Page footer ───────────────────────────────────────────────────────────────

def _page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        2*cm, 1.2*cm,
        "MedScan AI Platform — Confidential Medical Document — For Authorised Use Only"
    )
    canvas.drawRightString(
        A4[0] - 2*cm, 1.2*cm,
        f"Page {doc.page}"
    )
    canvas.restoreState()
