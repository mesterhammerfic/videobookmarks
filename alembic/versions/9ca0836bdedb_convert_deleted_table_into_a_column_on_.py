"""convert deleted table into a column on tag_list table

Revision ID: 9ca0836bdedb
Revises: 4d8f0c20470e
Create Date: 2023-12-20 15:20:20.060203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ca0836bdedb'
down_revision: Union[str, None] = '4d8f0c20470e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
            ALTER TABLE tag_list 
            ADD deleted boolean DEFAULT false NOT NULL;
            
            INSERT INTO tag_list (id, name, description, user_id, created, deleted)
            SELECT old_id, name, description, user_id, old_created, true
            FROM deleted_tag_list;
            
            DROP TABLE deleted_tag_list;
        """
    )


def downgrade() -> None:
    """
    This downgrade DOES NOT transfer the deleted tables from the tag_list
    table as you would expect. Instead it just removes the deleted column
    and creates the old deleted tag_list table.
    """
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
            ALTER TABLE tag_list 
            DROP COLUMN deleted;
        """
    )
