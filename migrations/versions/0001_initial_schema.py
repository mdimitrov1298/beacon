from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('companies',
        sa.Column('uid', sa.TEXT(), nullable=True),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.Column('manager', sa.TEXT(), nullable=False),
        sa.Column('address', sa.TEXT(), nullable=False),
        sa.Column('legal_form', sa.TEXT(), nullable=True),
        sa.Column('status', sa.TEXT(), nullable=True),
        sa.Column('registration_date', sa.TEXT(), nullable=True),
        sa.Column('capital', sa.TEXT(), nullable=True),
        sa.Column('main_activity', sa.TEXT(), nullable=True),
        sa.Column('phone', sa.TEXT(), nullable=True),
        sa.Column('email', sa.TEXT(), nullable=True),
        sa.Column('website', sa.TEXT(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('uid')
    )
    
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=True),
        sa.Column('username', sa.TEXT(), nullable=False),
        sa.Column('api_key', sa.TEXT(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('users')
    op.drop_table('companies')
