# Memoria

Memoria 是一个本地优先、由 LLM 驱动的工作记忆归档器。

它把日常输入的原始信息整理成可长期保存、可被 Agent 检索和更新的结构化记忆。当前 0.1.0 版本以 CLI 为主，支持导入原始记忆、运行“睡眠整理”、查询 Memory Issue / Chain / Proposal，并把 SQLite 数据库和 LLM 作业 transcript 保存在本机。

## 安装

Memoria 0.1.0 支持 Python 3.11 及以上。

推荐使用 `uv tool install`。`uv` 会为命令行工具创建隔离环境，不绑定当前项目目录或当前 shell 里的虚拟环境：

```bash
uv tool install memoria
memoria --help
```

也可以使用 pip 安装；这种方式要求当前 Python 环境已经是 3.11 及以上：

```bash
python -m pip install memoria
memoria --help
```

如果使用二进制发布包，可以下载对应平台的 `memoria` 可执行文件后直接运行，不需要预装 Python：

```bash
chmod +x memoria-linux-x86_64
./memoria-linux-x86_64 --help
```

二进制文件按操作系统和 CPU 架构分别构建。当前版本的本地 Git 备份功能仍会调用系统 `git` 命令，因此使用 `memoria backup create --git` 或默认 sleep 后 Git 备份时，机器上仍需要有 `git`。

## 快速开始

### 1. 导入一条原始记忆

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

### 2. 离线运行一次睡眠整理

```bash
memoria sleep --mock
```

`--mock` 使用确定性的本地 mock provider，适合测试 CLI 流程，不会调用 OpenAI。

返回示例：

```json
{"job_id": 1}
```

### 3. 查看整理出的记忆

```bash
memoria issue list --json
memoria issue show 1 --json
memoria chain list --json
memoria sleep list --json
```

### 4. 使用 OpenAI 运行真实整理

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
api_key = "<your-api-key>"
```

字段说明：

- `model`：OpenAI 模型名。
- `base_url`：OpenAI 或兼容 OpenAI API 的服务地址；使用官方 OpenAI 时可不填。
- `reasoning_effort`：推理强度，例如 `low`、`medium`、`high`。
- `reasoning_summary`：reasoning summary 设置，默认 `auto`。
- `api_key`：直接写在本地配置文件里的 API key。
- `api_key_env`：可选替代项，表示从哪个环境变量读取 API key，默认 `OPENAI_API_KEY`。

如果不想把 key 写进配置文件，也可以改用环境变量方式：

```toml
[openai]
model = "gpt-5.1"
api_key_env = "OPENAI_API_KEY"
```

然后在 shell 里设置 `OPENAI_API_KEY`。

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

## 设计边界

当前版本坚持几个边界：

- 默认全本地：SQLite 数据库、transcript、备份都在本机。
- 不做 Web UI、API server、MCP server。
- 不提供自然语言问答入口；Codex、Claude Code 等外部 Agent 后续通过 CLI/API 访问。
- LLM provider 直接使用 OpenAI Python SDK，不引入 LangChain / LangGraph。
- 不支持删除记忆；旧记忆可以被新记忆纠正、补充或降权。
- Git 只作为本地备份机制，不 push。

Memoria 的设计借用了几个认知隐喻：

- **原始记忆**：用户或外部 Agent 直接丢进来的原始内容，默认尽量完整保留。
- **Memory Issue**：表示一个任务、问题或持续关注的主题，类似 Jira issue，有标题、状态、标签、摘要和评论。
- **Memory Chain**：表示一条思维链或关联链，由 LLM 自主组织，可随时间合并、调整、重组。
- **睡眠整理**：系统主动调用 LLM，对待处理的原始记忆做抽取、归纳、链接和状态更新。
- **主动联想**：后续可以扩展为由 LLM 主动检索相关 issue / chain，发现新的关联。

## 开发者说明

### 本地开发安装

```bash
cd /home/miot/Work/memoria
python -m pip install -e ".[dev]"
```

源码目录直接运行：

```bash
PYTHONPATH=src python -m memoria --help
```

### 测试和检查

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

### 打包

构建 PyPI wheel 和 sdist：

```bash
uv build
```

从本地 wheel 验证隔离安装：

```bash
uv tool install --python 3.11 dist/memoria-0.1.0-py3-none-any.whl
memoria --help
```

构建 Linux x86_64 单文件二进制：

```bash
uv run --extra binary pyinstaller --onefile --name memoria-linux-x86_64 --clean src/memoria/__main__.py
```

发布到 PyPI：

```bash
uv publish dist/memoria-0.1.0-py3-none-any.whl dist/memoria-0.1.0.tar.gz
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
