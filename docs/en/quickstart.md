# Quick Start

## 1. Ingest a raw memory

```bash
memoria ingest text "Today we discussed the Memoria MVP: start with a local CLI, no Web UI, and use the OpenAI SDK directly." \
  --title "Memoria MVP direction" \
  --tag memoria \
  --hint "Summarize this as a project decision"
```

Example response:

```json
{"raw_entry_id": 1}
```

## 2. Run offline sleep consolidation

```bash
memoria sleep --mock
```

`--mock` uses a deterministic local mock provider. It is useful for testing the CLI flow and does not call OpenAI.

Example response:

```json
{"job_id": 1}
```

## 3. Inspect the consolidated memory

```bash
memoria issue list --json
memoria issue show 1 --json
memoria chain list --json
memoria sleep list --json
```

## 4. Run real OpenAI consolidation

```bash
export OPENAI_API_KEY="..."
memoria sleep --limit 20 --strictness balanced
```

Real consolidation will:

- Read pending raw entries.
- Call the OpenAI Responses API.
- Allow the LLM to retrieve existing issues and chains through read-only tools.
- Return a structured `MemoryPatch`.
- Apply the patch transactionally.
- Write the LLM job transcript as JSONL.
- Create a local Git backup after success.
