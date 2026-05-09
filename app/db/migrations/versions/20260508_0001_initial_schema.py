"""initial enterprise rag schema

Revision ID: 20260508_0001
Revises:
Create Date: 2026-05-08 00:00:00
"""
from alembic import op

revision = "20260508_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE knowledge_base_visibility AS ENUM ('PRIVATE', 'DEPARTMENT', 'COMPANY');
        CREATE TYPE knowledge_base_member_role AS ENUM ('OWNER', 'MANAGER', 'EDITOR', 'VIEWER');
        CREATE TYPE document_status AS ENUM ('ACTIVE', 'ARCHIVED', 'DELETED');
        CREATE TYPE document_version_status AS ENUM ('UPLOADED', 'PARSING', 'PARSED', 'EMBEDDING', 'READY', 'FAILED');
        CREATE TYPE qa_message_role AS ENUM ('USER', 'ASSISTANT', 'SYSTEM');
        CREATE TYPE feedback_rating AS ENUM ('UP', 'DOWN');
        CREATE TYPE llm_call_type AS ENUM ('CHAT', 'EMBEDDING', 'RERANK', 'EVALUATION');
        CREATE TYPE llm_call_status AS ENUM ('SUCCESS', 'FAILED');
        CREATE TYPE evaluation_run_status AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED');

        CREATE TABLE departments (
            id UUID PRIMARY KEY,
            name VARCHAR(128) NOT NULL,
            code VARCHAR(64) UNIQUE,
            parent_id UUID REFERENCES departments(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_departments_parent_name UNIQUE (parent_id, name)
        );

        CREATE TABLE users (
            id UUID PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            username VARCHAR(80) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(120),
            is_active BOOLEAN NOT NULL DEFAULT true,
            is_superuser BOOLEAN NOT NULL DEFAULT false,
            department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_users_email ON users(email);
        CREATE INDEX ix_users_username ON users(username);

        CREATE TABLE roles (
            id UUID PRIMARY KEY,
            name VARCHAR(80) NOT NULL UNIQUE,
            description VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE permissions (
            id UUID PRIMARY KEY,
            resource VARCHAR(80) NOT NULL,
            action VARCHAR(80) NOT NULL,
            description VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_permissions_resource_action UNIQUE (resource, action)
        );

        CREATE TABLE user_roles (
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, role_id)
        );

        CREATE TABLE role_permissions (
            role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
            PRIMARY KEY (role_id, permission_id)
        );

        CREATE TABLE knowledge_bases (
            id UUID PRIMARY KEY,
            name VARCHAR(160) NOT NULL,
            description VARCHAR(500),
            visibility knowledge_base_visibility NOT NULL DEFAULT 'PRIVATE',
            owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE knowledge_base_members (
            id UUID PRIMARY KEY,
            knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role knowledge_base_member_role NOT NULL DEFAULT 'VIEWER',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_kb_members_kb_user UNIQUE (knowledge_base_id, user_id)
        );

        CREATE TABLE documents (
            id UUID PRIMARY KEY,
            knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            source_type VARCHAR(50) NOT NULL DEFAULT 'upload',
            external_id VARCHAR(255),
            status document_status NOT NULL DEFAULT 'ACTIVE',
            current_version_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_documents_kb_external_id UNIQUE (knowledge_base_id, external_id)
        );

        CREATE TABLE document_versions (
            id UUID PRIMARY KEY,
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
            version_number INTEGER NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            file_size INTEGER NOT NULL,
            storage_path VARCHAR(500) NOT NULL,
            content_hash VARCHAR(128) NOT NULL,
            parser_name VARCHAR(80),
            parser_version VARCHAR(40),
            status document_version_status NOT NULL DEFAULT 'UPLOADED',
            raw_text TEXT,
            error_message TEXT,
            metadata JSONB NOT NULL DEFAULT '{}',
            is_latest BOOLEAN NOT NULL DEFAULT true,
            uploaded_by_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_document_versions_number UNIQUE (document_id, version_number)
        );

        CREATE TABLE document_chunks (
            id UUID PRIMARY KEY,
            knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            content_hash VARCHAR(128) NOT NULL,
            token_count INTEGER NOT NULL DEFAULT 0,
            page_start INTEGER,
            page_end INTEGER,
            embedding_model VARCHAR(120),
            search_vector TSVECTOR,
            metadata JSONB NOT NULL DEFAULT '{}',
            acl_snapshot JSONB NOT NULL DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_document_chunks_version_index UNIQUE (document_version_id, chunk_index)
        );
        CREATE INDEX ix_document_chunks_kb_version ON document_chunks(knowledge_base_id, document_version_id);
        CREATE INDEX ix_document_chunks_search_vector ON document_chunks USING gin(search_vector);

        CREATE TABLE qa_sessions (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE SET NULL,
            title VARCHAR(255),
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE qa_messages (
            id UUID PRIMARY KEY,
            session_id UUID NOT NULL REFERENCES qa_sessions(id) ON DELETE CASCADE,
            role qa_message_role NOT NULL,
            content TEXT NOT NULL,
            citations JSONB NOT NULL DEFAULT '[]',
            retrieval_trace JSONB NOT NULL DEFAULT '{}',
            prompt_tokens INTEGER NOT NULL DEFAULT 0,
            completion_tokens INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE answer_feedback (
            id UUID PRIMARY KEY,
            message_id UUID NOT NULL REFERENCES qa_messages(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rating feedback_rating NOT NULL,
            score INTEGER,
            comment TEXT,
            labels JSONB NOT NULL DEFAULT '[]',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE llm_call_logs (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            qa_message_id UUID REFERENCES qa_messages(id) ON DELETE SET NULL,
            provider VARCHAR(80) NOT NULL,
            model VARCHAR(120) NOT NULL,
            call_type llm_call_type NOT NULL,
            status llm_call_status NOT NULL,
            prompt_tokens INTEGER NOT NULL DEFAULT 0,
            completion_tokens INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            latency_ms INTEGER NOT NULL,
            cost_usd NUMERIC(12, 6) NOT NULL DEFAULT 0,
            request_payload JSONB NOT NULL DEFAULT '{}',
            response_payload JSONB NOT NULL DEFAULT '{}',
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE evaluation_datasets (
            id UUID PRIMARY KEY,
            name VARCHAR(160) NOT NULL,
            description TEXT,
            knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
            created_by_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE evaluation_cases (
            id UUID PRIMARY KEY,
            dataset_id UUID NOT NULL REFERENCES evaluation_datasets(id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            expected_answer TEXT,
            expected_citations JSONB NOT NULL DEFAULT '[]',
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE evaluation_runs (
            id UUID PRIMARY KEY,
            dataset_id UUID NOT NULL REFERENCES evaluation_datasets(id) ON DELETE CASCADE,
            triggered_by_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            status evaluation_run_status NOT NULL DEFAULT 'PENDING',
            config JSONB NOT NULL DEFAULT '{}',
            summary JSONB NOT NULL DEFAULT '{}',
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE evaluation_results (
            id UUID PRIMARY KEY,
            run_id UUID NOT NULL REFERENCES evaluation_runs(id) ON DELETE CASCADE,
            case_id UUID NOT NULL REFERENCES evaluation_cases(id) ON DELETE CASCADE,
            answer TEXT,
            citations JSONB NOT NULL DEFAULT '[]',
            metrics JSONB NOT NULL DEFAULT '{}',
            latency_ms INTEGER NOT NULL DEFAULT 0,
            cost_usd NUMERIC(12, 6) NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS evaluation_results;
        DROP TABLE IF EXISTS evaluation_runs;
        DROP TABLE IF EXISTS evaluation_cases;
        DROP TABLE IF EXISTS evaluation_datasets;
        DROP TABLE IF EXISTS llm_call_logs;
        DROP TABLE IF EXISTS answer_feedback;
        DROP TABLE IF EXISTS qa_messages;
        DROP TABLE IF EXISTS qa_sessions;
        DROP TABLE IF EXISTS document_chunks;
        DROP TABLE IF EXISTS document_versions;
        DROP TABLE IF EXISTS documents;
        DROP TABLE IF EXISTS knowledge_base_members;
        DROP TABLE IF EXISTS knowledge_bases;
        DROP TABLE IF EXISTS role_permissions;
        DROP TABLE IF EXISTS user_roles;
        DROP TABLE IF EXISTS permissions;
        DROP TABLE IF EXISTS roles;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS departments;
        DROP TYPE IF EXISTS evaluation_run_status;
        DROP TYPE IF EXISTS llm_call_status;
        DROP TYPE IF EXISTS llm_call_type;
        DROP TYPE IF EXISTS feedback_rating;
        DROP TYPE IF EXISTS qa_message_role;
        DROP TYPE IF EXISTS document_version_status;
        DROP TYPE IF EXISTS document_status;
        DROP TYPE IF EXISTS knowledge_base_member_role;
        DROP TYPE IF EXISTS knowledge_base_visibility;
        """
    )
