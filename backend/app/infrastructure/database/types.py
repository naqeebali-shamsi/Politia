"""
Dialect-aware column types that work on both PostgreSQL and SQLite.
PostgreSQL gets native ARRAY, JSONB, TSVECTOR.
SQLite falls back to Text/JSON strings.
"""
from sqlalchemy import Text, JSON
from sqlalchemy.types import TypeDecorator
import json


try:
    from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, JSONB as PG_JSONB, TSVECTOR as PG_TSVECTOR
    _HAS_PG = True
except ImportError:
    _HAS_PG = False


class StringArray(TypeDecorator):
    """ARRAY(String) on PostgreSQL, JSON-encoded Text on SQLite."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and _HAS_PG:
            return dialect.type_descriptor(PG_ARRAY(Text))
        return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if dialect.name == "postgresql":
            return value
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if dialect.name == "postgresql":
            return value or []
        if value is None:
            return []
        if isinstance(value, str):
            return json.loads(value)
        return value


class FlexibleJSON(TypeDecorator):
    """JSONB on PostgreSQL, JSON on SQLite."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and _HAS_PG:
            return dialect.type_descriptor(PG_JSONB)
        return dialect.type_descriptor(JSON)


class SearchVector(TypeDecorator):
    """TSVECTOR on PostgreSQL, ignored Text on SQLite."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and _HAS_PG:
            return dialect.type_descriptor(PG_TSVECTOR)
        return dialect.type_descriptor(Text)
