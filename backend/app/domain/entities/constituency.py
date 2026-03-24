from dataclasses import dataclass


@dataclass
class Constituency:
    id: int | None = None
    name: str = ""
    state: str = ""
    chamber: str = ""
    constituency_type: str | None = None  # General, SC, ST
    geo_data: dict | None = None  # GeoJSON for maps
