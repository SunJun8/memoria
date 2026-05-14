# 设计边界

## 数据和 LLM 作业记录

Memoria 会保存两类数据：

- **结构化数据**：SQLite 中的 raw entries、issues、chains、proposals、patch records、LLM jobs。
- **完整 LLM transcript**：本地 JSONL 文件，默认保存在 jobs 目录。

保存 transcript 的目的是让 LLM 整理过程可回放、可审计、可调试。后续可以增加保留天数和关闭开关。

## 当前边界

当前版本坚持几个边界：

- 默认全本地：SQLite 数据库、transcript、备份都在本机。
- 不做 Web UI、API server、MCP server。
- 不提供自然语言问答入口；Codex、Claude Code 等外部 Agent 后续通过 CLI/API 访问。
- LLM provider 直接使用 OpenAI Python SDK，不引入 LangChain / LangGraph。
- 不支持删除记忆；旧记忆可以被新记忆纠正、补充或降权。
- Git 只作为本地备份机制，不 push。

## 概念

Memoria 的设计借用了几个认知隐喻：

- **原始记忆**：用户或外部 Agent 直接丢进来的原始内容，默认尽量完整保留。
- **Memory Issue**：表示一个任务、问题或持续关注的主题，类似 Jira issue，有标题、状态、标签、摘要和评论。
- **Memory Chain**：表示一条思维链或关联链，由 LLM 自主组织，可随时间合并、调整、重组。
- **睡眠整理**：系统主动调用 LLM，对待处理的原始记忆做抽取、归纳、链接和状态更新。
- **主动联想**：后续可以扩展为由 LLM 主动检索相关 issue / chain，发现新的关联。

## 当前 MVP 范围

已包含：

- 本地 CLI。
- SQLite + Alembic 初始迁移。
- 原始文本 / 文件 / stdin 导入。
- OpenAI SDK 直接 provider。
- Mock LLM provider。
- LLM tool loop。
- MemoryPatch schema 和事务性 patch application。
- Issue / Chain / Proposal / Patch / Sleep 查询。
- LLM job transcript JSONL。
- zip 备份、本地 Git 备份、Git commit 恢复。

暂不包含：

- Web UI。
- API server。
- MCP server。
- Codex / Claude Code 历史自动导入。
- 自然语言问答。
- 授权系统。
- Git push / 云同步。
