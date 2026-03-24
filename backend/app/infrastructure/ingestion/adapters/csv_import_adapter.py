import csv
import logging
from pathlib import Path

from app.infrastructure.ingestion.base_adapter import BaseSourceAdapter

logger = logging.getLogger(__name__)


class CsvImportAdapter(BaseSourceAdapter):
    """
    Generic CSV importer for pre-existing datasets.
    Used for: datameet parliament.csv, bkamapantula affidavits, Vonter PRS data, etc.
    Subclass and override `parse` for source-specific normalization.
    """

    def __init__(self, file_path: str, source: str = "csv_import"):
        self._file_path = Path(file_path)
        self._source = source

    @property
    def source_name(self) -> str:
        return self._source

    def fetch(self) -> list[dict]:
        if not self._file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self._file_path}")

        records = []
        with open(self._file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))

        logger.info(f"[{self.source_name}] Read {len(records)} rows from {self._file_path.name}")
        return records

    def parse(self, raw_records: list[dict]) -> list[dict]:
        # Default: pass through. Override in subclasses for normalization.
        return raw_records


class DatameetElectionAdapter(CsvImportAdapter):
    """Parses datameet/india-election-data parliament.csv format."""

    def __init__(self, file_path: str):
        super().__init__(file_path, source="datameet_elections")

    def parse(self, raw_records: list[dict]) -> list[dict]:
        parsed = []
        for row in raw_records:
            try:
                parsed.append({
                    "candidate_name": (row.get("CANDIDATE") or "").strip(),
                    "party": (row.get("PARTY") or "").strip(),
                    "constituency": (row.get("PC_NAME") or row.get("CONSTITUENCY_NAME") or "").strip(),
                    "state": (row.get("STATE") or "").strip(),
                    "year": int(row.get("YEAR") or row.get("year") or 0),
                    "votes": int(row.get("VOTES") or row.get("TOTAL_VALID_VOTES") or 0),
                    "result": "Won" if (row.get("POSITION") or "") == "1" else "Lost",
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"[datameet] Skipping row: {e}")
                continue
        return parsed


class AffidavitCsvAdapter(CsvImportAdapter):
    """Parses bkamapantula/parliamentary-candidates-affidavit-data CSV format."""

    def __init__(self, file_path: str):
        super().__init__(file_path, source="affidavit_csv")

    def parse(self, raw_records: list[dict]) -> list[dict]:
        parsed = []
        for row in raw_records:
            try:
                parsed.append({
                    "candidate_name": (row.get("candidate_name") or row.get("Candidate") or "").strip(),
                    "constituency": (row.get("constituency") or row.get("Constituency") or "").strip(),
                    "state": (row.get("state") or row.get("State") or "").strip(),
                    "party": (row.get("party") or row.get("Party") or "").strip(),
                    "year": int(row.get("year") or row.get("Year") or 0),
                    "criminal_cases": int(row.get("criminal_cases") or row.get("No. of Criminal Cases") or 0),
                    "total_assets": self._parse_float(row.get("total_assets") or row.get("Total Assets")),
                    "total_liabilities": self._parse_float(row.get("liabilities") or row.get("Total Liabilities")),
                    "education": (row.get("education") or row.get("Education") or "").strip(),
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"[affidavit_csv] Skipping row: {e}")
                continue
        return parsed

    @staticmethod
    def _parse_float(value) -> float | None:
        if value is None or value == "" or value == "N/A":
            return None
        try:
            cleaned = str(value).replace(",", "").replace("Rs", "").replace("~", "").strip()
            return float(cleaned)
        except ValueError:
            return None
