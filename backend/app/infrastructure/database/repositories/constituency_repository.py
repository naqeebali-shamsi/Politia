from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.domain.entities.constituency import Constituency
from app.domain.interfaces.constituency_repository import ConstituencyRepository as IConstituencyRepository
from app.infrastructure.database.models.constituency_model import ConstituencyModel


class SqlConstituencyRepository(IConstituencyRepository):
    def __init__(self, db: Session):
        self._db = db

    def _to_entity(self, model: ConstituencyModel) -> Constituency:
        return Constituency(
            id=model.id, name=model.name, state=model.state,
            chamber=model.chamber, constituency_type=model.constituency_type,
            geo_data=model.geo_data,
        )

    def _to_model(self, entity: Constituency) -> ConstituencyModel:
        model = ConstituencyModel(
            name=entity.name, state=entity.state, chamber=entity.chamber,
            constituency_type=entity.constituency_type, geo_data=entity.geo_data,
        )
        if entity.id:
            model.id = entity.id
        return model

    def get_by_id(self, entity_id: int) -> Constituency | None:
        model = self._db.query(ConstituencyModel).filter(ConstituencyModel.id == entity_id).first()
        return self._to_entity(model) if model else None

    def get_all(self, offset: int = 0, limit: int = 20) -> list[Constituency]:
        return [self._to_entity(m) for m in self._db.query(ConstituencyModel).offset(offset).limit(limit).all()]

    def create(self, entity: Constituency) -> Constituency:
        model = self._to_model(entity)
        self._db.add(model)
        self._db.flush()
        return self._to_entity(model)

    def update(self, entity: Constituency) -> Constituency:
        model = self._db.query(ConstituencyModel).filter(ConstituencyModel.id == entity.id).first()
        if not model:
            raise ValueError(f"Constituency {entity.id} not found")
        for f in ["name", "state", "chamber", "constituency_type", "geo_data"]:
            setattr(model, f, getattr(entity, f))
        self._db.flush()
        return self._to_entity(model)

    def delete(self, entity_id: int) -> bool:
        return self._db.query(ConstituencyModel).filter(ConstituencyModel.id == entity_id).delete() > 0

    def count(self) -> int:
        return self._db.query(func.count(ConstituencyModel.id)).scalar()

    def search(self, query: str = "", state: str | None = None, chamber: str | None = None,
               offset: int = 0, limit: int = 20) -> list[Constituency]:
        q = self._db.query(ConstituencyModel)
        if query:
            q = q.filter(ConstituencyModel.name.ilike(f"%{query}%"))
        if state:
            q = q.filter(ConstituencyModel.state == state)
        if chamber:
            q = q.filter(ConstituencyModel.chamber == chamber)
        return [self._to_entity(m) for m in q.order_by(ConstituencyModel.name).offset(offset).limit(limit).all()]

    def get_by_name_and_state(self, name: str, state: str) -> Constituency | None:
        model = (
            self._db.query(ConstituencyModel)
            .filter(ConstituencyModel.name == name, ConstituencyModel.state == state)
            .first()
        )
        return self._to_entity(model) if model else None

    def bulk_create(self, entities: list[Constituency]) -> list[Constituency]:
        models = [self._to_model(e) for e in entities]
        self._db.add_all(models)
        self._db.flush()
        return [self._to_entity(m) for m in models]
