from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import logging

from app.domain.entities.source import SourceRecord

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    source_name: str
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    errors: list[str] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def success_rate(self) -> float:
        total = self.records_processed
        if total == 0:
            return 0.0
        return (total - self.records_failed) / total * 100


class BaseSourceAdapter(ABC):
    """
    Base class for all data source adapters.
    New data sources are added by implementing this interface (Open/Closed Principle).
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this source (e.g. 'myneta', 'prs_india')."""
        ...

    @abstractmethod
    def fetch(self) -> list[dict]:
        """
        Fetch raw data from the source.
        Returns list of raw records as dicts.
        """
        ...

    @abstractmethod
    def parse(self, raw_records: list[dict]) -> list[dict]:
        """
        Parse and normalize raw records into domain-ready dicts.
        """
        ...

    def create_source_record(self, url: str, content: str, content_type: str = "html") -> SourceRecord:
        return SourceRecord(
            source_name=self.source_name,
            url=url,
            checksum=hashlib.sha256(content.encode()).hexdigest(),
            content_type=content_type,
            fetch_timestamp=datetime.now(timezone.utc),
            parse_status="pending",
        )

    def run(self) -> IngestionResult:
        result = IngestionResult(
            source_name=self.source_name,
            started_at=datetime.now(timezone.utc),
            errors=[],
        )
        try:
            logger.info(f"[{self.source_name}] Starting ingestion")
            raw = self.fetch()
            result.records_processed = len(raw)
            logger.info(f"[{self.source_name}] Fetched {len(raw)} records")

            parsed = self.parse(raw)
            result.records_created = len(parsed)
            logger.info(f"[{self.source_name}] Parsed {len(parsed)} records")
        except Exception as e:
            logger.error(f"[{self.source_name}] Ingestion failed: {e}")
            result.errors.append(str(e))
            result.records_failed = result.records_processed

        result.completed_at = datetime.now(timezone.utc)
        return result
