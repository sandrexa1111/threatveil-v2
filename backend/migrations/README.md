# Database Migrations

## Phase 1.1 Migration: Company and ScanAI Models

### SQLite Migration

For SQLite, tables are auto-created on startup via SQLAlchemy's `Base.metadata.create_all()`.

### Postgres/Supabase Migration

If using Alembic, create a migration with:

```bash
alembic revision -m "add_company_and_scan_ai_models"
```

Then add this migration content:

```python
"""add_company_and_scan_ai_models

Revision ID: phase1_1_001
Revises: 
Create Date: 2024-01-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'phase1_1_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('primary_domain', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_companies_primary_domain', 'companies', ['primary_domain'], unique=True)
    op.create_index('ix_companies_created_at', 'companies', ['created_at'])
    
    # Add company_id to scans table
    op.add_column('scans', sa.Column('company_id', sa.String(), nullable=True))
    op.create_index('ix_scans_company_id', 'scans', ['company_id'])
    op.create_foreign_key(
        'fk_scans_company_id_companies',
        'scans', 'companies',
        ['company_id'], ['id']
    )
    
    # Create scan_ai table
    op.create_table(
        'scan_ai',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('ai_tools', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_vendors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_keys', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_score', sa.Integer(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scan_ai_scan_id', 'scan_ai', ['scan_id'], unique=True)
    op.create_index('ix_scan_ai_created_at', 'scan_ai', ['created_at'])
    op.create_foreign_key(
        'fk_scan_ai_scan_id_scans',
        'scan_ai', 'scans',
        ['scan_id'], ['id']
    )


def downgrade():
    op.drop_table('scan_ai')
    op.drop_constraint('fk_scans_company_id_companies', 'scans', type_='foreignkey')
    op.drop_index('ix_scans_company_id', 'scans')
    op.drop_column('scans', 'company_id')
    op.drop_table('companies')
```

### Manual SQL (Alternative)

If not using Alembic, run these SQL commands:

**Postgres/Supabase:**

```sql
-- Create companies table
CREATE TABLE companies (
    id VARCHAR PRIMARY KEY,
    name VARCHAR,
    primary_domain VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX ix_companies_primary_domain ON companies(primary_domain);
CREATE INDEX ix_companies_created_at ON companies(created_at);

-- Add company_id to scans
ALTER TABLE scans ADD COLUMN company_id VARCHAR;
CREATE INDEX ix_scans_company_id ON scans(company_id);
ALTER TABLE scans ADD CONSTRAINT fk_scans_company_id_companies 
    FOREIGN KEY (company_id) REFERENCES companies(id);

-- Create scan_ai table
CREATE TABLE scan_ai (
    id VARCHAR PRIMARY KEY,
    scan_id VARCHAR NOT NULL UNIQUE,
    ai_tools JSONB,
    ai_vendors JSONB,
    ai_keys JSONB,
    ai_score INTEGER,
    ai_summary TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_scan_ai_scan_id ON scan_ai(scan_id);
CREATE INDEX ix_scan_ai_created_at ON scan_ai(created_at);
ALTER TABLE scan_ai ADD CONSTRAINT fk_scan_ai_scan_id_scans 
    FOREIGN KEY (scan_id) REFERENCES scans(id);
```

**SQLite:**

SQLite will auto-create tables via SQLAlchemy. No manual migration needed.


