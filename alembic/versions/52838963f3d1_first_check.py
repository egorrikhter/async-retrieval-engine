"""first_check

Revision ID: 52838963f3d1
Revises:
Create Date: 2026-11-23 11:46:47.037546

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "52838963f3d1"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
