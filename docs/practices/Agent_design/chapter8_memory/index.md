# Chapter 8: Memory Management 记忆管理

## 概述

记忆管理使 Agent 能够记住之前的交互、用户偏好和重要信息，提升个性化服务能力。

## 记忆类型

- **短期记忆**：当前对话上下文
- **长期记忆**：持久存储的用户信息

## 实现

```python
self.short_term_memory = []
self.long_term_memory = {}
```

## 运行

```bash
python src/agents/patterns/memory.py
```
