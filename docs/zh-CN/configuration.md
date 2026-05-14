# 配置

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
