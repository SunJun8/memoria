# Configuration

Memoria follows XDG paths by default:

| Setting | Default path |
| --- | --- |
| Config file | `$XDG_CONFIG_HOME/memoria/config.toml` |
| SQLite database | `$XDG_DATA_HOME/memoria/memoria.db` |
| LLM job transcripts | `$XDG_DATA_HOME/memoria/jobs/` |
| Git backup repository | `$XDG_DATA_HOME/memoria/backups/git/` |
| Log directory | `$XDG_STATE_HOME/memoria/logs/` |

Create a config file:

```bash
mkdir -p ~/.config/memoria
$EDITOR ~/.config/memoria/config.toml
```

OpenAI config example:

```toml
[openai]
model = "gpt-5.1"
base_url = "https://api.openai.com/v1"
reasoning_effort = "medium"
reasoning_summary = "auto"
api_key = "<your-api-key>"
```

Fields:

- `model`: OpenAI model name.
- `base_url`: OpenAI or OpenAI-compatible API base URL. It can be omitted when using the official OpenAI API.
- `reasoning_effort`: Reasoning effort, for example `low`, `medium`, or `high`.
- `reasoning_summary`: Reasoning summary setting. Defaults to `auto`.
- `api_key`: API key written directly in the local config file.
- `api_key_env`: Optional environment variable name used to read the API key. Defaults to `OPENAI_API_KEY`.

To avoid writing the key into the config file, use an environment variable:

```toml
[openai]
model = "gpt-5.1"
api_key_env = "OPENAI_API_KEY"
```

Then set `OPENAI_API_KEY` in your shell.

Environment variables can also be used as temporary overrides:

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
