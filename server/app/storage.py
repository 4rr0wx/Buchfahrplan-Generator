from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from .models import Route, Station, Timetable, TimetableEntry, generate_base_timetable


class InMemoryStorage:
    def __init__(self) -> None:
        self.routes: Dict[str, Route] = {}
        self.timetables: Dict[str, Timetable] = {}
        self._bootstrap()

    def _bootstrap(self) -> None:
        westbahn = Route(
            id="wb",
            name="Westbahn Wien – Salzburg",
            description="Schnellfahrstrecke von Wien über Linz nach Salzburg",
            country="AT",
            estimated_speed_kmh=160,
            stations=[
                Station(id="wb-1", name="Wien Hbf", kilometer=0.0),
                Station(id="wb-2", name="St. Pölten Hbf", kilometer=59.1),
                Station(id="wb-3", name="Linz Hbf", kilometer=185.6),
                Station(id="wb-4", name="Wels Hbf", kilometer=210.4),
                Station(id="wb-5", name="Salzburg Hbf", kilometer=312.2),
            ],
        )

        s3_route = Route(
            id="s3",
            name="S-Bahn München S3 Holzkirchen – Mammendorf",
            description="S-Bahn Linie durch München",
            country="DE",
            estimated_speed_kmh=80,
            stations=[
                Station(id="s3-1", name="Holzkirchen", kilometer=0.0),
                Station(id="s3-2", name="Deisenhofen", kilometer=14.7),
                Station(id="s3-3", name="München Hbf (tief)", kilometer=34.1),
                Station(id="s3-4", name="Pasing", kilometer=41.4),
                Station(id="s3-5", name="Mammendorf", kilometer=61.7),
            ],
        )

        self.routes[westbahn.id] = westbahn
        self.routes[s3_route.id] = s3_route

        base_tt = generate_base_timetable(westbahn, datetime.fromisoformat("2024-01-01T08:00:00"))
        self.timetables[base_tt.id] = base_tt

    def list_routes(self) -> List[Route]:
        return list(self.routes.values())

    def get_route(self, route_id: str) -> Optional[Route]:
        return self.routes.get(route_id)

    def add_route(self, route: Route) -> Route:
        self.routes[route.id] = route
        return route

    def list_timetables(self) -> List[Timetable]:
        return list(self.timetables.values())

    def get_timetable(self, timetable_id: str) -> Optional[Timetable]:
        return self.timetables.get(timetable_id)

    def add_timetable(self, timetable: Timetable) -> Timetable:
        self.timetables[timetable.id] = timetable
        return timetable

    def update_timetable(self, timetable_id: str, entries: List[TimetableEntry]) -> Optional[Timetable]:
        timetable = self.timetables.get(timetable_id)
        if not timetable:
            return None
        timetable.entries = entries
        return timetable


storage = InMemoryStorage()
