from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .models import TimetableEntry, Timetable


def _format_time(value: Optional[datetime]) -> str:
    if value is None:
        return "-"
    return value.strftime("%H:%M")


def build_timetable_pdf(timetable: Timetable) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    margin = 15 * mm
    table_top = height - 50
    col_widths = [80, 60, 60, 40, 120]
    headers = ["Station", "Ankunft", "Abfahrt", "Gleis", "Bemerkungen"]

    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, height - 40, f"Buchfahrplan: {timetable.title}")
    c.setFont("Helvetica", 10)
    c.drawString(margin, height - 55, f"Zugnummer: {timetable.train_number}")

    # Draw headers
    c.setFillColor(colors.lightgrey)
    header_height = 18
    current_x = margin
    for idx, header in enumerate(headers):
        c.rect(current_x, table_top, col_widths[idx], header_height, fill=True, stroke=False)
        c.setFillColor(colors.black)
        c.drawString(current_x + 4, table_top + 4, header)
        current_x += col_widths[idx]
        c.setFillColor(colors.lightgrey)

    row_height = 16
    current_y = table_top - row_height

    for entry in timetable.entries:
        if current_y < margin + 20:
            c.showPage()
            current_y = table_top
        _draw_row(c, margin, current_y, col_widths, row_height, entry)
        current_y -= row_height

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


def _draw_row(
    c: canvas.Canvas,
    x_start: float,
    y: float,
    widths: list[float],
    height: float,
    entry: TimetableEntry,
) -> None:
    columns = [
        entry.station_name,
        _format_time(entry.arrival),
        _format_time(entry.departure),
        entry.track or "-",
        entry.remarks or "",
    ]
    current_x = x_start
    for idx, value in enumerate(columns):
        c.setFillColor(colors.whitesmoke if idx % 2 else colors.white)
        c.rect(current_x, y, widths[idx], height, fill=True, stroke=False)
        c.setFillColor(colors.black)
        c.rect(current_x, y, widths[idx], height, fill=False, stroke=True)
        c.drawString(current_x + 3, y + 4, value)
        current_x += widths[idx]
