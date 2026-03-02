#!/usr/bin/env python3
"""
UV 环境初始化脚本
支持在 Conda base 环境中使用 UV 作为包管理器
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

# 颜色输出
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"

def print_color(color, message):
    """打印彩色文本"""
    print(f"{color}{message}{NC}")

def run_command(cmd, check=True, capture_output=False):
    """运行命令并返回结果"""
    print_color(BLUE, f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True,
            shell=(sys.platform == "win32")
        )
        return result
    except subprocess.CalledProcessError as e:
        print_color(RED, f"Command failed: {e}")
        if capture_output:
            print_color(RED, f"stdout: {e.stdout}")
            print_color(RED, f"stderr: {e.stderr}")
        raise

def check_uv_installed():
    """检查 uv 是否已安装"""
    uv_path = shutil.which("uv")
    if uv_path:
        print_color(GREEN, f"✓ uv 已安装: {uv_path}")
        result = run_command(["uv", "--version"], capture_output=True)
        print_color(GREEN, f"  版本: {result.stdout.strip()}")
        return True
    return False

def install_uv():
    """安装 uv"""
    print_color(YELLOW, "正在安装 uv...")
    
    if sys.platform == "win32":
        # Windows: 使用 PowerShell 安装
        cmd = [
            "powershell", "-ExecutionPolicy", "ByPass", "-c",
            "irm https://astral.sh/uv/install.ps1 | iex"
        ]
    else:
        # Linux/macOS: 使用 curl 安装
        cmd = ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"]
    
    try:
        if sys.platform == "win32":
            run_command(cmd)
        else:
            # 对于 shell 管道命令，使用 shell=True
            subprocess.run(
                "curl -LsSf https://astral.sh/uv/install.sh | sh",
                shell=True,
                check=True
            )
        print_color(GREEN, "✓ uv 安装成功")
        return True
    except Exception as e:
        print_color(RED, f"✗ uv 安装失败: {e}")
        return False

def get_conda_info():
    """获取 conda 环境信息"""
    try:
        result = subprocess.run(
            ["conda", "info", "--json"],
            capture_output=True,
            text=True,
            check=True
        )
        import json
        return json.loads(result.stdout)
    except Exception as e:
        print_color(YELLOW, f"无法获取 conda 信息: {e}")
        return None

def setup_uv_environment():
    """配置 uv 环境"""
    project_root = Path(__file__).parent.parent.resolve()
    
    print_color(BLUE, "\n" + "="*50)
    print_color(BLUE, "UV 环境配置")
    print_color(BLUE, "="*50)
    
    # 1. 检查 uv
    if not check_uv_installed():
        if not install_uv():
            print_color(RED, "请先手动安装 uv: https://github.com/astral-sh/uv")
            sys.exit(1)
        # 重新检查
        if not check_uv_installed():
            print_color(YELLOW, "请重新打开终端或手动添加 uv 到 PATH")
            sys.exit(1)
    
    # 2. 检查 conda base 环境
    print_color(BLUE, "\n检查 Conda 环境...")
    conda_info = get_conda_info()
    if conda_info:
        print_color(GREEN, f"✓ Conda 已安装")
        print_color(GREEN, f"  Base 环境: {conda_info.get('root_prefix', 'Unknown')}")
        print_color(GREEN, f"  当前环境: {conda_info.get('active_prefix_name', 'None')}")
    
    # 3. 创建/更新虚拟环境
    print_color(BLUE, "\n配置 Python 环境...")
    venv_path = project_root / ".venv"
    
    if venv_path.exists():
        print_color(YELLOW, f"发现已有虚拟环境: {venv_path}")
        choice = input("是否重新创建? [y/N]: ").strip().lower()
        if choice == 'y':
            shutil.rmtree(venv_path)
            print_color(BLUE, "创建新的虚拟环境...")
            run_command(["uv", "venv", str(venv_path), "--python", "3.10"])
    else:
        print_color(BLUE, "创建虚拟环境...")
        run_command(["uv", "venv", str(venv_path), "--python", "3.10"])
    
    print_color(GREEN, f"✓ 虚拟环境已准备: {venv_path}")
    
    # 4. 安装依赖
    print_color(BLUE, "\n安装项目依赖...")
    pyproject_path = project_root / "pyproject.toml"
    
    if pyproject_path.exists():
        # 使用 uv pip 安装
        run_command([
            "uv", "pip", "install", "-e", ".",
            "--python", str(venv_path / "Scripts" / "python.exe" if sys.platform == "win32" else venv_path / "bin" / "python")
        ])
        print_color(GREEN, "✓ 依赖安装完成")
    else:
        print_color(YELLOW, f"未找到 pyproject.toml: {pyproject_path}")
    
    # 5. 创建激活脚本
    print_color(BLUE, "\n创建环境激活脚本...")
    create_activation_scripts(project_root, venv_path)
    
    # 6. 显示使用说明
    print_color(GREEN, "\n" + "="*50)
    print_color(GREEN, "✓ UV 环境配置完成!")
    print_color(GREEN, "="*50)
    print_color(BLUE, "\n使用说明:")
    print(f"  1. 激活环境: {BLUE}./activate_venv.ps1{NC} (PowerShell)")
    print(f"              {BLUE}source ./activate_venv.sh{NC} (Git Bash)")
    print(f"  2. 运行程序: {BLUE}python src/agents/patterns/chaining.py{NC}")
    print(f"  3. 添加依赖: {BLUE}uv pip install <package>{NC}")
    print(f"  4. 同步依赖: {BLUE}uv pip sync{NC}")
    print()

def create_activation_scripts(project_root: Path, venv_path: Path):
    """创建环境激活脚本"""
    
    # PowerShell 激活脚本
    ps_script = project_root / "activate_venv.ps1"
    venv_python = venv_path / "Scripts" / "python.exe"
    venv_activate = venv_path / "Scripts" / "Activate.ps1"
    
    ps_content = f'''# UV 虚拟环境激活脚本 (PowerShell)
$VenvPath = "{venv_path}"
$PythonPath = "{venv_python}"

if (Test-Path $PythonPath) {{
    # 激活虚拟环境
    & "{venv_activate}"
    Write-Host "✓ UV 虚拟环境已激活" -ForegroundColor Green
    Write-Host "Python: $PythonPath" -ForegroundColor Blue
    python --version
}} else {{
    Write-Error "虚拟环境不存在: $VenvPath"
}}
'''
    ps_script.write_text(ps_content, encoding="utf-8")
    print_color(GREEN, f"✓ 创建: {ps_script}")
    
    # Bash 激活脚本
    bash_script = project_root / "activate_venv.sh"
    venv_python_bash = venv_path / "bin" / "python"
    venv_activate_bash = venv_path / "bin" / "activate"
    
    bash_content = f'''#!/bin/bash
# UV 虚拟环境激活脚本 (Bash)
VENV_PATH="{venv_path}"
PYTHON_PATH="{venv_python_bash}"

if [ -f "$PYTHON_PATH" ]; then
    source "{venv_activate_bash}"
    echo -e "\\033[0;32m✓ UV 虚拟环境已激活\\033[0m"
    echo -e "\\033[0;34mPython: $PYTHON_PATH\\033[0m"
    python --version
else
    echo "错误: 虚拟环境不存在: $VENV_PATH"
    exit 1
fi
'''
    bash_script.write_text(bash_content, encoding="utf-8")
    # 添加执行权限 (Linux/macOS)
    if sys.platform != "win32":
        os.chmod(bash_script, 0o755)
    print_color(GREEN, f"✓ 创建: {bash_script}")
    
    # 创建 uv 快捷命令脚本
    uv_cmd_script = project_root / "uv_cmd.ps1"
    uv_cmd_content = f'''# UV 命令快捷脚本
param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$VenvPath = "{venv_path}"
$UvPath = (Get-Command uv -ErrorAction SilentlyContinue).Source

if (-not $UvPath) {{
    Write-Error "uv 未安装或未在 PATH 中"
    exit 1
}}

# 使用虚拟环境的 Python
$env:VIRTUAL_ENV = $VenvPath
$env:PATH = "$VenvPath\\Scripts;$env:PATH"

& $UvPath @Arguments
'''
    uv_cmd_script.write_text(uv_cmd_content, encoding="utf-8")
    print_color(GREEN, f"✓ 创建: {uv_cmd_script}")

def main():
    """主函数"""
    try:
        setup_uv_environment()
    except KeyboardInterrupt:
        print_color(YELLOW, "\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print_color(RED, f"\n错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
