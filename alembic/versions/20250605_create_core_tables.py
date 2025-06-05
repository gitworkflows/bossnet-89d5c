"""Create students, schools, enrollments tables."""

import uuid

import sqlalchemy as sa

from alembic import op

revision = "20250605"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Apply database schema changes."""
    op.create_table(
        "students",
        sa.Column("student_id", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("gender", sa.String(10)),
        sa.Column("date_of_birth", sa.Date),
        sa.Column("division", sa.String()),
        sa.Column("district", sa.String()),
        sa.Column("upazila", sa.String()),
        sa.Column("socioeconomic_status", sa.String()),
        sa.Column("disability_status", sa.String()),
        sa.Column("guardian_contact", sa.String()),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )

    op.create_table(
        "schools",
        sa.Column("school_id", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("division", sa.String()),
        sa.Column("district", sa.String()),
        sa.Column("upazila", sa.String()),
        sa.Column("type", sa.String()),
        sa.Column("education_level", sa.String()),
        sa.Column("is_rural", sa.Boolean()),
        sa.Column("geo_location", sa.String()),
        sa.Column("contact_info", sa.String()),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )

    op.create_table(
        "enrollments",
        sa.Column("enrollment_id", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", sa.UUID(as_uuid=True), sa.ForeignKey("students.student_id", ondelete="CASCADE")),
        sa.Column("school_id", sa.UUID(as_uuid=True), sa.ForeignKey("schools.school_id", ondelete="CASCADE")),
        sa.Column("enrollment_year", sa.Integer),
        sa.Column("grade", sa.String()),
        sa.Column("status", sa.String()),
        sa.Column("dropout_reason", sa.String()),
        sa.Column("transfer_school_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now()),
    )


def downgrade():
    """Revert database schema changes."""
    op.drop_table("enrollments")
    op.drop_table("schools")
    op.drop_table("students")
