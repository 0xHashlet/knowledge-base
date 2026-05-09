import pytest
from app.services.bm25_service import Bm25SearchService, SearchableChunk


def make_chunk(cid: str, content: str) -> SearchableChunk:
    return SearchableChunk(chunk_id=cid, content=content)


def test_bm25_returns_relevant_chunks():
    chunks = [
        make_chunk("1", "Python 是一门编程语言"),
        make_chunk("2", "员工年假管理制度规定每年五天"),
        make_chunk("3", "数据库连接池配置说明"),
    ]
    svc = Bm25SearchService(chunks)
    results = svc.search("年假", limit=2)
    assert len(results) > 0
    assert results[0].chunk_id == "2"


def test_bm25_empty_corpus_returns_empty():
    svc = Bm25SearchService([])
    assert svc.search("test") == []


def test_bm25_no_match_returns_empty():
    svc = Bm25SearchService([make_chunk("1", "今天天气不错")])
    results = svc.search("xyz不存在的关键词")
    assert results == []


def test_bm25_limits_results():
    chunks = [make_chunk(str(i), f"内容编号{i}") for i in range(20)]
    svc = Bm25SearchService(chunks)
    results = svc.search("内容", limit=5)
    assert len(results) <= 5
