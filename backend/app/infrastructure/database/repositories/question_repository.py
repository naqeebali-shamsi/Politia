from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.domain.entities.question import QuestionRecord
from app.domain.interfaces.question_repository import QuestionRepository as IQuestionRepository
from app.infrastructure.database.models.question_model import QuestionModel


class SqlQuestionRepository(IQuestionRepository):
    def __init__(self, db: Session):
        self._db = db

    def _to_entity(self, model: QuestionModel) -> QuestionRecord:
        return QuestionRecord(
            id=model.id,
            politician_id=model.politician_id,
            term_number=model.term_number,
            question_date=model.question_date,
            ministry=model.ministry,
            question_type=model.question_type,
            question_title=model.question_title,
            question_text=model.question_text,
            answer_text=model.answer_text,
            source_url=model.source_url,
        )

    def _to_model(self, entity: QuestionRecord) -> QuestionModel:
        model = QuestionModel(
            politician_id=entity.politician_id,
            term_number=entity.term_number,
            question_date=entity.question_date,
            ministry=entity.ministry,
            question_type=entity.question_type,
            question_title=entity.question_title,
            question_text=entity.question_text,
            answer_text=entity.answer_text,
            source_url=entity.source_url,
        )
        if entity.id:
            model.id = entity.id
        return model

    @staticmethod
    def _escape_like(value: str) -> str:
        """Escape SQL LIKE/ILIKE wildcards to prevent pattern injection."""
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def _apply_filters(self, q, politician_id, ministry, term, query):
        if politician_id is not None:
            q = q.filter(QuestionModel.politician_id == politician_id)
        if ministry:
            escaped = self._escape_like(ministry)
            q = q.filter(QuestionModel.ministry.ilike(f"%{escaped}%"))
        if term is not None:
            q = q.filter(QuestionModel.term_number == term)
        if query:
            escaped = self._escape_like(query)
            q = q.filter(QuestionModel.question_title.ilike(f"%{escaped}%"))
        return q

    # --- BaseRepository ---

    def get_by_id(self, entity_id: int) -> QuestionRecord | None:
        model = self._db.query(QuestionModel).filter(QuestionModel.id == entity_id).first()
        return self._to_entity(model) if model else None

    def get_all(self, offset: int = 0, limit: int = 20) -> list[QuestionRecord]:
        return [
            self._to_entity(m)
            for m in self._db.query(QuestionModel).offset(offset).limit(limit).all()
        ]

    def create(self, entity: QuestionRecord) -> QuestionRecord:
        model = self._to_model(entity)
        self._db.add(model)
        self._db.flush()
        return self._to_entity(model)

    def update(self, entity: QuestionRecord) -> QuestionRecord:
        model = self._db.query(QuestionModel).filter(QuestionModel.id == entity.id).first()
        if not model:
            raise ValueError(f"QuestionRecord {entity.id} not found")
        for f in [
            "politician_id", "term_number", "question_date", "ministry",
            "question_type", "question_title", "question_text",
            "answer_text", "source_url",
        ]:
            setattr(model, f, getattr(entity, f))
        self._db.flush()
        return self._to_entity(model)

    def delete(self, entity_id: int) -> bool:
        return self._db.query(QuestionModel).filter(QuestionModel.id == entity_id).delete() > 0

    def count(self) -> int:
        return self._db.query(func.count(QuestionModel.id)).scalar()

    # --- Domain-specific ---

    def search(
        self,
        politician_id: int | None = None,
        ministry: str | None = None,
        term: int | None = None,
        query: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[QuestionRecord]:
        q = self._db.query(QuestionModel)
        q = self._apply_filters(q, politician_id, ministry, term, query)
        q = q.order_by(desc(QuestionModel.question_date), desc(QuestionModel.id))
        return [self._to_entity(m) for m in q.offset(offset).limit(limit).all()]

    def search_count(
        self,
        politician_id: int | None = None,
        ministry: str | None = None,
        term: int | None = None,
        query: str | None = None,
    ) -> int:
        q = self._db.query(func.count(QuestionModel.id))
        q = self._apply_filters(q, politician_id, ministry, term, query)
        return q.scalar()

    def get_stats_by_ministry(self) -> list[dict]:
        rows = (
            self._db.query(QuestionModel.ministry, func.count(QuestionModel.id).label("cnt"))
            .filter(QuestionModel.ministry.isnot(None))
            .group_by(QuestionModel.ministry)
            .order_by(desc("cnt"))
            .all()
        )
        return [{"ministry": r[0], "count": r[1]} for r in rows]

    def get_stats_by_term(self) -> list[dict]:
        rows = (
            self._db.query(QuestionModel.term_number, func.count(QuestionModel.id).label("cnt"))
            .filter(QuestionModel.term_number.isnot(None))
            .group_by(QuestionModel.term_number)
            .order_by(QuestionModel.term_number)
            .all()
        )
        return [{"term_number": r[0], "count": r[1]} for r in rows]

    def get_distinct_ministries(self) -> list[str]:
        rows = (
            self._db.query(QuestionModel.ministry)
            .filter(QuestionModel.ministry.isnot(None))
            .distinct()
            .order_by(QuestionModel.ministry)
            .all()
        )
        return [r[0] for r in rows]

    def bulk_create(self, records: list[QuestionRecord]) -> list[QuestionRecord]:
        models = [self._to_model(r) for r in records]
        self._db.add_all(models)
        self._db.flush()
        return [self._to_entity(m) for m in models]
