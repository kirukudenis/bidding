"""image length

Revision ID: a47835281293
Revises: 28591b5d79fc
Create Date: 2021-11-20 05:20:21.613109

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a47835281293'
down_revision = '28591b5d79fc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('image_file', sa.String(length=255), nullable=False))
    op.drop_column('item', 'image_file_')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('image_file_', mysql.VARCHAR(length=255), nullable=False))
    op.drop_column('item', 'image_file')
    # ### end Alembic commands ###
