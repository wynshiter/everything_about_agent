# AGENTS.md - AI Coding Agent Guide

> This file provides essential information for AI coding agents working with the Everything About Agent project.
> 
> 本文档为AI编程助手提供项目关键信息，帮助快速理解和开发本项目。

---

## 1. Project Overview / 项目概览

**Everything About Agent** (v3.0.0) 是一个基于 Python 的 Agent 设计模式学习系统，采用**多后端架构**设计，支持 Ollama（本地开发）和 vLLM（生产环境）之间的无缝切换。

### Core Features / 核心特性
- **🔌 多后端支持**: Ollama（默认，本地开发）↔ vLLM（生产部署）
- **🧩 21个设计模式**: Prompt Chaining, Routing, Parallelization, Reflection, Tool Use, Planning, Multi-Agent, Memory, Learning, MCP, Goal Setting, Exception Handling, Human-in-Loop, RAG, A2A, Reasoning, Guardrails, Evaluation, Prioritization, Exploration
- **⚙️ 零代码切换**: 仅需修改配置文件即可切换后端
- **📚 MkDocs文档**: 完整的设计模式教程网站

---

## 2. Technology Stack / 技术栈

### Core Dependencies / 核心依赖
```
Python >= 3.10
├── langchain >= 0.3.0          # Agent框架核心
├── langchain-community         # 社区组件
├── langchain-ollama            # Ollama适配器
├── langchain-openai            # OpenAI API适配（用于vLLM）
├── ollama >= 0.4.0             # Ollama Python SDK
├── pydantic >= 2.9.0           # 数据验证与配置
├── pydantic-settings           # 设置管理
├── loguru >= 0.7.0             # 结构化日志
├── gradio >= 5.0.0             # Web界面
├── pyyaml >= 6.0.0             # YAML配置
└── requests, aiohttp           # HTTP客户端
```

