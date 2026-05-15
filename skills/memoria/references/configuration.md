# Memoria 安装与配置

## Install

Memoria 发布包名是 `memoria-cli`，安装后的命令是 `memoria`。

推荐隔离安装：

```bash
uv tool install memoria-cli
memoria --help
```

pip 安装要求 Python 3.11 或更高：

```bash
python -m pip install memoria-cli
memoria --help
```

二进制发布包可直接运行：

```bash
chmod +x memoria-linux-x86_64
./memoria-linux-x86_64 --help
```

如果使用 `backup create --git`，或依赖 sleep 后默认 Git 备份，系统仍需要安装 `git`。

## Local Source Checkout

在 Memoria 源码仓库内，优先用当前源码运行：

```bash
uv run memoria --help
uv run memoria --version
uv run pytest -q
```

这能避免误用全局已安装的旧版本。

## Default Paths

Memoria 默认遵循 XDG 路径：

| 内容 | 默认路径 |
| --- | --- |
| 配置文件 | `$XDG_CONFIG_HOME/memoria/config.toml`，通常是 `~/.config/memoria/config.toml` |
| SQLite 数据库 | `$XDG_DATA_HOME/memoria/memoria.db`，通常是 `~/.local/share/memoria/memoria.db` |
| LLM job transcript | `$XDG_DATA_HOME/memoria/jobs/` |
| 本地 Git 备份仓库 | `$XDG_DATA_HOME/memoria/backups/git/` |
| 日志目录 | `$XDG_STATE_HOME/memoria/logs/`，通常是 `~/.local/state/memoria/logs/` |

环境变量 `XDG_CONFIG_HOME`、`XDG_DATA_HOME`、`XDG_STATE_HOME` 会影响这些默认路径。

## OpenAI Config

推荐创建配置文件：

```bash
mkdir -p ~/.config/memoria
$EDITOR ~/.config/memoria/config.toml
```

使用环境变量保存 key：

```toml
[openai]
model = "gpt-5.5"
api_key_env = "OPENAI_API_KEY"
reasoning_effort = "medium"
reasoning_summary = "auto"
```

然后在 shell 中设置：

```bash
export OPENAI_API_KEY="..."
```

也可以把 key 写入本地配置文件，但不要把该文件提交到仓库：

```toml
[openai]
model = "gpt-5.5"
api_key = "<your-api-key>"
base_url = "https://api.openai.com/v1"
reasoning_effort = "medium"
reasoning_summary = "auto"
```

字段：

- `model`：OpenAI 模型名，默认 `gpt-5.1`。
- `base_url`：OpenAI 或兼容 OpenAI API 服务地址；官方 OpenAI 可省略。
- `reasoning_effort`：推理强度，例如 `low`、`medium`、`high`。
- `reasoning_summary`：reasoning summary 设置，默认 `auto`。
- `api_key`：直接写在本地配置文件里的 API key。
- `api_key_env`：从哪个环境变量读取 API key，默认 `OPENAI_API_KEY`。

`api_key_env` 必须是环境变量名，不是实际 API key。传入 `sk-...` 形式会被拒绝。

## Environment Overrides

可用环境变量：

```bash
export MEMORIA_CONFIG=/path/to/config.toml
export MEMORIA_DB_PATH=/path/to/memoria.db
export MEMORIA_JOBS_DIR=/path/to/jobs
export MEMORIA_BACKUP_GIT_REPO=/path/to/backup-git
export MEMORIA_LLM_MODEL=gpt-5.1
export MEMORIA_REASONING_EFFORT=high
export MEMORIA_REASONING_SUMMARY=auto
export MEMORIA_OPENAI_BASE_URL=https://openai-compatible.example/v1
export MEMORIA_OPENAI_API_KEY_ENV=OPENAI_API_KEY
```

隔离测试时，建议同时覆盖数据库、jobs 和备份仓库：

```bash
export MEMORIA_DB_PATH=/tmp/memoria-test/memoria.db
export MEMORIA_JOBS_DIR=/tmp/memoria-test/jobs
export MEMORIA_BACKUP_GIT_REPO=/tmp/memoria-test/backups/git
memoria sleep --mock
```

## Real Sleep Requirements

运行真实 `memoria sleep` 需要：

- 可用的 OpenAI API key，来自 `[openai].api_key` 或 `api_key_env` 指向的环境变量。
- 网络可访问 `base_url`。
- 模型支持 Responses API 和结构化输出。
- 如果启用默认 Git 备份，系统有 `git`。

缺 key 时，CLI 会报：

```text
OPENAI_API_KEY is required unless --mock is used.
```

如果只是验证 Memoria 流程，改用：

```bash
memoria sleep --mock
```

## JSON Output

供 agent 读取、比较或进一步处理的查询命令应加 `--json`：

```bash
memoria issue list --json
memoria chain list --json
memoria proposed list --json
memoria patch list --json
memoria sleep list --json
```

`ingest` 和 `sleep` 的主命令本身会输出简短 JSON，例如 `{"raw_entry_id": 1}`、`{"job_id": 1}`。

## Version and Help

检查当前命令：

```bash
memoria --version
memoria --help
memoria ingest --help
memoria sleep --help
memoria issue --help
```

当文档和本地命令冲突时，以本地 `--help` 为准。
