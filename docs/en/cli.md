# CLI Guide

## Ingest raw memory

Ingest text:

```bash
memoria ingest text "Raw content" --title "Optional title" --tag work --tag memoria --hint "Hint for the consolidation LLM"
```

Ingest a file:

```bash
memoria ingest file ./note.md --title "Meeting notes" --tag meeting
```

Ingest from stdin:

```bash
cat ./note.md | memoria ingest stdin --title "stdin import"
```

Options:

- `--title`: Raw content title.
- `--tag`: Repeatable tag.
- `--hint`: Hint passed to the consolidation LLM.
- `--project-path`: Related project path.

## Sleep consolidation

Offline mock mode:

```bash
memoria sleep --mock
```

Real OpenAI mode:

```bash
memoria sleep --limit 20 --strictness balanced
```

Options:

- `--mock`: Use the mock provider.
- `--limit`: Maximum number of pending raw entries to process in this run.
- `--strictness`: Consolidation strategy. Common values are `strict`, `balanced`, and `creative`.

Inspect sleep jobs:

```bash
memoria sleep list --json
memoria sleep show 1 --json
```

## Query Memory Issues

```bash
memoria issue list --json
memoria issue list --status open --json
memoria issue show 1 --json
memoria issue search "OpenAI" --json
```

An issue represents a task, problem, or long-running topic. It is the core object closest to a human-level memory item in the current system.

## Query Memory Chains

```bash
memoria chain list --json
memoria chain show 1 --json
memoria chain search "Memoria" --json
```

A chain is an association path organized by the LLM. One issue can appear in multiple chains; chains are not immutable facts and can be reorganized over time.

## Query and process Proposals

```bash
memoria proposed list --json
memoria proposed show 1 --json
memoria proposed accept 1 --json
memoria proposed reject 1 --json
```

Proposals represent structured changes that the LLM is unsure about and wants to keep as candidates, such as association links or merge suggestions.

## Inspect Patch audit records

```bash
memoria patch list --json
memoria patch show 1 --json
```

All LLM writes must first become a `MemoryPatch`, then be applied transactionally by the patch service. Patch records keep before and after summaries for auditing.

## Backup and restore

Create a zip backup:

```bash
memoria backup create ./memoria-backup.zip
```

Restore a zip backup to the current configured paths:

```bash
memoria backup restore ./memoria-backup.zip
```

Restore a zip backup to a specific directory:

```bash
memoria backup restore ./memoria-backup.zip ./restore-dir
```

Create a local Git backup commit:

```bash
memoria backup create --git
```

Restore from a local Git backup commit:

```bash
memoria backup restore-git <commit-sha>
```

`memoria sleep` creates a local Git backup after a successful run by default. It does not push to a remote.
