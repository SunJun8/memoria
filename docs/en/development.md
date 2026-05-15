# Development

## Local development install

```bash
python -m pip install -e ".[dev]"
```

Run directly from the source tree:

```bash
PYTHONPATH=src python -m memoria --help
```

## Tests and checks

Run tests:

```bash
pytest -v
```

Compile check:

```bash
python -m compileall -q src tests
```

Check whitespace problems in the git diff:

```bash
git diff --check
```

## Packaging

Build the PyPI wheel and sdist:

```bash
uv build
```

Verify isolated installation from a local wheel:

```bash
uv tool install --python 3.11 dist/memoria_cli-0.1.4-py3-none-any.whl
memoria --help
```

Build a Linux x86_64 single-file binary:

```bash
uv run --extra binary pyinstaller --onefile --name memoria-linux-x86_64 --clean src/memoria/__main__.py
```

## Release

Releases are handled by GitHub Actions. After creating and pushing a `vX.Y.Z` tag, the release workflow will:

- Validate that the tag version matches `pyproject.toml`.
- Run tests on Python 3.11, 3.12, and 3.13.
- Build the PyPI wheel and sdist.
- Publish to PyPI through Trusted Publisher.
- Build Linux, macOS, and Windows binaries.
- Create or update the GitHub Release and upload binary assets.
