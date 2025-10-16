"""Add gas and wind measurements

Revision ID: 0002_add_gas_wind
Revises: 0001_init
Create Date: 2025-10-15 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_add_gas_wind'
down_revision = '0001_init'
branch_labels = None
depends_on = None


def upgrade():
    """Add new columns for gas and wind measurements."""
    # Add NO2 column
    op.add_column('measurements', 
        sa.Column('no2', sa.Float(), nullable=True, 
                  comment='Nitrogen Dioxide (NO2) from n0310Um1')
    )
    
    # Add CO2 column
    op.add_column('measurements', 
        sa.Column('co2', sa.Float(), nullable=True,
                  comment='Carbon Dioxide (CO2) from n0310Um2')
    )
    
    # Add wind speed column
    op.add_column('measurements', 
        sa.Column('vel_viento', sa.Float(), nullable=True,
                  comment='Wind speed from vel')
    )
    
    # Add wind direction column
    op.add_column('measurements', 
        sa.Column('dir_viento', sa.Float(), nullable=True,
                  comment='Wind direction in degrees from dir')
    )


def downgrade():
    """Remove gas and wind measurement columns."""
    op.drop_column('measurements', 'dir_viento')
    op.drop_column('measurements', 'vel_viento')
    op.drop_column('measurements', 'co2')
    op.drop_column('measurements', 'no2')
