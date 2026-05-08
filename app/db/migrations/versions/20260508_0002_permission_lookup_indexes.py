"""add permission lookup indexes

Revision ID: 20260508_0002
Revises: 20260508_0001
Create Date: 2026-05-08 23:30:00
"""
from alembic import op

revision = "20260508_0002"
down_revision = "20260508_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.create_index(
        "ix_role_permissions_permission_id",
        "role_permissions",
        ["permission_id"],
    )
    op.create_index("ix_kb_members_user_id", "knowledge_base_members", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_kb_members_user_id", table_name="knowledge_base_members")
    op.drop_index("ix_role_permissions_permission_id", table_name="role_permissions")
    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
