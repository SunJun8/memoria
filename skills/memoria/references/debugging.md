# Memoria 调试与内部流程

## First Checks

先确认命令、版本和路径：

```bash
memoria --version
memoria --help
memoria sleep --mock
```

在源码仓库内用：

```bash
uv run memoria --version
uv run memoria sleep --mock
uv run pytest -q
```

如果问题只在真实 LLM 模式出现，先用 `--mock` 分离 CLI/DB 问题和 OpenAI/provider 问题。

## Missing API Key

真实 `memoria sleep` 没有 key 时会失败：

```text
OPENAI_API_KEY is required unless --mock is used.
```

处理方式：

```bash
export OPENAI_API_KEY="..."
memoria sleep --limit 20 --strictness balanced
```

或在配置文件中指定：

```toml
[openai]
model = "gpt-5.1"
api_key_env = "OPENAI_API_KEY"
```

如果只是做流程检查，不要配置 key，直接运行：

```bash
memoria sleep --mock
```

## Inspect Sleep Jobs

查询最近 job：

```bash
memoria sleep list --json
memoria sleep show <job-id> --json
```

重点看：

- job 状态是否成功或失败。
- model、strictness、provider 是否符合预期。
- 是否有关联 patch id。
- 失败时的 error 字段。

## Inspect Patches

```bash
memoria patch list --json
memoria patch show <patch-id> --json
```

重点看：

- `before` / `after` 摘要。
- operations 里创建或更新了哪些 issue、chain、proposal。
- refs 里是否包含 raw entry id。
- 是否执行了 raw processed 标记。

所有 LLM 写入应经过 `MemoryPatch`，再由 `PatchService` 事务性应用。排查“为什么出现这条记忆”时，patch record 是主要审计入口。

## Raw Entry Tracking

当前 CLI 没有 `raw list`。不要使用或建议不存在的命令。

追踪 raw entry：

1. 从 `memoria ingest ...` 输出记录 `raw_entry_id`。
2. 运行 sleep 后记下 `job_id`。
3. `memoria sleep show <job-id> --json` 查看 job 摘要。
4. `memoria patch show <patch-id> --json` 查看 patch refs 和 operations。
5. 如果仍不清楚，查看 transcript JSONL。

## Transcript Files

LLM job transcript 默认在：

```text
$XDG_DATA_HOME/memoria/jobs/
```

通常是：

```text
~/.local/share/memoria/jobs/
```

如果设置了环境变量：

```bash
echo "$MEMORIA_JOBS_DIR"
```

transcript events 可能包括：

- `request`
- `response`
- `tool_call`
- `tool_result`
- `patch`

查看 transcript 时只摘取必要字段，不要把大型 JSON 全量贴给用户。

## Internal Sleep Flow

源码关键类：

- `src/memoria/application/services/sleep_service.py`
- `src/memoria/application/services/llm_tool_service.py`
- `src/memoria/infrastructure/llm/openai_provider.py`
- `src/memoria/application/services/patch_service.py`
- `src/memoria/infrastructure/transcript/jsonl_store.py`

流程：

1. `SleepService.run(limit, strictness)` 创建 `LLMJob`。
2. `_run_and_commit_job()` 调用 `LLMToolService.get_system_state(limit)` 读取 pending raw entries。
3. provider 执行 memory job。
4. transcript store 写入 LLM 交互事件。
5. `PatchService.apply_patch_in_session()` 事务性应用 `MemoryPatch`。
6. job 记录 patch id、完成状态和 transcript 路径。
7. 成功后执行 after-success hook，默认创建本地 Git backup。

失败时，`SleepService._mark_failed()` 会把 job 标记为 failed 并记录错误。

## OpenAI Tool-Call Flow

`OpenAIProvider.run_memory_job()` 使用 OpenAI Responses API，并暴露严格 function tools：

- `list_issues(limit, status)`
- `search_issues(query, limit)`
- `get_issue(issue_id)`
- `list_chains(limit)`

约束：

- tool limit 最大 100。
- 只允许上述工具名。
- 每个 function call 都由本地 `LLMToolService` 执行只读查询。
- provider 追加 `function_call_output` 并循环，直到没有 tool calls。
- 默认最大 tool rounds 是 8。
- 最终响应必须能验证为严格 `MemoryPatch`。

如果 tool-call 循环异常，检查：

- transcript 里的 `tool_call` / `tool_result` 是否成对。
- provider 返回是否超过 tool rounds。
- 最终 output 是否是 JSON 且符合 `MemoryPatch` schema。

## Common Problems

### `memoria` 命令不存在

检查是否安装：

```bash
uv tool install memoria-cli
memoria --help
```

源码仓库内可直接：

```bash
uv run memoria --help
```

### 查询不到刚导入的内容

`ingest` 只创建 raw entry，不会立刻生成 issue。需要运行：

```bash
memoria sleep --mock
memoria issue list --json
```

如果使用 mock，生成内容可能是确定性测试结构，不代表真实 LLM 整理质量。

### `issue list` 没有 raw 内容

正常。`issue list` 展示整理后的 Memory Issues，不是 raw entries。看 raw 消费情况请查 patch / sleep / transcript。

### sleep 成功但 Git 备份失败

检查系统是否有 `git`，以及 `MEMORIA_BACKUP_GIT_REPO` 路径是否可写。可以手动创建 zip 备份：

```bash
memoria backup create ./memoria-backup.zip
```

### JSON 太大

先用 list 找 id，再 show 单个对象：

```bash
memoria issue list --json
memoria issue show <id> --json
```

向用户汇报时总结关键字段，不要贴完整 transcript。

## Code-Level Debugging

在源码仓库中：

```bash
uv run pytest -q
uv run pytest tests/test_cli.py -q
uv run pytest tests/test_openai_provider.py -q
uv run pytest tests/test_llm_worker_mock.py -q
```

定位建议：

- CLI 参数问题：看 `src/memoria/interfaces/cli/commands/`。
- 配置/路径问题：看 `src/memoria/config.py`。
- OpenAI 请求和 tool loop：看 `openai_provider.py`。
- patch 应用和审计：看 `patch_service.py`。
- 查询结果：看 `query_service.py`。

修改 Python 代码时按项目要求优先用 LSP 导航定义和引用。
