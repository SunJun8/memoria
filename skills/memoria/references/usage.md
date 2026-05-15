# Memoria CLI 使用手册

## Command Prefix

选择命令前缀：

- 在 Memoria 源码仓库内测试当前工作树：`uv run memoria ...`
- 使用已安装的发布版：`memoria ...`
- 如果用户给了具体二进制路径：`/path/to/memoria ...`

下文用 `memoria` 表示命令本体；在源码仓库中执行时可替换为 `uv run memoria`。

## Core Workflow

标准工作流：

1. `ingest` 记录 raw entry。
2. `sleep` 整理 raw entry，生成结构化 memory。
3. `issue` / `chain` / `proposed` 查询结果。
4. `patch` / `sleep show` 审计本轮 LLM 写入。
5. 必要时 `backup` 创建或恢复本地备份。

对于 agent 工作交接，优先记录“未来 agent 需要知道什么”，而不是完整聊天记录。

## Record Memory

### 何时记录

应该记录：

- 项目决策：选择了什么方案，为什么。
- 已验证事实：命令输出、测试结果、版本、路径、环境约束。
- 工作状态：已完成、未完成、阻塞原因、下一步。
- 调试结论：根因、排除过的假设、复现方式。
- 用户偏好：只记录与当前项目/工具使用相关且用户明确表达的偏好。

不要记录：

- API key、token、密码、私钥、cookie、会话凭据。
- 未脱敏个人敏感信息。
- 大段日志或完整 diff；记录摘要和定位路径即可。
- 没有验证的猜测，除非明确标为“待验证假设”。

### 记录短文本

```bash
memoria ingest text "今天决定：Memoria MVP 先做本地 CLI，不做 Web UI。测试命令 pytest -q 已通过。" \
  --title "Memoria MVP direction" \
  --tag memoria \
  --tag decision \
  --hint "整理成项目决策和测试结果" \
  --project-path "$PWD"
```

参数含义：

- `CONTENT`：必填，原始内容。
- `--title`：短标题，方便后续审计 raw 来源。
- `--tag`：可重复。建议使用项目名、主题、类型，例如 `memoria`、`decision`、`debugging`。
- `--hint`：给整理 LLM 的提示，说明希望如何归档。
- `--project-path`：关联项目路径。项目工作记录建议总是传 `$PWD`。

返回通常包含：

```json
{"raw_entry_id": 1}
```

### 记录文件

适合导入会议纪要、调试日志摘要、设计文档片段。

```bash
memoria ingest file ./note.md \
  --title "会议记录" \
  --tag meeting \
  --project-path "$PWD"
```

不要导入包含 secret 的原始日志。先脱敏，再导入。

### 通过 stdin 记录长内容

长内容优先使用 stdin，避免 shell quoting 出错。

```bash
printf '%s\n' "多行工作记录" | memoria ingest stdin \
  --title "工作记录" \
  --tag work \
  --hint "整理成进度、决策和下一步" \
  --project-path "$PWD"
```

从文件管道导入：

```bash
cat ./note.md | memoria ingest stdin --title "stdin 导入" --tag work
```

## Consolidate

`sleep` 会读取 pending raw entries，调用 mock provider 或 OpenAI provider，生成 `MemoryPatch`，事务性应用 patch，并写入 sleep job / transcript。

### 冒烟测试和离线整理

```bash
memoria sleep --mock
```

`--mock` 不调用 OpenAI，适合：

- 检查 CLI 和数据库是否可用。
- 测试 ingest -> sleep -> query 流程。
- 在没有 API key 时演示。
- 避免真实 LLM 费用或网络依赖。

### 真实 OpenAI 整理

仅在用户明确要求或环境已经配置 key 时运行：

```bash
memoria sleep --limit 20 --strictness balanced
```

常用参数：

- `--limit INTEGER`：本轮最多读取多少条 pending raw entries；默认 20。
- `--strictness TEXT`：整理策略，常用 `strict`、`balanced`、`creative`；默认 `balanced`。
- `--mock`：使用本地 mock provider。

建议：

- 重要工作记录先用 `--mock` 冒烟，再运行真实 sleep。
- 批量整理时使用较小 `--limit`，便于审计。
- 输出 `{"job_id": N}` 后，用 `sleep show` 和 `patch list` 查看本轮结果。

## Query

给 agent 继续处理时，使用 `--json`。给人快速看时，可省略 `--json`。

### Issue

Memory Issue 是任务、问题、决策或持续关注主题，是最接近“记忆事项”的核心对象。

```bash
memoria issue list --json
memoria issue list --status open --json
memoria issue show 1 --json
memoria issue search "OpenAI" --json
```

