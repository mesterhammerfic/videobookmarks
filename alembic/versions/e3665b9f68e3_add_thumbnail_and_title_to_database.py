"""add thumbnail and title to database

Revision ID: e3665b9f68e3
Revises: 83f79d5fe03b
Create Date: 2023-11-09 17:46:12.463195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3665b9f68e3'
down_revision: Union[str, None] = '83f79d5fe03b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
            ALTER TABLE video ADD COLUMN thumbnail TEXT NOT NULL;
            ALTER TABLE video ADD COLUMN title TEXT NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute(
        """
            ALTER TABLE video DROP COLUMN thumbnail;
            ALTER TABLE video DROP COLUMN title;
        """
    )
