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
# 快速开始
1.激活docker
2.大模型启动（这里可以使用其它本地部署大模型，或者优先云大模型，可以修改模型和策略）
ollama run deepseek-r1:7b
3. docker-compose up -d （这里采用docker部署数据库，后面可以用k8s）
4. python servers/weather_server.py 先启动mcp服务再启动主服务
5. uvicorn app.main:app --reload --port 7000
6. celery -A app.core.celery_app worker --loglevel=info
可视化接口网址（端口可以自定义修改）
http://127.0.0.1:7000/docs#/
登录 pgAdmin （可视化数据库）
浏览器打开：http://localhost:5050
