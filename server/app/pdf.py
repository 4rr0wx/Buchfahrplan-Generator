from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .models import Route, Timetable, TrackSegment


def _format_time(value: Optional[datetime]) -> str:
    if value is None:
        return "-"
    return value.strftime("%H:%M")


def build_timetable_pdf(timetable: Timetable, route: Route) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    margin = 15 * mm
    content_top = height - 55

    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, height - 35, f"Buchfahrplan: {timetable.title}")
    c.setFont("Helvetica", 10)
    c.drawString(margin, height - 50, f"Zugnummer: {timetable.train_number} – Route: {route.name}")

    station_index = {station.id: station for station in route.stations}

    main_headers = ["Kilometer", "Ort / Abschnitt", "Ank", "Abf", "Vmax (km/h)", "Steigung (‰)", "Bemerkung"]
    main_widths = [70, 150, 55, 55, 90, 90, 160]

    main_rows = []
    for entry in timetable.entries:
        station = station_index.get(entry.station_id)
        kilometer = station.kilometer if station else None
        segment = _segment_for_km(route.segments, kilometer if kilometer is not None else 0.0)
        remark_parts = []
        if entry.track:
            remark_parts.append(f"Gleis {entry.track}")
        if entry.remarks:
            remark_parts.append(entry.remarks)
        elif segment and segment.note:
            remark_parts.append(segment.note)
        main_rows.append(
            [
                f"{kilometer:.1f} km" if kilometer is not None else "-",
                station.name if station else entry.station_name,
                _format_time(entry.arrival),
                _format_time(entry.departure),
                f"{segment.speed_limit}" if segment else "-",
                _format_gradient(segment.gradient if segment else None),
                " – ".join(remark_parts) if remark_parts else "",
            ]
        )

    current_y = _draw_table(c, margin, content_top, main_headers, main_rows, main_widths)

    segment_headers = ["Km von", "Km bis", "Vmax (km/h)", "Steigung (‰)", "Hinweis"]
    segment_widths = [70, 70, 90, 90, 300]

    segment_rows = [
        [
            f"{seg.km_start:.1f}",
            f"{seg.km_end:.1f}",
            str(seg.speed_limit),
            _format_gradient(seg.gradient),
            seg.note or "",
        ]
        for seg in route.segments
    ]

    if current_y - (len(segment_rows) + 2) * 18 < margin:
        c.showPage()
        current_y = height - 40

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, current_y - 20, "Streckenelemente")
    current_y -= 35
    _draw_table(c, margin, current_y, segment_headers, segment_rows, segment_widths)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


def _draw_table(
    c: canvas.Canvas,
    x_start: float,
    y_start: float,
    headers: list[str],
    rows: list[list[str]],
    widths: list[float],
) -> float:
    header_height = 18
    row_height = 18
    current_x = x_start
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.lightgrey)
    for idx, header in enumerate(headers):
        c.rect(current_x, y_start, widths[idx], header_height, fill=True, stroke=False)
        c.setFillColor(colors.black)
        c.rect(current_x, y_start, widths[idx], header_height, fill=False, stroke=True)
        c.drawString(current_x + 3, y_start + 4, header)
        current_x += widths[idx]
        c.setFillColor(colors.lightgrey)

    current_y = y_start - row_height
    c.setFont("Helvetica", 9)
    for row_idx, row in enumerate(rows):
        current_x = x_start
        for idx, value in enumerate(row):
            c.setFillColor(colors.whitesmoke if (row_idx % 2) else colors.white)
            c.rect(current_x, current_y, widths[idx], row_height, fill=True, stroke=False)
            c.setFillColor(colors.black)
            c.rect(current_x, current_y, widths[idx], row_height, fill=False, stroke=True)
            text = str(value)
            c.drawString(current_x + 3, current_y + 4, text[:90])
            current_x += widths[idx]
        current_y -= row_height
    return current_y


def _segment_for_km(segments: list[TrackSegment], kilometer: float) -> Optional[TrackSegment]:
    for segment in segments:
        if segment.km_start <= kilometer < segment.km_end:
            return segment
    return segments[-1] if segments else None


def _format_gradient(value: Optional[int]) -> str:
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return f"{sign}{value}"
