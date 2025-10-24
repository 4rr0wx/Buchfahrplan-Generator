from __future__ import annotations

import io
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .models import Route, Station, Timetable, TrackSegment


def build_timetable_pdf(timetable: Timetable, route: Route) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    margin = 15 * mm
    sidebar_width = 60 * mm
    speed_bar_width = 8
    station_label_width = 110
    header_height = 28

    speed_bar_x = margin + sidebar_width + 6
    graph_left = speed_bar_x + speed_bar_width + station_label_width
    graph_right = width - margin
    graph_bottom = margin
    graph_top = height - margin - header_height
    label_right = graph_left - 8

    station_index = {station.id: station for station in route.stations}
    start_time, end_time = _time_bounds(timetable)
    min_km, max_km = _km_bounds(route)

    _draw_header(pdf, margin, height - margin + 6, timetable, route, start_time, end_time)
    _draw_sidebar(
        pdf,
        margin,
        graph_top,
        graph_bottom,
        sidebar_width,
        timetable,
        route,
        start_time,
        end_time,
        min_km,
        max_km,
    )
    _draw_grid(
        pdf,
        graph_left,
        graph_bottom,
        graph_right,
        graph_top,
        start_time,
        end_time,
        route,
        min_km,
        max_km,
        label_right,
    )
    _draw_speed_profile(
        pdf,
        speed_bar_x,
        speed_bar_width,
        graph_bottom,
        graph_top,
        route.segments,
        min_km,
        max_km,
    )
    _draw_run_path(
        pdf,
        graph_left,
        graph_bottom,
        graph_right,
        graph_top,
        timetable,
        station_index,
        start_time,
        end_time,
        min_km,
        max_km,
    )

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read()


def _draw_header(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    timetable: Timetable,
    route: Route,
    start_time: datetime,
    end_time: datetime,
) -> None:
    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(colors.black)
    pdf.drawString(x, y, "EBuLa Fahrplan")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)
    pdf.drawString(x, y - 16, f"Zugnummer: {timetable.train_number}")
    pdf.drawString(x + 220, y - 16, f"Strecke: {route.name}")
    pdf.drawString(x, y - 28, f"Zeitraum: {start_time.strftime('%H:%M')} – {end_time.strftime('%H:%M')} Uhr")


def _draw_sidebar(
    pdf: canvas.Canvas,
    x: float,
    top: float,
    bottom: float,
    width: float,
    timetable: Timetable,
    route: Route,
    start_time: datetime,
    end_time: datetime,
    min_km: float,
    max_km: float,
) -> None:
    pdf.setFillColor(colors.whitesmoke)
    pdf.roundRect(x - 4, bottom - 10, width + 8, (top - bottom) + 20, 10, fill=True, stroke=False)

    cursor_y = top + 10
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.black)
    pdf.drawString(x + 6, cursor_y, timetable.title)

    pdf.setFont("Helvetica", 9)
    cursor_y -= 18
    pdf.drawString(x + 6, cursor_y, f"Route: {route.name}")
    cursor_y -= 12
    pdf.drawString(x + 6, cursor_y, f"Kilometer: {min_km:.1f} – {max_km:.1f}")
    cursor_y -= 12
    pdf.drawString(x + 6, cursor_y, f"Laufzeit: {_duration_text(start_time, end_time)}")

    cursor_y -= 18
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(x + 6, cursor_y, "Streckensegmente")

    cursor_y -= 12
    pdf.setFont("Helvetica", 8)
    for segment in route.segments:
        if cursor_y < bottom + 30:
            break
        pdf.setFillColor(colors.black)
        pdf.drawString(
            x + 6,
            cursor_y,
            f"{segment.km_start:.1f} – {segment.km_end:.1f} km | V{segment.speed_limit}",
        )
        cursor_y -= 10
        gradient_text = _format_gradient(segment.gradient)
        note_text = f"{gradient_text}  {segment.note or ''}".strip()
        if note_text:
            pdf.setFillColor(colors.HexColor("#475569"))
            pdf.drawString(x + 12, cursor_y, note_text)
            cursor_y -= 10
        else:
            cursor_y -= 4

    if route.segments and cursor_y < bottom + 30:
        pdf.setFillColor(colors.HexColor("#475569"))
        pdf.drawString(x + 6, bottom + 14, "… weitere Segmente via API abrufbar")


