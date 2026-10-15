"""Phase 5 — Tamper-evident hash chain for the agent action ledger.

Adds previous_hash and entry_hash columns to agent_actions so each entry forms a
per-organization SHA-256 hash chain (audit tampering integrity control).

Revision ID: 005_agent_ledger_hash_chain
Revises: 004_phase5_enterprise_schema
Create Date: 2026-10-11 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005_agent_ledger_hash_chain"
down_revision: Union[str, None] = "004_phase5_enterprise_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agent_actions", sa.Column("chain_index", sa.Integer(), nullable=True))
    op.add_column("agent_actions", sa.Column("previous_hash", sa.String(length=64), nullable=True))
    op.add_column("agent_actions", sa.Column("entry_hash", sa.String(length=64), nullable=True))
    op.create_index("ix_agent_actions_entry_hash", "agent_actions", ["entry_hash"])


def downgrade() -> None:
    op.drop_index("ix_agent_actions_entry_hash", table_name="agent_actions")
    op.drop_column("agent_actions", "entry_hash")
    op.drop_column("agent_actions", "previous_hash")
    op.drop_column("agent_actions", "chain_index")
