from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('companies_new',
        sa.Column('uid', sa.TEXT(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.Column('manager', sa.TEXT(), nullable=True),
        sa.Column('address', sa.TEXT(), nullable=True),
        sa.Column('legal_form', sa.TEXT(), nullable=True),
        sa.Column('status', sa.TEXT(), nullable=True),
        sa.Column('registration_date', sa.TEXT(), nullable=True),
        sa.Column('capital', sa.TEXT(), nullable=True),
        sa.Column('main_activity', sa.TEXT(), nullable=True),
        sa.Column('phone', sa.TEXT(), nullable=True),
        sa.Column('email', sa.TEXT(), nullable=True),
        sa.Column('website', sa.TEXT(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('uid')
    )
    
    op.execute("""
        INSERT INTO companies_new 
        SELECT uid, name, manager, address, legal_form, status, registration_date, 
               capital, main_activity, phone, email, website, created_at, updated_at
        FROM companies
    """)
    
    op.drop_table('companies')
    
    op.rename_table('companies_new', 'companies')


def downgrade() -> None:
    op.create_table('companies_old',
        sa.Column('uid', sa.TEXT(), nullable=False),
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
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('uid')
    )
    
    op.execute("""
        INSERT INTO companies_old 
        SELECT uid, name, 
               COALESCE(manager, 'Unknown') as manager,
               COALESCE(address, 'Unknown') as address,
               legal_form, status, registration_date, 
               capital, main_activity, phone, email, website, created_at, updated_at
        FROM companies
    """)
    
    op.drop_table('companies')
    
    op.rename_table('companies_old', 'companies')
