from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Blueprint, Response, jsonify, render_template, request, send_file

from .models import Route, Station, Timetable, TimetableEntry, generate_base_timetable
from .pdf import build_timetable_pdf
from .storage import storage

page_bp = Blueprint("pages", __name__)
api_bp = Blueprint("api", __name__)


@page_bp.route("/")
def index() -> str:
    return render_template("index.html")


@api_bp.get("/routes")
def list_routes() -> Response:
    routes = [_route_to_dict(route) for route in storage.list_routes()]
    return jsonify({"routes": routes})


@api_bp.post("/routes")
def create_route() -> Response:
    payload = request.get_json() or {}
    route = _route_from_payload(payload)
    storage.add_route(route)
    return jsonify(_route_to_dict(route)), 201


@api_bp.post("/timetables")
def create_timetable() -> Response:
    payload = request.get_json() or {}
    route_id = payload.get("route_id")
    start_time = payload.get("start_time")
    dwell = payload.get("dwell_minutes", 2)
    route = storage.get_route(route_id)
    if not route:
        return jsonify({"error": "Route not found"}), 404

    timetable = generate_base_timetable(route, datetime.fromisoformat(start_time), dwell)
    storage.add_timetable(timetable)
    return jsonify(_timetable_to_dict(timetable)), 201


@api_bp.get("/timetables")
def list_timetables() -> Response:
    timetables = [_timetable_to_dict(tt) for tt in storage.list_timetables()]
    return jsonify({"timetables": timetables})


@api_bp.put("/timetables/<timetable_id>")
def update_timetable(timetable_id: str) -> Response:
    payload = request.get_json() or {}
    entries_payload = payload.get("entries", [])
    entries: List[TimetableEntry] = []
    for item in entries_payload:
        entry = TimetableEntry(
            station_id=item["station_id"],
            station_name=item["station_name"],
            arrival=_parse_optional_time(item.get("arrival")),
            departure=_parse_optional_time(item.get("departure")),
            track=item.get("track"),
            remarks=item.get("remarks"),
        )
        entries.append(entry)

    timetable = storage.update_timetable(timetable_id, entries)
    if not timetable:
        return jsonify({"error": "Timetable not found"}), 404
    return jsonify(_timetable_to_dict(timetable))


@api_bp.get("/timetables/<timetable_id>/pdf")
def download_pdf(timetable_id: str) -> Response:
    timetable = storage.get_timetable(timetable_id)
    if not timetable:
        return jsonify({"error": "Timetable not found"}), 404

    pdf_bytes = build_timetable_pdf(timetable)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{timetable_id}.pdf",
    )


def _route_to_dict(route: Route) -> Dict[str, Any]:
    return {
        "id": route.id,
        "name": route.name,
        "description": route.description,
        "country": route.country,
        "estimated_speed_kmh": route.estimated_speed_kmh,
        "stations": [
            {
                "id": station.id,
                "name": station.name,
                "kilometer": station.kilometer,
                "elevation": station.elevation,
            }
            for station in route.stations
        ],
    }


def _route_from_payload(payload: Dict[str, Any]) -> Route:
    stations = [
        Station(
            id=station.get("id", f"st-{idx}"),
            name=station["name"],
            kilometer=station.get("kilometer", 0.0),
            elevation=station.get("elevation"),
        )
        for idx, station in enumerate(payload.get("stations", []), start=1)
    ]
    return Route(
        id=payload.get("id") or payload["name"].lower().replace(" ", "-"),
        name=payload["name"],
        description=payload.get("description", ""),
        country=payload.get("country", "AT"),
        estimated_speed_kmh=int(payload.get("estimated_speed_kmh", 100)),
        stations=stations,
    )


def _timetable_to_dict(timetable: Timetable) -> Dict[str, Any]:
    return {
        "id": timetable.id,
        "route_id": timetable.route_id,
        "train_number": timetable.train_number,
        "title": timetable.title,
        "entries": [
            {
                "station_id": entry.station_id,
                "station_name": entry.station_name,
                "arrival": entry.arrival.isoformat() if entry.arrival else None,
                "departure": entry.departure.isoformat() if entry.departure else None,
                "track": entry.track,
                "remarks": entry.remarks,
            }
            for entry in timetable.entries
        ],
    }


def _parse_optional_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)