def _draw_grid(
    pdf: canvas.Canvas,
    left: float,
    bottom: float,
    right: float,
    top: float,
    start_time: datetime,
    end_time: datetime,
    route: Route,
    min_km: float,
    max_km: float,
    label_right: float,
) -> None:
    width = right - left
    height = top - bottom

    pdf.setFillColor(colors.white)
    pdf.rect(left, bottom, width, height, fill=True, stroke=False)
    pdf.setStrokeColor(colors.black)
    pdf.rect(left, bottom, width, height, fill=False, stroke=True)

    total_minutes = max((end_time - start_time).total_seconds() / 60, 1.0)
    minute_step = 5
    total_steps = int(math.ceil(total_minutes / minute_step))

    for idx in range(total_steps + 1):
        minute = idx * minute_step
        ratio = min(minute / total_minutes, 1)
        x = left + ratio * width
        is_major = minute % 15 == 0 or idx == 0 or idx == total_steps
        pdf.setStrokeColor(colors.lightgrey if not is_major else colors.HexColor("#94a3b8"))
        pdf.setLineWidth(0.4 if is_major else 0.2)
        if not is_major:
            pdf.setDash(1, 2)
        else:
            pdf.setDash([])
        pdf.line(x, bottom, x, top)

        if idx == total_steps:
            label_dt = end_time
        else:
            label_dt = start_time + timedelta(minutes=minute)
        pdf.setFont("Helvetica", 7)
        pdf.setFillColor(colors.HexColor("#475569"))
        pdf.drawCentredString(x, top + 10, label_dt.strftime("%H:%M"))
        pdf.drawCentredString(x, bottom - 14, label_dt.strftime("%H:%M"))

    pdf.setDash([])

    for station in route.stations:
        y = _km_to_y(station.kilometer, min_km, max_km, bottom, top)
        pdf.setStrokeColor(colors.HexColor("#d1d5db"))
        pdf.setLineWidth(0.25)
        pdf.setDash(1, 2)
        pdf.line(left, y, right, y)
        pdf.setDash([])

        pdf.setFont("Helvetica-Bold", 8)
        pdf.setFillColor(colors.black)
        pdf.drawRightString(label_right, y + 4, station.name)
        pdf.setFont("Helvetica", 7)
        pdf.setFillColor(colors.HexColor("#475569"))
        pdf.drawRightString(label_right, y - 6, f"{station.kilometer:.1f} km")


def _draw_speed_profile(
    pdf: canvas.Canvas,
    bar_x: float,
    bar_width: float,
    bottom: float,
    top: float,
    segments: Sequence[TrackSegment],
    min_km: float,
    max_km: float,
) -> None:
    if not segments:
        return

    for segment in segments:
        y_start = _km_to_y(segment.km_start, min_km, max_km, bottom, top)
        y_end = _km_to_y(segment.km_end, min_km, max_km, bottom, top)
        y_low = min(y_start, y_end)
        height = max(abs(y_end - y_start), 1.5)
        color = _color_for_speed(segment.speed_limit)

        pdf.setFillColor(color)
        pdf.rect(bar_x, y_low, bar_width, height, fill=True, stroke=False)

        pdf.setFont("Helvetica-Bold", 7)
        pdf.setFillColor(colors.white if segment.speed_limit >= 120 else colors.black)
        pdf.drawCentredString(bar_x + bar_width / 2, y_low + height / 2 + 3, str(segment.speed_limit))
        pdf.setFont("Helvetica", 6)
        pdf.drawCentredString(bar_x + bar_width / 2, y_low + height / 2 - 6, _format_gradient(segment.gradient))

    pdf.setFillColor(colors.black)


