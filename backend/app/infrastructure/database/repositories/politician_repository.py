from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.domain.entities.politician import Politician
from app.domain.interfaces.politician_repository import PoliticianRepository as IPoliticianRepository
from app.infrastructure.database.models.politician_model import PoliticianModel


class SqlPoliticianRepository(IPoliticianRepository):
    def __init__(self, db: Session):
        self._db = db

    # -- Mappers --

    def _to_entity(self, model: PoliticianModel) -> Politician:
        return Politician(
            id=model.id,
            full_name=model.full_name,
            name_variants=model.name_variants or [],
            photo_url=model.photo_url,
            gender=model.gender,
            date_of_birth=model.date_of_birth,
            education=model.education,
            profession=model.profession,
            current_party=model.current_party,
            current_chamber=model.current_chamber,
            current_constituency=model.current_constituency,
            current_state=model.current_state,
            is_active=model.is_active,
            tcpd_id=model.tcpd_id,
            myneta_id=model.myneta_id,
            prs_slug=model.prs_slug,
            opensanctions_id=model.opensanctions_id,
            last_updated=model.last_updated,
            created_at=model.created_at,
        )

    def _to_model(self, entity: Politician) -> PoliticianModel:
        model = PoliticianModel(
            full_name=entity.full_name,
            name_variants=entity.name_variants,
            photo_url=entity.photo_url,
            gender=entity.gender,
            date_of_birth=entity.date_of_birth,
            education=entity.education,
            profession=entity.profession,
            current_party=entity.current_party,
            current_chamber=entity.current_chamber,
            current_constituency=entity.current_constituency,
            current_state=entity.current_state,
            is_active=entity.is_active,
            tcpd_id=entity.tcpd_id,
            myneta_id=entity.myneta_id,
            prs_slug=entity.prs_slug,
            opensanctions_id=entity.opensanctions_id,
        )
        if entity.id:
            model.id = entity.id
        return model

    # -- BaseRepository --

    def get_by_id(self, entity_id: int) -> Politician | None:
        model = self._db.query(PoliticianModel).filter(PoliticianModel.id == entity_id).first()
        return self._to_entity(model) if model else None

    def get_all(self, offset: int = 0, limit: int = 20) -> list[Politician]:
        models = self._db.query(PoliticianModel).offset(offset).limit(limit).all()
        return [self._to_entity(m) for m in models]

    def create(self, entity: Politician) -> Politician:
        model = self._to_model(entity)
        self._db.add(model)
        self._db.flush()
        return self._to_entity(model)

    def update(self, entity: Politician) -> Politician:
        model = self._db.query(PoliticianModel).filter(PoliticianModel.id == entity.id).first()
        if not model:
            raise ValueError(f"Politician {entity.id} not found")
        for field in [
            "full_name", "name_variants", "photo_url", "gender", "date_of_birth",
            "education", "profession", "current_party", "current_chamber",
            "current_constituency", "current_state", "is_active",
            "tcpd_id", "myneta_id", "prs_slug", "opensanctions_id",
        ]:
            setattr(model, field, getattr(entity, field))
        self._db.flush()
        return self._to_entity(model)

    def delete(self, entity_id: int) -> bool:
        rows = self._db.query(PoliticianModel).filter(PoliticianModel.id == entity_id).delete()
        return rows > 0

    def count(self) -> int:
        return self._db.query(func.count(PoliticianModel.id)).scalar()

    # -- PoliticianRepository specific --

    def search(
        self,
        query: str = "",
        state: str | None = None,
        party: str | None = None,
        chamber: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Politician]:
        q = self._db.query(PoliticianModel)
        q = self._apply_filters(q, query, state, party, chamber, is_active)
        models = q.order_by(PoliticianModel.full_name).offset(offset).limit(limit).all()
        return [self._to_entity(m) for m in models]

    def search_count(
        self,
        query: str = "",
        state: str | None = None,
        party: str | None = None,
        chamber: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        q = self._db.query(func.count(PoliticianModel.id))
        q = self._apply_filters(q, query, state, party, chamber, is_active)
        return q.scalar()

    def get_by_name(self, name: str) -> list[Politician]:
        escaped = self._escape_like(name)
        models = self._db.query(PoliticianModel).filter(
            PoliticianModel.full_name.ilike(f"%{escaped}%")
        ).all()
        return [self._to_entity(m) for m in models]

    def get_by_constituency(self, constituency_id: int) -> list[Politician]:
        from app.infrastructure.database.models.office_model import OfficeModel
        models = (
            self._db.query(PoliticianModel)
            .join(OfficeModel)
            .filter(OfficeModel.constituency_id == constituency_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def get_by_external_id(self, source: str, external_id: str) -> Politician | None:
        field_map = {
            "tcpd": PoliticianModel.tcpd_id,
            "myneta": PoliticianModel.myneta_id,
            "prs": PoliticianModel.prs_slug,
            "opensanctions": PoliticianModel.opensanctions_id,
        }
        column = field_map.get(source)
        if not column:
            raise ValueError(f"Unknown source: {source}")
        model = self._db.query(PoliticianModel).filter(column == external_id).first()
        return self._to_entity(model) if model else None

    def get_distinct_states(self) -> list[str]:
        rows = (
            self._db.query(PoliticianModel.current_state)
            .filter(PoliticianModel.current_state.isnot(None))
            .distinct()
            .order_by(PoliticianModel.current_state)
            .all()
        )
        return [r[0] for r in rows]

    def get_distinct_parties(self) -> list[str]:
        rows = (
            self._db.query(PoliticianModel.current_party)
            .filter(PoliticianModel.current_party.isnot(None))
            .distinct()
            .order_by(PoliticianModel.current_party)
            .all()
        )
        return [r[0] for r in rows]

    def get_by_ids(self, entity_ids: list[int]) -> dict[int, Politician]:
        if not entity_ids:
            return {}
        models = self._db.query(PoliticianModel).filter(PoliticianModel.id.in_(entity_ids)).all()
        return {m.id: self._to_entity(m) for m in models}

    def bulk_create(self, entities: list[Politician]) -> list[Politician]:
        models = [self._to_model(e) for e in entities]
        self._db.add_all(models)
        self._db.flush()
        return [self._to_entity(m) for m in models]

    # -- Private helpers --

    @staticmethod
    def _escape_like(value: str) -> str:
        """Escape SQL LIKE/ILIKE wildcards to prevent pattern injection."""
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def _apply_filters(self, q, query, state, party, chamber, is_active):
        if query:
            escaped = self._escape_like(query)
            pattern = f"%{escaped}%"
            q = q.filter(
                or_(
                    PoliticianModel.full_name.ilike(pattern),
                    PoliticianModel.current_constituency.ilike(pattern),
                )
            )
        if state:
            q = q.filter(PoliticianModel.current_state == state)
        if party:
            q = q.filter(PoliticianModel.current_party == party)
        if chamber:
            q = q.filter(PoliticianModel.current_chamber == chamber)
        if is_active is not None:
            q = q.filter(PoliticianModel.is_active == is_active)
        return q
