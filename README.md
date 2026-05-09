# Permission-Aware Enterprise RAG Platform

权限感知企业知识库 RAG 平台。

本项目面向企业内部制度、合同、产品文档、客服知识、技术文档等场景，目标是构建一套接近真实业务链路的 RAG 知识库问答后端，而不是简单的 PDF 上传问答 Demo。

## 项目定位

平台的核心要求是：用户无权访问的内容，不能进入 LLM 上下文。

RAG 检索链路必须保持清晰：

```text
权限过滤 -> 关键词召回 -> 向量召回 -> 合并去重 -> rerank -> 上下文构造 -> LLM 回答 -> 引用溯源
```

其中权限过滤必须发生在 chunk 进入 rerank、prompt context 和 LLM 调用之前。

## 当前开发阶段

当前处于 **阶段 4 已启动，具备检索链路最小骨架**：

- 阶段 1：基础工程骨架已完成。
- 阶段 2：认证、组织与权限体系已完成。
- 阶段 2.5：向量存储已从 PostgreSQL 内置向量方案切换为 Milvus。
- 阶段 3：已实现基于 S3-compatible 对象存储的文档上传、版本记录、解析任务骨架和 chunk 生成。
- 阶段 4：已实现权限过滤前置的关键词召回、向量召回和合并去重 service 骨架。

## 技术栈

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic
- PostgreSQL
- Milvus
- MinIO / S3-compatible Object Storage
- Redis
- Celery
- pytest
- uv
- Docker Compose

## 存储边界

- PostgreSQL 保存业务元数据：用户、权限、知识库、文档、文档版本、chunk 文本、权限快照和引用溯源信息。
- MinIO 当前作为 S3-compatible 对象存储实现，用于保存上传的原始文档文件。
- Milvus 保存 chunk embedding，用于后续向量召回。
- 数据库中的 `DocumentVersion.storage_path` 只保存相对 object key，不保存 MinIO URL，方便后续迁移到阿里云 OSS、AWS S3、腾讯 COS 等对象存储。
- Milvus 返回候选 chunk 后，仍必须基于 PostgreSQL 中的权限和 chunk 元数据完成过滤，再进入 rerank 和 LLM 上下文。

## 目录结构

```text
app/
  api/                 FastAPI 路由与依赖
  core/                配置、安全、日志与异常
  db/                  数据库连接、Base、Alembic 迁移
  models/              SQLAlchemy 数据模型
  repositories/        数据访问层
  schemas/             Pydantic 入参与出参模型
  services/            业务服务层
  storage/             S3-compatible 对象存储抽象与实现
  vectorstores/        Milvus 向量存储抽象与实现
  workers/             Celery worker 与任务
tests/                 pytest 测试
```

后端分层约定：

```text
api -> services -> repositories -> models
```

API 层只负责请求解析、依赖注入和响应返回；复杂业务逻辑放在 service 层；数据库访问收敛在 repository 层；对象存储和向量库分别通过 `storage`、`vectorstores` 抽象隔离。

## 已实现能力

### 阶段 1：基础骨架

- FastAPI 基础应用
- SQLAlchemy 2.x 数据库连接
- Alembic 迁移目录与初始迁移
- Docker Compose 编排：`api`、`postgres`、`redis`、`celery-worker`、`minio`、`milvus`
- Celery worker 基础骨架
- pytest 测试结构
- uv 依赖管理与锁文件

### 阶段 2：认证、组织与权限

- JWT 登录与密码哈希
- 用户、部门、角色、权限 CRUD
- 用户角色绑定、角色权限绑定
- 知识库 CRUD
- 知识库成员授权
- `PermissionService`
- 当前用户、管理员、知识库成员校验依赖
- 面向知识库、文档、chunk 查询的权限过滤接口预留

### 阶段 3：文档上传与 chunk 生成

- 文档上传 API：`POST /api/v1/knowledge-bases/{knowledge_base_id}/documents`
- 上传前校验当前用户是否可访问知识库
- 原始文件写入 S3-compatible 对象存储
- 创建或复用 `documents`
- 每次上传创建新的 `document_versions`
- Celery 文档解析任务骨架
- `text/plain` 与 PDF 基础解析
- chunk 生成并写入 `document_chunks`
- 解析失败时将文档版本标记为 `FAILED`

