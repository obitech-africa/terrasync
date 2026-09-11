import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PDF_EXPORT_DIR = Path("exports/pdf")
PDF_EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def safe_text(value):
    if value is None:
        return ""
    return str(value)


def resolve_upload_path(file_url: str) -> Path | None:
    if not file_url:
        return None

    clean_url = file_url.lstrip("/")

    if not clean_url.startswith("uploads/"):
        return None

    path = Path(clean_url)

    if path.exists():
        return path

    return None


def build_photo_block(photo: dict, max_width=3.2 * inch, max_height=2.4 * inch):
    elements = []

    caption = photo.get("caption") or photo.get("photo_type") or "Photo"
    file_url = photo.get("file_url")
    image_path = resolve_upload_path(file_url)

    elements.append(
        Paragraph(
            f"<b>{safe_text(photo.get('photo_type'))}</b>",
            ParagraphStyle(
                name="PhotoTitle",
                fontSize=8,
                leading=10,
                alignment=1,
            ),
        )
    )

    if image_path:
        try:
            img = Image(str(image_path))
            img._restrictSize(max_width, max_height)
            elements.append(img)
        except Exception:
            elements.append(Paragraph("Image could not be loaded.", getSampleStyleSheet()["Normal"]))
    else:
        elements.append(Paragraph(f"Image file not found: {safe_text(file_url)}", getSampleStyleSheet()["Normal"]))

    elements.append(
        Paragraph(
            safe_text(caption),
            ParagraphStyle(
                name="PhotoCaption",
                fontSize=7,
                leading=9,
                alignment=1,
            ),
        )
    )

    gps_parts = []
    if photo.get("latitude") is not None:
        gps_parts.append(f"Lat: {photo.get('latitude')}")
    if photo.get("longitude") is not None:
        gps_parts.append(f"Lng: {photo.get('longitude')}")
    if photo.get("captured_at"):
        gps_parts.append(f"Captured: {photo.get('captured_at')}")

    if gps_parts:
        elements.append(
            Paragraph(
                " | ".join(gps_parts),
                ParagraphStyle(
                    name="PhotoMeta",
                    fontSize=6,
                    leading=8,
                    alignment=1,
                    textColor=colors.grey,
                ),
            )
        )

    return elements


def add_header_footer(canvas, doc, report_id: str):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.red)
    canvas.drawString(35, 20, report_id)
    canvas.setFillColor(colors.black)
    canvas.drawRightString(560, 20, f"Page {doc.page}")
    canvas.restoreState()


def generate_report_pdf(report) -> Path:
    answers = json.loads(report.answers)
    defects = json.loads(report.defects) if report.defects else []

    output_path = PDF_EXPORT_DIR / f"{report.report_id}.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="TerraSyncTitle",
        parent=styles["Title"],
        fontSize=16,
        leading=20,
        alignment=1,
        textColor=colors.red,
    )

    section_style = ParagraphStyle(
        name="SectionTitle",
        fontSize=10,
        leading=12,
        alignment=1,
        backColor=colors.lightgrey,
        borderColor=colors.black,
        borderWidth=0.5,
        borderPadding=5,
        spaceBefore=8,
        spaceAfter=6,
    )

    story = []

    story.append(Paragraph("TerraSync Field Maintenance Report", title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>{safe_text(report.template_name)}</b>", styles["Heading3"]))
    story.append(Spacer(1, 10))

    site_table_data = [
        ["Report Number:", safe_text(report.report_id)],
        ["Site ID:", safe_text(report.site_id)],
        ["Work Order ID:", safe_text(report.work_order_id)],
        ["Template:", safe_text(report.template_name)],
        ["Inspector:", safe_text(report.inspector_name)],
        ["Inspector Company:", safe_text(report.inspector_company)],
        ["Inspection Status:", safe_text(report.inspection_status)],
        ["Approval Status:", safe_text(report.approval_status)],
        ["Coordinator:", safe_text(report.coordinator_name)],
        ["Coordinator Comment:", safe_text(report.coordinator_comment)],
        ["Created At:", safe_text(report.created_at)],
        ["Reviewed At:", safe_text(report.reviewed_at)],
    ]

    site_table = Table(site_table_data, colWidths=[2.0 * inch, 4.7 * inch])
    site_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(site_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Findings", section_style))
    story.append(Paragraph(safe_text(report.findings), styles["Normal"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Recommendations", section_style))
    story.append(Paragraph(safe_text(report.recommendations), styles["Normal"]))
    story.append(PageBreak())

    grouped_answers = {}

    for answer in answers:
        section_id = answer.get("section_id", "UNKNOWN")
        grouped_answers.setdefault(section_id, []).append(answer)

    for section_id, section_answers in grouped_answers.items():
        story.append(Paragraph(section_id, section_style))

        table_rows = [["Item", "Value", "Comment"]]

        for answer in section_answers:
            table_rows.append(
                [
                    safe_text(answer.get("label")),
                    safe_text(answer.get("value")),
                    safe_text(answer.get("comment")),
                ]
            )

        section_table = Table(table_rows, colWidths=[2.4 * inch, 1.6 * inch, 2.7 * inch])
        section_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )

        story.append(section_table)
        story.append(Spacer(1, 8))

        photos = []
        for answer in section_answers:
            for photo in answer.get("photos", []):
                photos.append(photo)

        if photos:
            photo_cells = []

            for photo in photos:
                photo_cells.append(build_photo_block(photo))

            rows = []
            for i in range(0, len(photo_cells), 2):
                row = photo_cells[i : i + 2]
                if len(row) == 1:
                    row.append("")
                rows.append(row)

            photo_table = Table(rows, colWidths=[3.25 * inch, 3.25 * inch])
            photo_table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(photo_table)

        story.append(PageBreak())

    if defects:
        story.append(Paragraph("Defects and Corrective Actions", section_style))

        defect_rows = [["Defect", "Severity", "Recommended Action"]]

        for defect in defects:
            defect_rows.append(
                [
                    safe_text(defect.get("defect_title")),
                    safe_text(defect.get("severity")),
                    safe_text(defect.get("recommended_action")),
                ]
            )

        defect_table = Table(defect_rows, colWidths=[2.4 * inch, 1.2 * inch, 3.1 * inch])
        defect_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )

        story.append(defect_table)

    doc.build(
        story,
        onFirstPage=lambda canvas, doc: add_header_footer(canvas, doc, report.report_id),
        onLaterPages=lambda canvas, doc: add_header_footer(canvas, doc, report.report_id),
    )

    return output_path