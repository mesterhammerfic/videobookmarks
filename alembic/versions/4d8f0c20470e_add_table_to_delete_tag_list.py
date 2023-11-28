"""add table to delete tag list

Revision ID: 4d8f0c20470e
Revises: e3665b9f68e3
Create Date: 2023-11-28 14:34:44.974848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d8f0c20470e'
down_revision: Union[str, None] = 'e3665b9f68e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
            CREATE TABLE deleted_tag_list (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users ON DELETE CASCADE,
                deleted TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                name TEXT NOT NULL,
                description TEXT,
                old_id INTEGER,
                old_created TIMESTAMP
            );
        """
    )


def downgrade() -> None:
    op.execute(
        """ 
            DROP TABLE deleted_tag_list;
        """
    )

