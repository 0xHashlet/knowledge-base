# Permission-Aware Enterprise RAG Platform

权限感知企业知识库 RAG 平台。

本项目面向企业内部制度、合同、产品文档、客服知识、技术文档等场景，目标是构建一套接近真实业务链路的 RAG 知识库问答后端，而不是简单的 PDF 上传问答 Demo。

## 项目定位

平台的核心目标是让知识库问答在进入 LLM 之前就完成权限约束，确保用户只能检索、重排、引用和生成其有权访问的内容。

核心检索链路必须保持清晰：

```text
权限过滤 -> 关键词召回 -> 向量召回 -> 合并去重 -> rerank -> 上下文构造 -> LLM 回答 -> 引用溯源
```

任何当前用户无权访问的 chunk，都不能进入 rerank、prompt context 或 LLM 调用。

## 当前阶段

### 阶段 1：基础工程骨架

已完成：

- FastAPI 基础应用与健康检查接口
- SQLAlchemy 2.x 数据库连接与声明式模型
- Alembic 迁移目录与初始迁移
- Docker Compose 编排：`api`、`postgres`、`redis`、`celery-worker`
- Celery worker 基础骨架
- pytest 基础测试结构
- 企业 RAG 核心数据模型

### 阶段 2：认证、组织与权限体系

已实现基础能力：

- JWT 登录与密码哈希
- 用户 CRUD
- 部门 CRUD
- 角色 CRUD
- 权限 CRUD
- 用户角色绑定
- 角色权限绑定
- 知识库 CRUD
- 知识库成员授权
- `PermissionService` 权限服务
- FastAPI 依赖：当前用户、管理员校验、知识库成员校验
- 面向知识库、文档、chunk 查询的权限过滤接口预留
- 阶段 2 相关 pytest 测试用例

## 技术栈

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic
- PostgreSQL
- pgvector
- Redis
- Celery
- pytest
- Docker Compose

## 目录结构

```text
app/
  api/                 FastAPI 路由与依赖
  core/                配置、安全与基础设施能力
  db/                  数据库连接、Base、Alembic 迁移
  models/              SQLAlchemy 数据模型
  repositories/        数据访问层
  schemas/             Pydantic 入参与出参模型
  services/            业务服务层
  workers/             Celery worker
tests/                 pytest 测试
docker-compose.yml     本地服务编排
pyproject.toml         项目依赖与工具配置
```

后端分层约定：

```text
api -> services -> repositories -> models
```

API 层只负责请求解析、依赖注入和响应返回；复杂业务逻辑应放在 service 层；数据库访问应收敛在 repository 层。

## 核心数据域

当前已建模的数据域包括：

- 用户、部门、角色、权限
- 用户角色、角色权限
- 知识库、知识库成员
- 文档、文档版本、文档 chunk
- 问答会话、问答消息
- 用户反馈
- LLM 调用日志
- 评测集、评测用例、评测运行、评测结果

## API 分组

当前主要接口分组：

```text
GET    /api/v1/health

POST   /api/v1/auth/login
GET    /api/v1/auth/me

GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/{user_id}
PATCH  /api/v1/users/{user_id}
DELETE /api/v1/users/{user_id}
POST   /api/v1/users/{user_id}/roles/{role_id}
DELETE /api/v1/users/{user_id}/roles/{role_id}

GET    /api/v1/departments
POST   /api/v1/departments
GET    /api/v1/departments/{department_id}
PATCH  /api/v1/departments/{department_id}
DELETE /api/v1/departments/{department_id}

GET    /api/v1/roles
POST   /api/v1/roles
GET    /api/v1/roles/{role_id}
PATCH  /api/v1/roles/{role_id}
DELETE /api/v1/roles/{role_id}
POST   /api/v1/roles/{role_id}/permissions/{permission_id}
DELETE /api/v1/roles/{role_id}/permissions/{permission_id}

GET    /api/v1/permissions
POST   /api/v1/permissions
GET    /api/v1/permissions/{permission_id}
PATCH  /api/v1/permissions/{permission_id}
DELETE /api/v1/permissions/{permission_id}

GET    /api/v1/knowledge-bases
POST   /api/v1/knowledge-bases
GET    /api/v1/knowledge-bases/{knowledge_base_id}
PATCH  /api/v1/knowledge-bases/{knowledge_base_id}
DELETE /api/v1/knowledge-bases/{knowledge_base_id}
PUT    /api/v1/knowledge-bases/{knowledge_base_id}/members
DELETE /api/v1/knowledge-bases/{knowledge_base_id}/members/{user_id}
```

## 本地启动

复制环境变量文件：

```bash
cp .env.example .env
```

启动服务：

```bash
docker compose up --build
```

执行数据库迁移：

```bash
docker compose run --rm api alembic upgrade head
```

健康检查：

```bash
curl http://localhost:8000/api/v1/health
```

## 测试

在 Docker 环境中运行：

```bash
docker compose run --rm api pytest
```

如果使用本机 Python 环境，建议使用 Python 3.12，并在安装依赖后运行：

```bash
python -m pytest
```

当前工作区所在机器缺少可用的 Python、pytest 和 Docker 命令，因此测试需要在具备 Docker 或 Python 3.12 的环境中执行。

## 开发规范

- 每个阶段保持可运行代码、数据库迁移、测试和验收方式。
- 新增数据库结构必须配套 Alembic 迁移。
- 新增业务能力应补充 pytest 测试。
- 权限相关逻辑必须集中在 service/repository 层，不应散落在 API 层。
- RAG 检索链路中，权限过滤必须发生在 chunk 进入 LLM 上下文之前。
- 不引入无关页面、演示性花哨功能或一次性堆完整系统。

## 后续路线

建议继续按阶段推进：

- 阶段 3：文档上传、解析、版本管理与 chunk 生成
- 阶段 4：关键词召回、向量召回、权限过滤与结果合并
- 阶段 5：rerank、上下文构造、LLM 回答与引用溯源
- 阶段 6：评测集、评测运行、质量指标与反馈闭环
