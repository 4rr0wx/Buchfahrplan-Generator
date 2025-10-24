from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
import itertools


def _generate_id(prefix: str) -> str:
    counter = next(_generate_id._counters.setdefault(prefix, itertools.count(1)))
    return f"{prefix}-{counter}"


_generate_id._counters = {}  # type: ignore[attr-defined]


@dataclass
class Station:
    id: str
    name: str
    kilometer: float
    elevation: Optional[int] = None


@dataclass
class Route:
    id: str
    name: str
    description: str
    country: str
    estimated_speed_kmh: int
    stations: List[Station] = field(default_factory=list)


@dataclass
class TimetableEntry:
    station_id: str
    station_name: str
    arrival: Optional[datetime]
    departure: Optional[datetime]
    track: Optional[str] = None
    remarks: Optional[str] = None


@dataclass
class Timetable:
    id: str
    route_id: str
    train_number: str
    title: str
    entries: List[TimetableEntry] = field(default_factory=list)

    @property
    def route_name(self) -> str:
        return self.title


def generate_base_timetable(route: Route, start_time: datetime, dwell_minutes: int = 2) -> Timetable:
    timetable = Timetable(
        id=_generate_id("tt"),
        route_id=route.id,
        train_number=f"{route.id.upper()}-001",
        title=f"{route.name} – Grundfahrplan",
    )

    current_time = start_time
    previous_km: Optional[float] = None

    for station in route.stations:
        arrival = current_time if previous_km is not None else None
        if previous_km is not None:
            distance_km = max(station.kilometer - previous_km, 0.1)
            travel_minutes = distance_km / route.estimated_speed_kmh * 60
            arrival = current_time + timedelta(minutes=travel_minutes)
            current_time = arrival
        departure = arrival + timedelta(minutes=dwell_minutes) if arrival else start_time
        entry = TimetableEntry(
            station_id=station.id,
            station_name=station.name,
            arrival=arrival,
            departure=departure if station != route.stations[-1] else None,
        )
        timetable.entries.append(entry)
        previous_km = station.kilometer
        if departure:
            current_time = departure

    return timetable


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)
