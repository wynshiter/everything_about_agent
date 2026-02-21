---
name: MkDocs文档站点优化
overview: 使用MkDocs优化Agent设计模式文档展示，配置21个章节按难度级别分组，并添加入口到启动脚本
todos:
  - id: update-mkdocs-config
    content: 更新 mkdocs.yml 配置文件，添加全部21个章节导航
    status: completed
  - id: verify-chapter-docs
    content: 检查并补充所有章节的 index.md 文件
    status: completed
    dependencies:
      - update-mkdocs-config
  - id: update-start-bat
    content: 修改 start.bat 添加 MkDocs 服务启动选项
    status: completed
    dependencies:
      - update-mkdocs-config
  - id: update-start-sh
    content: 修改 start.sh 添加 MkDocs 服务启动选项
    status: completed
    dependencies:
      - update-start-bat
  - id: test-mkdocs-service
    content: 测试 MkDocs 服务启动和文档展示效果
    status: completed
    dependencies:
      - update-start-bat
---

## 用户需求

1. 使用 MkDocs 实现文档独立展示功能（与现有HTML前端共存）
2. 在启动脚本中添加 MkDocs 服务启动选项
3. 按难度级别（基础/进阶/高级）组织21个章节
4. 完善主页导航链接，确保每个章节能从主页正确跳转
5. 实现简洁美观的文档展示界面，保持整体风格一致

## 核心功能

- 文档独立展示：每个设计模式章节作为独立文档页面
- 导航完善：主页与文档之间的双向链接
- 服务启动：启动脚本集成 MkDocs 服务管理
- 界面美观：使用 Material 主题，保持简洁专业风格

## 技术方案

- **文档框架**: MkDocs + Material 主题
- **启动方式**: MkDocs serve --dev-addr 实现本地服务
- **端口管理**: 复用现有端口选择逻辑，使用 Python socket 查找可用端口
- **文件结构**: docs/practices/Agent_design/ 下21个章节的 index.md 文件

## 实现步骤

### 1. 更新 mkdocs.yml 配置

扩展 mkdocs.yml 配置文件，添加全部21个章节导航，按难度分组：

- 基础模式 (basic): Chaining, Routing, Parallelization, Reflection
- 进阶模式 (intermediate): Tool Use, Planning, Multi-Agent, Memory, Learning, MCP, Goal Setting, Exception Handling, Human-in-Loop, RAG, A2A
- 高级模式 (advanced): Reasoning, Guardrails, Evaluation, Prioritization, Exploration

### 2. 更新章节 index.md

确保所有21个章节的 index.md 文件存在且内容完整

### 3. 修改 start.bat 启动脚本

- 添加选项启动 MkDocs 服务
- 使用 Python 查找可用端口
- 显示访问 URL

### 4. 修改 start.sh (Linux版本)

同步添加 MkDocs 启动选项

### 5. 优化文档样式

配置 Material 主题的美化选项：导航栏、代码高亮、配色方案

## Agent 扩展

无需使用额外扩展，本任务为配置和脚本修改类任务