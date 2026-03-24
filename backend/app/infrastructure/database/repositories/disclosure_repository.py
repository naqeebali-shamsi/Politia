from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.domain.entities.disclosure import DisclosureRecord
from app.domain.interfaces.disclosure_repository import DisclosureRepository as IDisclosureRepository
from app.infrastructure.database.models.disclosure_model import DisclosureModel


class SqlDisclosureRepository(IDisclosureRepository):
    def __init__(self, db: Session):
        self._db = db

    def _to_entity(self, model: DisclosureModel) -> DisclosureRecord:
        return DisclosureRecord(
            id=model.id, politician_id=model.politician_id, election_year=model.election_year,
            total_assets=model.total_assets, movable_assets=model.movable_assets,
            immovable_assets=model.immovable_assets, cash_on_hand=model.cash_on_hand,
            bank_deposits=model.bank_deposits, total_liabilities=model.total_liabilities,
            criminal_cases=model.criminal_cases, serious_criminal_cases=model.serious_criminal_cases,
            criminal_case_details=model.criminal_case_details,
            affidavit_complete=model.affidavit_complete, pan_declared=model.pan_declared,
            source_id=model.source_id,
        )

    def _to_model(self, entity: DisclosureRecord) -> DisclosureModel:
        model = DisclosureModel(
            politician_id=entity.politician_id, election_year=entity.election_year,
            total_assets=entity.total_assets, movable_assets=entity.movable_assets,
            immovable_assets=entity.immovable_assets, cash_on_hand=entity.cash_on_hand,
            bank_deposits=entity.bank_deposits, total_liabilities=entity.total_liabilities,
            criminal_cases=entity.criminal_cases, serious_criminal_cases=entity.serious_criminal_cases,
            criminal_case_details=entity.criminal_case_details,
            affidavit_complete=entity.affidavit_complete, pan_declared=entity.pan_declared,
            source_id=entity.source_id,
        )
        if entity.id:
            model.id = entity.id
        return model

    def get_by_id(self, entity_id: int) -> DisclosureRecord | None:
        model = self._db.query(DisclosureModel).filter(DisclosureModel.id == entity_id).first()
        return self._to_entity(model) if model else None

    def get_all(self, offset: int = 0, limit: int = 20) -> list[DisclosureRecord]:
        return [self._to_entity(m) for m in self._db.query(DisclosureModel).offset(offset).limit(limit).all()]

    def create(self, entity: DisclosureRecord) -> DisclosureRecord:
        model = self._to_model(entity)
        self._db.add(model)
        self._db.flush()
        return self._to_entity(model)

    def update(self, entity: DisclosureRecord) -> DisclosureRecord:
        model = self._db.query(DisclosureModel).filter(DisclosureModel.id == entity.id).first()
        if not model:
            raise ValueError(f"DisclosureRecord {entity.id} not found")
        for f in ["election_year", "total_assets", "movable_assets", "immovable_assets",
                   "cash_on_hand", "bank_deposits", "total_liabilities", "criminal_cases",
                   "serious_criminal_cases", "criminal_case_details", "affidavit_complete",
                   "pan_declared", "source_id"]:
            setattr(model, f, getattr(entity, f))
        self._db.flush()
        return self._to_entity(model)

    def delete(self, entity_id: int) -> bool:
        return self._db.query(DisclosureModel).filter(DisclosureModel.id == entity_id).delete() > 0

    def count(self) -> int:
        return self._db.query(func.count(DisclosureModel.id)).scalar()

    def get_by_politician(self, politician_id: int) -> list[DisclosureRecord]:
        models = (
            self._db.query(DisclosureModel)
            .filter(DisclosureModel.politician_id == politician_id)
            .order_by(desc(DisclosureModel.election_year))
            .all()
        )
        return [self._to_entity(m) for m in models]

    def get_latest_by_politician(self, politician_id: int) -> DisclosureRecord | None:
        model = (
            self._db.query(DisclosureModel)
            .filter(DisclosureModel.politician_id == politician_id)
            .order_by(desc(DisclosureModel.election_year))
            .first()
        )
        return self._to_entity(model) if model else None

    def bulk_create(self, records: list[DisclosureRecord]) -> list[DisclosureRecord]:
        models = [self._to_model(r) for r in records]
        self._db.add_all(models)
        self._db.flush()
        return [self._to_entity(m) for m in models]
