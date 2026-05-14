# Installation

Memoria currently supports Python 3.11 and newer.

## uv tool install

The recommended installation method is `uv tool install`. `uv` creates an isolated environment for the CLI, so the command is not tied to the current project directory or the active shell environment:

```bash
uv tool install memoria-cli
memoria --help
```

## pip

You can also install with pip. This requires the current Python environment to be Python 3.11 or newer:

```bash
python -m pip install memoria-cli
memoria --help
```

## Binary releases

You can download a platform-specific `memoria` executable from [GitHub Releases](https://github.com/SunJun8/memoria/releases) and run it without installing Python:

```bash
chmod +x memoria-linux-x86_64
./memoria-linux-x86_64 --help
```

Binaries are built per operating system and CPU architecture. The local Git backup feature still calls the system `git` command, so machines using `memoria backup create --git` or the default post-sleep Git backup need `git` installed.
