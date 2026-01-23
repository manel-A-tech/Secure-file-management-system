"""updates

Revision ID: c41bee9b6f62
Revises: c4926ff0b125
Create Date: 2026-01-22 19:42:29.572595

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c41bee9b6f62'
down_revision = 'c4926ff0b125'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('collab_member', schema=None) as batch_op:
        batch_op.add_column(sa.Column('invite_token', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('invite_status', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('invited_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('invited_by', sa.Integer(), nullable=True))

        batch_op.create_unique_constraint(
            'uq_collab_member_invite_token',
            ['invite_token']
        )

        batch_op.create_foreign_key(
            'fk_collab_member_invited_by_account',
            'account',
            ['invited_by'],
            ['id']
        )


def downgrade():
    with op.batch_alter_table('collab_member', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_collab_member_invited_by_account',
            type_='foreignkey'
        )

        batch_op.drop_constraint(
            'uq_collab_member_invite_token',
            type_='unique'
        )

        batch_op.drop_column('invited_by')
        batch_op.drop_column('invited_at')
        batch_op.drop_column('invite_status')
        batch_op.drop_column('invite_token')

