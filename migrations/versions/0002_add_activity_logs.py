from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.TEXT(), nullable=False),
        sa.Column('action', sa.TEXT(), nullable=False),
        sa.Column('details', sa.TEXT(), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_activity_log_user_timestamp', 'activity_logs', ['user_id', 'timestamp'])
    op.create_index('idx_activity_log_action', 'activity_logs', ['action'])


def downgrade() -> None:
    op.drop_index('idx_activity_log_action', 'activity_logs')
    op.drop_index('idx_activity_log_user_timestamp', 'activity_logs')
    op.drop_table('activity_logs')
