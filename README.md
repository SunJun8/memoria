# Memoria

Memoria 是一个本地优先、由 LLM 驱动的工作记忆归档器。

它的核心目标不是做一个聊天机器人，而是把日常输入的原始信息整理成可长期保存、可被 Agent 检索和更新的结构化记忆。当前 MVP 以 CLI 为主，支持导入原始记忆、运行“睡眠整理”、查询 Memory Issue / Chain / Proposal，并把数据库和 LLM 作业 transcript 保存在本地。

## 背景

人在工作和生活中会不断接收碎片信息：任务、问题、决策、调试过程、项目上下文、临时想法、生活流水账。这些信息如果只留在聊天记录、终端历史或笔记里，后续很难被系统性地回忆和串联。

Memoria 的设计借用了几个认知隐喻：

- **原始记忆**：用户或外部 Agent 直接丢进来的原始内容，默认尽量完整保留。
- **Memory Issue**：表示一个任务、问题或持续关注的主题，类似 Jira issue，有标题、状态、标签、摘要和评论。
- **Memory Chain**：表示一条思维链或关联链，由 LLM 自主组织，可随时间合并、调整、重组。
- **睡眠整理**：系统主动调用 LLM，对待处理的原始记忆做抽取、归纳、链接和状态更新。
- **主动联想**：后续可以扩展为由 LLM 主动检索相关 issue / chain，发现新的关联。

当前版本坚持几个边界：

- 默认全本地：SQLite 数据库、transcript、备份都在本机。
- 不做 Web UI、API server、MCP server。
- 不提供自然语言问答入口；Codex、Claude Code 等外部 Agent 后续通过 CLI/API 访问。
- LLM provider 直接使用 OpenAI Python SDK，不引入 LangChain / LangGraph。
- 不支持删除记忆；旧记忆可以被新记忆纠正、补充或降权。
- Git 只作为本地备份机制，不 push。

## Quickstart

### 1. 安装开发环境

```bash
cd /home/miot/Work/memoria
python -m pip install -e ".[dev]"
```

如果只想在源码目录直接运行，也可以使用：

```bash
PYTHONPATH=src python -m memoria.interfaces.cli.app --help
```

### 2. 导入一条原始记忆

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

### 3. 离线运行一次睡眠整理

```bash
memoria sleep --mock
```

`--mock` 使用确定性的本地 mock provider，适合测试 CLI 流程，不会调用 OpenAI。

返回示例：

```json
{"job_id": 1}
```

### 4. 查看整理出的记忆

```bash
memoria issue list --json
memoria issue show 1 --json
memoria chain list --json
memoria sleep list --json
```

### 5. 使用 OpenAI 运行真实整理

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

## 配置

Memoria 默认遵循 XDG 路径：

| 配置项 | 默认路径 |
| --- | --- |
| 配置文件 | `$XDG_CONFIG_HOME/memoria/config.toml` |
| SQLite 数据库 | `$XDG_DATA_HOME/memoria/memoria.db` |
| LLM job transcript | `$XDG_DATA_HOME/memoria/jobs/` |
| Git 备份仓库 | `$XDG_DATA_HOME/memoria/backups/git/` |
| 日志目录 | `$XDG_STATE_HOME/memoria/logs/` |

建议创建配置文件：

```bash
mkdir -p ~/.config/memoria
$EDITOR ~/.config/memoria/config.toml
```

OpenAI 配置示例：

```toml
[openai]
model = "gpt-5.1"
base_url = "https://api.openai.com/v1"
reasoning_effort = "medium"
reasoning_summary = "auto"
api_key_env = "OPENAI_API_KEY"
```

字段说明：

- `model`：OpenAI 模型名。
- `base_url`：OpenAI 或兼容 OpenAI API 的服务地址；使用官方 OpenAI 时可不填。
- `reasoning_effort`：推理强度，例如 `low`、`medium`、`high`。
- `reasoning_summary`：reasoning summary 设置，默认 `auto`。
- `api_key_env`：读取 API key 的环境变量名，默认 `OPENAI_API_KEY`。

API key 仍建议放在环境变量或系统密钥管理里，不建议明文写进配置文件：

```bash
export OPENAI_API_KEY=...
```

