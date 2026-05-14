# Memoria

<p align="center">
  <img src="docs/assets/memoria-hero.png" alt="Memoria turns raw work context into structured local memory" width="860">
</p>

<p align="center">
  <strong>Local memory for long-running agents.</strong>
</p>

<p align="center">
  把零散上下文沉淀成可检索、可审计、可持续更新的工作记忆。
</p>

<p align="center">
  <a href="https://pypi.org/project/memoria-cli/"><img src="https://img.shields.io/pypi/v/memoria-cli.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/memoria-cli/"><img src="https://img.shields.io/pypi/pyversions/memoria-cli.svg" alt="Python versions"></a>
  <a href="https://github.com/SunJun8/memoria/actions/workflows/ci.yml"><img src="https://github.com/SunJun8/memoria/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/SunJun8/memoria/actions/workflows/release.yml"><img src="https://github.com/SunJun8/memoria/actions/workflows/release.yml/badge.svg" alt="Release"></a>
  <a href="https://github.com/SunJun8/memoria/stargazers"><img src="https://img.shields.io/github/stars/SunJun8/memoria?style=social" alt="GitHub stars"></a>
  <a href="https://github.com/SunJun8/memoria/releases"><img src="https://img.shields.io/github/downloads/SunJun8/memoria/total.svg?maxAge=2592001" alt="Downloads"></a>
</p>

Memoria 是一个本地优先、由 LLM 驱动的工作记忆归档器。它把原始笔记、任务上下文、项目决策和 Agent 工作记录整理成 Memory Issue、Memory Chain、Proposal 和可审计的 Patch。

当前版本以 CLI 为主，数据默认保存在本机 SQLite 和 JSONL transcript 中；`sleep` 整理流程可以离线 mock，也可以调用 OpenAI Responses API。

## 安装

推荐使用 `uv tool install`。`uv` 会自动创建隔离环境，不绑定当前项目目录或 shell 里的虚拟环境：

```bash
uv tool install memoria-cli
memoria --help
```

也可以使用 pip；这种方式要求当前 Python 环境已经是 3.11 及以上：

```bash
python -m pip install memoria-cli
memoria --help
```

或者从 [GitHub Releases](https://github.com/SunJun8/memoria/releases) 下载单文件二进制，不需要预装 Python。

## 快速开始

```bash
memoria ingest text "今天决定：Memoria MVP 先做本地 CLI，不做 Web UI。" \
  --title "Memoria MVP direction" \
  --tag memoria \
  --hint "整理成项目决策"

memoria sleep --mock
memoria issue list --json
```

使用真实 LLM 整理：

```bash
export OPENAI_API_KEY="..."
memoria sleep --limit 20 --strictness balanced
```

## 文档

完整文档入口见 [docs/README.md](docs/README.md)。

| 中文 | English |
| --- | --- |
| [安装](docs/zh-CN/installation.md) | [Installation](docs/en/installation.md) |
| [快速开始](docs/zh-CN/quickstart.md) | [Quick Start](docs/en/quickstart.md) |
| [配置](docs/zh-CN/configuration.md) | [Configuration](docs/en/configuration.md) |
| [CLI 使用说明](docs/zh-CN/cli.md) | [CLI Guide](docs/en/cli.md) |
| [设计边界](docs/zh-CN/design.md) | [Design Notes](docs/en/design.md) |
| [开发者说明](docs/zh-CN/development.md) | [Development](docs/en/development.md) |

## 特性

- Local-first storage with SQLite, JSONL transcripts, zip backups, and local Git backups.
- Raw text, file, and stdin ingestion.
- LLM sleep consolidation with deterministic mock mode and OpenAI mode.
- Tool-assisted memory lookup during LLM consolidation.
- Transactional `MemoryPatch` application with patch audit records.
- Query commands for Memory Issue, Chain, Proposal, Patch, and Sleep jobs.
- Optional single-file binaries for Linux, macOS, and Windows.

## 状态

Memoria is early alpha software. The current scope is intentionally narrow: local CLI first, no Web UI, no API server, no MCP server, no cloud sync, and no destructive memory deletion.

Memoria 仍处于 early alpha 阶段。当前范围刻意保持克制：本地 CLI 优先，没有 Web UI、API server、MCP server、云同步，也没有破坏性删除记忆。

## 开发

```bash
python -m pip install -e ".[dev]"
pytest -q
uv build
```

See [Development](docs/en/development.md) or [开发者说明](docs/zh-CN/development.md) for the full workflow.
