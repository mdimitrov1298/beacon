from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('activity_logs', 'username')


def downgrade() -> None:
    op.add_column('activity_logs', sa.Column('username', sa.TEXT(), nullable=False, server_default='unknown'))
