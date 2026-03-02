# UV 环境支持 - 变更总结

> 本文档记录了为支持 Python UV 包管理器所做的所有更改。

---

## 新增文件

### 1. `scripts/setup_uv.py`
UV 环境初始化脚本，功能包括：
- 检测/安装 uv
- 创建 `.venv` 虚拟环境
- 安装项目依赖
- 生成激活脚本 (`activate_venv.ps1`, `activate_venv.sh`)
- 兼容 Conda base 环境

### 2. `scripts/setup_uv.bat`
Windows 快捷脚本，用于一键初始化 UV 环境。

### 3. `scripts/setup_uv.sh`
Linux/macOS 快捷脚本，用于一键初始化 UV 环境。

### 4. `docs/UV_SETUP.md`
完整的 UV 环境配置指南，包括：
- UV 简介和特性
- 快速开始指南
- UV 与 Conda 共存方案
- 常用命令参考
- 故障排除

---

## 修改的文件

### 1. `pyproject.toml`
新增 UV 配置段：
```toml
[tool.uv]
managed = true
dev-dependencies = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[tool.uv.pip]
python = ".venv/Scripts/python.exe"
```

### 2. `start.bat`
- 新增 UV 环境检测逻辑
- 菜单新增选项 12: "Init UV Environment"
- 菜单新增选项 13: "Exit" (原选项 12)
- 自动检测并使用 UV 模式运行命令
- 菜单显示 UV 模式状态: `[UV Mode: .venv]`

### 3. `start.sh`
- 新增 UV 环境检测逻辑
- 菜单新增选项 12: "Init UV Environment"
- 菜单新增选项 13: "Exit" (原选项 12)
- 自动检测并使用 UV 模式运行命令
- 菜单显示 UV 模式状态: `[UV Mode: .venv]`

### 4. `AGENTS.md`
- 更新构建系统说明，添加 UV 支持
- 新增 "12. UV 环境管理" 章节
- 更新运行选项说明

---

## 使用流程

### 首次使用 UV

**Windows:**
```bash
# 方法 1: 使用启动菜单
.\start.bat
# 选择选项 12: Init UV Environment

# 方法 2: 命令行直接运行
python scripts\setup_uv.py
```

**Linux/macOS:**
```bash
# 方法 1: 使用启动菜单
./start.sh
# 选择选项 12: Init UV Environment

# 方法 2: 命令行直接运行
python3 scripts/setup_uv.py
```

### 激活环境

**Windows:**
```powershell
.\activate_venv.ps1
```

**Linux/macOS:**
```bash
source ./activate_venv.sh
```

### 日常使用

**Windows:**
```bash
# 启动菜单会自动检测 UV 环境并使用
.\start.bat

# 或者直接使用 UV 命令
uv pip install <package>
uv pip install -e .
```

**Linux/macOS:**
```bash
# 启动菜单会自动检测 UV 环境并使用
./start.sh

# 或者直接使用 UV 命令
uv pip install <package>
uv pip install -e .
```

---

## 技术细节

### UV 环境检测逻辑

```python
# 检测 .venv 目录是否存在
if exist ".venv\Scripts\python.exe" (Windows)
if [ -f ".venv/bin/python" ] (Linux/macOS)

# 如果存在，设置相关变量
UV_ENV=1
PYTHON_CMD=.venv/Scripts/python.exe (或 .venv/bin/python)
PIP_CMD=.venv/Scripts/pip.exe (或 .venv/bin/pip)
```

### 与 Conda 的兼容性

- **不冲突**: UV 虚拟环境完全隔离，不影响 Conda base 环境
- **优先使用**: 当 `.venv` 存在时，启动脚本优先使用 UV 环境
- **灵活切换**: 删除 `.venv` 目录即可恢复使用系统 Python/Conda

---

## 文件清单

```
everything_about_agent/
├── .venv/                      # UV 虚拟环境 (运行时生成)
│   ├── Scripts/python.exe      # Windows Python 解释器
│   └── bin/python              # Linux/macOS Python 解释器
├── scripts/
│   ├── setup_uv.py             # UV 初始化脚本 [NEW]
│   ├── setup_uv.bat            # Windows 快捷脚本 [NEW]
│   └── setup_uv.sh             # Linux/macOS 快捷脚本 [NEW]
├── activate_venv.ps1           # PowerShell 激活脚本 [运行时生成]
├── activate_venv.sh            # Bash 激活脚本 [运行时生成]
├── docs/
│   ├── UV_SETUP.md             # UV 配置指南 [NEW]
│   └── UV_SETUP_CHANGELOG.md   # 本文件 [NEW]
├── pyproject.toml              # 添加 [tool.uv] 配置 [MODIFIED]
├── start.bat                   # 添加 UV 支持 [MODIFIED]
├── start.sh                    # 添加 UV 支持 [MODIFIED]
└── AGENTS.md                   # 添加 UV 章节 [MODIFIED]
```

---

## 回滚方案

如果需要恢复原始配置：

```bash
# 删除 UV 虚拟环境
rmdir /s /q .venv        # Windows
rm -rf .venv             # Linux/macOS

# 删除生成的激活脚本
del activate_venv.ps1    # Windows
rm activate_venv.sh      # Linux/macOS

# 然后使用传统的 pip 安装
pip install -e .
```

---

*Last Updated: 2026-03-02*
