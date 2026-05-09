from pathlib import Path


def test_project_uses_milvus_client_instead_of_postgres_vector_extension():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "pymilvus" in pyproject
    assert "boto3" in pyproject
    assert "pg" + "vector" not in pyproject
