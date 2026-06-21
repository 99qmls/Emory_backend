# Emory - Multi-Tenant AI Agent Knowledge Platform

<div align="center">

# 🧠 Emory

### 基于 FastAPI + LangGraph + RAG + Multi-Agent 构建的企业级 AI 知识库平台

支持 **多租户**、**RAG 检索增强生成**、**Multi-Agent 工作流**、**情感分析**、**MCP 工具调用**、**长期记忆**、**流式聊天**、**Docker 一键部署**。

---

![Python](https://img.shields.io/badge/Python-3.11-blue)

![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green)

![LangChain](https://img.shields.io/badge/LangChain-Latest-orange)

![LangGraph](https://img.shields.io/badge/LangGraph-Agent-red)

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)

![Redis](https://img.shields.io/badge/Redis-Cache-red)

![Chroma](https://img.shields.io/badge/Chroma-VectorDB-purple)

![Docker](https://img.shields.io/badge/Docker-Compose-blue)

</div>

---

# 📖 项目简介（Project Introduction）

Emory 是一个面向企业知识管理与智能问答场景设计的 **企业级 AI Agent 平台**。项目采用现代 Python Web 后端架构，结合大语言模型（LLM）、RAG（Retrieval-Augmented Generation）、LangGraph 多智能体编排、MCP 工具调用及多级记忆机制，实现了一个具备知识检索、智能对话、情感分析和工具调用能力的 AI 系统。

不同于传统聊天机器人，Emory 更注重 **工程化、模块化、可扩展性** 与 **生产级架构设计**。系统将 Web 服务、AI 能力、向量检索、缓存、异步任务、文件存储等组件解耦，能够根据不同业务需求灵活扩展。

目前项目已实现：

* 多租户企业知识库
* 用户认证与权限管理
* 文档上传与异步处理
* RAG 检索增强生成
* 混合检索（向量 + BM25）
* BGE-Reranker 重排序
* LangGraph Multi-Agent 工作流
* 情感分析模块
* MCP 工具调用
* 本地/云端大模型统一接口
* 长期记忆管理
* SSE 流式聊天
* Docker 一键部署

项目整体采用经典的 **Router → Service → CRUD → Database** 分层架构，同时通过独立 AI 服务层（LLM、Embedding、RAG、Agent）实现业务逻辑与 AI 能力的完全解耦，为后续功能扩展和生产部署提供良好的基础。

---

# 🎯 项目目标

Emory 的目标不是简单封装一个聊天接口，而是构建一个可持续演进的 AI 平台，具备以下能力：

* 支持企业级知识库问答
* 支持多租户数据隔离
* 支持多模型自由切换
* 支持 Agent 工作流编排
* 支持工具调用（MCP）
* 支持长期记忆
* 支持情感分析
* 支持 Docker 容器化部署
* 支持后续模型微调与多模态扩展

---

# 🚀 项目特点

## 企业级多租户

所有业务数据均采用 Tenant 隔离，包括：

* 用户
* 知识库
* 文档
* 会话
* 消息
* 向量索引

每个租户拥有独立的数据空间，可满足 SaaS 场景需求。

---

## AI 与传统 Web 深度融合

项目同时包含：

传统业务：

* JWT 登录认证
* 用户管理
* 文件上传
* 权限控制
* CRUD 操作
* RESTful API

AI 能力：

* LLM 调用
* Embedding
* RAG
* Multi-Agent
* Memory
* MCP
* Emotion

形成完整 AI 应用开发体系。

---

## 统一 AI 工厂模式

为了支持不同模型供应商，项目采用 Factory Pattern。

目前支持：

* Ollama（本地部署）
* OpenAI Compatible API
* DeepSeek
* 智谱 AI
* Qwen（兼容 OpenAI API）

所有模型统一调用方式：

```python
llm = LLMFactory.create()

response = await llm.generate(prompt)
```

业务层无需关心底层模型来源。

---

## 云端模型自动降级

系统支持模型降级策略：

```
Cloud LLM
     │
     │ 可用
     ▼
返回结果

否则

Local Ollama

↓

继续生成回复
```

当云端模型不可用时，系统能够自动切换至本地 Ollama 模型，提高系统稳定性与可用性。

---

## 完整的 AI 服务抽象

整个 AI 能力按照职责划分为多个独立模块：

```
LLM
│
├── Embedding
│
├── Vector Store
│
├── RAG
│
├── Emotion
│
├── Agent
│
└── Memory
```

每个模块均采用接口抽象，可独立替换实现，降低模块耦合度。

---

# 🌟 核心亮点

## 1. 多租户 SaaS 架构

所有数据均按 Tenant 隔离：

```
Tenant A

├── Users

├── Knowledge Base

├── Chroma Collection

└── Conversations

────────────────────────

Tenant B

├── Users

├── Knowledge Base

├── Chroma Collection

└── Conversations
```

确保不同企业之间数据互不影响。

---

## 2. 统一模型管理

支持：

* 云端大模型
* 本地 Ollama
* 后续新增模型

无需修改业务代码即可切换模型。

---

## 3. Multi-Agent 工作流

采用 LangGraph 构建 Agent。

包括：

* Supervisor
* Retriever
* Emotion
* Generator
* Tool Node

支持复杂任务编排。

---

## 4. 混合检索

采用：

```
Vector Search

+

BM25

+

RRF

+

BGE-Reranker
```

相比单纯向量检索，能够显著提升知识库问答准确率。

---

## 5. 三层 Memory

系统构建完整记忆体系：

```
短期记忆

↓

Redis

↓

PostgreSQL

↓

LLM Summary
```

实现上下文保持、长期历史存储及摘要压缩。

---

## 6. MCP 工具调用

系统支持 MCP 微服务。

可通过 Tool Node 调用：

* 天气
* 地图
* 搜索
* 计算器

后续可继续扩展更多工具。

---

# 📂 项目整体架构

```
                     Frontend
                         │
                         │ HTTP / SSE
                         ▼
                  FastAPI API Gateway
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     Auth API       Knowledge API     Chat API
                         │
                         ▼
                  LangGraph Workflow
                         │
     ┌──────────────┬──────────────┬──────────────┐
     ▼              ▼              ▼
 Emotion Node   Retriever Node   Tool Node
                         │
                         ▼
                    Generator Node
                         │
                         ▼
                        LLM
                         │
      ┌──────────────────┼──────────────────┐
      ▼                  ▼                  ▼
 Embedding         Chroma VectorDB      PostgreSQL
      │                  │                  │
      └──────────────┬───┘                  │
                     ▼                      ▼
                  Redis Cache            MinIO
```

---

# 📌 技术选型

| 分类              | 技术                        |
| --------------- | ------------------------- |
| Web Framework   | FastAPI                   |
| ORM             | SQLAlchemy Async          |
| Data Validation | Pydantic                  |
| Authentication  | JWT                       |
| Database        | PostgreSQL                |
| Cache           | Redis                     |
| Object Storage  | MinIO                     |
| Vector Database | Chroma                    |
| LLM Framework   | LangChain                 |
| Agent Framework | LangGraph                 |
| Local Model     | Ollama                    |
| Embedding       | M3E / SentenceTransformer |
| File Parsing    | LangChain Loader          |
| Async Task      | Celery                    |
| Deployment      | Docker Compose            |

---

# 📈 当前实现进度

| 模块               | 状态           |
| ---------------- | ------------ |
| 用户认证             | ✅ 已完成        |
| 多租户              | ✅ 已完成        |
| JWT              | ✅ 已完成        |
| CRUD             | ✅ 已完成        |
| 文档上传             | ✅ 已完成        |
| MinIO            | ✅ 已完成        |
| Chroma           | ✅ 已完成        |
| Embedding        | ✅ 已完成        |
| Hybrid Retrieval | ✅ 已完成        |
| RAG              | ✅ 已完成        |
| LangGraph        | ✅ 已完成        |
| Emotion          | ✅ 已完成        |
| MCP              | ✅ 已完成        |
| Memory           | ✅ 已完成        |
| SSE Chat         | ✅ 已完成        |
| Docker           | ✅ 已完成        |
| 模型微调             | 🚧 预留接口，暂未实现 |

---

> **说明**：目前已完成平台核心能力建设，大模型微调（LoRA / QLoRA）尚未实现，但已在系统中预留模型管理与扩展接口，后续可在不影响现有架构的情况下快速接入。

```markdown
# 📂 项目目录结构（Project Structure）

一个优秀的后端项目，不仅要功能完善，更要具备良好的可维护性、可扩展性和团队协作能力。

本项目采用 **分层架构（Layered Architecture）+ 模块化设计（Modular Design）+ DDD（部分领域驱动思想）**，保证每一个目录都具有单一职责。

整个系统遵循：

```

Client
│
▼
FastAPI Router
│
▼
Controller(API)
│
▼
Service
│
▼
CRUD
│
▼
Database

```

AI 相关模块则采用：

```

User
│
▼
Chat API
│
▼
Agent
│
▼
Retriever
│
▼
Vector Database
│
▼
LLM
│
▼
Streaming Response

```

整个项目结构如下：

```

project/
│
├── app/
│
│   ├── api/
│   ├── core/
│   ├── crud/
│   ├── db/
│   ├── middleware/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── agents/
│   ├── rag/
│   ├── memory/
│   ├── mcp/
│   ├── llm/
│   ├── embeddings/
│   ├── vectorstores/
│   ├── tools/
│   ├── utils/
│   └── main.py
│
├── scripts/
├── tests/
├── docs/
├── docker/
├── nginx/
├── alembic/
├── requirements.txt
├── docker-compose.yml
└── README.md

```

---

# 📁 app/

这是整个系统的核心目录。

所有业务逻辑都集中在这里。

可以理解成：

```

整个后端 = app

```

里面又拆分为多个子模块，每个模块互不干扰。

这种设计具有以下优点：

- 高内聚
- 低耦合
- 易测试
- 易维护
- 易扩展

---

# 📁 api/

API 层负责处理 HTTP 请求。

它只负责：

- 接收请求
- 参数校验
- 调用 Service
- 返回 Response

例如：

```

POST /chat

↓

ChatRouter

↓

ChatService.chat()

↓

返回 StreamingResponse

```

API 不负责：

❌ SQL

❌ AI 推理

❌ 文件解析

❌ RAG

❌ Memory

这些全部交给 Service。

因此 API 层通常非常轻量。

例如：

```

@router.post("/chat")
async def chat(req):

```
return await ChatService.chat(req)
```

```

整个 Router 基本只有几十行。

---

# 📁 core/

core 可以理解成整个项目的大脑。

里面放的是：

整个项目共享的核心配置。

例如：

```

Config

Settings

Environment

Logger

Security

JWT

Redis

Exception

Constants

```

所有模块都会依赖 core。

例如：

```

API

↓

读取 Config

↓

数据库连接

↓

Redis

↓

JWT

↓

日志

```

这样所有配置统一管理。

修改一处即可影响全局。

---

# 📁 crud/

CRUD 层专门负责数据库。

很多初学者喜欢：

```

Router

↓

SQLAlchemy

↓

Database

```

企业项目不会这样。

而是：

```

Router

↓

Service

↓

CRUD

↓

Database

```

CRUD 只负责：

Create

Read

Update

Delete

例如：

```

UserCRUD.create()

UserCRUD.update()

UserCRUD.delete()

KnowledgeCRUD.search()

```

CRUD 不允许写业务逻辑。

例如：

```

if vip:

...

```

这种代码不能放这里。

这里只能：

```

session.query()

session.add()

session.commit()

```

保持数据库层纯净。

---

# 📁 db/

数据库相关配置全部放这里。

包括：

```

Database Engine

Session

Base

Migration

Connection Pool

```

整个项目共享一个 Session Factory。

所有 CRUD 都从这里获取数据库连接。

例如：

```

SessionLocal()

↓

CRUD

↓

Commit

```

统一管理数据库生命周期。

---

# 📁 models/

这里定义 ORM Model。

例如：

```

User

Knowledge

Conversation

Document

Chunk

Message

```

每一个 Model 对应数据库中的一张表。

例如：

```

class User(Base):

```
id

username

password
```

```

Model 只描述：

数据库结构。

不写业务。

---

# 📁 schemas/

Schema 负责数据校验。

采用：

Pydantic。

例如：

```

UserCreate

UserLogin

ChatRequest

ChatResponse

KnowledgeUpload

```

请求流程：

```

JSON

↓

Schema

↓

Service

↓

Model

```

Schema 永远不会操作数据库。

只负责：

数据是否合法。

例如：

```

email

长度

枚举

类型

默认值

```

这样 API 永远不用自己判断。

---

# 📁 services/

Service 是整个系统最重要的一层。

所有业务逻辑都放这里。

例如：

聊天：

```

ChatService

```

用户：

```

UserService

```

知识库：

```

KnowledgeService

```

文件：

```

FileService

```

Agent：

```

AgentService

```

Service 可以：

调用 CRUD

调用 Redis

调用 AI

调用 MCP

调用 VectorDB

调用 Memory

但是：

Service 不允许写 SQL。

全部交给 CRUD。

---
```
# AI 模块与工程目录（AI Modules & Project Infrastructure）

```markdown
# 🤖 AI 模块设计

相比传统 Web 后端，本项目最大的特点在于：

整个 AI 能力全部进行了模块化拆分。

每一个 AI 能力都是独立模块。

例如：

```

LLM

Embedding

RAG

Memory

Agent

MCP

Tools

Workflow

```

它们之间仅通过接口进行通信，而不是直接相互依赖。

这种设计便于：

- 更换模型
- 增加 Agent
- 更换向量数据库
- 新增 Tool
- 新增 MCP Server

而不会影响其它模块。

---

# 📁 agents/

Agent 是整个 AI 系统的决策中心（Decision Layer）。

它负责：

```

用户问题

↓

分析任务

↓

决定调用哪些能力

↓

组织执行流程

↓

生成最终回答

```

Agent 不直接负责：

- 数据库存储
- 向量检索
- LLM 初始化
- Embedding
- HTTP API

这些都交由其它模块完成。

一个典型 Agent 包括：

```

BaseAgent

ChatAgent

KnowledgeAgent

WorkflowAgent

PlannerAgent

SupervisorAgent

```

推荐结构：

```

agents/

├── base_agent.py
├── chat_agent.py
├── planner_agent.py
├── workflow_agent.py
├── supervisor.py
├── state.py
└── prompts.py

```

---

# 为什么需要 BaseAgent？

所有 Agent 都有很多公共能力：

例如：

- 初始化模型
- 初始化 Memory
- 初始化 Retriever
- Prompt 加载
- Tool 调用
- 日志

这些都可以抽象：

```

BaseAgent

↑

ChatAgent

KnowledgeAgent

WorkflowAgent

```

避免重复代码。

---

# 📁 rag/

RAG（Retrieval-Augmented Generation）

负责知识增强。

整体流程：

```

Question

↓

Embedding

↓

Vector Search

↓

BM25

↓

Hybrid Retrieval

↓

Rerank

↓

Top K

↓

LLM

```

推荐目录：

```

rag/

├── retriever.py
├── hybrid.py
├── reranker.py
├── splitter.py
├── loader.py
├── parser.py
└── pipeline.py

```

其中：

Retriever：

负责向量检索。

Hybrid：

融合：

Vector

+

BM25

Reranker：

负责重新排序。

Pipeline：

负责串联整个 RAG。

这样每一步都可以单独替换。

---

# 📁 memory/

Memory 是 AI Agent 的长期能力。

项目采用：

```

Short Memory

*

Long Memory

*

Summary Memory

```

目录：

```

memory/

├── short_memory.py
├── long_memory.py
├── summary_memory.py
├── conversation.py
└── manager.py

```

Manager：

统一管理所有 Memory。

例如：

```

Chat

↓

Short Memory

↓

Token 超限

↓

Summary

↓

写入 Long Memory

```

这样上下文长度不会无限增长。

---

# 📁 llm/

LLM 模块负责：

统一管理所有大模型。

例如：

```

OpenAI

DeepSeek

Qwen

Gemini

Claude

Ollama

```

统一接口：

```

LLMFactory

↓

create()

↓

返回具体模型

```

所有业务：

只依赖：

```

LLMFactory

```

永远不会直接依赖某一家模型。

以后新增：

```

Moonshot

Doubao

GLM

Llama

```

无需修改业务代码。

---

# 📁 embeddings/

Embedding 独立管理。

推荐：

```

EmbeddingFactory

↓

BGE

↓

OpenAI

↓

Jina

↓

Nomic

↓

M3E

```

统一：

```

embed(text)

↓

Vector

```

业务层无需关心：

具体模型是谁。

---

# 📁 vectorstores/

负责：

所有向量数据库。

例如：

```

Chroma

Milvus

PGVector

Qdrant

FAISS

Weaviate

```

统一接口：

```

VectorStore

↓

insert()

↓

search()

↓

delete()

```

以后：

从 Chroma

切换到：

Milvus

业务无需修改。

---

# 📁 mcp/

MCP（Model Context Protocol）

负责：

AI 与外部工具通信。

例如：

```

Filesystem

GitHub

MySQL

Postgres

Browser

Slack

Email

Search

```

推荐结构：

```

mcp/

├── client.py
├── server.py
├── manager.py
├── registry.py
└── adapters/

```

Registry：

统一管理：

所有 MCP Server。

Manager：

统一连接：

所有 MCP Client。

这样：

Agent

无需知道：

Server 的具体实现。

---

# 📁 tools/

Tool 是 Agent 可以调用的能力。

例如：

```

Search

Calculator

Python

Weather

SQL

Email

Knowledge Search

```

推荐：

```

BaseTool

↓

SearchTool

↓

CalculatorTool

↓

WeatherTool

↓

PythonTool

```

所有 Tool：

统一：

```

run()

↓

返回结果

```

Agent：

只需要：

```

Tool.run()

```

即可。

---

# 📁 utils/

Utils：

放置所有通用工具。

例如：

```

Hash

Time

UUID

Token

Retry

Logger

File

JSON

```

特点：

没有业务逻辑。

任何模块：

都可以调用。

例如：

```

utils/

├── logger.py
├── token.py
├── time.py
├── file.py
├── retry.py
├── uuid.py
└── json.py

```

---

# 📁 tests/

测试目录。

建议保持：

```

tests/

├── api/
├── crud/
├── service/
├── rag/
├── agents/
├── memory/
└── integration/

```

测试分层：

Unit Test

↓

Integration Test

↓

End-to-End Test

保证：

修改一个模块：

不会影响整个系统。

---

# 📁 docs/

项目文档。

推荐：

```

docs/

├── architecture.md
├── api.md
├── deployment.md
├── database.md
├── rag.md
├── memory.md
├── agent.md
└── faq.md

```

所有设计：

全部文档化。

方便团队协作。

---

# 📁 docker/

Docker 部署文件。

例如：

```

docker/

├── backend.Dockerfile
├── worker.Dockerfile
├── nginx.Dockerfile
└── compose/

```

统一：

镜像构建。

---

# 📁 nginx/

负责：

统一网关。

例如：

```

HTTPS

↓

Nginx

↓

FastAPI

↓

Streaming

↓

WebSocket

```

同时负责：

- SSL
- Gzip
- 静态资源
- 反向代理
- 负载均衡

---

# 📁 scripts/

自动化脚本。

例如：

```

scripts/

├── init_db.py
├── create_admin.py
├── import_docs.py
├── export_data.py
└── backup.py

```

方便：

一键初始化。

---

# 🔄 AI 模块整体调用关系

整个 AI 请求的数据流如下：

```

```
         User
           │
           ▼
      FastAPI API
           │
           ▼
     Chat Service
           │
           ▼
     Agent Manager
           │
 ┌─────────┼─────────┐
 ▼         ▼         ▼
```

Memory     Tools      MCP
│         │         │
└────┬────┴────┬────┘
▼         ▼
RAG Pipeline  External Services
│
▼
Vector Store
│
▼
Embedding Model
│
▼
LLM Factory
│
▼
Streaming Output
│
▼
User

```

整个系统采用：

> API → Service → Agent → RAG / Memory / Tools / MCP → LLM → Streaming Response

这种调用链保证了：

- 各模块职责单一
- 模块之间低耦合
- AI 能力可插拔
- 模型、向量库、工具均可自由替换
- 易于水平扩展与团队协作
```

数据库选择 
PostgreSQL
所有结构化业务数据（用户、租户、知识库元数据、对话记录、用量日志）
MinIO
用户上传的原始文件（PDF、Markdown、音频视频等）
Redis
缓存（会话、限流）、Celery 任务队列
Chroma
文档的向量嵌入及检索索引

传统开发
登录请求
用户请求 → FastAPI 路由 → 依赖注入（认证/租户）
大模型开发
Llm 这里采用本地和云大模型，可以进行模型切换，默认可使用云大模型，如果没有将使用本地ollama
大模型进行降级处理，节点也是本地部署大模型，这里我做了两类大模型集成，通过统一接口调用
Embedding 
嵌入模型工厂，根据配置返回合适的 Embedding 实例。
支持的模型名称：'m3e' 或任何 SentenceTransformer 兼容名称。
vector_store
向量数据库的选型、客户端封装、增删查改逻辑可以基于约定的向量格式进行开发。完成 `embedding` 后即可快速集成，打通“文本→向量→存储与检索”的全链路
emotion
情感分析可以被 LLM 直接调用实现，也可以用单独模型。它与 RAG 无直接依赖，放在此处不影响核心检索流。先完成它可以作为独立工具
识别用户语气并选择性模仿，通过主要情感，次要情感，情感外部诱因，最后再对分析情感分析打分
rag
异步文档加载器：支持多种格式文件的文本提取
自动集成混合检索器、LLM
文本分割
- 支持中文、Markdown 等自然分隔符
- 保护代码块、表格等特殊结构的完整性
- 可配置块大小与重叠长度
- 异步安全（通过线程池执行同步分割）
对于块过大进行2次分割
安全获取 BM25 索引（带自动重建和锁机制）
 BM25 检索：每次从 Chroma 获取该知识库全部文本构建索引（已做简单缓存优化）这里是简单字典进行缓存
融合：RRF (Reciprocal Rank Fusion)
重排序：BGE‑Reranker 对候选文档重新打分
agent
Agent 需要组合 LLM、RAG、情感分析等能力，实现工具调用、多步推理与业务逻辑。
这里采用多智能体和langgraph
节点选择是通过低温大模型直接判断输出节点
  1. 全局错误处理节点 + 装饰器：任意节点异常均可捕获并短路到 error_handler
  2. 历史记录截断：archive_node 限制最大保留轮数 (MAX_HISTORY = 10)
  3. 动态路由注册：有效节点名自动从 workflow.nodes 提取，无需硬编码
  4. 双重路由保护：supervisor 输出 + 错误检测，两级条件边确保安全
   Supervisor → 工具调用 → MCP 微服务 → 高德 API → 工具结果 → Generator 回答
 这里历史记忆采用短期记忆checkpointer，中期记忆采用redis缓存，长期记忆PostgreSQL，当记忆过长时采用大模型摘要，全链路追踪 ID对历史记忆追踪
这里集成了mcp服务和简单编码的情感工具类和一些知识库
mcp作为其它端口微服务通过http和大模型服务进行连接3次握手

通过docker拉取镜像部署数据库，可以一键部署

大模型优化分析，判断大模型输出是否合理和打分，token消耗统计


# 📊 Project Status

Emory 已完成 AI Agent 平台的大部分核心能力建设，涵盖 Web 服务、AI 工作流、知识库、记忆管理、多模型支持及工程化部署等模块。

---

## ✅ 基础后端（Backend）

### Web Framework

* ✅ FastAPI 全异步架构
* ✅ SQLAlchemy Async ORM
* ✅ Pydantic 数据校验
* ✅ RESTful API
* ✅ SSE 流式响应
* ✅ 全局异常处理
* ✅ 统一日志系统
* ✅ 配置中心

### Authentication

* ✅ JWT 登录认证
* ✅ RBAC 权限控制
* ✅ 多租户隔离
* ✅ Token 刷新
* ✅ 接口权限校验

---

## ✅ 数据存储（Storage）

### PostgreSQL

负责所有业务数据管理：

* 用户
* 租户
* 会话
* 对话记录
* 知识库元数据
* Agent 配置
* Token 使用统计
* 系统日志

### Redis

作为高速缓存与消息组件：

* 会话缓存
* Memory 中间层
* Celery Broker
* 请求限流
* 热数据缓存

### MinIO

对象存储：

* PDF
* Markdown
* Word
* 图片
* 音视频
* 用户上传文件

### Chroma

向量数据库：

* 文档向量存储
* 相似度检索
* Metadata Filter
* Hybrid Retrieval 支撑

---

## ✅ LLM Factory

统一封装所有大模型调用。

支持：

* ✅ OpenAI
* ✅ DeepSeek
* ✅ Qwen
* ✅ Ollama 本地模型

能力：

* 模型热切换
* 云模型优先
* 本地模型自动降级
* 统一 Prompt 接口
* Token 消耗统计
* 输出质量评分
* 调用日志记录

---

## ✅ Embedding Factory

统一管理所有向量模型。

支持：

* M3E
* SentenceTransformer
* 自定义 Embedding

提供：

* Embedding Factory
* 模型自动切换
* 配置驱动初始化

---

## ✅ Vector Store

统一封装向量数据库接口。

当前支持：

* Chroma

完成能力：

* 文档写入
* 批量删除
* Metadata 查询
* 相似度检索
* 统一 CRUD 接口

预留扩展：

* Milvus
* PGVector
* Elasticsearch

---

## ✅ Emotion Engine

情感分析作为独立 AI 工具。

完成：

* 主情绪识别
* 次情绪识别
* 外部诱因分析
* 情绪评分
* 回复风格适配

支持：

* LLM 分析
* 独立模型替换

---

## ✅ RAG Pipeline

完整知识库系统。

### 文档处理

* PDF
* Markdown
* Word
* TXT

### 文本切分

* 中文优化
* Markdown 保留
* Code Block 保留
* Table 保留
* 二次切分
* Chunk 重叠

### Embedding

自动生成向量

### Retrieval

支持：

* Vector Search
* BM25
* Hybrid Search
* RRF 融合
* BGE-Reranker

优化：

* BM25 自动缓存
* 自动重建索引
* 异步检索

---

## ✅ Agent Workflow

采用 LangGraph 实现多节点工作流。

完成：

* Supervisor Router
* Dynamic Routing
* Generator
* Retriever
* Emotion
* MCP Tool
* Error Handler
* Archive Node

特点：

* 动态节点注册
* 双重路由保护
* 自动错误恢复
* Workflow 解耦

---

## ✅ Memory System

三级记忆管理。

### Short Memory

* LangGraph Checkpointer

### Middle Memory

* Redis

### Long Memory

* PostgreSQL

优化：

* 自动摘要
* 历史压缩
* Conversation Trace ID
* Memory 生命周期管理

---

## ✅ MCP

MCP 微服务独立部署。

完成：

* HTTP 通信
* 工具注册
* 工具发现
* MCP Server
* MCP Client
* 高德地图示例
* 自定义工具

---

## ✅ 工程化

完成：

* Docker Compose
* 环境变量管理
* Celery
* Redis
* MinIO
* PostgreSQL
* Chroma

支持：

一键部署全部服务。

---

# 🚧 Planned Features

以下能力已预留接口，但尚未完全实现。

## AI

* [ ] 多 Agent 智能协作调度
例如入A2A技术，对注册智能体进行发现进行多智能体自动协作
用户提出一个复杂问题：

帮我分析销售数据，并生成 PPT。

整个任务会自动拆解
查询数据库
      │
      ▼
统计数据
      │
      ▼
调用Python分析
      │
      ▼
生成图表
      │
      ▼
生成PPT
      │
      ▼
返回下载链接
Orchestrator 自动发现并调用
多个agent可以项目自动调用
* [ ] Workflow 可视化编排
┌──────┐
│开始  │
└──┬───┘
   │
   ▼
检索节点
   │
   ▼
情绪节点
   │
   ▼
工具节点
   │
   ▼
LLM
   │
   ▼
结束
全部拖拽。

类似：
比如这些低代码平台
LangFlow
Dify
Coze 
（这个平台可以创建属于自己的专属于自己的ai助手，比如：agent说话语气和添加各种工具
n8n
* [ ] Agent Marketplace
上传
↓
注册
↓
共享
↓
安装
↓
调用

涉及知识：
插件系统
动态加载
Python EntryPoint
Plugin Architecture
版本管理
依赖管理

Agent Registry
* [ ] 多模态（Vision / Audio）
这里我实现较为简单，视频，音频，我通过将声音或视频里的声音转化为字幕
通过清洗字幕数据进行分割
* [ ] Fine-tuning
上传数据集
↓
训练
↓
生成 Adapter
↓
自动切换模型
示例 Hugging Face PEFT
原生支持 LoRA、QLoRA、Prefix Tuning、Adapter 等 10+ 种 PEFT 方法。
* [ ] Function Calling 自动优化

## Retrieval

* [ ] Milvus
* [ ] PGVector
* [ ] Elasticsearch

## Memory

* [ ] 用户画像长期建模
* [ ] 跨知识库记忆融合

## Observability

* [ ] Prometheus
* [ ] Grafana
* [ ] OpenTelemetry
* [ ] 链路追踪 Dashboard

## Deployment

* [ ] Kubernetes
* [ ] Helm
* [ ] CI/CD Pipeline
* [ ] GitHub Actions 自动部署

## Enterprise

* [ ] API Gateway
* [ ] OAuth2 / SSO
* [ ] 审计日志
* [ ] 多区域部署
* [ ] 配额管理
