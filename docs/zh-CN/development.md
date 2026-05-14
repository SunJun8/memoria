# 开发者说明

## 本地开发安装

```bash
python -m pip install -e ".[dev]"
```

源码目录直接运行：

```bash
PYTHONPATH=src python -m memoria --help
```

## 测试和检查

运行测试：

```bash
pytest -v
```

编译检查：

```bash
python -m compileall -q src tests
```

检查 git diff 空白问题：

```bash
git diff --check
```

## 打包

构建 PyPI wheel 和 sdist：

```bash
uv build
```

从本地 wheel 验证隔离安装：

```bash
uv tool install --python 3.11 dist/memoria_cli-0.1.3-py3-none-any.whl
memoria --help
```

构建 Linux x86_64 单文件二进制：

```bash
uv run --extra binary pyinstaller --onefile --name memoria-linux-x86_64 --clean src/memoria/__main__.py
```

## 发布

发布流程由 GitHub Actions 触发。创建并推送 `vX.Y.Z` tag 后，release workflow 会：

- 校验 tag 版本与 `pyproject.toml` 一致。
- 在 Python 3.11、3.12、3.13 上运行测试。
- 构建 PyPI wheel 和 sdist。
- 通过 Trusted Publisher 发布 PyPI。
- 构建 Linux、macOS、Windows 二进制。
- 创建或更新 GitHub Release 并上传二进制资产。
