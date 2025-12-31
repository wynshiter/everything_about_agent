# Chapter 1: Prompt Chaining (提示词链)

## 📖 核心概念

**Prompt Chaining (提示词链)** 是一种将复杂任务分解为一系列较小、较简单的子任务的设计模式。每个子任务由一个独立的 LLM 调用（Prompt）处理，前一个步骤的输出作为下一个步骤的输入。

这种模式的优势在于：
*   **降低复杂度**：LLM 在处理单一、专注的任务时表现更好。
*   **提高可靠性**：可以检查和验证每一步的中间结果。
*   **便于调试**：容易定位哪个环节出了问题。

## 🛠 代码功能介绍

本章节的代码文件 `chapter1_chaining_practice.py` 包含两个练习：

1.  **基础提取流水线 (Basic Extraction Pipeline)**:
    *   **输入**: 一段包含技术规格的非结构化文本。
    *   **步骤 1**: 提取关键参数（CPU, 内存, 存储）。
    *   **步骤 2**: 将提取的信息转换为标准的 JSON 格式。
    *   **输出**: JSON 对象。

2.  **创意写作流水线 (Creative Writing Pipeline)**:
    *   **输入**: 一个写作主题。
    *   **步骤 1**: 生成一个吸引人的标题。
    *   **步骤 2**: 根据标题生成大纲。
    *   **步骤 3**: 根据标题和大纲撰写引言。
    *   **输出**: 完整的博客文章引言。

## ⚙️ 运行环境与依赖

*   **Python**: 3.10+
*   **依赖包**:
    *   `langchain`
    *   `langchain-core`
    *   `loguru`
    *   项目自身的 `src` 模块 (需正确配置 PYTHONPATH)

## 🚀 执行步骤

### 方法 1: 使用启动脚本 (推荐)

1.  在文件资源管理器中找到本目录。
2.  双击运行 **`run.bat`** 脚本。

### 方法 2: 命令行运行

1.  打开终端 (Terminal) 或命令提示符 (CMD)。
2.  导航到本目录：
    ```bash
    cd d:\code\python\everything_about_agent\src\practices\Agent_design\chapter1_chaining
    ```
3.  运行 Python 脚本：
    ```bash
    python chapter1_chaining_practice.py
    ```

---
**注意**: 请确保已经正确配置了项目根目录下的 `configs/models.yaml`，并启动了相应的模型后端 (Ollama 或 vLLM)。
