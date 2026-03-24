from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.domain.entities.election import ElectionRecord
from app.domain.interfaces.election_repository import ElectionRepository as IElectionRepository
from app.infrastructure.database.models.election_model import ElectionModel


class SqlElectionRepository(IElectionRepository):
    def __init__(self, db: Session):
        self._db = db

    def _to_entity(self, model: ElectionModel) -> ElectionRecord:
        return ElectionRecord(
            id=model.id, politician_id=model.politician_id,
            constituency_id=model.constituency_id, election_year=model.election_year,
            election_type=model.election_type, party=model.party, result=model.result,
            votes=model.votes, vote_share=model.vote_share, margin=model.margin,
            deposit_lost=model.deposit_lost, affidavit_url=model.affidavit_url,
            source_id=model.source_id,
        )

    def _to_model(self, entity: ElectionRecord) -> ElectionModel:
        model = ElectionModel(
            politician_id=entity.politician_id, constituency_id=entity.constituency_id,
            election_year=entity.election_year, election_type=entity.election_type,
            party=entity.party, result=entity.result, votes=entity.votes,
            vote_share=entity.vote_share, margin=entity.margin,
            deposit_lost=entity.deposit_lost, affidavit_url=entity.affidavit_url,
            source_id=entity.source_id,
        )
        if entity.id:
            model.id = entity.id
        return model

    def get_by_id(self, entity_id: int) -> ElectionRecord | None:
        model = self._db.query(ElectionModel).filter(ElectionModel.id == entity_id).first()
        return self._to_entity(model) if model else None

    def get_all(self, offset: int = 0, limit: int = 20) -> list[ElectionRecord]:
        return [self._to_entity(m) for m in self._db.query(ElectionModel).offset(offset).limit(limit).all()]

    def create(self, entity: ElectionRecord) -> ElectionRecord:
        model = self._to_model(entity)
        self._db.add(model)
        self._db.flush()
        return self._to_entity(model)

    def update(self, entity: ElectionRecord) -> ElectionRecord:
        model = self._db.query(ElectionModel).filter(ElectionModel.id == entity.id).first()
        if not model:
            raise ValueError(f"ElectionRecord {entity.id} not found")
        for f in ["constituency_id", "election_year", "election_type", "party", "result",
                   "votes", "vote_share", "margin", "deposit_lost", "affidavit_url", "source_id"]:
            setattr(model, f, getattr(entity, f))
        self._db.flush()
        return self._to_entity(model)

    def delete(self, entity_id: int) -> bool:
        return self._db.query(ElectionModel).filter(ElectionModel.id == entity_id).delete() > 0

    def count(self) -> int:
        return self._db.query(func.count(ElectionModel.id)).scalar()

    def get_by_politician(self, politician_id: int) -> list[ElectionRecord]:
        models = (
            self._db.query(ElectionModel)
            .filter(ElectionModel.politician_id == politician_id)
            .order_by(desc(ElectionModel.election_year))
            .all()
        )
        return [self._to_entity(m) for m in models]

    def get_by_constituency(self, constituency_id: int, year: int | None = None) -> list[ElectionRecord]:
        q = self._db.query(ElectionModel).filter(ElectionModel.constituency_id == constituency_id)
        if year:
            q = q.filter(ElectionModel.election_year == year)
        return [self._to_entity(m) for m in q.order_by(desc(ElectionModel.election_year)).all()]

    def bulk_create(self, records: list[ElectionRecord]) -> list[ElectionRecord]:
        models = [self._to_model(r) for r in records]
        self._db.add_all(models)
        self._db.flush()
        return [self._to_entity(m) for m in models]
