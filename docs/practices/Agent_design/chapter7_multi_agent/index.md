# Chapter 7: Multi-Agent Collaboration 多智能体协作模式

## 概述

多智能体协作模式通过多个专业化的 Agent 协同工作来解决复杂问题。每个 Agent 有特定的角色和目标，通过协作产生超越单个 Agent 的能力。

## 核心概念

### 协作形式

1. **顺序交接**：一个 Agent 完成後传递给下一个
2. **并行处理**：多个 Agent 同时工作
3. **层级结构**：Supervisor 管理 Worker Agents
4. **专家团队**：不同领域的专业 Agent 协作

### 通信结构

- Network: 去中心化点对点
- Supervisor: 中央协调器
- Hierarchical: 多层管理结构

## 实现框架

### CrewAI

```python
from crewai import Agent, Task, Crew

researcher = Agent(role='Researcher', goal='Research topic')
writer = Agent(role='Writer', goal='Write content')

crew = Crew(agents=[researcher, writer], tasks=[...])
```

### Google ADK

```python
from google.adk.agents import SequentialAgent, ParallelAgent, LlmAgent
```

## 运行示例

```bash
python src/agents/patterns/multi_agent.py
```
