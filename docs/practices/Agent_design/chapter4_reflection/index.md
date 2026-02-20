# Chapter 4: Reflection 反思模式

## 概述

反思模式引入了一个反馈循环，使 Agent 能够评估和改进自己的输出。通过引入"生产者-批评者"机制，Agent 可以迭代地改进结果，提高质量和准确性。

## 核心概念

### 什么是反思？

反思模式让 Agent 评估自己的工作成果，并利用评估结果来改进性能。这是一种自我纠正或自我改进的形式。

### 工作流程

1. **执行**：Agent 执行任务或生成初始输出
2. **评估/批评**：Agent 分析上一步的结果
3. **反思/改进**：根据批评确定如何改进
4. **迭代**：重复直到达到满意结果或满足停止条件

### 生产者-批评者模型

最有效的实现是将过程分为两个独立角色：
- **生产者 (Producer)**：负责生成初始内容
- **批评者 (Critic)**：专门评估生产者的输出

## 适用场景

1. **创意写作** - 改进生成的文本、故事、营销文案
2. **代码生成与调试** - 编写代码、识别错误、修复问题
3. **复杂问题解决** - 评估多步推理任务中的中间步骤
4. **摘要与合成** - 改进摘要的准确性、完整性和简洁性
5. **规划与策略** - 评估计划并识别潜在缺陷

## LangChain 实现

### 迭代反思循环

```python
for i in range(max_iterations):
    # 生成或改进
    output = generate(task, history)
    
    # 反思
    critique = reflect(task, output)
    
    if "PERFECT" in critique:
        break
    
    history.append({"output": output, "critique": critique})
```

### 关键组件

| 组件 | 作用 |
|------|------|
| `generate()` | 生成或改进输出 |
| `reflect()` | 评估输出并提供批评 |
| 迭代循环 | 持续改进直到满足条件 |

## Google ADK 实现

### SequentialAgent 实现

```python
from google.adk.agents import SequentialAgent, LlmAgent

generator = LlmAgent(
    name="Generator",
    output_key="draft",
    instruction="Generate initial content"
)

reviewer = LlmAgent(
    name="Reviewer",
    input_key="draft",
    output_key="review", 
    instruction="Review and critique the draft"
)

pipeline = SequentialAgent(
    name="ReflectionPipeline",
    sub_agents=[generator, reviewer]
)
```

## 核心优势

1. **提高质量** - 迭代改进产生更准确、更完整的结果
2. **自我纠正** - Agent 能够识别和修复自己的错误
3. **适应性** - 根据反馈动态调整方法

## 注意事项

- 每次迭代都会增加延迟和成本
- 需要管理上下文长度以避免超出限制
- 迭代历史会快速膨胀

## 运行示例

```bash
python src/agents/patterns/reflection.py
```

## 参考

- LangChain: https://python.langchain.com/docs/introduction/
- Google ADK: https://google.github.io/adk-docs/
