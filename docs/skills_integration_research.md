# Skills 集成调研报告与最佳实践

> 本文档汇总全网关于 Skills 集成到 Agent 的方案调研，以及基于 Google ADK 规范的数据分析 Skill 实现示例。

## 目录

1. [调研概述](#调研概述)
2. [Google ADK Skills 详解](#google-adk-skills-详解)
3. [主流框架对比](#主流框架对比)
4. [项目实现方案](#项目实现方案)
5. [最佳实践总结](#最佳实践总结)

---

## 调研概述

### 什么是 Skill？

Skill（技能）是一个**自包含的功能单元**，Agent 可以使用它来执行特定任务。它遵循 [Agent Skill Specification](https://agentskills.io) 开放标准，已被 30+ 个 Agent 工具采用。

### 为什么要使用 Skills？

| 优势 | 说明 |
|------|------|
| **模块化** | 功能封装，易于复用和维护 |
| **可发现** | Agent 根据描述自动选择合适的 Skill |
| **渐进式** | 按需加载（L1/L2/L3），节省上下文窗口 |
| **标准化** | 遵循开放标准，跨框架兼容 |
| **可组合** | 多个 Skills 可以组合使用 |

### 调研范围

本次调研涵盖以下框架的 Skills 集成方案：

1. **Google Agent Development Kit (ADK)** - 原生 Skills 支持
2. **LangChain** - Tools 机制
3. **AutoGen** - FunctionTool 机制
4. **CrewAI** - Tools 系统
5. **LlamaIndex** - QueryEngineTool
6. **Semantic Kernel** - Plugins (原 Skills)

---

## Google ADK Skills 详解

### 三层架构设计

Google ADK 采用 **渐进式披露（Progressive Disclosure）** 架构：

```
┌─────────────────────────────────────────┐
│              L1 - Metadata              │  ← 启动时加载
│   (名称、描述、版本、支持的 Tools)        │
├─────────────────────────────────────────┤
│           L2 - Instructions             │  ← Skill 激活时加载
│      (使用说明、步骤、示例、约束)          │
├─────────────────────────────────────────┤
│            L3 - Resources               │  ← 按需加载
│   (references/, assets/, scripts/)      │
└─────────────────────────────────────────┘
```

### Skill 目录结构

```
my_skill/
├── SKILL.md              # 必需：元数据(L1) + 指令(L2)
├── references/           # 可选：额外文档(L3)
│   └── details.md
├── assets/               # 可选：静态资源(L3)
│   └── template.png
└── scripts/              # 可选：可执行脚本(L3)
    └── setup.py
```

### SKILL.md 格式规范

```markdown
---
name: my-skill
description: 简洁的功能描述，这是 LLM 选择 Skill 的关键依据
metadata:
  version: "1.0.0"
  author: "Author Name"
  category: "data_science"
  adk_additional_tools:
    - "tool1"
    - "tool2"
---

# Skill 名称

## 功能概述
...

## 使用步骤
1. Step 1
2. Step 2

## 最佳实践
...
```

### 集成方式

**方式1：目录加载（推荐）**

```python
from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset

skill = load_skill_from_dir("./skills/data_analysis")
toolset = skill_toolset.SkillToolset(skills=[skill])

agent = Agent(
    model="gemini-2.5-flash",
    tools=[toolset],
)
```

**方式2：内联定义（简单场景）**

```python
from google.adk.skills import models

greeting_skill = models.Skill(
    frontmatter=models.Frontmatter(
        name="greeting-skill",
        description="A friendly greeting skill.",
    ),
    instructions="Step 1: ... Step 2: ...",
)
```

### 核心交互机制

```
用户请求
    ↓
Agent 解析意图
    ↓
┌──────────────────┐
│ 1. 匹配 L1 元数据 │ ← 所有 Skills 的名称+描述
│    (轻量级)       │
└──────────────────┘
    ↓
决定调用 load_skill("data-analysis")
    ↓
┌──────────────────┐
│ 2. 加载 L2 指令   │ ← 完整的使用说明
│    (按需)         │
└──────────────────┘
    ↓
执行 Skill 逻辑
    ↓
┌──────────────────┐
│ 3. 加载 L3 资源   │ ← 参考资料、代码片段
│    (按需)         │
└──────────────────┘
    ↓
返回结果
```

---

## 主流框架对比

### 功能对比表

| 框架 | 核心概念 | 定义方式 | Agent 集成 | 多 Agent 支持 | 代码执行 |
|------|---------|---------|-----------|--------------|---------|
| **Google ADK** | Skill + SkillToolset | `SKILL.md` + 目录 | `tools=[toolset]` | ✅ 原生支持 | ✅ 内置 |
| **LangChain** | Tool | `@tool` 装饰器 | `create_tool_calling_agent` | ✅ LangGraph | ⚠️ 需配置 |
| **AutoGen** | FunctionTool | 类/函数包装 | `AssistantAgent(tools=...)` | ✅ 核心特性 | ✅ 内置 |
| **CrewAI** | Tool | `@tool` / `BaseTool` | `Agent(tools=...)` | ✅ Crew 编排 | ⚠️ 需配置 |
| **LlamaIndex** | QueryEngineTool | 包装 QueryEngine | `FunctionAgent.from_tools` | ✅ AgentWorkflow | ⚠️ 需配置 |
| **Semantic Kernel** | Plugin/Function | `@kernel_function` | `kernel.import_plugin` | ⚠️ 手动编排 | ⚠️ 需配置 |

### 设计哲学对比

| 框架 | 设计理念 | 适用场景 |
|------|---------|---------|
| **Google ADK** | 渐进式披露、标准化 | 企业级应用、跨团队协作 |
| **LangChain** | 模块化、可组合 | 通用 LLM 应用、原型开发 |
| **AutoGen** | 多 Agent 对话、协作 | 复杂工作流、角色扮演 |
| **CrewAI** | 角色驱动、任务分配 | 团队协作场景 |
| **LlamaIndex** | 数据中心、RAG | 知识库问答、文档分析 |
| **Semantic Kernel** | 企业级、多语言 | 微软生态、企业集成 |

---

## 项目实现方案

### 架构适配

本项目基于 **LangChain + 多后端(Ollama/vLLM)** 架构，适配 Google ADK 的 Skill 规范：

```
┌───────────────────────────────────────────────┐
│           LangChain Agent                     │
│  (create_tool_calling_agent)                  │
├───────────────────────────────────────────────┤
│        Skill Tools (LangChain Tools)          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│  │ load_   │ │ clean_  │ │analyze_ │         │
│  │ data    │ │ data    │ │stats    │         │
│  └─────────┘ └─────────┘ └─────────┘         │
├───────────────────────────────────────────────┤
│      DataAnalysisSkill (Skill Core)           │
├───────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐    │
│  │  L1: Metadata (SKILL.md frontmatter) │    │
│  │  L2: Instructions (SKILL.md body)    │    │
│  │  L3: Resources (references/, assets/)│    │
│  └──────────────────────────────────────┘    │
├───────────────────────────────────────────────┤
│       Multi-Backend Support                   │
│    Ollama ◄────────────────► vLLM             │
└───────────────────────────────────────────────┘
```

### 实现亮点

1. **遵循 ADK 规范**
   - SKILL.md 包含 L1 Metadata 和 L2 Instructions
   - references/ 目录存放 L3 Resources
   - 渐进式披露：Tool 描述作为 L1，实际调用时加载完整逻辑

2. **LangChain 集成**
   - Skill 提供 `get_tools()` 方法返回 `List[StructuredTool]`
   - 可直接集成到 `create_tool_calling_agent`
   - 支持工具调用链和 Agent 编排

3. **多后端兼容**
   - 通过 `model_loader` 自动适配 Ollama/vLLM
   - 无需修改 Skill 代码即可切换后端

4. **数据分析能力**
   - 数据加载（CSV/Excel/JSON）
   - 数据清洗（去重、缺失值处理）
   - 统计分析（描述统计、相关性、分布）
   - 可视化（折线图、柱状图、散点图、热力图）

### 代码结构

```
src/skills/data_analysis/
├── SKILL.md                    # L1 + L2 规范
├── __init__.py                 # 导出接口
├── data_analysis_skill.py      # 核心实现 (600+ 行)
│   ├── DataAnalysisResult      # 统一结果对象
│   ├── DataAnalysisSkill       # Skill 主类
│   │   ├── load_data()         # 数据加载
│   │   ├── clean_data()        # 数据清洗
│   │   ├── analyze_statistics() # 统计分析
│   │   ├── visualize()         # 可视化
│   │   ├── analyze()           # 一键智能分析
│   │   └── get_tools()         # 导出 Tools
│   └── analyze_data()          # 便捷函数
├── tools.py                    # LangChain Tools 封装
│   ├── load_data_tool
│   ├── clean_data_tool
│   ├── analyze_statistics_tool
│   └── visualize_tool
└── references/                 # L3 Resources
    ├── pandas_guide.md
    └── visualization_guide.md
```

### 使用示例

**方式1：直接使用 Skill**

```python
from src.skills.data_analysis import DataAnalysisSkill

skill = DataAnalysisSkill(output_dir="./output")

# 加载数据
result = skill.load_data("data.csv")
print(result.summary)

# 生成可视化
result = skill.visualize(
    "data.csv",
    chart_type="line",
    x_column="date",
    y_column="sales",
    title="销售趋势"
)
```

**方式2：一键智能分析**

```python
from src.skills.data_analysis import analyze_data

result = analyze_data(
    file_path="data.csv",
    analysis_goal="分析销售趋势和产品表现",
    output_dir="./output"
)

print(result.summary)      # Markdown 报告
print(result.artifacts)    # 图表路径列表
```

**方式3：集成到 Agent**

```python
from src.skills.data_analysis import get_data_tools
from src.utils.model_loader import model_loader
from langchain.agents import create_tool_calling_agent

# 加载模型和工具
llm = model_loader.load_llm()
tools = get_data_tools()

# 创建 Agent
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个数据分析助手..."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# 执行自然语言查询
result = agent_executor.invoke({
    "input": "请分析 sales.csv 的销售趋势"
})
```

---

## 最佳实践总结

### Skill 设计原则

1. **单一职责**
   - 每个 Skill 专注于一个领域（如数据分析、代码审查、文档生成）
   - 复杂的 Skill 可以拆分为多个子 Skill

2. **渐进式披露**
   - L1 Metadata 简洁明了，便于 Agent 选择
   - L2 Instructions 详细完整，包含使用步骤
   - L3 Resources 按需加载，避免上下文膨胀

3. **类型安全**
   - 使用 Pydantic 定义输入输出模式
   - 清晰的参数描述和约束

4. **可观测性**
   - 详细的执行日志（使用 loguru）
   - 统一的返回结果对象

5. **错误处理**
   - 优雅处理异常情况
   - 返回有意义的错误信息

### 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| Skill 名称 | kebab-case | `data-analysis-skill` |
| Tool 名称 | snake_case | `load_data`, `analyze_statistics` |
| 类名 | PascalCase | `DataAnalysisSkill` |
| 文件/目录 | snake_case | `data_analysis_skill.py` |

### 目录结构模板

```
src/skills/{skill_name}/
├── SKILL.md                    # 必需
├── __init__.py                 # 导出接口
├── {skill_name}_skill.py       # 核心实现
├── tools.py                    # Tools 封装（可选）
├── references/                 # L3 参考资料
│   ├── guide.md
│   └── examples.md
└── assets/                     # L3 静态资源
    └── templates/
```

### 与其他框架的协作

| 场景 | 推荐方案 |
|------|---------|
| 需要复杂工作流编排 | LangGraph + Skills |
| 多 Agent 协作场景 | AutoGen + Skills |
| 团队协作任务 | CrewAI + Skills |
| RAG + 数据分析 | LlamaIndex + Skills |
| 企业微软服务集成 | Semantic Kernel + Skills |

---

## 参考资源

### 官方文档
- [Google ADK Skills](https://google.github.io/adk-docs/skills/)
- [Agent Skill Specification](https://agentskills.io/)
- [LangChain Tools](https://python.langchain.com/docs/how_to/custom_tools/)
- [AutoGen Tools](https://microsoft.github.io/autogen/docs/tutorial/tool-use/)

### 开源项目
- [Google ADK Samples](https://github.com/google/adk-samples)
- [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) - 金融数据分析 Agent
- [OpenManus](https://github.com/FoundationAgents/OpenManus) - 通用 AI Agent

### 技能市场
- [skills.sh](https://skills.sh/) - Agent Skills 市场

---

*报告生成时间: 2026-03-29*
*基于 Google ADK 规范 + LangChain 实现*
