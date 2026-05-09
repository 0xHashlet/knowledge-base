# Enterprise RAG Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the runnable foundation for an enterprise RAG knowledge-base QA platform with API, database, migrations, worker wiring, and core data models.

**Architecture:** A FastAPI application owns synchronous API traffic, SQLAlchemy 2.x models define the business schema, Alembic manages PostgreSQL migrations, and Celery workers consume Redis-backed asynchronous document-processing jobs. Milvus owns embedding storage and vector retrieval, while PostgreSQL keeps chunk text, ACL snapshots, and citation metadata.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Milvus, Redis, Celery, pytest, Docker Compose.

---

### Task 1: Foundation Tests

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_health.py`
- Create: `tests/test_settings.py`
- Create: `tests/models/test_metadata.py`

- [ ] Write tests for the health endpoint, settings defaults, and required SQLAlchemy table names.
- [ ] Run `pytest` and confirm it fails because the application files do not exist yet.

### Task 2: FastAPI and Configuration

**Files:**
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/core/config.py`
- Create: `app/core/security.py`
- Create: `app/core/logging.py`
- Create: `app/core/exceptions.py`
- Create: `app/api/__init__.py`
- Create: `app/api/deps.py`
- Create: `app/api/v1/__init__.py`
- Create: `app/api/v1/router.py`
- Create: `app/api/v1/health.py`

- [ ] Implement environment-driven settings.
- [ ] Implement `/api/v1/health`.
- [ ] Run health and settings tests.

### Task 3: Database and Models

**Files:**
- Create: `app/db/__init__.py`
- Create: `app/db/base.py`
- Create: `app/db/session.py`
- Create: model files under `app/models/`

- [ ] Implement SQLAlchemy declarative base and session factory.
- [ ] Define organization, RBAC, knowledge-base, document-version, chunk, QA, feedback, LLM log, and evaluation models.
- [ ] Run metadata tests.

### Task 4: Alembic Migration

**Files:**
- Create: `alembic.ini`
- Create: `app/db/migrations/env.py`
- Create: `app/db/migrations/script.py.mako`
- Create: `app/db/migrations/versions/20260508_0001_initial_schema.py`

- [ ] Configure Alembic to read the application database URL.
- [ ] Add initial schema migration for business metadata and chunk text; keep embedding vectors in Milvus.

### Task 5: Worker and Deployment Skeleton

**Files:**
- Create: `app/workers/__init__.py`
- Create: `app/workers/celery_app.py`
- Create: `app/workers/tasks/__init__.py`
- Create: `app/workers/tasks/document_tasks.py`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `pyproject.toml`
- Create: `README.md`

- [ ] Wire Celery to Redis.
- [ ] Define a placeholder document task for future parsing pipeline.
- [ ] Add local deployment files and validation instructions.

### Verification

- [ ] Run `pytest`.
- [ ] Run `python -m compileall app tests`.
- [ ] If dependencies are unavailable in the host environment, report the exact blocker and provide Docker-based verification commands.
