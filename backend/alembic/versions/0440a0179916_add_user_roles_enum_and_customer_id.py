"""Add user roles enum and customer_id

Revision ID: 0440a0179916
Revises: da7939229234
Create Date: 2026-08-25 11:54:15.101350

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0440a0179916"
down_revision: Union[str, Sequence[str], None] = "da7939229234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ---------------------------------------------------------
    # 1. Add customer_id column
    # ---------------------------------------------------------

    op.add_column(
        "users",
        sa.Column("customer_id", sa.Integer(), nullable=True)
    )

    # ---------------------------------------------------------
    # 2. Create PostgreSQL enum
    # ---------------------------------------------------------

    user_role_enum = sa.Enum(
        "PLATFORM_ADMIN",
        "BUSINESS_OWNER",
        "CUSTOMER",
        name="user_role_enum",
    )

    user_role_enum.create(
        op.get_bind(),
        checkfirst=True
    )

    # ---------------------------------------------------------
    # 3. Convert existing role values
    #
    # Existing database currently contains:
    #
    #     owner
    #
    # We convert:
    #
    #     owner -> BUSINESS_OWNER
    #
    # before converting the column to the enum.
    # ---------------------------------------------------------

    op.alter_column(
        "users",
        "role",
        existing_type=sa.VARCHAR(length=20),
        type_=user_role_enum,
        postgresql_using="""
            CASE
                WHEN role = 'owner' THEN 'BUSINESS_OWNER'
                WHEN role = 'platform_admin' THEN 'PLATFORM_ADMIN'
                WHEN role = 'customer' THEN 'CUSTOMER'
                ELSE role
            END::user_role_enum
        """,
        nullable=False,
    )

    # ---------------------------------------------------------
    # 4. Create indexes
    # ---------------------------------------------------------

    op.create_index(
        op.f("ix_users_business_id"),
        "users",
        ["business_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_users_customer_id"),
        "users",
        ["customer_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_users_phone"),
        "users",
        ["phone"],
        unique=False,
    )

    op.create_index(
        op.f("ix_users_role"),
        "users",
        ["role"],
        unique=False,
    )

    # ---------------------------------------------------------
    # 5. Create foreign key
    # ---------------------------------------------------------

    op.create_foreign_key(
        "fk_users_customer_id_customers",
        "users",
        "customers",
        ["customer_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    # ---------------------------------------------------------
    # 1. Remove foreign key
    # ---------------------------------------------------------

    op.drop_constraint(
        "fk_users_customer_id_customers",
        "users",
        type_="foreignkey",
    )

    # ---------------------------------------------------------
    # 2. Remove indexes
    # ---------------------------------------------------------

    op.drop_index(
        op.f("ix_users_role"),
        table_name="users",
    )

    op.drop_index(
        op.f("ix_users_phone"),
        table_name="users",
    )

    op.drop_index(
        op.f("ix_users_customer_id"),
        table_name="users",
    )

    op.drop_index(
        op.f("ix_users_business_id"),
        table_name="users",
    )

    # ---------------------------------------------------------
    # 3. Convert enum back to VARCHAR
    # ---------------------------------------------------------

    op.alter_column(
        "users",
        "role",
        existing_type=sa.Enum(
            "PLATFORM_ADMIN",
            "BUSINESS_OWNER",
            "CUSTOMER",
            name="user_role_enum",
        ),
        type_=sa.VARCHAR(length=20),
        postgresql_using="role::text",
        nullable=False,
    )

    # ---------------------------------------------------------
    # 4. Drop enum
    # ---------------------------------------------------------

    user_role_enum = sa.Enum(
        "PLATFORM_ADMIN",
        "BUSINESS_OWNER",
        "CUSTOMER",
        name="user_role_enum",
    )

    user_role_enum.drop(
        op.get_bind(),
        checkfirst=True
    )

    # ---------------------------------------------------------
    # 5. Remove customer_id
    # ---------------------------------------------------------

    op.drop_column(
        "users",
        "customer_id"
    )