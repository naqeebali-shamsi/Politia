"""
In-memory fake repository implementations for unit testing.
These implement the same abstract interfaces as the SQL repositories,
allowing services to be tested without any database.
"""
from app.domain.entities.politician import Politician
from app.domain.entities.score import ScoreRecord
from app.domain.entities.activity import ActivityRecord
from app.domain.entities.disclosure import DisclosureRecord
from app.domain.entities.election import ElectionRecord
from app.domain.entities.constituency import Constituency
from app.domain.entities.source import SourceRecord
from app.domain.interfaces.politician_repository import PoliticianRepository
from app.domain.interfaces.score_repository import ScoreRepository
from app.domain.interfaces.activity_repository import ActivityRepository
from app.domain.interfaces.disclosure_repository import DisclosureRepository
from app.domain.interfaces.election_repository import ElectionRepository
from app.domain.interfaces.constituency_repository import ConstituencyRepository
from app.domain.interfaces.source_repository import SourceRepository


class FakePoliticianRepository(PoliticianRepository):
    def __init__(self):
        self._store: dict[int, Politician] = {}
        self._next_id = 1

    def get_by_id(self, entity_id: int) -> Politician | None:
        return self._store.get(entity_id)

    def get_all(self, offset: int = 0, limit: int = 20) -> list[Politician]:
        items = sorted(self._store.values(), key=lambda p: p.id or 0)
        return items[offset:offset + limit]

    def create(self, entity: Politician) -> Politician:
        entity.id = self._next_id
        self._next_id += 1
        self._store[entity.id] = entity
        return entity

    def update(self, entity: Politician) -> Politician:
        if entity.id not in self._store:
            raise ValueError(f"Politician {entity.id} not found")
        self._store[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        return self._store.pop(entity_id, None) is not None

    def count(self) -> int:
        return len(self._store)

    def search(self, query: str = "", state: str | None = None, party: str | None = None,
               chamber: str | None = None, is_active: bool | None = None,
               offset: int = 0, limit: int = 20) -> list[Politician]:
        results = list(self._store.values())
        if query:
            q = query.lower()
            results = [p for p in results if q in (p.full_name or "").lower()
                       or q in (p.current_constituency or "").lower()]
        if state:
            results = [p for p in results if p.current_state == state]
        if party:
            results = [p for p in results if p.current_party == party]
        if chamber:
            results = [p for p in results if p.current_chamber == chamber]
        if is_active is not None:
            results = [p for p in results if p.is_active == is_active]
        return results[offset:offset + limit]

    def search_count(self, query: str = "", state: str | None = None, party: str | None = None,
                     chamber: str | None = None, is_active: bool | None = None) -> int:
        return len(self.search(query, state, party, chamber, is_active, 0, 99999))

    def get_by_name(self, name: str) -> list[Politician]:
        return [p for p in self._store.values() if name.lower() in (p.full_name or "").lower()]

    def get_by_constituency(self, constituency_id: int) -> list[Politician]:
        return []  # Simplified for unit tests

    def get_by_external_id(self, source: str, external_id: str) -> Politician | None:
        field = f"{source}_id" if source != "prs" else "prs_slug"
        for p in self._store.values():
            if getattr(p, field, None) == external_id:
                return p
        return None

    def get_distinct_states(self) -> list[str]:
        return sorted({p.current_state for p in self._store.values() if p.current_state})

    def get_distinct_parties(self) -> list[str]:
        return sorted({p.current_party for p in self._store.values() if p.current_party})

    def get_by_ids(self, entity_ids: list[int]) -> dict[int, Politician]:
        return {pid: p for pid, p in self._store.items() if pid in entity_ids}

    def bulk_create(self, entities: list[Politician]) -> list[Politician]:
        return [self.create(e) for e in entities]


class FakeScoreRepository(ScoreRepository):
    def __init__(self):
        self._store: dict[int, ScoreRecord] = {}
        self._next_id = 1

    def get_by_id(self, entity_id: int) -> ScoreRecord | None:
        return self._store.get(entity_id)

    def get_all(self, offset: int = 0, limit: int = 20) -> list[ScoreRecord]:
        items = [s for s in self._store.values() if s.is_current]
        return items[offset:offset + limit]

    def create(self, entity: ScoreRecord) -> ScoreRecord:
        entity.id = self._next_id
        self._next_id += 1
        self._store[entity.id] = entity
        return entity

    def update(self, entity: ScoreRecord) -> ScoreRecord:
        if entity.id not in self._store:
            raise ValueError(f"ScoreRecord {entity.id} not found")
        self._store[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        return self._store.pop(entity_id, None) is not None

    def count(self) -> int:
        return len([s for s in self._store.values() if s.is_current])

    def get_current_score(self, politician_id: int) -> ScoreRecord | None:
        for s in self._store.values():
            if s.politician_id == politician_id and s.is_current:
                return s
        return None

    def get_score_history(self, politician_id: int) -> list[ScoreRecord]:
        return [s for s in self._store.values() if s.politician_id == politician_id]

    def get_leaderboard(self, chamber: str | None = None, state: str | None = None,
                        party: str | None = None, sort_by: str = "overall_score",
                        offset: int = 0, limit: int = 20) -> list[tuple[int, ScoreRecord]]:
        current = [s for s in self._store.values() if s.is_current]
        current.sort(key=lambda s: getattr(s, sort_by, 0), reverse=True)
        return [(s.politician_id, s) for s in current[offset:offset + limit]]

    def get_scores_for_politicians(self, politician_ids: list[int]) -> dict[int, ScoreRecord]:
        result = {}
        for s in self._store.values():
            if s.politician_id in politician_ids and s.is_current:
                result[s.politician_id] = s
        return result

    def bulk_create(self, records: list[ScoreRecord]) -> list[ScoreRecord]:
        return [self.create(r) for r in records]

    def invalidate_current_scores(self, politician_ids: list[int]) -> int:
        count = 0
        for s in self._store.values():
            if s.politician_id in politician_ids and s.is_current:
                s.is_current = False
                count += 1
        return count


class FakeActivityRepository(ActivityRepository):
    def __init__(self):
        self._store: dict[int, ActivityRecord] = {}
        self._next_id = 1

    def get_by_id(self, entity_id: int) -> ActivityRecord | None:
        return self._store.get(entity_id)

    def get_all(self, offset: int = 0, limit: int = 20) -> list[ActivityRecord]:
        return list(self._store.values())[offset:offset + limit]

    def create(self, entity: ActivityRecord) -> ActivityRecord:
        entity.id = self._next_id
        self._next_id += 1
        self._store[entity.id] = entity
        return entity

    def update(self, entity: ActivityRecord) -> ActivityRecord:
        self._store[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        return self._store.pop(entity_id, None) is not None

    def count(self) -> int:
        return len(self._store)

    def get_by_politician(self, politician_id: int, term_number: int | None = None) -> list[ActivityRecord]:
        results = [a for a in self._store.values() if a.politician_id == politician_id]
        if term_number is not None:
            results = [a for a in results if a.term_number == term_number]
        return results

    def get_chamber_averages(self, term_number: int | None = None) -> dict[str, float]:
        items = list(self._store.values())
        if term_number:
            items = [a for a in items if a.term_number == term_number]
        if not items:
            return {"avg_attendance": 0, "avg_questions": 0, "avg_debates": 0}
        return {
            "avg_attendance": sum(a.attendance_percentage or 0 for a in items) / len(items),
            "avg_questions": sum(a.questions_asked for a in items) / len(items),
            "avg_debates": sum(a.debates_participated for a in items) / len(items),
        }

    def bulk_create(self, records: list[ActivityRecord]) -> list[ActivityRecord]:
        return [self.create(r) for r in records]


class FakeDisclosureRepository(DisclosureRepository):
    def __init__(self):
        self._store: dict[int, DisclosureRecord] = {}
        self._next_id = 1

    def get_by_id(self, entity_id: int) -> DisclosureRecord | None:
        return self._store.get(entity_id)

    def get_all(self, offset: int = 0, limit: int = 20) -> list[DisclosureRecord]:
        return list(self._store.values())[offset:offset + limit]

    def create(self, entity: DisclosureRecord) -> DisclosureRecord:
        entity.id = self._next_id
        self._next_id += 1
        self._store[entity.id] = entity
        return entity

    def update(self, entity: DisclosureRecord) -> DisclosureRecord:
        self._store[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        return self._store.pop(entity_id, None) is not None

    def count(self) -> int:
        return len(self._store)

    def get_by_politician(self, politician_id: int) -> list[DisclosureRecord]:
        results = [d for d in self._store.values() if d.politician_id == politician_id]
        return sorted(results, key=lambda d: d.election_year, reverse=True)

    def get_latest_by_politician(self, politician_id: int) -> DisclosureRecord | None:
        records = self.get_by_politician(politician_id)
        return records[0] if records else None

    def bulk_create(self, records: list[DisclosureRecord]) -> list[DisclosureRecord]:
        return [self.create(r) for r in records]


class FakeElectionRepository(ElectionRepository):
    def __init__(self):
        self._store: dict[int, ElectionRecord] = {}
        self._next_id = 1

    def get_by_id(self, entity_id: int) -> ElectionRecord | None:
        return self._store.get(entity_id)

    def get_all(self, offset: int = 0, limit: int = 20) -> list[ElectionRecord]:
        return list(self._store.values())[offset:offset + limit]

    def create(self, entity: ElectionRecord) -> ElectionRecord:
        entity.id = self._next_id
        self._next_id += 1
        self._store[entity.id] = entity
        return entity

    def update(self, entity: ElectionRecord) -> ElectionRecord:
        self._store[entity.id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        return self._store.pop(entity_id, None) is not None

    def count(self) -> int:
        return len(self._store)

    def get_by_politician(self, politician_id: int) -> list[ElectionRecord]:
        results = [e for e in self._store.values() if e.politician_id == politician_id]
        return sorted(results, key=lambda e: e.election_year, reverse=True)

    def get_by_constituency(self, constituency_id: int, year: int | None = None) -> list[ElectionRecord]:
        results = [e for e in self._store.values() if e.constituency_id == constituency_id]
        if year:
            results = [e for e in results if e.election_year == year]
        return sorted(results, key=lambda e: e.election_year, reverse=True)

    def bulk_create(self, records: list[ElectionRecord]) -> list[ElectionRecord]:
        return [self.create(r) for r in records]
