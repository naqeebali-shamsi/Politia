from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.domain.entities.score import ScoreRecord
from app.domain.interfaces.score_repository import ScoreRepository as IScoreRepository
from app.infrastructure.database.models.score_model import ScoreModel
from app.infrastructure.database.models.politician_model import PoliticianModel


class SqlScoreRepository(IScoreRepository):
    def __init__(self, db: Session):
        self._db = db

    def _to_entity(self, model: ScoreModel) -> ScoreRecord:
        return ScoreRecord(
            id=model.id,
            politician_id=model.politician_id,
            overall_score=model.overall_score,
            participation_score=model.participation_score,
            disclosure_score=model.disclosure_score,
            integrity_risk_adjustment=model.integrity_risk_adjustment,
            participation_breakdown=model.participation_breakdown,
            disclosure_breakdown=model.disclosure_breakdown,
            integrity_breakdown=model.integrity_breakdown,
            formula_version=model.formula_version,
            computed_at=model.computed_at,
            is_current=model.is_current,
        )

    def _to_model(self, entity: ScoreRecord) -> ScoreModel:
        model = ScoreModel(
            politician_id=entity.politician_id,
            overall_score=entity.overall_score,
            participation_score=entity.participation_score,
            disclosure_score=entity.disclosure_score,
            integrity_risk_adjustment=entity.integrity_risk_adjustment,
            participation_breakdown=entity.participation_breakdown,
            disclosure_breakdown=entity.disclosure_breakdown,
            integrity_breakdown=entity.integrity_breakdown,
            formula_version=entity.formula_version,
            is_current=entity.is_current,
        )
        if entity.id:
            model.id = entity.id
        return model

    def get_by_id(self, entity_id: int) -> ScoreRecord | None:
        model = self._db.query(ScoreModel).filter(ScoreModel.id == entity_id).first()
        return self._to_entity(model) if model else None

    def get_all(self, offset: int = 0, limit: int = 20) -> list[ScoreRecord]:
        models = (
            self._db.query(ScoreModel)
            .filter(ScoreModel.is_current.is_(True))
            .offset(offset).limit(limit).all()
        )
        return [self._to_entity(m) for m in models]

    def create(self, entity: ScoreRecord) -> ScoreRecord:
        model = self._to_model(entity)
        self._db.add(model)
        self._db.flush()
        return self._to_entity(model)

    def update(self, entity: ScoreRecord) -> ScoreRecord:
        model = self._db.query(ScoreModel).filter(ScoreModel.id == entity.id).first()
        if not model:
            raise ValueError(f"ScoreRecord {entity.id} not found")
        for field in [
            "overall_score", "participation_score", "disclosure_score",
            "integrity_risk_adjustment", "participation_breakdown",
            "disclosure_breakdown", "integrity_breakdown",
            "formula_version", "is_current",
        ]:
            setattr(model, field, getattr(entity, field))
        self._db.flush()
        return self._to_entity(model)

    def delete(self, entity_id: int) -> bool:
        rows = self._db.query(ScoreModel).filter(ScoreModel.id == entity_id).delete()
        return rows > 0

    def count(self) -> int:
        return self._db.query(func.count(ScoreModel.id)).filter(ScoreModel.is_current.is_(True)).scalar()

    def get_current_score(self, politician_id: int) -> ScoreRecord | None:
        model = (
            self._db.query(ScoreModel)
            .filter(ScoreModel.politician_id == politician_id, ScoreModel.is_current.is_(True))
            .first()
        )
        return self._to_entity(model) if model else None

    def get_score_history(self, politician_id: int) -> list[ScoreRecord]:
        models = (
            self._db.query(ScoreModel)
            .filter(ScoreModel.politician_id == politician_id)
            .order_by(desc(ScoreModel.computed_at))
            .all()
        )
        return [self._to_entity(m) for m in models]

    def get_leaderboard(
        self,
        chamber: str | None = None,
        state: str | None = None,
        party: str | None = None,
        sort_by: str = "overall_score",
        offset: int = 0,
        limit: int = 20,
    ) -> list[tuple[int, ScoreRecord]]:
        _allowed_sort_columns = {
            "overall_score", "participation_score", "disclosure_score",
            "integrity_risk_adjustment",
        }
        if sort_by not in _allowed_sort_columns:
            sort_by = "overall_score"
        sort_column = getattr(ScoreModel, sort_by)
        q = (
            self._db.query(ScoreModel)
            .join(PoliticianModel, PoliticianModel.id == ScoreModel.politician_id)
            .filter(ScoreModel.is_current.is_(True))
        )
        if chamber:
            q = q.filter(PoliticianModel.current_chamber == chamber)
        if state:
            q = q.filter(PoliticianModel.current_state == state)
        if party:
            q = q.filter(PoliticianModel.current_party == party)

        models = q.order_by(desc(sort_column)).offset(offset).limit(limit).all()
        return [(m.politician_id, self._to_entity(m)) for m in models]

    def count_leaderboard(
        self,
        chamber: str | None = None,
        state: str | None = None,
        party: str | None = None,
    ) -> int:
        q = (
            self._db.query(func.count(ScoreModel.id))
            .join(PoliticianModel, PoliticianModel.id == ScoreModel.politician_id)
            .filter(ScoreModel.is_current.is_(True))
        )
        if chamber:
            q = q.filter(PoliticianModel.current_chamber == chamber)
        if state:
            q = q.filter(PoliticianModel.current_state == state)
        if party:
            q = q.filter(PoliticianModel.current_party == party)
        return q.scalar()

    def get_scores_for_politicians(self, politician_ids: list[int]) -> dict[int, ScoreRecord]:
        models = (
            self._db.query(ScoreModel)
            .filter(
                ScoreModel.politician_id.in_(politician_ids),
                ScoreModel.is_current.is_(True),
            )
            .all()
        )
        return {m.politician_id: self._to_entity(m) for m in models}

    def bulk_create(self, records: list[ScoreRecord]) -> list[ScoreRecord]:
        models = [self._to_model(r) for r in records]
        self._db.add_all(models)
        self._db.flush()
        return [self._to_entity(m) for m in models]

    def invalidate_current_scores(self, politician_ids: list[int]) -> int:
        rows = (
            self._db.query(ScoreModel)
            .filter(
                ScoreModel.politician_id.in_(politician_ids),
                ScoreModel.is_current.is_(True),
            )
            .update({"is_current": False}, synchronize_session="fetch")
        )
        return rows
