"""Initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-27 00:00:00.000000

Reflects the actual ORM models in app/infrastructure/database/models/.
Generated manually to replace the stale auto-generated migration that
referenced wrong column names (party/state/current_office) from an
earlier prototype.  That orphan alembic/ directory has been deleted.
alembic.ini already points script_location at migrations/ (this directory).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'source_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_name', sa.String(length=100), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('snapshot_url', sa.String(length=1000), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('content_type', sa.String(length=20), nullable=True),
        sa.Column('fetch_timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('parse_status', sa.String(length=20), nullable=False),
        sa.Column('parser_version', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('ingestion_batch_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_source_records_checksum'), 'source_records', ['checksum'])
    op.create_index(op.f('ix_source_records_ingestion_batch_id'), 'source_records', ['ingestion_batch_id'])
    op.create_index(op.f('ix_source_records_parse_status'), 'source_records', ['parse_status'])
    op.create_index(op.f('ix_source_records_source_name'), 'source_records', ['source_name'])
    op.create_index('ix_source_name_status', 'source_records', ['source_name', 'parse_status'])

    op.create_table(
        'constituencies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('chamber', sa.String(length=50), nullable=False),
        sa.Column('constituency_type', sa.String(length=20), nullable=True),
        sa.Column('geo_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_constituencies_chamber'), 'constituencies', ['chamber'])
    op.create_index(op.f('ix_constituencies_name'), 'constituencies', ['name'])
    op.create_index(op.f('ix_constituencies_state'), 'constituencies', ['state'])
    op.create_index('ix_constituency_name_state_chamber', 'constituencies', ['name', 'state', 'chamber'], unique=True)

    # name_variants: ARRAY(Text) on PG, JSON-encoded Text on SQLite (StringArray)
    # search_vector: TSVECTOR on PG, Text on SQLite (SearchVector)
    op.create_table(
        'politicians',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('name_variants', sa.Text(), nullable=True),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('date_of_birth', sa.DateTime(), nullable=True),
        sa.Column('education', sa.String(length=255), nullable=True),
        sa.Column('profession', sa.String(length=255), nullable=True),
        sa.Column('current_party', sa.String(length=255), nullable=True),
        sa.Column('current_chamber', sa.String(length=50), nullable=True),
        sa.Column('current_constituency', sa.String(length=255), nullable=True),
        sa.Column('current_state', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('tcpd_id', sa.String(length=100), nullable=True),
        sa.Column('myneta_id', sa.String(length=100), nullable=True),
        sa.Column('prs_slug', sa.String(length=255), nullable=True),
        sa.Column('opensanctions_id', sa.String(length=100), nullable=True),
        sa.Column('search_vector', sa.Text(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.UniqueConstraint('tcpd_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_politicians_current_chamber'), 'politicians', ['current_chamber'])
    op.create_index(op.f('ix_politicians_current_party'), 'politicians', ['current_party'])
    op.create_index(op.f('ix_politicians_current_state'), 'politicians', ['current_state'])
    op.create_index(op.f('ix_politicians_full_name'), 'politicians', ['full_name'])
    op.create_index(op.f('ix_politicians_is_active'), 'politicians', ['is_active'])
    op.create_index(op.f('ix_politicians_myneta_id'), 'politicians', ['myneta_id'])
    op.create_index(op.f('ix_politicians_opensanctions_id'), 'politicians', ['opensanctions_id'])
    op.create_index(op.f('ix_politicians_prs_slug'), 'politicians', ['prs_slug'])
    op.create_index(op.f('ix_politicians_tcpd_id'), 'politicians', ['tcpd_id'])
    op.create_index('ix_politicians_state_party', 'politicians', ['current_state', 'current_party'])
    op.create_index('ix_politicians_chamber_active', 'politicians', ['current_chamber', 'is_active'])

    op.create_table(
        'offices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('politician_id', sa.Integer(), nullable=False),
        sa.Column('constituency_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=50), nullable=False),
        sa.Column('chamber', sa.String(length=50), nullable=False),
        sa.Column('party', sa.String(length=255), nullable=False),
        sa.Column('term_number', sa.Integer(), nullable=True),
        sa.Column('term_start', sa.DateTime(), nullable=True),
        sa.Column('term_end', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['constituency_id'], ['constituencies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['politician_id'], ['politicians.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_offices_is_active'), 'offices', ['is_active'])
    op.create_index(op.f('ix_offices_politician_id'), 'offices', ['politician_id'])
    op.create_index('ix_office_politician_active', 'offices', ['politician_id', 'is_active'])

    op.create_table(
        'election_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('politician_id', sa.Integer(), nullable=False),
        sa.Column('constituency_id', sa.Integer(), nullable=True),
        sa.Column('election_year', sa.Integer(), nullable=False),
        sa.Column('election_type', sa.String(length=50), nullable=True),
        sa.Column('party', sa.String(length=255), nullable=False),
        sa.Column('result', sa.String(length=20), nullable=False),
        sa.Column('votes', sa.Integer(), nullable=True),
        sa.Column('vote_share', sa.Float(), nullable=True),
        sa.Column('margin', sa.Integer(), nullable=True),
        sa.Column('deposit_lost', sa.Boolean(), nullable=True),
        sa.Column('affidavit_url', sa.String(length=500), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['constituency_id'], ['constituencies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['politician_id'], ['politicians.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['source_records.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_election_records_constituency_id'), 'election_records', ['constituency_id'])
    op.create_index(op.f('ix_election_records_election_year'), 'election_records', ['election_year'])
    op.create_index(op.f('ix_election_records_politician_id'), 'election_records', ['politician_id'])
    op.create_index('ix_election_politician_year', 'election_records', ['politician_id', 'election_year'])
    op.create_index('ix_election_constituency_year', 'election_records', ['constituency_id', 'election_year'])

    # committee_names: ARRAY(Text) on PG, JSON-encoded Text on SQLite (StringArray)
    op.create_table(
        'activity_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('politician_id', sa.Integer(), nullable=False),
        sa.Column('term_number', sa.Integer(), nullable=True),
        sa.Column('session_name', sa.String(length=255), nullable=True),
        sa.Column('attendance_percentage', sa.Float(), nullable=True),
        sa.Column('questions_asked', sa.Integer(), nullable=True),
        sa.Column('debates_participated', sa.Integer(), nullable=True),
        sa.Column('private_bills_introduced', sa.Integer(), nullable=True),
        sa.Column('committee_memberships', sa.Integer(), nullable=True),
        sa.Column('committee_names', sa.Text(), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['politician_id'], ['politicians.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['source_records.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_activity_records_politician_id'), 'activity_records', ['politician_id'])
    op.create_index(op.f('ix_activity_records_term_number'), 'activity_records', ['term_number'])
    op.create_index('ix_activity_politician_term', 'activity_records', ['politician_id', 'term_number'])

    op.create_table(
        'disclosure_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('politician_id', sa.Integer(), nullable=False),
        sa.Column('election_year', sa.Integer(), nullable=False),
        sa.Column('total_assets', sa.Float(), nullable=True),
        sa.Column('movable_assets', sa.Float(), nullable=True),
        sa.Column('immovable_assets', sa.Float(), nullable=True),
        sa.Column('cash_on_hand', sa.Float(), nullable=True),
        sa.Column('bank_deposits', sa.Float(), nullable=True),
        sa.Column('total_liabilities', sa.Float(), nullable=True),
        sa.Column('criminal_cases', sa.Integer(), nullable=True),
        sa.Column('serious_criminal_cases', sa.Integer(), nullable=True),
        sa.Column('criminal_case_details', sa.Text(), nullable=True),
        sa.Column('affidavit_complete', sa.Boolean(), nullable=True),
        sa.Column('pan_declared', sa.Boolean(), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['politician_id'], ['politicians.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['source_records.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_disclosure_records_politician_id'), 'disclosure_records', ['politician_id'])
    op.create_index('ix_disclosure_politician_year', 'disclosure_records', ['politician_id', 'election_year'])

    # breakdown cols: JSONB on PostgreSQL, JSON on SQLite (FlexibleJSON)
    op.create_table(
        'score_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('politician_id', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('participation_score', sa.Float(), nullable=False),
        sa.Column('disclosure_score', sa.Float(), nullable=False),
        sa.Column('integrity_risk_adjustment', sa.Float(), nullable=False),
        sa.Column('participation_breakdown', sa.JSON(), nullable=True),
        sa.Column('disclosure_breakdown', sa.JSON(), nullable=True),
        sa.Column('integrity_breakdown', sa.JSON(), nullable=True),
        sa.Column('formula_version', sa.String(length=20), nullable=False),
        sa.Column('computed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['politician_id'], ['politicians.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_score_records_formula_version'), 'score_records', ['formula_version'])
    op.create_index(op.f('ix_score_records_is_current'), 'score_records', ['is_current'])
    op.create_index(op.f('ix_score_records_politician_id'), 'score_records', ['politician_id'])
    op.create_index('ix_score_politician_current', 'score_records', ['politician_id', 'is_current'])
    op.create_index('ix_score_leaderboard', 'score_records', ['is_current', 'overall_score'])

    op.create_table(
        'question_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('politician_id', sa.Integer(), nullable=False),
        sa.Column('term_number', sa.Integer(), nullable=True),
        sa.Column('question_date', sa.Date(), nullable=True),
        sa.Column('ministry', sa.String(length=255), nullable=True),
        sa.Column('question_type', sa.String(length=50), nullable=True),
        sa.Column('question_title', sa.Text(), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=True),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['politician_id'], ['politicians.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_question_records_ministry'), 'question_records', ['ministry'])
    op.create_index(op.f('ix_question_records_politician_id'), 'question_records', ['politician_id'])
    op.create_index(op.f('ix_question_records_term_number'), 'question_records', ['term_number'])
    op.create_index('ix_question_politician_term', 'question_records', ['politician_id', 'term_number'])
    op.create_index('ix_question_date', 'question_records', ['question_date'])
    op.create_index('ix_question_ministry_type', 'question_records', ['ministry', 'question_type'])


def downgrade() -> None:
    op.drop_table('question_records')
    op.drop_table('score_records')
    op.drop_table('disclosure_records')
    op.drop_table('activity_records')
    op.drop_table('election_records')
    op.drop_table('offices')
    op.drop_table('politicians')
    op.drop_table('constituencies')
    op.drop_table('source_records')