### 阶段 4：检索链路骨架

- `ChunkRepository.keyword_search`
- `ChunkRepository.get_active_chunks_by_ids`
- `RetrievalService`
- 检索顺序：权限过滤 -> 关键词召回 -> 向量召回 -> 合并去重
- 当前阶段不接 LLM、不做 rerank

## API 分组

当前主要接口：

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

POST   /api/v1/knowledge-bases/{knowledge_base_id}/documents
```

启动后访问 API 文档：

```text
http://localhost:8000/docs
```

## 本地调试

推荐使用 Docker Desktop + WSL2 后端。当前机器已将 Docker WSL 数据目录迁到非 C 盘：

```text
E:\DockerData\DockerDesktop\wsl
```

启动项目：

```powershell
cd C:\Users\Administrator\Desktop\dev\work\knowledge-base
docker compose up -d --build
```

执行数据库迁移：

```powershell
docker compose run --rm api uv run alembic upgrade head
```

运行测试：

```powershell
docker compose run --rm api uv run pytest
```

健康检查：

```powershell
curl.exe http://localhost:8000/api/v1/health
```

停止服务：

```powershell
docker compose down
```

查看 Docker 空间占用：

```powershell
docker system df
```

不要随意执行 `docker system prune -a --volumes`，它会删除未使用镜像、构建缓存和 volume，可能导致 PostgreSQL、Milvus 或 MinIO 数据被清掉。

## 环境变量

默认配置在 `.env.example` 中。首次本地开发可复制一份：

```powershell
Copy-Item .env.example .env
```

关键变量：

- `DATABASE_URL`：完整数据库连接串，设置后优先使用
- `POSTGRES_HOST`、`POSTGRES_PORT`、`POSTGRES_USER`、`POSTGRES_PASSWORD`、`POSTGRES_DB`：数据库连接参数
- `REDIS_URL`：Redis 地址
- `JWT_SECRET_KEY`：JWT 签名密钥，生产环境必须替换为足够长且随机的值
- `MILVUS_URI`：Milvus 服务地址
- `MILVUS_TOKEN`：Milvus 鉴权 token，可为空
- `MILVUS_COLLECTION`：chunk embedding collection 名称
- `VECTOR_DIMENSION`：默认向量维度
- `OBJECT_STORAGE_ENDPOINT`：S3-compatible 对象存储 endpoint，本地默认 MinIO
- `OBJECT_STORAGE_BUCKET`：文档对象 bucket
- `OBJECT_STORAGE_ACCESS_KEY`：对象存储 access key
- `OBJECT_STORAGE_SECRET_KEY`：对象存储 secret key
- `OBJECT_STORAGE_REGION`：对象存储 region

## MinIO 与生产迁移

当前项目可以先使用 MinIO，包括私有化生产场景。但代码层只依赖 S3-compatible 抽象，数据库只保存 object key，不保存 MinIO URL。

如果后续迁移到阿里云 OSS，通常只需要：

1. 将 MinIO bucket 中的对象同步到 OSS bucket。
2. 修改对象存储环境变量。
3. 重启 API 和 worker。
4. 运行文件读取、解析和上传回归测试。

## 开发规范

- 每个阶段保持可运行代码、数据库迁移、测试和验收方式。
- 新增数据库结构必须配 Alembic 迁移。
- 新增业务能力应补充 pytest 测试。
- 权限相关逻辑集中在 service/repository 层，不散落在 API 层。
- RAG 检索链路中，权限过滤必须发生在 chunk 进入 LLM 上下文之前。
- 对象存储访问必须通过 `app/storage` 抽象。
- 向量库访问必须通过 `app/vectorstores` 抽象。
- 不引入无关页面、演示性花哨功能，按阶段推进。

## 下一步计划

建议继续完善 **阶段 4：关键词召回、向量召回、权限过滤与结果合并**。

阶段 4 后续建议拆分为：

1. 将文档解析后的 embedding 写入 Milvus。
2. 增加正式检索 API。
3. 引入全文检索排序或 BM25 替代当前基础 `ILIKE`。
4. 增加 rerank 接口和上下文构造。
5. 输出引用溯源结构。
