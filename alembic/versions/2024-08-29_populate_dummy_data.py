"""populate dummy data

Revision ID: e0c8e6484eb8
Revises: 8790f1df9407
Create Date: 2024-08-29 11:43:32.328965

"""

import datetime as dt
import random
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e0c8e6484eb8"
down_revision: Union[str, None] = "8790f1df9407"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    for i in range(1_000_000):
        stmt = sa.text(
            "INSERT INTO TODO (title, completed_at) VALUES (:title, :completed_at)"
        )
        completed_at = random.choice([dt.datetime.now(tz=dt.UTC), None])
        bind.execute(stmt, dict(title=f"Todo {i}", completed_at=completed_at))
    bind.commit()


def downgrade() -> None:
    op.execute("TRUNCATE TABLE todo;")
