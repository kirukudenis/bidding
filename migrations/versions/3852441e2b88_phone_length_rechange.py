"""phone length rechange

Revision ID: 3852441e2b88
Revises: 13fb71da77a4
Create Date: 2021-11-19 12:23:53.589073

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '3852441e2b88'
down_revision = '13fb71da77a4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('phone', sa.String(length=100), nullable=False))
    op.drop_column('user', 'phone_')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('phone_', mysql.VARCHAR(length=100), nullable=False))
    op.drop_column('user', 'phone')
    # ### end Alembic commands ###
