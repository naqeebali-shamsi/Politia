from dataclasses import dataclass
from datetime import datetime


@dataclass
class SourceRecord:
    id: int | None = None
    source_name: str = ""  # e.g. "myneta", "prs_india", "eci", "data_gov_in"
    url: str = ""
    snapshot_url: str | None = None  # R2/S3 path to archived raw artifact
    checksum: str | None = None
    content_type: str | None = None  # html, pdf, csv, json
    fetch_timestamp: datetime | None = None
    parse_status: str = "pending"
    parser_version: str | None = None
    error_message: str | None = None
    ingestion_batch_id: str | None = None
