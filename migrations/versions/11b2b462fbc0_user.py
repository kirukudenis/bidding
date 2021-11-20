"""user

Revision ID: 11b2b462fbc0
Revises: bf319bb4350d
Create Date: 2021-11-19 17:24:33.267870

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11b2b462fbc0'
down_revision = 'bf319bb4350d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('sds', sa.String(length=250), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('item', 'sds')
    # ### end Alembic commands ###