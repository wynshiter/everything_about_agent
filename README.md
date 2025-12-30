# 🤖 Everything About Agent - Agent 学习与开发系统 (v3.0)

欢迎使用 **Everything About Agent**！这是一个基于 Python 构建的现代化 Agent 开发框架，旨在帮助开发者学习和实践各种 Agent 设计模式。

本项目采用**多后端架构**，支持在 **Ollama**（本地开发）和 **vLLM**（生产环境）之间无缝切换，并内置了多种经典的 Agent 设计模式实现。

---

## ✨ 核心特性

*   **🔌 多后端支持**: 
    *   **Ollama**: 开箱即用，适合本地开发和学习 (默认)。
    *   **vLLM**: 高性能推理，适合生产环境部署。
    *   **零代码切换**: 仅需修改配置文件即可切换后端。
*   **🧩 设计模式实践**:
    *   **Prompt Chaining (提示词链)**: 将复杂任务分解为流水线。
    *   **Routing (路由模式)**: 基于意图的动态任务分发。
    *   *(更多模式持续更新中...)*
*   **⚙️ 灵活配置**: 通过 YAML 文件集中管理模型、后端和应用配置。
*   **🛠️ 现代化技术栈**: 基于 LangChain, Pydantic, Loguru 等构建。

---

## 🚀 快速开始

### 1. 环境准备

确保你已经安装了以下环境：
*   **Python 3.10+**
*   **Ollama**: [下载并安装](https://ollama.com/) (用于本地运行模型)

### 2. 安装依赖

运行根目录下的启动脚本或手动安装：

```bash
pip install -e .
```

### 3. 启动系统

双击根目录下的 **`start.bat`** 脚本，即可看到交互式菜单：

```text
================================================
    🤖 Everything About Agent - 启动菜单
================================================
1. 📦 安装/更新依赖
2. ✅ 运行系统自检 (System Verification)
3. 🔗 运行 Prompt Chaining 模式演示
4. 🔀 运行 Routing 模式演示
5. 🚪 退出
```

### 4. 模型配置

默认情况下，系统会自动拉取并使用 **`qwen3:4b`** 模型。
如果需要修改模型或后端，请编辑 `configs/models.yaml`：

```yaml
# configs/models.yaml
active_model: "qwen3:4b"  # 修改此处切换模型
active_backend: "ollama"  # 修改此处切换后端 (ollama / vllm)
```

---

## 📂 项目结构

```
everything_about_agent/
├── configs/                 # ⚙️ 配置文件中心
│   ├── backends/            # 后端具体配置 (ollama.yaml, vllm.yaml)
│   ├── models.yaml          # 模型定义与激活配置
│   └── ...
├── src/                     # 🧠 源代码
│   ├── agents/              # Agent 实现
│   │   └── patterns/        # 设计模式具体实现 (chaining.py, routing.py)
│   ├── backends/            # 后端抽象层实现
│   └── utils/               # 工具类 (模型加载器, 后端管理器)
├── tests/                   # 🧪 测试代码
├── start.bat                # 🚀 启动脚本 (Windows)
├── pyproject.toml           # 📦 项目依赖管理
└── README.md                # 📄 项目文档
```

## 📚 Agent 设计模式指南

### 🔗 Prompt Chaining (提示词链)
将一个大任务拆解为多个步骤。例如：先从文本中提取参数，再将其格式化为 JSON。
*   **代码**: `src/agents/patterns/chaining.py`
*   **运行**: 在启动菜单中选择 `3`。

### 🔀 Routing (路由模式)
根据用户的输入意图，将请求分发给不同的处理程序（Handler）。例如：区分“预订机票”和“查询天气”。
*   **代码**: `src/agents/patterns/routing.py`
*   **运行**: 在启动菜单中选择 `4`。

---

## 📝 常见问题

**Q: 第一次运行报错 "Connection refused"?**
A: 请确保 Ollama 服务已在后台运行 (`ollama serve`)。

**Q: 如何添加新模型？**
A: 在 `configs/models.yaml` 中添加模型定义，并在 `active_model` 中引用它。

**Q: 如何切换到 vLLM?**
A: 确保已安装 vLLM 环境，在 `configs/models.yaml` 中设置 `active_backend: "vllm"`，并根据 `configs/backends/vllm.yaml` 配置连接地址。

---

Happy Coding with Agents! 🤖
