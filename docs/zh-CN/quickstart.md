# 快速开始

## 1. 导入一条原始记忆

```bash
memoria ingest text "今天讨论了 Memoria MVP：先做本地 CLI，不做 Web UI。LLM 用 OpenAI SDK 直接实现。" \
  --title "Memoria MVP 方向" \
  --tag memoria \
  --hint "整理成项目决策"
```

返回示例：

```json
{"raw_entry_id": 1}
```

## 2. 离线运行一次睡眠整理

```bash
memoria sleep --mock
```

`--mock` 使用确定性的本地 mock provider，适合测试 CLI 流程，不会调用 OpenAI。

返回示例：

```json
{"job_id": 1}
```

## 3. 查看整理出的记忆

```bash
memoria issue list --json
memoria issue show 1 --json
memoria chain list --json
memoria sleep list --json
```

## 4. 使用 OpenAI 运行真实整理

```bash
export OPENAI_API_KEY="..."
memoria sleep --limit 20 --strictness balanced
```

真实整理会：

- 读取 pending raw entries。
- 调用 OpenAI Responses API。
- 允许 LLM 通过只读工具检索已有 issue / chain。
- 返回结构化 `MemoryPatch`。
- 事务性应用 patch。
- 写入 LLM job transcript JSONL。
- 成功后创建本地 Git backup。
