from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Politician:
    id: int | None = None
    full_name: str = ""
    name_variants: list[str] = field(default_factory=list)
    photo_url: str | None = None
    gender: str | None = None
    date_of_birth: datetime | None = None
    education: str | None = None
    profession: str | None = None

    # Current office (denormalized for quick access)
    current_party: str | None = None
    current_chamber: str | None = None
    current_constituency: str | None = None
    current_state: str | None = None
    is_active: bool = True

    # Cross-source identifiers
    tcpd_id: str | None = None
    myneta_id: str | None = None
    prs_slug: str | None = None
    opensanctions_id: str | None = None

    last_updated: datetime | None = None
    created_at: datetime | None = None
