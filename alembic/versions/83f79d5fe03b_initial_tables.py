"""initial tables

Revision ID: 83f79d5fe03b
Revises: 
Create Date: 2023-11-08 15:06:10.266180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83f79d5fe03b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            
            CREATE TABLE tag_list (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users ON DELETE CASCADE,
                created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                name TEXT NOT NULL,
                description TEXT
            );
            
            CREATE TABLE video (
                id SERIAL PRIMARY KEY,
                link TEXT NOT NULL
            );
            
            CREATE TABLE tag (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users ON DELETE CASCADE,
                tag_list_id INTEGER REFERENCES tag_list ON DELETE CASCADE,
                video_id INTEGER REFERENCES video ON DELETE CASCADE,
                tag TEXT NOT NULL,
                youtube_timestamp FLOAT NOT NULL,
                created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """
    )


def downgrade() -> None:
    op.execute(
        """ 
            DROP TABLE tag;
            DROP TABLE video;
            DROP TABLE tag_list;
            DROP TABLE users;
        """
    )
