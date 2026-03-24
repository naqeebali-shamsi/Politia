from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.entities.activity import ActivityRecord
from app.domain.interfaces.activity_repository import ActivityRepository as IActivityRepository
from app.infrastructure.database.models.activity_model import ActivityModel


class SqlActivityRepository(IActivityRepository):
    def __init__(self, db: Session):
        self._db = db

    def _to_entity(self, model: ActivityModel) -> ActivityRecord:
        return ActivityRecord(
            id=model.id,
            politician_id=model.politician_id,
            term_number=model.term_number,
            session_name=model.session_name,
            attendance_percentage=model.attendance_percentage,
            questions_asked=model.questions_asked,
            debates_participated=model.debates_participated,
            private_bills_introduced=model.private_bills_introduced,
            committee_memberships=model.committee_memberships,
            committee_names=model.committee_names,
            source_id=model.source_id,
        )

    def _to_model(self, entity: ActivityRecord) -> ActivityModel:
        model = ActivityModel(
            politician_id=entity.politician_id,
            term_number=entity.term_number,
            session_name=entity.session_name,
            attendance_percentage=entity.attendance_percentage,
            questions_asked=entity.questions_asked,
            debates_participated=entity.debates_participated,
            private_bills_introduced=entity.private_bills_introduced,
            committee_memberships=entity.committee_memberships,
            committee_names=entity.committee_names,
            source_id=entity.source_id,
        )
        if entity.id:
            model.id = entity.id
        return model

    def get_by_id(self, entity_id: int) -> ActivityRecord | None:
        model = self._db.query(ActivityModel).filter(ActivityModel.id == entity_id).first()
        return self._to_entity(model) if model else None

    def get_all(self, offset: int = 0, limit: int = 20) -> list[ActivityRecord]:
        return [self._to_entity(m) for m in self._db.query(ActivityModel).offset(offset).limit(limit).all()]

    def create(self, entity: ActivityRecord) -> ActivityRecord:
        model = self._to_model(entity)
        self._db.add(model)
        self._db.flush()
        return self._to_entity(model)

    def update(self, entity: ActivityRecord) -> ActivityRecord:
        model = self._db.query(ActivityModel).filter(ActivityModel.id == entity.id).first()
        if not model:
            raise ValueError(f"ActivityRecord {entity.id} not found")
        for f in ["term_number", "session_name", "attendance_percentage", "questions_asked",
                   "debates_participated", "private_bills_introduced", "committee_memberships",
                   "committee_names", "source_id"]:
            setattr(model, f, getattr(entity, f))
        self._db.flush()
        return self._to_entity(model)

    def delete(self, entity_id: int) -> bool:
        return self._db.query(ActivityModel).filter(ActivityModel.id == entity_id).delete() > 0

    def count(self) -> int:
        return self._db.query(func.count(ActivityModel.id)).scalar()

    def get_by_politician(self, politician_id: int, term_number: int | None = None) -> list[ActivityRecord]:
        q = self._db.query(ActivityModel).filter(ActivityModel.politician_id == politician_id)
        if term_number:
            q = q.filter(ActivityModel.term_number == term_number)
        return [self._to_entity(m) for m in q.all()]

    def get_chamber_averages(self, term_number: int | None = None) -> dict[str, float]:
        q = self._db.query(
            func.avg(ActivityModel.attendance_percentage),
            func.avg(ActivityModel.questions_asked),
            func.avg(ActivityModel.debates_participated),
        )
        if term_number:
            q = q.filter(ActivityModel.term_number == term_number)
        row = q.first()
        return {
            "avg_attendance": float(row[0] or 0),
            "avg_questions": float(row[1] or 0),
            "avg_debates": float(row[2] or 0),
        }

    def bulk_create(self, records: list[ActivityRecord]) -> list[ActivityRecord]:
        models = [self._to_model(r) for r in records]
        self._db.add_all(models)
        self._db.flush()
        return [self._to_entity(m) for m in models]
