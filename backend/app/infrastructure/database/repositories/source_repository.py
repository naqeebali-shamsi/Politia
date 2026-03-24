from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.entities.source import SourceRecord
from app.domain.interfaces.source_repository import SourceRepository as ISourceRepository
from app.infrastructure.database.models.source_model import SourceModel


class SqlSourceRepository(ISourceRepository):
    def __init__(self, db: Session):
        self._db = db

    def _to_entity(self, model: SourceModel) -> SourceRecord:
        return SourceRecord(
            id=model.id, source_name=model.source_name, url=model.url,
            snapshot_url=model.snapshot_url, checksum=model.checksum,
            content_type=model.content_type, fetch_timestamp=model.fetch_timestamp,
            parse_status=model.parse_status, parser_version=model.parser_version,
            error_message=model.error_message, ingestion_batch_id=model.ingestion_batch_id,
        )

    def _to_model(self, entity: SourceRecord) -> SourceModel:
        model = SourceModel(
            source_name=entity.source_name, url=entity.url,
            snapshot_url=entity.snapshot_url, checksum=entity.checksum,
            content_type=entity.content_type, parse_status=entity.parse_status,
            parser_version=entity.parser_version, error_message=entity.error_message,
            ingestion_batch_id=entity.ingestion_batch_id,
        )
        if entity.id:
            model.id = entity.id
        return model

    def get_by_id(self, entity_id: int) -> SourceRecord | None:
        model = self._db.query(SourceModel).filter(SourceModel.id == entity_id).first()
        return self._to_entity(model) if model else None

    def get_all(self, offset: int = 0, limit: int = 20) -> list[SourceRecord]:
        return [self._to_entity(m) for m in self._db.query(SourceModel).offset(offset).limit(limit).all()]

    def create(self, entity: SourceRecord) -> SourceRecord:
        model = self._to_model(entity)
        self._db.add(model)
        self._db.flush()
        return self._to_entity(model)

    def update(self, entity: SourceRecord) -> SourceRecord:
        model = self._db.query(SourceModel).filter(SourceModel.id == entity.id).first()
        if not model:
            raise ValueError(f"SourceRecord {entity.id} not found")
        for f in ["source_name", "url", "snapshot_url", "checksum", "content_type",
                   "parse_status", "parser_version", "error_message", "ingestion_batch_id"]:
            setattr(model, f, getattr(entity, f))
        self._db.flush()
        return self._to_entity(model)

    def delete(self, entity_id: int) -> bool:
        return self._db.query(SourceModel).filter(SourceModel.id == entity_id).delete() > 0

    def count(self) -> int:
        return self._db.query(func.count(SourceModel.id)).scalar()

    def get_by_url(self, url: str) -> SourceRecord | None:
        model = self._db.query(SourceModel).filter(SourceModel.url == url).first()
        return self._to_entity(model) if model else None

    def get_by_checksum(self, checksum: str) -> SourceRecord | None:
        model = self._db.query(SourceModel).filter(SourceModel.checksum == checksum).first()
        return self._to_entity(model) if model else None

    def get_failed(self, limit: int = 100) -> list[SourceRecord]:
        models = (
            self._db.query(SourceModel)
            .filter(SourceModel.parse_status == "failed")
            .limit(limit).all()
        )
        return [self._to_entity(m) for m in models]

    def bulk_create(self, records: list[SourceRecord]) -> list[SourceRecord]:
        models = [self._to_model(r) for r in records]
        self._db.add_all(models)
        self._db.flush()
        return [self._to_entity(m) for m in models]
