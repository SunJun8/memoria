# 安装

Memoria 当前版本支持 Python 3.11 及以上。

## uv tool install

推荐使用 `uv tool install`。`uv` 会为命令行工具创建隔离环境，不绑定当前项目目录或当前 shell 里的虚拟环境：

```bash
uv tool install memoria-cli
memoria --help
```

## pip

也可以使用 pip 安装；这种方式要求当前 Python 环境已经是 3.11 及以上：

```bash
python -m pip install memoria-cli
memoria --help
```

## 二进制发布包

如果使用二进制发布包，可以从 [GitHub Releases](https://github.com/SunJun8/memoria/releases) 下载对应平台的 `memoria` 可执行文件后直接运行，不需要预装 Python：

```bash
chmod +x memoria-linux-x86_64
./memoria-linux-x86_64 --help
```

二进制文件按操作系统和 CPU 架构分别构建。当前版本的本地 Git 备份功能仍会调用系统 `git` 命令，因此使用 `memoria backup create --git` 或默认 sleep 后 Git 备份时，机器上仍需要有 `git`。
