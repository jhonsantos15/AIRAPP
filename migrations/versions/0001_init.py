"""init measurements table

Revision ID: 0001_init
Revises: 
Create Date: 2025-10-02 00:00:00
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "measurements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.String(length=64), nullable=False),
        sa.Column("sensor_channel", sa.Enum("Um1", "Um2", name="sensorchannel"), nullable=False),
        sa.Column("pm25", sa.Float(), nullable=True),
        sa.Column("pm10", sa.Float(), nullable=True),
        sa.Column("temp", sa.Float(), nullable=True),
        sa.Column("rh", sa.Float(), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("hora", sa.Time(), nullable=True),
        sa.Column("fechah_local", sa.DateTime(timezone=True), nullable=False),
        sa.Column("doy", sa.Integer(), nullable=True),
        sa.Column("w", sa.Float(), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_device_channel_ts", "measurements", ["device_id", "sensor_channel", "fechah_local"])
    op.create_index("idx_fechah_local", "measurements", ["fechah_local"])


def downgrade():
    op.drop_index("idx_fechah_local", table_name="measurements")
    op.drop_constraint("uq_device_channel_ts", "measurements", type_="unique")
    op.drop_table("measurements")
