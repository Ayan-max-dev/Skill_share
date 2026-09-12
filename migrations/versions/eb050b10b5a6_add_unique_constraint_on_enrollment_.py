"""Add unique constraint on enrollment session and student

Revision ID: eb050b10b5a6
Revises: c5c02eea5d0c
Create Date: 2026-09-11 20:03:50.060019

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb050b10b5a6'
down_revision = 'c5c02eea5d0c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('enrollment', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'unique_session_enrollment', ['session_id', 'student_id']
        )


def downgrade():
    with op.batch_alter_table('enrollment', schema=None) as batch_op:
        batch_op.drop_constraint('unique_session_enrollment', type_='unique')
