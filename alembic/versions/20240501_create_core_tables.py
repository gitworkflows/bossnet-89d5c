"""Create students, schools, enrollments, and lookup tables."""

import sqlalchemy as sa

from alembic import op

revision = "20240501_create_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Apply database schema changes."""
    op.create_table(
        "students",
        sa.Column("student_id", sa.String(length=36), primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("gender", sa.String(length=10)),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("division", sa.String(length=50)),
        sa.Column("district", sa.String(length=50)),
        sa.Column("upazila", sa.String(length=50)),
        sa.Column("socioeconomic_status", sa.String(length=50)),
        sa.Column("disability_status", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("guardian_contact", sa.String(length=20)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "schools",
        sa.Column("school_id", sa.String(length=36), primary_key=True),
        sa.Column("school_name", sa.String(length=255), nullable=False),
        sa.Column("division", sa.String(length=50)),
        sa.Column("district", sa.String(length=50)),
        sa.Column("upazila", sa.String(length=50)),
        sa.Column("school_type", sa.String(length=50)),
        sa.Column("education_level", sa.String(length=50)),
        sa.Column("geo_location", sa.String(length=100)),
        sa.Column("contact_number", sa.String(length=20)),
        sa.Column("is_rural", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "enrollments",
        sa.Column("enrollment_id", sa.String(length=36), primary_key=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("students.student_id", ondelete="CASCADE")),
        sa.Column("school_id", sa.String(length=36), sa.ForeignKey("schools.school_id", ondelete="CASCADE")),
        sa.Column("enrollment_year", sa.Integer(), nullable=False),
        sa.Column("grade_level", sa.String(length=10)),
        sa.Column("enrollment_status", sa.String(length=20)),
        sa.Column("reason_for_dropout", sa.Text()),
        sa.Column("transfer_school_id", sa.String(length=36), sa.ForeignKey("schools.school_id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "lookup_grades",
        sa.Column("grade_id", sa.Integer(), primary_key=True),
        sa.Column("grade_level", sa.String(length=10), nullable=False),
        sa.Column("description", sa.String(length=100)),
    )
    op.create_table(
        "lookup_divisions",
        sa.Column("division_id", sa.Integer(), primary_key=True),
        sa.Column("division_name", sa.String(length=50), nullable=False),
    )
    op.create_table(
        "lookup_districts",
        sa.Column("district_id", sa.Integer(), primary_key=True),
        sa.Column("district_name", sa.String(length=50), nullable=False),
        sa.Column("division_id", sa.Integer(), sa.ForeignKey("lookup_divisions.division_id")),
    )
    op.create_table(
        "lookup_upazilas",
        sa.Column("upazila_id", sa.Integer(), primary_key=True),
        sa.Column("upazila_name", sa.String(length=50), nullable=False),
        sa.Column("district_id", sa.Integer(), sa.ForeignKey("lookup_districts.district_id")),
    )
    op.create_table(
        "dropout_reasons",
        sa.Column("reason_id", sa.Integer(), primary_key=True),
        sa.Column("reason_text", sa.String(length=100), nullable=False),
    )


def downgrade():
    """Revert database schema changes."""
    op.drop_table("dropout_reasons")
    op.drop_table("lookup_upazilas")
    op.drop_table("lookup_districts")
    op.drop_table("lookup_divisions")
    op.drop_table("lookup_grades")
    op.drop_table("enrollments")
    op.drop_table("schools")
    op.drop_table("students")
