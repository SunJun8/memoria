# CLI 使用说明

## 导入原始记忆

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

## 睡眠整理

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

## 查询 Memory Issue

```bash
memoria issue list --json
memoria issue list --status open --json
memoria issue show 1 --json
memoria issue search "OpenAI" --json
```

Issue 表示一个任务、问题或持续关注的主题。它是当前系统里最接近“人的主观记忆事项”的核心对象。

## 查询 Memory Chain

```bash
memoria chain list --json
memoria chain show 1 --json
memoria chain search "Memoria" --json
```

Chain 是 LLM 整理出的关联链。一个 issue 可以出现在多个 chain 中；chain 不是不可变事实，而是可被 LLM 持续重组的思维结构。

## 查询和处理 Proposal

```bash
memoria proposed list --json
memoria proposed show 1 --json
memoria proposed accept 1 --json
memoria proposed reject 1 --json
```

Proposal 用来表达 LLM 不确定、需要保留为候选的结构化变更，例如链路关联、合并建议等。

## 查看 Patch 审计

```bash
memoria patch list --json
memoria patch show 1 --json
```

所有 LLM 写入都必须先形成 `MemoryPatch`，再由 patch service 事务性应用。Patch record 会保存 before / after 摘要，便于审计。

## 备份和恢复

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
