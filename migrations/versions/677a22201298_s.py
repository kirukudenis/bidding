"""s

Revision ID: 677a22201298
Revises: 59377405fc36
Create Date: 2021-11-19 14:55:43.143250

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '677a22201298'
down_revision = '59377405fc36'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('name', sa.String(length=250), nullable=False))
    op.drop_column('item', 'name_')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('name_', mysql.VARCHAR(length=250), nullable=False))
    op.drop_column('item', 'name')
    # ### end Alembic commands ###
