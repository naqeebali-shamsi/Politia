from dataclasses import dataclass


@dataclass
class DisclosureRecord:
    id: int | None = None
    politician_id: int = 0
    election_year: int = 0

    # Assets breakdown (all in INR)
    total_assets: float | None = None
    movable_assets: float | None = None
    immovable_assets: float | None = None
    cash_on_hand: float | None = None
    bank_deposits: float | None = None

    # Liabilities
    total_liabilities: float | None = None

    # Criminal disclosures
    criminal_cases: int = 0
    serious_criminal_cases: int = 0
    criminal_case_details: str | None = None  # JSON string for structured IPC sections

    # Completeness
    affidavit_complete: bool = False
    pan_declared: bool = False

    source_id: int | None = None
