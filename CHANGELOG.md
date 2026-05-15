# Changelog

## 0.1.5 - 2026-05-15

### 修复

- 修复 `memoria sleep` 在 LLM 返回 `create_sleep_report` 操作时因为缺少 `job_id` 导致提交失败的问题。
- 为 LLM 生成的 sleep report 操作自动注入当前 job id。
- 避免 LLM 已创建 sleep report 时服务层重复写入报告。

### 验证

- `pytest`
- `compileall`
- wheel 安装 smoke test
