from app.db.base import Base


def test_metadata_contains_enterprise_rag_core_tables():
    expected_tables = {
        "departments",
        "users",
        "roles",
        "permissions",
        "user_roles",
        "role_permissions",
        "knowledge_bases",
        "knowledge_base_members",
        "documents",
        "document_versions",
        "document_chunks",
        "qa_sessions",
        "qa_messages",
        "answer_feedback",
        "llm_call_logs",
        "evaluation_datasets",
        "evaluation_cases",
        "evaluation_runs",
        "evaluation_results",
    }

    assert expected_tables.issubset(set(Base.metadata.tables))


def test_document_chunks_keep_metadata_but_not_postgres_embedding_column():
    columns = Base.metadata.tables["document_chunks"].columns

    assert "document_chunks" in Base.metadata.tables
    assert "embedding_model" in columns
    assert "embedding" not in columns
