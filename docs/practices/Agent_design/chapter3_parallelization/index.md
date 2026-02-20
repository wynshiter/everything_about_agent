# Chapter 3: Parallelization 并行化模式

## 概述

并行化模式通过同时执行多个独立任务来提高 Agent 的效率。与顺序执行不同，并行化允许独立的子任务同时运行，显著减少总体执行时间。

## 核心概念

### 什么是并行化？

当工作流中存在多个**相互独立**的子任务时，可以同时执行它们而不是等待一个完成后再开始下一个。这对于涉及外部 API 调用、数据库查询等有延迟的操作特别有效。

### 适用场景

1. **信息收集与研究** - 同时从多个来源获取信息
2. **数据处理与分析** - 对不同数据段并行执行分析
3. **多 API 调用** - 并行查询多个独立的 API
4. **内容生成** - 并行生成复杂内容的不同部分
5. **验证与检查** - 并行执行多个独立验证

## LangChain 实现

### 使用 RunnableParallel

```python
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# 定义三个独立的处理分支
summarize_chain = summarize_prompt | llm | StrOutputParser()
questions_chain = questions_prompt | llm | StrOutputParser()
terms_chain = terms_prompt | llm | StrOutputParser()

# 并行执行
map_chain = RunnableParallel({
    "summary": summarize_chain,
    "questions": questions_chain,
    "key_terms": terms_chain,
    "original_topic": RunnablePassthrough()
})

# 合成结果
full_chain = map_chain | synthesis_prompt | llm | StrOutputParser()
```

### 关键组件

| 组件 | 作用 |
|------|------|
| `RunnableParallel` | 并行执行多个 Runnable |
| `RunnablePassthrough` | 传递原始输入到下一步 |

## Google ADK 实现

### ParallelAgent

```python
from google.adk.agents import ParallelAgent, LlmAgent

# 定义并行执行的子 Agent
researcher_1 = LlmAgent(
    name="Researcher1",
    model="gemini-2.0-flash",
    instruction="Research topic A",
    output_key="result_a"
)

researcher_2 = LlmAgent(
    name="Researcher2",
    model="gemini-2.0-flash", 
    instruction="Research topic B",
    output_key="result_b"
)

# 创建并行 Agent
parallel_agent = ParallelAgent(
    name="ParallelResearch",
    sub_agents=[researcher_1, researcher_2]
)
```

## 核心优势

1. **降低延迟** - 总体执行时间接近最长单个任务的时间
2. **提高吞吐量** - 更有效地利用计算资源
3. **改善用户体验** - 更快获得完整结果

## 注意事项

- 只能并行执行**相互独立**的任务
- 并行化增加了系统复杂度和成本
- 需要适当的错误处理和结果聚合机制

## 运行示例

```bash
# 运行并行化演示
python src/agents/patterns/parallelization.py
```

## 参考

- LangChain LCEL: https://python.langchain.com/docs/introduction/
- Google ADK: https://google.github.io/adk-docs/