使用建议：

- 查“有没有相关记忆”：先 `issue search "关键词" --json`。
- 查当前上下文：`issue list --status open --json`。
- 需要完整细节：`issue show <id> --json`。

### Chain

Memory Chain 是 LLM 整理出的关联链。一个 issue 可以出现在多个 chain 中；chain 是可被持续重组的结构，不是不可变事实。

```bash
memoria chain list --json
memoria chain show 1 --json
memoria chain search "Memoria" --json
```

使用建议：

- 用 chain 理解跨任务关联、长期主题、设计演进。
- 不要把 chain 当作唯一事实来源；需要回到 issue / patch 审计具体内容。

### Proposal

Proposal 表示 LLM 不确定、需要候选保留或人工确认的结构化变更，例如关联、合并、重组建议。

```bash
memoria proposed list --json
memoria proposed show 1 --json
memoria proposed accept 1 --json
memoria proposed reject 1 --json
```

注意：

- `accept` 和 `reject` 会改变 proposal 状态。
- 如果用户只要求查看，不要执行 accept/reject。
- 接受前先 `show`，确认 proposal 内容。

### Patch

所有 LLM 写入都应形成 `MemoryPatch`，由 patch service 事务性应用。Patch record 保存 before / after 摘要，便于审计。

```bash
memoria patch list --json
memoria patch show 1 --json
```

使用建议：

- sleep 后查看最近 patch，确认创建/更新了哪些 issue、chain、proposal。
- 调试 raw entry 是否被处理时，看 patch 里是否包含 mark-raw-processed 类操作或相关 refs。

### Sleep Job

```bash
memoria sleep list --json
memoria sleep show 1 --json
```

使用建议：

- `sleep list` 查最近 job 状态。
- `sleep show <job-id>` 查 provider、model、strictness、状态、错误、patch 关联等摘要。
- 如果 sleep 失败，先看 `sleep show`，再看 debugging reference。

## Raw Entries

当前 CLI 没有 `raw list` 命令。不要告诉用户运行不存在的 raw 查询命令。

需要追踪 raw-to-issue：

1. 记录 ingest 返回的 `raw_entry_id`。
2. 运行 `memoria sleep --mock` 或真实 sleep。
3. 查看 `memoria sleep show <job-id> --json`。
4. 查看 `memoria patch list --json` 和相关 `patch show`。
5. 如需更深排查，读 [debugging.md](debugging.md) 查看 transcript 和内部流程。

## Backup

### 创建 zip 备份

```bash
memoria backup create ./memoria-backup.zip
```

### 创建本地 Git 备份

```bash
memoria backup create --git
```

`memoria sleep` 成功后默认会触发本地 Git backup。机器上需要有 `git` 命令。

### 恢复备份

恢复会改动本地 Memoria 数据。除非用户明确要求，不要执行。

```bash
memoria backup restore ./memoria-backup.zip
memoria backup restore ./memoria-backup.zip ./restore-dir
memoria backup restore-git <commit-sha>
```

建议：

- 恢复到指定目录比覆盖当前配置路径更安全。
- 恢复前先确认当前 `MEMORIA_DB_PATH`、`MEMORIA_JOBS_DIR` 和备份来源。

## Common Recipes

### 记录一次开发工作

```bash
memoria ingest text "完成 X：修改 A/B 文件；pytest -q 通过；下一步处理 Y。" \
  --title "X implementation status" \
  --tag work \
  --tag project-name \
  --hint "整理成开发进度、验证结果和下一步" \
  --project-path "$PWD"
memoria sleep --mock
memoria issue list --json
```

### 查询某个项目的记忆

```bash
memoria issue search "project-name" --json
memoria chain search "project-name" --json
```

如果项目名不稳定，也搜索关键路径、模块名、功能名。

### 整理真实记忆并审计

```bash
memoria sleep --limit 20 --strictness balanced
memoria sleep list --json
memoria patch list --json
```

拿到最近 job / patch id 后：

```bash
memoria sleep show <job-id> --json
memoria patch show <patch-id> --json
```

### 只检查工具是否可用

```bash
memoria --version
memoria --help
memoria sleep --mock
```

如果 `sleep --mock` 失败，通常是数据库路径、权限、迁移或安装问题；读 [debugging.md](debugging.md)。

## Output Discipline

向用户汇报时，不要粘贴大型 JSON。总结：

- 创建了哪个 raw entry / sleep job。
- 生成或更新了哪些 issue / chain / proposal。
- 是否有失败和错误消息。
- 下一步建议。

如果用户要求原始输出，再给关键片段或说明命令可复现。
