"""regions table

Revision ID: 823b55d52941
Revises: a62aff795f5f
Create Date: 2024-04-01 14:56:18.134374

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '823b55d52941'
down_revision = 'a62aff795f5f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('regions',
    sa.Column('region_entry_id', sa.Integer(), nullable=False),
    sa.Column('oopt_id', sa.Integer(), nullable=True),
    sa.Column('region', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['oopt_id'], ['fires.id'], ),
    sa.PrimaryKeyConstraint('region_entry_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('regions')
    # ### end Alembic commands ###