# Design Notes

## Data and LLM job records

Memoria stores two categories of data:

- **Structured data**: raw entries, issues, chains, proposals, patch records, and LLM jobs in SQLite.
- **Full LLM transcripts**: local JSONL files, stored in the jobs directory by default.

Transcripts make the LLM consolidation process replayable, auditable, and debuggable. Retention and disable controls can be added later.

## Current boundaries

The current version keeps a narrow set of boundaries:

- Local by default: SQLite database, transcripts, and backups stay on the machine.
- No Web UI, API server, or MCP server.
- No natural-language question answering entry point. External agents such as Codex and Claude Code can later access the system through a CLI or API.
- The LLM provider uses the OpenAI Python SDK directly. Memoria does not introduce LangChain or LangGraph.
- No destructive memory deletion. Older memories can be corrected, supplemented, or de-emphasized by newer memories.
- Git is used only as a local backup mechanism and does not push.

## Concepts

Memoria uses a few cognitive metaphors:

- **Raw memory**: Original content submitted by a user or external agent. It is preserved as completely as possible by default.
- **Memory Issue**: A task, problem, or long-running topic, similar to a Jira issue, with title, status, tags, summary, and comments.
- **Memory Chain**: A thought or association chain organized by the LLM. It can be merged, adjusted, and reorganized over time.
- **Sleep consolidation**: The system calls an LLM to extract, summarize, link, and update state from pending raw memories.
- **Active association**: A future extension where the LLM actively retrieves related issues and chains to discover new links.

## Current MVP scope

Included:

- Local CLI.
- SQLite + initial Alembic migration.
- Raw text, file, and stdin ingestion.
- Direct OpenAI SDK provider.
- Mock LLM provider.
- LLM tool loop.
- `MemoryPatch` schema and transactional patch application.
- Issue, Chain, Proposal, Patch, and Sleep query commands.
- LLM job transcript JSONL.
- Zip backup, local Git backup, and Git commit restore.

Not included:

- Web UI.
- API server.
- MCP server.
- Automatic Codex / Claude Code history import.
- Natural-language question answering.
- Authorization system.
- Git push or cloud sync.