OpenAI live test 默认不会强制执行。只有设置下面变量时，测试才要求真实调用 OpenAI：

```bash
export MEMORIA_REQUIRE_OPENAI_LIVE=1
```

环境变量仍可作为临时覆盖：

```bash
export MEMORIA_CONFIG=/path/to/config.toml
export MEMORIA_DB_PATH=/path/to/memoria.db
export MEMORIA_JOBS_DIR=/path/to/jobs
export MEMORIA_BACKUP_GIT_REPO=/path/to/backup-git
export MEMORIA_LLM_MODEL=gpt-5.1
export MEMORIA_REASONING_EFFORT=high
export MEMORIA_REASONING_SUMMARY=auto
export MEMORIA_OPENAI_BASE_URL=https://openai-compatible.example/v1
```

## 使用说明

### 导入原始记忆

导入文本：

```bash
memoria ingest text "原始内容" --title "可选标题" --tag work --tag memoria --hint "给 LLM 的整理提示"
```

导入文件：

```bash
memoria ingest file ./note.md --title "会议记录" --tag meeting
```

从 stdin 导入：

```bash
cat ./note.md | memoria ingest stdin --title "stdin 导入"
```

可选参数：

- `--title`：原始内容标题。
- `--tag`：可重复使用。
- `--hint`：给整理 LLM 的提示。
- `--project-path`：记录相关项目路径。

### 睡眠整理

离线 mock：

```bash
memoria sleep --mock
```

真实 OpenAI：

```bash
memoria sleep --limit 20 --strictness balanced
```

参数：

- `--mock`：使用 mock provider。
- `--limit`：本轮最多读取多少条 pending raw entries。
- `--strictness`：整理策略，当前常用值为 `strict`、`balanced`、`creative`。

查询 sleep job：

```bash
memoria sleep list --json
memoria sleep show 1 --json
```

### 查询 Memory Issue

```bash
memoria issue list --json
memoria issue list --status open --json
memoria issue show 1 --json
memoria issue search "OpenAI" --json
```

Issue 表示一个任务、问题或持续关注的主题。它是当前系统里最接近“人的主观记忆事项”的核心对象。

### 查询 Memory Chain

```bash
memoria chain list --json
memoria chain show 1 --json
memoria chain search "Memoria" --json
```

Chain 是 LLM 整理出的关联链。一个 issue 可以出现在多个 chain 中；chain 不是不可变事实，而是可被 LLM 持续重组的思维结构。

### 查询和处理 Proposal

```bash
memoria proposed list --json
memoria proposed show 1 --json
memoria proposed accept 1 --json
memoria proposed reject 1 --json
```

Proposal 用来表达 LLM 不确定、需要保留为候选的结构化变更，例如链路关联、合并建议等。

### 查看 Patch 审计

```bash
memoria patch list --json
memoria patch show 1 --json
```

所有 LLM 写入都必须先形成 `MemoryPatch`，再由 patch service 事务性应用。Patch record 会保存 before / after 摘要，便于审计。

### 备份和恢复

创建 zip 备份：

```bash
memoria backup create ./memoria-backup.zip
```

恢复 zip 到当前配置路径：

```bash
memoria backup restore ./memoria-backup.zip
```

恢复 zip 到指定目录：

```bash
memoria backup restore ./memoria-backup.zip ./restore-dir
```

创建本地 Git 备份 commit：

```bash
memoria backup create --git
```

从本地 Git 备份 commit 恢复：

```bash
memoria backup restore-git <commit-sha>
```

`memoria sleep` 成功完成后会默认触发一次本地 Git backup。当前不会 push 到远端。

## 数据和 LLM 作业记录

Memoria 会保存两类数据：

- **结构化数据**：SQLite 中的 raw entries、issues、chains、proposals、patch records、LLM jobs。
- **完整 LLM transcript**：本地 JSONL 文件，默认保存在 jobs 目录。

保存 transcript 的目的是让 LLM 整理过程可回放、可审计、可调试。后续可以增加保留天数和关闭开关。

## 开发和验证

运行测试：

```bash
pytest -v
```

编译检查：

```bash
python -m compileall -q src tests
```

检查 git diff 空白问题：

```bash
git diff --check
```

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
