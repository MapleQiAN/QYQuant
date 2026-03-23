"""marketplace search zhparser

Revision ID: c3d9e1f7a2b4
Revises: b7e4c2a1d9f0
Create Date: 2026-03-19 20:40:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c3d9e1f7a2b4"
down_revision = "b7e4c2a1d9f0"
branch_labels = None
depends_on = None


def upgrade():
    # Note: zhparser extension is not available in standard PostgreSQL images
    # Using default 'english' configuration for full-text search
    # For Chinese search, consider using a custom PostgreSQL image with zhparser

    op.add_column("strategies", sa.Column("title_tsv", postgresql.TSVECTOR(), nullable=True))
    op.add_column("strategies", sa.Column("description_tsv", postgresql.TSVECTOR(), nullable=True))

    op.execute(
        """
        UPDATE strategies
        SET title_tsv = to_tsvector('english', COALESCE(title, '')),
            description_tsv = to_tsvector('english', COALESCE(description, ''))
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION strategies_tsv_trigger() RETURNS trigger AS $func$
        BEGIN
            NEW.title_tsv := to_tsvector('english', COALESCE(NEW.title, ''));
            NEW.description_tsv := to_tsvector('english', COALESCE(NEW.description, ''));
            RETURN NEW;
        END
        $func$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER strategies_tsv_update
        BEFORE INSERT OR UPDATE OF title, description ON strategies
        FOR EACH ROW EXECUTE FUNCTION strategies_tsv_trigger()
        """
    )

    op.create_index("ix_strategies_title_tsv", "strategies", ["title_tsv"], unique=False, postgresql_using="gin")
    op.create_index(
        "ix_strategies_description_tsv",
        "strategies",
        ["description_tsv"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade():
    op.drop_index("ix_strategies_description_tsv", table_name="strategies")
    op.drop_index("ix_strategies_title_tsv", table_name="strategies")
    op.execute("DROP TRIGGER IF EXISTS strategies_tsv_update ON strategies")
    op.execute("DROP FUNCTION IF EXISTS strategies_tsv_trigger()")
    op.drop_column("strategies", "description_tsv")
    op.drop_column("strategies", "title_tsv")
    op.execute("DROP TEXT SEARCH CONFIGURATION IF EXISTS chinese CASCADE")
