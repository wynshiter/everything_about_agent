# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## 常用命令

### 安装与依赖
```bash
pip install -e .          # 安装项目依赖（开发模式）
```

### 测试与验证
```bash
python tests/test_system.py                    # 运行系统自检
python src/agents/patterns/chaining.py         # 运行 Prompt Chaining 模式演示
python src/agents/patterns/routing.py          # 运行 Routing 模式演示
```

### 启动脚本

#### Windows
双击 `start.bat` 打开交互式菜单，或直接运行：
```powershell
.\start.bat
```

#### Linux/macOS
```bash
chmod +x start.sh
./start.sh
```

### 启动脚本功能菜单
| 选项 | 功能 | 说明 |
|------|------|------|
| 1 | Install/Update Dependencies | 安装/更新项目依赖 |
| 2 | Run System Verification | 运行系统自检测试 |
| 3 | Run Prompt Chaining Demo | 运行链式处理演示 |
| 4 | Run Routing Demo | 运行路由模式演示 |
| 5 | Start Web Frontend | 启动课程前端页面 (http://localhost:8080) |
| 6 | Start Web with File Watcher | 启动前端+文件监控自动重载 |
| 7 | Stop All Services | 停止所有运行中的服务 |
| 8 | Check Service Status | 检查服务状态（端口、进程、PID） |
| 9 | Run Diagnostics | 运行系统诊断工具 |
| 10 | View Logs | 查看日志文件 |
| 11 | Exit | 退出菜单 |

### 故障排查

#### 使用诊断工具
```bash
python scripts/diagnose.py          # 运行完整诊断
python scripts/diagnose.py --save   # 保存诊断报告到 logs/
```

诊断工具检查：
- 系统信息（OS、Python版本）
- 端口占用状态
- 进程运行状态
- 日志分析
- 依赖检查
- 配置文件验证
- 后端连接状态
- PID文件状态

#### 常见问题解决

**问题：启动后窗口立即关闭**
- 运行诊断工具检查端口占用
- 查看日志文件定位错误
- 使用选项 7 停止已存在的服务

**问题：端口 8080 被占用**
- 使用选项 8 检查端口状态
- 使用选项 7 停止占用进程
- 或修改脚本中的 PORT 变量使用其他端口

**问题：服务异常停止**
- 检查 logs/ 目录下的日志文件
- 运行诊断工具获取详细报告
- 检查 .pids/ 目录中的PID文件状态

## 架构概览

### 多后端架构
项目采用**后端抽象层**设计，支持 Ollama（本地开发）和 vLLM（生产环境）之间零代码切换：

```
src/backends/
├── base.py           # ModelBackend 抽象基类
├── ollama_backend.py # Ollama 后端实现
└── vllm_backend.py   # vLLM 后端实现
```

- **ModelBackend** 定义统一接口：`load_model()`, `generate()`, `generate_stream()`, `is_available()`
- 每个后端实现独立的模型加载、推理和健康检查逻辑
- 后端配置位于 `configs/backends/` 目录

### 核心组件协作流程

```
配置文件 (configs/models.yaml)
        ↓
  BackendManager (单例)
        ↓
    ModelLoader
        ↓
   LangChain LLM 适配器
        ↓
    Agent Pattern
```

1. **BackendManager** (`src/utils/backend_manager.py`): 单例模式，管理所有后端实例，从 `configs/models.yaml` 读取 `active_backend` 决定当前后端
2. **ModelLoader** (`src/utils/model_loader.py`): 通过当前后端加载模型，自动返回适配的 LangChain 组件（Ollama → `ChatOllama`, vLLM → `ChatOpenAI`）
3. **Agent Patterns** (`src/agents/patterns/`): 使用 LangChain LCEL 构建的 Agent 设计模式实现

### 切换后端/模型
修改 `configs/models.yaml`：
```yaml
active_model: "qwen3:4b"    # 切换模型
active_backend: "ollama"    # 切换后端 (ollama/vllm)
```

模型必须在 `models` 字段中定义，且 `supported_backends` 必须包含目标后端。

### Agent 设计模式
设计模式使用 LangChain LCEL (LangChain Expression Language) 构建：

- **Prompt Chaining** (`chaining.py`): 将复杂任务分解为流水线，通过 `|` 操作符串联多个步骤。示例：文本提取 → JSON 转换
- **Routing** (`routing.py`): 使用 `RunnableBranch` 根据意图分类路由到不同的 Handler。示例：预订请求 vs 信息查询

### 配置文件说明
- `configs/models.yaml`: 模型定义、激活配置、后端仓库映射、资源要求
- `configs/backends/ollama.yaml`: Ollama 连接参数、特性标志、性能基准
- `configs/backends/vllm.yaml`: vLLM 连接参数、GPU 配置、量化设置
- `configs/app.yaml`: 应用名称、版本、日志级别

### 添加新模型
在 `configs/models.yaml` 的 `models` 字段添加：
```yaml
model_id:
  name: "Display Name"
  model_id: "unique_id"
  supported_backends: ["ollama", "vllm"]
  backend_repos:
    ollama: "ollama_model_name"
    vllm: "huggingface/repo/path"
  parameters:
    temperature: 0.7
    max_tokens: 2048
```

### 添加新的 Agent 模式
1. 在 `src/agents/patterns/` 创建新文件
2. 使用 `model_loader.load_llm()` 获取 LLM 实例
3. 使用 LangChain LCEL 构建处理链
4. 在 `start.bat` 和 `tests/test_system.py` 中添加入口

### 依赖说明
项目基于 LangChain 生态构建，核心依赖：
- `langchain`, `langchain-community`: 核心框架和链式处理
- `langchain-ollama`, `langchain-openai`: LangChain 后端适配器
- `ollama`: Ollama Python SDK
- `pydantic`: 数据验证和配置模型
- `loguru`: 结构化日志
