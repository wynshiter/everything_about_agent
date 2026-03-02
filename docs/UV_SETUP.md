# UV 环境配置指南

> 本指南介绍如何使用 [UV](https://github.com/astral-sh/uv) 作为 Python 包管理器来构建项目环境，同时兼容 Conda base 环境。

---

## 什么是 UV?

[UV](https://github.com/astral-sh/uv) 是一个用 Rust 编写的极速 Python 包管理器，比 pip 快 **10-100 倍**，支持：

- ⚡ **极速安装**: 并行下载和解析依赖
- 📦 **虚拟环境管理**: 内置 venv 创建和管理
- 🔒 **可复现构建**: 支持 `uv.lock` 锁定依赖版本
- 🐍 **Python 版本管理**: 支持安装和管理多个 Python 版本
- 🔄 **Pip 兼容**: 完全兼容 pip 命令

---

## 快速开始

### 方法一: 使用启动脚本 (推荐)

**Windows:**
```bash
# 运行启动菜单，选择选项 12 初始化 UV 环境
.\start.bat

# 或者在命令行直接运行
python scripts\setup_uv.py
```

**Linux/macOS:**
```bash
# 运行启动菜单，选择选项 12 初始化 UV 环境
./start.sh

# 或者在命令行直接运行
python3 scripts/setup_uv.py
```

### 方法二: 手动配置

```bash
# 1. 安装 uv (如果尚未安装)
# Windows (PowerShell):
irm https://astral.sh/uv/install.ps1 | iex

# Linux/macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 创建虚拟环境
uv venv .venv --python 3.10

# 3. 激活环境 (Windows)
.venv\Scripts\activate

# 3. 激活环境 (Linux/macOS)
source .venv/bin/activate

# 4. 安装依赖
uv pip install -e .
```

---

## UV 与 Conda 共存

本项目设计支持与 Conda base 环境共存：

```
系统层级:
├── Conda base (python, conda 命令)
│   └── 系统全局可用
│
└── 项目层级 (.venv)
    ├── uv 管理的虚拟环境
    ├── 项目依赖 (langchain, gradio 等)
    └── 完全隔离，不影响 Conda
```

### 使用场景

| 场景 | 推荐方式 |
|------|---------|
| 日常开发 | UV (更快、更轻量) |
| 数据科学/ML | Conda (更好的 C 库支持) |
| CI/CD | UV (极速安装) |
| 多版本 Python | UV (`uv venv --python 3.11`) |

---

## 常用 UV 命令

### 环境管理

```bash
# 创建虚拟环境
uv venv .venv

# 指定 Python 版本
uv venv .venv --python 3.11

# 激活环境 (Windows)
.\activate_venv.ps1

# 激活环境 (Linux/macOS)
source ./activate_venv.sh
```

### 包管理

```bash
# 安装包
uv pip install langchain

# 从 requirements.txt 安装
uv pip install -r requirements.txt

# 安装开发模式
uv pip install -e .

# 导出依赖 (生成 requirements.txt)
uv pip freeze > requirements.txt

# 同步依赖 (删除未列出的包，安装缺失的包)
uv pip sync requirements.txt
```

### 与 pip 对比

| 命令 | pip | uv |
|------|-----|-----|
| 安装包 | `pip install <pkg>` | `uv pip install <pkg>` |
| 从文件安装 | `pip install -r req.txt` | `uv pip install -r req.txt` |
| 导出依赖 | `pip freeze > req.txt` | `uv pip freeze > req.txt` |
| 创建 venv | `python -m venv .venv` | `uv venv .venv` |
| 安装速度 | 基准 | 10-100x 更快 |

---

## 项目结构

```
everything_about_agent/
├── .venv/                      # UV 虚拟环境 (自动生成)
│   ├── Scripts/                # Windows 可执行文件
│   │   ├── python.exe
│   │   ├── pip.exe
│   │   └── uv.exe
│   └── bin/                    # Linux/macOS 可执行文件
│       ├── python
│       ├── pip
│       └── uv
├── scripts/
│   ├── setup_uv.py             # UV 环境初始化脚本
│   ├── setup_uv.bat            # Windows 快捷脚本
│   └── setup_uv.sh             # Linux/macOS 快捷脚本
├── activate_venv.ps1           # PowerShell 激活脚本 (自动生成)
├── activate_venv.sh            # Bash 激活脚本 (自动生成)
├── pyproject.toml              # 包含 UV 配置
├── start.bat                   # 支持 UV 的启动菜单 (Windows)
├── start.sh                    # 支持 UV 的启动菜单 (Linux/macOS)
└── ...
```

---

## 配置文件说明

### pyproject.toml

```toml
[project]
name = "everything-about-agent"
version = "3.0.0"
requires-python = ">=3.10"
dependencies = [
    "langchain>=0.3.0",
    "gradio>=5.0.0",
    # ...
]

[tool.uv]
# UV 专用配置
managed = true
dev-dependencies = [
    "pytest>=7.0.0",
    "black>=23.0.0",
]
```

---

## 故障排除

### 1. UV 未找到

```bash
# 检查 uv 是否在 PATH 中
uv --version

# 如果没有，重新安装
# Windows:
irm https://astral.sh/uv/install.ps1 | iex

# 然后重新打开终端，或手动添加 PATH
# Windows: %USERPROFILE%\.cargo\bin
# Linux/macOS: ~/.cargo/bin
```

### 2. Conda 和 UV 冲突

```bash
# 检查当前激活的 Python
which python

# 如果显示的是 Conda 的 Python，先停用
conda deactivate

# 然后激活 UV 环境
source ./activate_venv.sh  # 或 .\activate_venv.ps1
```

### 3. 安装失败

```bash
# 清理缓存
uv cache clean

# 重新安装
uv pip install -e . --force-reinstall
```

### 4. Python 版本不匹配

```bash
# 检查可用 Python 版本
uv python list

# 创建指定版本的环境
uv venv .venv --python 3.11
```

---

## 迁移指南

### 从纯 Conda 迁移到 UV

```bash
# 1. 导出当前 Conda 依赖
conda list --export > conda_packages.txt

# 2. 安装 UV
pip install uv

# 3. 创建 UV 环境
uv venv .venv --python 3.10

# 4. 安装依赖 (逐个或从 requirements.txt)
# 推荐手动整理依赖到 pyproject.toml

# 5. 测试
uv pip install -e .
python -c "import langchain; print('OK')"
```

### 混合使用方案

```bash
# Conda 管理 Python 版本和系统级包
conda install python=3.10

# UV 管理项目依赖
uv pip install -e .
```

---

## 参考资源

- [UV GitHub](https://github.com/astral-sh/uv)
- [UV 官方文档](https://docs.astral.sh/uv/)
- [LangChain 文档](https://python.langchain.com/)
- [Conda 文档](https://docs.conda.io/)

---

*Last Updated: 2026-03-02*
