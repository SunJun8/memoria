---
name: memoria
description: "Use when an agent needs to record work context into Memoria, query memory issues/chains/patches/jobs, run sleep consolidation, inspect raw-to-issue results, or explain/debug Memoria's LLM memory tool-call flow."
---

# Memoria

## Overview

Memoria 是一个本地优先的 CLI 记忆系统。用这个 skill 记录简洁的工作记忆、运行睡眠整理、查询结构化记忆，并解释 LLM 后端的 tool-call 流程。

## Install

优先使用隔离安装：

```bash
uv tool install memoria-cli
memoria --help
```

如果使用 pip，用户本机 Python 必须已经是 3.11 或更高版本：

```bash
python -m pip install memoria-cli
memoria --help
```

PyPI 包名是 `memoria-cli`；安装后的命令是 `memoria`。

## Record Memory

记录未来 agent 应该知道的事实、决策、测试结果和路径。不要把 secrets、token、凭据或私钥写进 memory。

```bash
memoria ingest text "事实、决策或测试结果。" \
  --title "简短标题" \
  --tag memoria \
  --hint "整理成项目决策" \
  --project-path "$PWD"
```

较长内容优先用 stdin：

```bash
printf '%s\n' "多行工作记录" | memoria ingest stdin --title "工作记录" --tag work
```

## Consolidate

冒烟测试和流程检查优先使用 mock：

```bash
memoria sleep --mock
```

只有在用户明确要求或环境已经配置好时，才运行真实 OpenAI 整理：

```bash
export OPENAI_API_KEY="..."
memoria sleep --limit 20 --strictness balanced
```

## Query

需要比较结果或继续交给 agent 处理时，使用 JSON 输出：

```bash
memoria issue list --json
memoria issue show <id> --json
memoria issue search "keyword" --json
memoria chain list --json
memoria patch list --json
memoria sleep list --json
memoria sleep show <job-id> --json
```

Memoria 0.1.0 没有暴露 `raw list` CLI 命令。`issue list` 展示的是整理后的 Memory Issues，不是 raw entries；需要追踪 raw 如何被消费时，查看 patch 和 sleep job。

## LLM Tool Flow

后端里，`SleepService.run()` 先创建 sleep job，然后 `_run_and_commit_job()` 调用 `LLMToolService.get_system_state(limit)` 收集 pending raw entries。

`OpenAIProvider.run_memory_job()` 把 prompt 发给 OpenAI Responses API，并暴露严格 function tools：

- `list_issues(limit, status)`
- `search_issues(query, limit)`
- `get_issue(issue_id)`
- `list_chains(limit)`

每个 function call 都通过本地 `LLMToolService` 执行为只读查询。Provider 追加 `function_call_output` 消息并循环，直到没有 tool calls。最终响应必须是严格的 `MemoryPatch`；`PatchService` 事务性应用 patch，transcript events 会记录 `request`、`response`、`tool_call`、`tool_result` 和 `patch`。
