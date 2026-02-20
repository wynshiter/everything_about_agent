# Chapter 5: Tool Use 工具使用模式

## 概述

工具使用模式（也称为 Function Calling）使 Agent 能够与外部系统交互，获取实时信息、执行计算、调用 API 等。这是将 LLM 从文本生成器转变为能够感知、推理和行动的 Agent 的核心技术。

## 核心概念

### 工具调用流程

1. **工具定义**：定义外部函数并描述给 LLM
2. **LLM 决策**：LLM 判断是否需要调用工具
3. **生成调用**：LLM 生成结构化的函数调用
4. **执行工具**：框架执行实际的外部函数
5. **返回结果**：工具结果返回给 LLM
6. **处理结果**：LLM 使用工具结果生成最终响应

### 可用工具类型

- **信息检索**：搜索 API、数据库查询
- **计算工具**：数学计算、数据分析
- **执行工具**：代码执行、系统操作
- **通信工具**：发送邮件、消息
- **控制工具**：智能家居、设备控制

## LangChain 实现

### 定义工具

```python
from langchain_core.tools import tool

@tool
def search_information(query: str) -> str:
    """Provides factual information on a given topic."""
    # Implementation here
    pass
```

### 创建 Tool-Calling Agent

```python
from langchain.agents import create_tool_calling_agent, AgentExecutor

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)
```

### 绑定工具到 LLM

```python
llm_with_tools = llm.bind_tools(tools)
```

## Google ADK 实现

### 使用内置工具

```python
from google.adk.agents import LlmAgent
from google.adk.tools import google_search, code_execution

tool_agent = LlmAgent(
    name="ToolAgent",
    model="gemini-2.0-flash",
    tools=[google_search, code_execution]
)
```

### 常用内置工具

| 工具 | 功能 |
|------|------|
| google_search | 搜索互联网 |
| code_execution | 执行 Python 代码 |
| vertex_search | 搜索企业知识库 |

## 适用场景

1. **实时信息获取** - 天气、股票价格、新闻
2. **数据库交互** - 查询、更新数据
3. **执行计算** - 数学运算、数据分析
4. **发送通信** - 邮件、消息
5. **代码执行** - 运行代码片段
6. **系统控制** - 智能家居、IoT

## 注意事项

- 工具描述要清晰、准确
- 处理工具执行错误
- 避免过度依赖工具
- 考虑安全性

## 运行示例

```bash
python src/agents/patterns/tool_use.py
```

## 参考

- LangChain Tools: https://python.langchain.com/docs/modules/tools/
- Google ADK Tools: https://google.github.io/adk-docs/tools/
