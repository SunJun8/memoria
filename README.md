# Memoria

Memoria is a local-first LLM-driven memory system.

The first version provides a CLI for ingesting raw memory, running sleep consolidation, querying memory issues/chains/proposals, and creating local backups.

## MVP CLI

```bash
memoria ingest text "Build a local memory system" --title "Memoria MVP"
memoria sleep --mock
memoria issue list --json
memoria chain list --json
memoria proposed list --json
memoria backup create --git
```

Use `memoria sleep --mock` for deterministic offline testing. Use `memoria sleep`
without `--mock` only after setting `OPENAI_API_KEY`.

## OpenAI

Set `OPENAI_API_KEY` to let the OpenAI provider run live. If no key is present, tests use an explicit mock fallback unless `MEMORIA_REQUIRE_OPENAI_LIVE=1` is set.

The first provider uses the OpenAI Python SDK directly. LangChain/LangGraph are intentionally not part of the MVP core path.