### Build System / 构建系统
- **Package Manager**: pip / [uv](https://github.com/astral-sh/uv) (推荐，极速安装)
- **Install (pip)**: `pip install -e .`
- **Install (uv)**: `uv pip install -e .`
- **Config**: `pyproject.toml`
- **Environment**: Conda base + UV venv (兼容方案)

---

## 3. Project Structure / 项目结构

```
everything_about_agent/
├── 📁 configs/                    # 配置中心
│   ├── backends/                  # 后端配置
│   │   ├── ollama.yaml           # Ollama后端配置
│   │   └── vllm.yaml             # vLLM后端配置
│   ├── models.yaml               # 模型定义与激活配置
│   ├── tools.yaml                # 工具配置
│   └── app.yaml                  # 应用配置
│
├── 📁 src/                        # 源代码
│   ├── backends/                  # 后端抽象层
│   │   ├── base.py               # ModelBackend抽象基类
│   │   ├── ollama_backend.py     # Ollama实现
│   │   └── vllm_backend.py       # vLLM实现
│   ├── agents/patterns/           # 21个设计模式实现
│   │   ├── chaining.py           # Prompt Chaining
│   │   ├── routing.py            # Routing
│   │   ├── parallelization.py    # Parallelization
│   │   ├── reflection.py         # Reflection
│   │   ├── tool_use.py           # Tool Use
│   │   ├── planning.py           # Planning
│   │   ├── multi_agent.py        # Multi-Agent
│   │   ├── memory.py             # Memory
│   │   ├── learning.py           # Learning
│   │   ├── mcp.py                # MCP
│   │   ├── goal_setting.py       # Goal Setting
│   │   ├── exception_handling.py # Exception Handling
│   │   ├── human_in_loop.py      # Human-in-Loop
│   │   ├── rag.py                # RAG
│   │   ├── a2a.py                # A2A
│   │   ├── reasoning.py          # Reasoning
│   │   ├── guardrails.py         # Guardrails
│   │   ├── evaluation.py         # Evaluation
│   │   ├── prioritization.py     # Prioritization
│   │   └── exploration.py        # Exploration
│   ├── utils/                     # 工具模块
│   │   ├── backend_manager.py    # 后端管理器（单例）
│   │   └── model_loader.py       # 模型加载器
│   └── practices/                 # 实践代码
│
├── 📁 tests/                      # 测试代码
│   └── test_system.py            # 系统自检测试
│
├── 📁 scripts/                    # 脚本工具
│   ├── diagnose.py               # 诊断工具
│   └── file_watcher.py           # 文件监控
│
├── 📁 docs/                       # MkDocs文档
│   └── practices/Agent_design/   # 21个设计模式文档
│
├── 📁 logs/                       # 日志目录
├── 📁 .pids/                      # PID文件目录
├── start.bat                      # Windows启动脚本
├── start.sh                       # Linux/macOS启动脚本
├── pyproject.toml                 # 项目配置
└── mkdocs.yml                     # MkDocs配置
```

---

## 4. Architecture Overview / 架构概览

### Multi-Backend Architecture / 多后端架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Pattern (LCEL)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              LangChain LLM Adapter                          │
│     (ChatOllama for Ollama / ChatOpenAI for vLLM)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              ModelLoader (src/utils/model_loader.py)        │
│         - 验证模型支持当前后端                                │
│         - 调用后端加载模型                                   │
│         - 返回适配的LangChain组件                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           BackendManager (src/utils/backend_manager.py)     │
│              - 单例模式管理后端实例                          │
│              - 动态切换后端                                  │
│              - 健康检查                                      │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          ▼                                       ▼
┌───────────────────────┐           ┌───────────────────────┐
│   OllamaBackend       │           │     VLLMBackend       │
│   (ollama_backend.py) │           │    (vllm_backend.py)  │
├───────────────────────┤           ├───────────────────────┤
│ - ollama.pull()       │           │ - HTTP API /v1/       │
│ - ollama.chat()       │           │   chat/completions    │
│ - Local dev, easy     │           │ - Production, high    │
│   setup               │           │   performance         │
│ - Port: 11434         │           │ - Port: 8000          │
└───────────────────────┘           └───────────────────────┘
```

### Key Components / 关键组件

1. **ModelBackend (base.py)**: 抽象基类定义统一接口
   - `load_model(model_id, config) -> bool`
   - `generate(prompt, **kwargs) -> ModelResponse`
   - `generate_stream(prompt, **kwargs) -> AsyncIterator[ModelResponse]`
   - `is_available() -> bool`

2. **BackendManager**: 全局单例，管理所有后端
   - 从 `configs/models.yaml` 读取 `active_backend`
   - 支持动态切换后端
   - 提供后端健康状态查询

3. **ModelLoader**: 通过当前后端加载模型
   - 验证模型是否支持当前后端
   - 返回适配的 LangChain LLM 实例

---

## 5. Build and Run Commands / 构建与运行命令

### Installation / 安装

#### 方式一: 使用 UV (推荐，极速安装)
```bash
# 初始化 UV 环境 (首次使用)
python scripts/setup_uv.py

# 激活环境
.\activate_venv.ps1        # Windows PowerShell
source ./activate_venv.sh  # Linux/macOS

# 安装依赖
uv pip install -e .
```

#### 方式二: 使用 Pip
```bash
# 安装项目依赖（开发模式）
pip install -e .
```

### Run Options / 运行选项

#### Windows / Windows平台
```bash
# 交互式菜单（推荐）
.\start.bat

# 选项说明:
# 1. 安装/更新依赖 (自动检测 UV 或 Pip)
# 2. 运行系统自检
# 3. 运行 Prompt Chaining 演示
# 4. 运行 Routing 演示
# 5. 启动 Web 前端 (http://localhost:8080)
# 6. 启动 Web + 文件监控
# 7. 启动 MkDocs 文档服务器
# 8. 停止所有服务
# 9. 检查服务状态
# 10. 运行诊断工具
# 11. 查看日志
# 12. 初始化 UV 环境
# 13. 退出

# 如果检测到 .venv 目录，菜单会显示 [UV Mode: .venv]
```

#### Direct Execution / 直接运行
```bash
# 系统自检
python tests/test_system.py

# 设计模式演示
python src/agents/patterns/chaining.py
python src/agents/patterns/routing.py
python src/agents/patterns/parallelization.py
python src/agents/patterns/reflection.py
python src/agents/patterns/tool_use.py

# 诊断工具
python scripts/diagnose.py
python scripts/diagnose.py --save    # 保存报告到 logs/
```

#### MkDocs Documentation / 文档服务
```bash
# 启动文档服务器
python -m mkdocs serve

# 构建文档
python -m mkdocs build
```

---

## 6. Configuration Guide / 配置指南

### Switch Backend / 切换后端

修改 `configs/models.yaml`:
```yaml
active_model: "qwen3:4b"     # 当前激活模型
active_backend: "ollama"      # 当前激活后端: ollama 或 vllm
```

### Add New Model / 添加新模型

在 `configs/models.yaml` 中添加:
```yaml
models:
  your_model_id:
    name: "Display Name"
    model_id: "unique_id"
    supported_backends:
      - "ollama"
      - "vllm"
    backend_repos:
      ollama: "ollama_model_name"
      vllm: "huggingface/repo/path"
    parameters:
      temperature: 0.7
      max_tokens: 2048
    capabilities:
      function_calling: true
      multi_agent: true
```

### Backend Configurations / 后端配置

- **Ollama**: `configs/backends/ollama.yaml`
  - Host: `http://localhost:11434`
  - Features: streaming support, local install required

- **vLLM**: `configs/backends/vllm.yaml`
  - Host: `http://localhost:8000`
  - Features: batching, concurrent, streaming support

---

## 7. Code Style Guidelines / 代码风格指南

### Language / 语言
- **Code Comments**: 中文（面向中文开发者）
- **Docstrings**: 英文（面向AI工具）
- **Variable Names**: snake_case
- **Class Names**: PascalCase

### Agent Pattern Structure / Agent模式结构
```python
from src.utils.model_loader import model_loader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from loguru import logger

class PatternAgent:
    """
    Implements the [Pattern Name] pattern.
    Based on Chapter [N]: [Pattern Name].
    
    Scenario: [Brief description of use case].
    """
    
    def __init__(self, model_id: str = None):
        self.llm = model_loader.load_llm(model_id)
        effective_id = model_id if model_id else model_loader.active_model_id
        self.chain = self._build_chain()
        logger.info(f"[Emoji] AgentName initialized with model: {effective_id}")
    
    def _build_chain(self):
        """Build the processing chain using LCEL."""
        # Implementation
        pass
    
    def run(self, input_data: str) -> str:
        """Execute the agent."""
        logger.info(f"Running with input: {input_data[:50]}...")
        return self.chain.invoke(input_data)

if __name__ == "__main__":
    # Demo block
    pass
```

### LCEL (LangChain Expression Language) / LCEL使用规范
- 使用 `|` 操作符连接组件
- 使用 `RunnableParallel` 实现并行处理
- 使用 `RunnableBranch` 实现条件路由
- 使用 `StrOutputParser()` 解析字符串输出

### Logging / 日志规范
- 使用 `from loguru import logger`
- 初始化日志：`logger.info(f"🔧 组件名称 initialized")`
- 执行日志：`logger.info(f"Processing: {data[:50]}...")`
- 错误日志：`logger.error(f"操作失败: {e}")`

---

## 8. Testing Strategy / 测试策略

### System Verification / 系统自检
```bash
python tests/test_system.py
```

测试内容包括:
1. Backend Manager 初始化与后端列表
2. 模型加载（通过当前后端）
3. Chaining Pattern 功能测试
4. Routing Pattern 功能测试

### Adding New Pattern Tests / 添加新模式测试
在 `tests/test_system.py` 中添加:
```python
def test_new_pattern():
    logger.info("Testing New Pattern...")
    try:
        from src.agents.patterns.new_pattern import NewPatternAgent
        agent = NewPatternAgent()
        result = agent.run("test input")
        logger.info(f"Result: {result}")
        assert "expected" in result
    except Exception as e:
        logger.error(f"Test failed: {e}")
```

---

## 9. Troubleshooting / 故障排查

### Diagnostic Tool / 诊断工具
```bash
python scripts/diagnose.py
```

诊断内容包括:
- 系统信息（OS、Python版本）
- 端口占用状态（11434, 8000, 8080）
- 进程运行状态
- 日志分析
- 依赖检查
- 配置文件验证
- 后端连接状态

### Common Issues / 常见问题

**Q: Connection refused when running patterns?**
A: 确保 Ollama 服务已启动: `ollama serve`

**Q: How to switch to vLLM?**
A: 修改 `configs/models.yaml` 中的 `active_backend: "vllm"`，并确保 vLLM 服务已启动

**Q: Port 8080 is occupied?**
A: 使用 `start.bat` 选项 7 停止占用进程，或使用选项 8 检查端口状态

**Q: Model not found?**
A: 在 `configs/models.yaml` 中添加模型定义，确保 `supported_backends` 包含目标后端

---

## 10. Security Considerations / 安全注意事项

### Tool Use Safety / 工具使用安全
- `tool_use.py` 中的 `calculate` 函数使用了 `eval()`，仅限演示使用
- 生产环境应使用安全的数学表达式解析器
- 所有工具调用都应验证输入参数

### API Keys / API密钥
- vLLM 使用 `api_key="EMPTY"`（本地部署无需密钥）
- 如需连接外部API，使用环境变量存储密钥
- 不要硬编码任何敏感信息

---

## 11. Development Workflow / 开发流程

### Adding New Agent Pattern / 添加新Agent模式

1. **创建文件**: `src/agents/patterns/new_pattern.py`
2. **实现Agent类**: 继承或使用 `model_loader.load_llm()`
3. **使用LCEL**: 构建处理链
4. **添加文档**: 在 `docs/practices/Agent_design/chapterX_new_pattern/index.md`
5. **更新导航**: 在 `mkdocs.yml` 中添加导航项
6. **添加测试**: 在 `tests/test_system.py` 中添加测试
7. **更新启动脚本**: 在 `start.bat` 中添加菜单选项（可选）

### Adding New Backend / 添加新后端

1. **实现Backend类**: 继承 `ModelBackend` 抽象基类
2. **添加配置**: 在 `configs/backends/` 添加 YAML 配置文件
3. **注册Backend**: 在 `backend_manager.py` 中注册新后端
4. **添加LangChain适配**: 在 `model_loader.py` 中添加适配逻辑

---

## 12. UV 环境管理

### 什么是 UV?
[UV](https://github.com/astral-sh/uv) 是用 Rust 编写的极速 Python 包管理器，比 pip 快 10-100 倍。

### 快速开始
```bash
# 初始化 UV 环境
python scripts/setup_uv.py

# 或者使用启动菜单选项 12
.\start.bat  # Windows
./start.sh   # Linux/macOS
```

### UV 常用命令
```bash
# 创建虚拟环境
uv venv .venv --python 3.10

# 安装依赖
uv pip install -e .

# 导出依赖
uv pip freeze > requirements.txt

# 激活环境 (Windows)
.\activate_venv.ps1

# 激活环境 (Linux/macOS)
source ./activate_venv.sh
```

### UV 与 Conda 共存
本项目支持在 Conda base 环境中使用 UV 管理项目依赖：
- **Conda**: 管理 Python 版本和系统级包
- **UV**: 管理项目依赖，提供极速安装

更多详情参见 [docs/UV_SETUP.md](docs/UV_SETUP.md)

---

## 13. Resources / 参考资源

### Documentation / 文档
- **README.md**: 项目简介与快速开始
- **CODEBUDDY.md**: 开发命令与架构说明
- **prompt.txt**: 完整的多后端架构设计文档

### External References / 外部参考
- **LangChain LCEL**: https://python.langchain.com/docs/expression_language/
- **Ollama**: https://ollama.com/
- **vLLM**: https://docs.vllm.ai/
- **MkDocs Material**: https://squidfunk.github.io/mkdocs-material/

---

*Last Updated: 2026-03-01*
*Version: 3.0.0*