def _draw_run_path(
    pdf: canvas.Canvas,
    left: float,
    bottom: float,
    right: float,
    top: float,
    timetable: Timetable,
    station_index: Dict[str, Station],
    start_time: datetime,
    end_time: datetime,
    min_km: float,
    max_km: float,
) -> None:
    points = _collect_run_points(timetable, station_index)
    if not points:
        return

    total_minutes = max((end_time - start_time).total_seconds() / 60, 1.0)
    width = right - left
    height = top - bottom
    km_span = max(max_km - min_km, 0.5)

    path = pdf.beginPath()
    marker_points: List[Tuple[float, float]] = []
    for idx, (time_point, kilometer) in enumerate(points):
        minutes_from_start = (time_point - start_time).total_seconds() / 60
        ratio_time = min(max(minutes_from_start / total_minutes, 0), 1)
        ratio_km = (kilometer - min_km) / km_span
        x = left + ratio_time * width
        y = bottom + ratio_km * height
        marker_points.append((x, y))
        if idx == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)

    pdf.setStrokeColor(colors.HexColor("#38bdf8"))
    pdf.setLineWidth(1.8)
    pdf.setDash([])
    pdf.drawPath(path, stroke=1, fill=0)

    pdf.setFillColor(colors.white)
    for x, y in marker_points:
        pdf.circle(x, y, 2.4, stroke=1, fill=1)
        pdf.setFillColor(colors.HexColor("#1e293b"))
        pdf.circle(x, y, 1.2, stroke=0, fill=1)
        pdf.setFillColor(colors.white)


def _collect_run_points(timetable: Timetable, station_index: Dict[str, Station]) -> List[Tuple[datetime, float]]:
    points: List[Tuple[datetime, float]] = []
    for entry in timetable.entries:
        station = station_index.get(entry.station_id)
        if not station:
            continue
        kilometer = station.kilometer
        if entry.departure:
            points.append((entry.departure, kilometer))
        if entry.arrival:
            points.append((entry.arrival, kilometer))
    points.sort(key=lambda item: item[0])
    return points


def _time_bounds(timetable: Timetable) -> Tuple[datetime, datetime]:
    times: List[datetime] = []
    for entry in timetable.entries:
        if entry.arrival:
            times.append(entry.arrival)
        if entry.departure:
            times.append(entry.departure)
    if not times:
        now = datetime.now()
        return now, now + timedelta(minutes=10)
    start = min(times)
    end = max(times)
    if start == end:
        end = start + timedelta(minutes=10)
    return start, end


def _km_bounds(route: Route) -> Tuple[float, float]:
    kilometers = [station.kilometer for station in route.stations]
    if not kilometers:
        return 0.0, 1.0
    min_km = min(kilometers)
    max_km = max(kilometers)
    if min_km == max_km:
        max_km += 1.0
    return min_km, max_km


def _km_to_y(km: float, min_km: float, max_km: float, bottom: float, top: float) -> float:
    ratio = (km - min_km) / max(max_km - min_km, 0.5)
    return bottom + ratio * (top - bottom)


def _color_for_speed(speed: int):
    if speed >= 230:
        return colors.HexColor("#1d4ed8")
    if speed >= 200:
        return colors.HexColor("#2563eb")
    if speed >= 160:
        return colors.HexColor("#3b82f6")
    if speed >= 120:
        return colors.HexColor("#0ea5e9")
    if speed >= 80:
        return colors.HexColor("#10b981")
    return colors.HexColor("#f97316")


def _format_gradient(value: Optional[int]) -> str:
    if value is None:
        return "0‰"
    return f"{'+' if value > 0 else ''}{value}‰"


def _duration_text(start: datetime, end: datetime) -> str:
    minutes = int((end - start).total_seconds() / 60)
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins} Minuten"
