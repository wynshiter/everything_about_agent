# Skills 集成完整指南

> 本文档汇总所有 Skills 相关的文档和资料，帮助你快速上手和深入理解。

## 📚 文档导航

### 入门文档
| 文档 | 描述 | 适合人群 |
|------|------|----------|
| [快速开始](#快速开始) | 5 分钟上手 | 新用户 |
| [examples/skills_demo/README.md](../examples/skills_demo/README.md) | 详细使用示例 | 初学者 |
| [src/skills/data_analysis/SKILL.md](../src/skills/data_analysis/SKILL.md) | 数据分析 Skill 规范 | 使用者 |

### 架构文档
| 文档 | 描述 | 适合人群 |
|------|------|----------|
| [docs/skills_integration_research.md](skills_integration_research.md) | 全网调研报告 | 架构师 |
| [docs/skills_architecture.md](skills_architecture.md) | 架构设计详解 | 开发者 |
| [src/skills/README.md](../src/skills/README.md) | API 参考和最佳实践 | 开发者 |

### 代码示例
| 文件 | 描述 | 场景 |
|------|------|------|
| [examples/skills_demo/demo_data_analysis_skill.py](../examples/skills_demo/demo_data_analysis_skill.py) | 完整演示 | 全面理解 |
| [examples/skills_demo/test_skill_simple.py](../examples/skills_demo/test_skill_simple.py) | 简单测试 | 快速验证 |
| [examples/skills_demo/advanced_examples.py](../examples/skills_demo/advanced_examples.py) | 高级示例 | 进阶用法 |

---

## 快速开始

### 1. 安装（1分钟）

```bash
cd d:/code/python/everything_about_agent

# 安装数据分析依赖
pip install pandas matplotlib seaborn openpyxl
```

### 2. 验证（1分钟）

```bash
# Windows PowerShell
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
python examples/skills_demo/test_skill_simple.py
```

预期输出：
```
Loading: .../sample_sales_data.csv
Success: True
Rows: 30
Columns: 8
Chart generated: True
Chart path: output/chart_bar_xxxx.png
Test completed!
```

### 3. 使用（3分钟）

#### 方式A: 直接使用（无需 LLM）

```python
from src.skills.data_analysis import DataAnalysisSkill

skill = DataAnalysisSkill(output_dir="./output")

# 加载数据
result = skill.load_data("data.csv")
print(result.summary)

# 生成图表
skill.visualize("data.csv", chart_type="bar", 
                x_column="product", y_column="sales",
                title="产品销售对比")
```

#### 方式B: 集成到 Agent（需要 LLM）

```python
from src.skills.data_analysis import get_data_tools
from src.utils.model_loader import model_loader
from langchain.agents import create_tool_calling_agent

# 加载模型和工具
llm = model_loader.load_llm()
tools = get_data_tools()

# 创建 Agent
agent = create_tool_calling_agent(llm, tools, prompt)

# 自然语言查询
result = agent.invoke({"input": "分析销售数据，哪个产品卖得最好？"})
```

---

## 核心概念

### Skill 是什么？

Skill 是一个**自包含的功能单元**，遵循三层架构：

```
L1 - Metadata (启动时加载)
  └── 名称、描述、版本
  
L2 - Instructions (激活时加载)
  └── 使用说明、步骤、示例
  
L3 - Resources (按需加载)
  └── 参考资料、代码片段
```

### 与 Google ADK 的关系

本项目采用 Google ADK 的 Skill 规范，但适配到 LangChain + 多后端架构：

| 特性 | Google ADK | 本项目 |
|------|-----------|--------|
| 规范 | ✅ SKILL.md | ✅ 兼容 |
| 后端 | Google/Vertex AI | ✅ Ollama/vLLM |
| Agent 框架 | ADK Agents | ✅ LangChain |
| 渐进披露 | ✅ L1/L2/L3 | ✅ 模拟实现 |

---

## 功能特性

### 数据分析 Skill (data_analysis)

#### 数据操作
- ✅ CSV/Excel/JSON 加载
- ✅ 数据清洗（去重、缺失值处理）
- ✅ 描述性统计
- ✅ 相关性分析
- ✅ 分布分析

#### 可视化
- ✅ 折线图（趋势）
- ✅ 柱状图（对比）
- ✅ 散点图（关系）
- ✅ 热力图（相关性）
- ✅ 饼图（占比）
- ✅ 直方图（分布）

#### 集成方式
- ✅ 直接使用（无 LLM）
- ✅ LangChain Agent 集成
- ✅ 多 Agent 系统

---

## 使用场景

### 场景1: 数据探索分析

```python
from src.skills.data_analysis import analyze_data

# 一键分析
result = analyze_data(
    file_path="sales.csv",
    analysis_goal="分析销售趋势和关键指标",
    output_dir="./output"
)

print(result.summary)      # Markdown 报告
print(result.artifacts)    # 图表路径
```

### 场景2: 智能数据助手

```python
# 让 LLM 自主分析
agent = create_tool_calling_agent(llm, get_data_tools(), prompt)

response = agent.invoke({
    "input": "分析数据并告诉我关键洞察"
})
```

### 场景3: 批量数据处理

```python
# 批量分析多个文件
for file in csv_files:
    result = skill.analyze(str(file), f"分析 {file.stem}")
    results.append(result)
```

### 场景4: 自定义分析流程

```python
# 扩展 Skill 类
class MyAnalysisSkill(DataAnalysisSkill):
    def custom_analysis(self, file_path):
        # 自定义逻辑
        pass
```

---

## 项目结构

```
everything_about_agent/
├── src/skills/                           # Skills 目录
│   ├── README.md                         # 详细使用文档
│   ├── data_analysis/                    # 数据分析 Skill
│   │   ├── SKILL.md                      # 规范定义
│   │   ├── __init__.py                   # 模块导出
│   │   ├── data_analysis_skill.py        # 核心实现
│   │   ├── tools.py                      # Tools 封装
│   │   └── references/                   # L3 资源
│   │       ├── pandas_guide.md
│   │       └── visualization_guide.md
│   └── (其他 Skills...)
│
├── examples/skills_demo/                 # 示例代码
│   ├── README.md                         # 示例文档
│   ├── demo_data_analysis_skill.py       # 完整演示
│   ├── advanced_examples.py              # 高级示例
│   └── sample_sales_data.csv             # 示例数据
│
├── docs/
│   ├── SKILLS_GUIDE.md                   # 本文档
│   ├── skills_integration_research.md    # 调研报告
│   └── skills_architecture.md            # 架构设计
│
└── output/                               # 输出目录
    └── *.png                             # 生成的图表
```

---

## API 速查

### DataAnalysisSkill

```python
# 初始化
skill = DataAnalysisSkill(output_dir="./output")

# 数据操作
skill.load_data(file_path, file_type="csv")
skill.clean_data(file_path, operations=["drop_duplicates"])
skill.analyze_statistics(file_path, analysis_type="correlation")

# 可视化
skill.visualize(file_path, chart_type="bar", 
                x_column="col1", y_column="col2")

# 一键分析
skill.analyze(file_path, analysis_goal="描述")

# Agent 集成
skill.get_tools()  # 返回 List[StructuredTool]
```

### 便捷函数

```python
from src.skills.data_analysis import (
    analyze_data,        # 一键分析
    get_data_tools,      # 获取所有 Tools
    DataAnalysisSkill,   # Skill 类
    DataAnalysisResult,  # 结果对象
)
```

---

## 最佳实践

### 1. 选择合适的集成方式

| 场景 | 推荐方式 | 原因 |
|------|---------|------|
| 批处理脚本 | 直接使用 | 快速、无依赖 |
| 交互式分析 | Agent 集成 | 自然语言交互 |
| 复杂流程 | 自定义流程 | 精确控制 |

### 2. 性能优化

```python
# 批量处理
for chunk in pd.read_csv(file, chunksize=10000):
    process(chunk)

# 缓存结果
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_analysis(file_hash):
    return skill.analyze(file_hash)
```

### 3. 错误处理

```python
result = skill.load_data("file.csv")

if not result.success:
    print(f"Error: {result.error_message}")
    # 降级处理
else:
    # 正常处理
    pass
```

---

## 扩展开发

### 创建新 Skill 步骤

1. **创建目录**
```bash
mkdir -p src/skills/my_skill/{references,assets}
```

2. **编写 SKILL.md**
```markdown
---
name: my-skill
description: 功能描述
metadata:
  version: "1.0.0"
---

# My Skill

## 功能概述
...
```

3. **实现 Skill 类**
```python
class MySkill:
    def process(self, param: str) -> Result:
        # 实现
        pass
    
    def get_tools(self):
        return [StructuredTool(...)]
```

4. **导出接口**
```python
# __init__.py
from .my_skill import MySkill
__all__ = ["MySkill"]
```

详细指南见 [src/skills/README.md](../src/skills/README.md)

---

## 常见问题

### Q: 如何支持更多数据格式？

扩展 `load_data` 方法：
```python
if file_type == "parquet":
    df = pd.read_parquet(file_path)
```

### Q: 如何处理大数据集？

使用分块读取：
```python
for chunk in pd.read_csv(file, chunksize=10000):
    process(chunk)
```

### Q: 如何自定义图表样式？

扩展可视化方法：
```python
def visualize_custom(self, file_path, style_config):
    plt.rcParams.update(style_config)
    return self.visualize(...)
```

更多问题见 [src/skills/README.md#故障排查](../src/skills/README.md#故障排查)

---

## 参考资源

### 官方文档
- [Google ADK Skills](https://google.github.io/adk-docs/skills/)
- [Agent Skill Specification](https://agentskills.io/)
- [LangChain Tools](https://python.langchain.com/docs/how_to/custom_tools/)

### 项目文档
- [完整调研报告](skills_integration_research.md) - 全网 Skills 调研
- [架构设计](skills_architecture.md) - 详细架构说明
- [API 参考](../src/skills/README.md) - 完整 API 文档
- [使用示例](../examples/skills_demo/README.md) - 详细使用示例

### 社区
- [skills.sh](https://skills.sh/) - Agent Skills 市场

---

## 更新日志

### v1.0.0 (2026-03-29)
- ✅ 数据分析 Skill 完整实现
- ✅ 支持 6 种图表类型
- ✅ LangChain Agent 集成
- ✅ 多后端兼容 (Ollama/vLLM)
- ✅ 完整文档和示例

---

## 贡献指南

欢迎贡献新的 Skills！请遵循以下规范：

1. **目录结构**: 遵循 `src/skills/{skill_name}/` 结构
2. **文档**: 必须包含 SKILL.md，遵循 L1/L2/L3 规范
3. **代码**: 继承 BaseSkill，实现 get_tools() 方法
4. **测试**: 包含单元测试和集成测试
5. **示例**: 提供使用示例代码

---

*文档版本: 1.0.0*
*最后更新: 2026-03-29*

**下一步**: 查看 [examples/skills_demo/README.md](../examples/skills_demo/README.md) 开始实践！
