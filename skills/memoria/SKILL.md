---
name: memoria
description: "Use when an agent needs to operate Memoria CLI, record work context as local memory, query issues/chains/proposals/patches/sleep jobs, configure Memoria, run sleep consolidation, inspect memory audit results, or explain/debug Memoria's LLM memory flow."
---

# Memoria

## Overview

Memoria 是本地优先的 CLI 记忆系统，用 SQLite、JSONL transcript 和本地备份保存 agent 工作记忆。它把 raw notes、任务上下文、项目决策和工作记录整理成 Memory Issue、Memory Chain、Proposal 与可审计 Patch。

这个 skill 的目标是让 agent 会用 Memoria，而不是重新解释 Memoria 的产品概念。遇到 Memoria 相关任务时，先按下面的索引读取对应 reference。

## Start Here

- 日常记录、整理、查询、审计、备份：读 [references/usage.md](references/usage.md)。
- 安装、路径、配置、OpenAI key、隔离测试环境：读 [references/configuration.md](references/configuration.md)。
- 排障、sleep job、transcript、raw-to-issue、内部 LLM tool-call 流程：读 [references/debugging.md](references/debugging.md)。

如果用户只说“把这次工作记到 memoria”，通常只需要读 `references/usage.md` 的 `Record Memory` 和 `Consolidate`。

## Operating Rules

- 对 agent 后续要消费的输出，优先使用 `--json`。
- 记录 memory 时写事实、决策、路径、测试结果、约束和待办；不要写 secret、token、凭据、私钥或未脱敏个人敏感信息。
- 在 Memoria 源码仓库内验证当前代码时，用 `uv run memoria ...`；使用已安装工具时，用 `memoria ...`。
- 冒烟测试、演示和不确定环境优先用 `memoria sleep --mock`。只有用户要求或环境已配置 OpenAI key 时，才运行真实 `memoria sleep`。
- 不要假设存在 raw 查询命令。当前 CLI 没有 `raw list`；追踪 raw entry 是否被消费时，查看 sleep job、patch record 和 transcript。
- 恢复备份会改动本地 Memoria 数据，除非用户明确要求，不要运行 `backup restore` 或 `backup restore-git`。

## Minimal Command Set

```bash
memoria ingest text "事实、决策或测试结果。" --title "简短标题" --tag work --project-path "$PWD"
printf '%s\n' "多行工作记录" | memoria ingest stdin --title "工作记录" --tag work
memoria sleep --mock
memoria issue list --json
memoria issue search "keyword" --json
memoria sleep list --json
memoria patch list --json
```

需要更多参数、配置和排障步骤时，加载对应 reference，不要凭记忆补命令。
