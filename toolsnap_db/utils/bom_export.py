"""BOM export — generates PDF from BOM lines.

Uses reportlab for PDF creation. Produces a clean,
professional parts list grouped by category.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.bom import BomLine


def export_pdf(lines: list[BomLine], output_path: str, title: str = "Bill of Materials") -> str:
    """Generate a BOM PDF at the given path. Returns the path written."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "BomTitle", parent=styles["Title"], fontSize=16, spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "BomSubtitle", parent=styles["Normal"], fontSize=9,
        textColor=colors.gray, spaceAfter=16,
    )
    normal = styles["Normal"]

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    story = []

    # Title block
    story.append(Paragraph(title, title_style))
    now = datetime.now().strftime("%Y-%m-%d  %H:%M")
    story.append(Paragraph(f"Generated: {now}", subtitle_style))

    if not lines:
        story.append(Paragraph("No items.", normal))
        doc.build(story)
        return output_path

    # Table header
    header = ["Qty", "Name", "Category", "Manufacturer", "Catalog #"]
    table_data = [header]

    for ln in lines:
        table_data.append([
            str(ln.quantity),
            ln.name,
            ln.category,
            ln.manufacturer,
            ln.catalog_number,
        ])

    # Summary row
    total_pieces = sum(ln.quantity for ln in lines)
    table_data.append([
        str(total_pieces), f"TOTAL ({len(lines)} line items)", "", "", "",
    ])

    # Column widths: Qty, Name, Category, Manufacturer, Catalog #
    col_widths = [0.5 * inch, 2.5 * inch, 1.3 * inch, 1.5 * inch, 1.2 * inch]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),

        # Data rows
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -2), 8),
        ("TOPPADDING", (0, 1), (-1, -2), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -2), 4),

        # Summary row
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 9),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ecf0f1")),
        ("TOPPADDING", (0, -1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 6),

        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8f9fa")]),

        # Alignment
        ("ALIGN", (0, 0), (0, -1), "CENTER"),  # Qty column centered
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(table)
    doc.build(story)
    return output_path
