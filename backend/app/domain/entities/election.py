from dataclasses import dataclass


@dataclass
class ElectionRecord:
    id: int | None = None
    politician_id: int = 0
    constituency_id: int | None = None
    election_year: int = 0
    election_type: str = ""  # General, Bye-election
    party: str = ""
    result: str = ""  # Won, Lost
    votes: int | None = None
    vote_share: float | None = None
    margin: int | None = None
    deposit_lost: bool | None = None
    affidavit_url: str | None = None
    source_id: int | None = None
