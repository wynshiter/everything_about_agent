# Chapter 6: Planning 规划模式

## 概述

规划模式使 Agent 能够将复杂任务分解为可执行的步骤序列。通过推理和计划创建，Agent 可以系统地处理多步骤任务。

## 核心概念

### 什么是规划？

规划是 Agent 将复杂目标分解为可管理步骤的能力。这涉及：
- 任务分解
- 步骤排序
- 依赖关系管理
- 执行和调整

### 规划方法

1. **静态规划**：预先定义所有步骤
2. **动态规划**：根据上下文实时生成步骤
3. **ReAct**：推理+行动交织进行

## LangChain 实现

```python
planning_prompt = ChatPromptTemplate.from_template(
    "Break down the task into numbered steps: {task}"
)
chain = planning_prompt | llm | StrOutputParser()
```

## Google ADK 实现

使用 LoopAgent 实现迭代执行：
```python
from google.adk.agents import LoopAgent, LlmAgent
```

## 运行示例

```bash
python src/agents/patterns/planning.py
```
