# User Guide

## 1. AgentOS Lite 是什么

AgentOS Lite 是一个自托管 AI Agent 工作台 MVP。它不是普通聊天机器人，而是把一次用户问题拆成可观察的 Agent Run：

用户问题 -> 获取上下文（Documents/RAG、Memory、Codebase）-> Agent 计划与工具选择 -> 高风险工具人工审批 -> 输出带引用的回答 -> LLMOps 记录全过程。

默认使用 MockLLMProvider 和 MockEmbeddingProvider，不需要 API key，不花钱。Gemini 是可选真实模型模式。

## 2. 它解决什么问题

- 回答需要证据：文档问答会显示 citations、chunk snippet 和 relevance score。
- 项目上下文需要长期保存：Memory 可以保存偏好、项目背景和备注。
- Agent 工具需要安全控制：safe 工具直接运行，approval_required 工具暂停等待人工确认，blocked 工具永不执行。
- AI 系统需要可诊断：LLMOps 展示 provider、model、latency、tokens、trace、retrieval、tool calls 和 fallback reason。
- 代码库需要被理解：Codebase Skill 可以索引仓库、解释架构、定位相关文件、生成测试建议。

## 3. 每个页面怎么用

### Overview

Overview 展示产品主线：Ask、Retrieve context、Plan、Use tools、Require approval、Monitor runs。录 Demo 时从这里讲清楚 AgentOS Lite 的闭环。

### Chat

Chat 是 Agent 工作区。你可以问：

- `What can AgentOS Lite do?`
- `Summarize the uploaded product brief.`
- `How should you explain technical topics to me?`
- `Which files are related to document upload?`

回答旁边会显示 trace steps、citations、tool calls。如果某个工具需要人工审批，Chat 会显示 paused 状态并提示去 Tools 页面处理。

### Documents

Documents 是本地知识库。

- 上传 TXT 或 Markdown。
- 查看文档类型、chunk 数、上传时间。
- 查看 chunk preview。
- 删除文档或重新索引。
- 使用 sample docs 快速加载演示文档。

PDF 当前是清晰 stub，不做真实解析。

### Memory

Memory 用于长期偏好和项目上下文。常见用法：

- 保存用户解释风格偏好。
- 保存项目背景。
- 保存工具结果或备注。

之后在 Chat 中问相关问题，Agent 会自然引用这些 memory。

### Tools / Approvals

Tools 页面是 Agent 执行控制台。

- safe：可以直接执行。
- approval_required：创建 pending approval，等待人工 approve/reject。
- blocked：永不执行，用来展示安全 guardrails。

Approval history 可以说明 AgentOS Lite 不是盲目执行工具，而是有人类确认机制。

### Codebase

Codebase 是项目亮点页面。

- `Index sample repo`：索引 demo 仓库。
- `Index AgentOS Lite repo`：索引当前项目自身。
- Repo map 显示文件数、symbols、languages、main modules、top directories。
- 可以问：
  - `Explain the architecture of this repo.`
  - `Where is Gemini provider implemented?`
  - `Which files are related to document upload?`
  - `Generate test suggestions for Gemini provider.`

Codebase indexing 会忽略 `.env`、数据库、logs、node_modules、.git、.next、build/dist/cache 等。

### LLMOps

LLMOps 是诊断页面。它显示：

- Recent Agent Runs
- Model Calls
- Retrieval Logs
- Tool Calls
- Errors
- Provider
- Fallback count
- Raw JSON debug

Mock 模式会显示 local mock 或 `<1ms`，Gemini 模式显示真实 latency、error 和 fallback reason。

### Settings

Settings 显示安全配置：

- active provider
- active model
- API key configured yes/no
- fallback enabled yes/no
- embedding provider
- RAG mode
- strict citation mode
- demo mode and call limits

Settings 不会显示真实 API key。只有点击 `Test Provider` 才会测试 Gemini。

## 4. Mock 模式怎么用

Mock 是默认模式：

```env
LLM_PROVIDER=mock
LLM_FALLBACK_TO_MOCK=true
```

直接运行：

```powershell
.\scripts\start_backend.ps1
.\scripts\start_frontend.ps1
```

Mock 模式适合开发、截图、演示和 CI。成本为 `$0`。

## 5. Gemini 模式怎么用

复制 `.env.example` 到 `backend/.env`，填写：

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-local-key
GEMINI_MODEL=gemini-3.1-pro-preview
LLM_FALLBACK_TO_MOCK=true
```

重启后端，打开 Settings，确认：

- `llm_provider = gemini`
- `active_model = gemini-3.1-pro-preview`
- `llm_api_key_configured = yes`

然后点击 `Test Provider`。

## 6. 别人 clone 后怎么用

推荐 Windows 路径：

```powershell
git clone https://github.com/KemiZHANG/agentos-lite.git
cd agentos-lite
Copy-Item .env.example backend/.env
.\scripts\start_backend.ps1
```

另开终端：

```powershell
.\scripts\start_frontend.ps1
```

打开 `http://localhost:3000`。

## 7. 如何不花钱使用

保持 `LLM_PROVIDER=mock`。不要填写 Gemini key，也不要点击真实 provider 测试。Mock 模式可以完整展示 RAG、Memory、Tools、Approval、Codebase、LLMOps 的产品流程。

## 8. 如何安全使用 Gemini

- 只把真实 key 放在本机 `backend/.env` 或系统环境变量。
- 不要把 key 写进 README、docs、tests、screenshots、seed data。
- 不要提交 `.env`。
- Settings 只显示 key configured yes/no。
- LLMOps 不记录 key。
- 公共 demo 建议开启：

```env
DEMO_MODE=true
MAX_LLM_CALLS_PER_SESSION=20
MAX_LLM_CALLS_PER_DAY=100
```

如果 Gemini 不可用或达到 demo limit，系统会 fallback 到 local mock，并在 LLMOps 记录 fallback reason。
