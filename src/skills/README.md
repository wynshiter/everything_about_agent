# Skills 目录

本目录包含遵循 Google ADK Skill 规范的模块化能力组件。Skills 是**可复用的功能单元**，可以被 Agent 动态发现和调用。

## 目录

- [核心概念](#核心概念)
- [快速开始](#快速开始)
- [现有 Skills](#现有-skills)
- [API 参考](#api-参考)
- [设计模式](#设计模式)
- [创建新 Skill](#创建新-skill)
- [最佳实践](#最佳实践)
- [故障排查](#故障排查)

---

## 核心概念

### 什么是 Skill？

Skill 是一个**自包含的功能单元**，封装了特定领域的知识和能力。它遵循 [Agent Skill Specification](https://agentskills.io) 开放标准。

```
┌─────────────────────────────────────────┐
│              Skill                      │
├─────────────────────────────────────────┤
│  L1 - Metadata                          │
│  (名称、描述、版本、能力标签)             │
├─────────────────────────────────────────┤
│  L2 - Instructions                      │
│  (使用说明、步骤、示例、约束)             │
├─────────────────────────────────────────┤
│  L3 - Resources                         │
│  (参考资料、代码片段、模板)               │
├─────────────────────────────────────────┤
│  Implementation                         │
│  (Python 实现、Tools 封装)               │
└─────────────────────────────────────────┘
```

### 三层渐进式架构

采用 **Google ADK** 的渐进式披露（Progressive Disclosure）设计：

| 层级 | 名称 | 内容 | 加载时机 | 大小 |
|------|------|------|----------|------|
| **L1** | Metadata | Skill 名称、描述、版本等 | Agent 启动时 | ~100B |
| **L2** | Instructions | Skill 主要指令、使用步骤 | Skill 被激活时 | ~1KB |
| **L3** | Resources | 参考资料、资产、脚本 | 按需加载 | ~10KB+ |

**优势**: 最小化对 Agent 上下文窗口的影响，只有被使用的 Skill 才会加载完整内容。

---

## 快速开始

### 方式1: 直接使用 Skill

适合脚本、数据处理任务，无需 LLM 参与。

```python
from src.skills.data_analysis import DataAnalysisSkill, analyze_data

# 初始化 Skill
skill = DataAnalysisSkill(output_dir="./output")

# 加载并分析数据
result = skill.load_data("data/sales.csv")
print(f"数据规模: {result.statistics['rows']} 行")

# 生成可视化
viz_result = skill.visualize(
    "data/sales.csv",
    chart_type="line",
    x_column="date",
    y_column="revenue",
    title="收入趋势"
)

# 一键智能分析
full_result = skill.analyze(
    file_path="data/sales.csv",
    analysis_goal="分析销售趋势和关键指标",
    auto_visualize=True
)

print(full_result.summary)  # Markdown 格式报告
print(full_result.artifacts)  # 生成的图表路径
```

### 方式2: 集成到 LangChain Agent

让 LLM 自主决定如何使用数据分析能力。

```python
from src.skills.data_analysis import get_data_tools
from src.utils.model_loader import model_loader
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# 1. 加载模型（自动适配 Ollama/vLLM）
llm = model_loader.load_llm()

# 2. 获取数据分析工具
tools = get_data_tools()

# 3. 创建 Agent
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的数据分析师。

你可以使用以下工具帮助用户分析数据：
1. load_data - 加载 CSV/Excel/JSON 数据文件
2. clean_data - 清洗数据（去重、处理缺失值）
3. analyze_statistics - 执行统计分析
4. visualize_data - 生成可视化图表

工作流程：
1. 先加载数据了解数据结构
2. 根据用户问题选择合适的分析方法
3. 使用可视化辅助数据理解
4. 用中文回复，提供清晰的结论
"""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10
)

# 4. 执行自然语言查询
response = agent_executor.invoke({
    "input": "请分析 sales.csv 文件，告诉我哪个产品销量最好，并生成柱状图"
})

print(response["output"])
```

### 方式3: 在 Multi-Agent 系统中使用

结合其他 Agent 模式使用。

```python
from src.skills.data_analysis import get_data_tools
from src.agents.patterns.routing import RouterAgent

# 数据分析专用 Agent
data_agent = Agent(
    name="DataAnalyst",
    tools=get_data_tools(),
    system_message="你专门负责数据分析任务"
)

# 路由 Agent 根据任务类型分配
router = RouterAgent(agents={
    "data_analysis": data_agent,
    "code_generation": code_agent,
    "qa": qa_agent
})

result = router.route("分析销售数据")  # 自动路由到 data_agent
```

---

## 现有 Skills

### data_analysis - 数据分析 Skill

专业的数据分析能力，支持完整的数据处理流程。

#### 功能特性

| 功能 | 说明 | 对应 Tool |
|------|------|-----------|
| **数据加载** | 支持 CSV、Excel、JSON 格式 | `load_data` |
| **数据清洗** | 去重、缺失值处理、类型转换 | `clean_data` |
| **描述统计** | 均值、标准差、分位数等 | `analyze_statistics` |
| **相关性分析** | 相关系数矩阵、强相关识别 | `analyze_statistics` |
| **分布分析** | 偏度、峰度、分布特征 | `analyze_statistics` |
| **趋势可视化** | 折线图、柱状图、散点图 | `visualize_data` |
| **相关性可视化** | 热力图 | `visualize_data` |
| **占比可视化** | 饼图 | `visualize_data` |

#### 快速参考

```python
from src.skills.data_analysis import (
    DataAnalysisSkill,      # Skill 主类
    analyze_data,           # 便捷函数
    get_data_tools,         # 获取 Tools 列表
    DataAnalysisResult,     # 结果对象
)

# 常用方法
skill = DataAnalysisSkill(output_dir="./output")

# 数据操作
skill.load_data(file_path, file_type="csv")
skill.clean_data(file_path, operations=["drop_duplicates", "fillna_mean"])
skill.analyze_statistics(file_path, analysis_type="correlation")

# 可视化
skill.visualize(
    file_path,
    chart_type="line",      # line/bar/scatter/histogram/heatmap/pie
    x_column="date",
    y_column="sales",
    title="图表标题"
)

# 一键分析
skill.analyze(file_path, analysis_goal="分析目标描述")
```

#### 详细文档

- [SKILL.md](data_analysis/SKILL.md) - 规范定义和使用说明
- [references/pandas_guide.md](data_analysis/references/pandas_guide.md) - Pandas 速查
- [references/visualization_guide.md](data_analysis/references/visualization_guide.md) - 可视化指南

---

## API 参考

### DataAnalysisSkill 类

```python
class DataAnalysisSkill:
    """
    数据分析 Skill 主类
    
    Args:
        output_dir: 输出文件保存目录，默认 "./output"
    """
    
    def __init__(self, output_dir: str = "./output")
    
    # 数据操作
    def load_data(self, file_path: str, file_type: str = "csv", 
                  encoding: str = "utf-8") -> DataAnalysisResult
    
    def clean_data(self, file_path: str, 
                   operations: List[str] = None,
                   output_path: Optional[str] = None) -> DataAnalysisResult
    
    def analyze_statistics(self, file_path: str,
                          analysis_type: str = "overview",
                          columns: Optional[List[str]] = None,
                          group_by: Optional[str] = None) -> DataAnalysisResult
    
    def visualize(self, file_path: str, chart_type: str,
                  x_column: str, y_column: Optional[str] = None,
                  title: str = "Chart",
                  output_path: Optional[str] = None) -> DataAnalysisResult
    
    # 高级功能
    def analyze(self, file_path: str, analysis_goal: str,
                auto_visualize: bool = True) -> DataAnalysisResult
    
    # Agent 集成
    def get_tools(self) -> List[StructuredTool]
```

### DataAnalysisResult 对象

```python
@dataclass
class DataAnalysisResult:
    success: bool                    # 执行是否成功
    summary: str                     # 结果摘要（Markdown 格式）
    statistics: Dict[str, Any]       # 详细统计数据
    artifacts: List[Dict[str, str]]  # 生成的文件（图表等）
    execution_log: List[str]         # 执行日志
    error_message: Optional[str]     # 错误信息（失败时）
```

### 便捷函数

```python
def analyze_data(
    file_path: str,
    analysis_goal: str,
    output_dir: str = "./output"
) -> DataAnalysisResult
"""一键分析函数，封装完整分析流程"""

def get_data_tools() -> List[StructuredTool]
"""获取所有数据分析工具，用于 Agent 集成"""
```

---

## 设计模式

### 模式1: Tool Wrapper（工具包装）

将现有库/工具包装为 Skill。

```python
# 示例：将 Pandas 包装为 Skill
class PandasSkill:
    def __init__(self):
        self.context = {}
    
    def get_tools(self):
        return [
            StructuredTool.from_function(
                func=self.query_dataframe,
                name="query_dataframe",
                description="使用 Pandas 查询 DataFrame",
                args_schema=QueryInput,
            )
        ]
    
    def query_dataframe(self, query: str) -> str:
        """执行 Pandas 查询"""
        df = self.context.get("current_df")
        result = df.query(query)
        return result.to_json()
```

### 模式2: Pipeline（管道）

多步骤顺序执行，每个步骤可独立复用。

```python
class DataPipelineSkill:
    """数据处理管道 Skill"""
    
    def pipeline(self, file_path: str, steps: List[str]) -> DataAnalysisResult:
        """
        执行数据处理管道
        
        steps: ["load", "clean", "transform", "analyze", "visualize"]
        """
        for step in steps:
            if step == "load":
                self.load_data(file_path)
            elif step == "clean":
                self.clean_data(file_path)
            # ...
```

### 模式3: Generator（生成器）

确保输出格式一致的生成型 Skill。

```python
class ReportGeneratorSkill:
    """报告生成 Skill"""
    
    def generate_report(self, data: Dict, template: str) -> str:
        """
        根据模板生成报告
        
        Args:
            data: 报告数据
            template: 模板名称（引用自 L3 assets/）
        """
        template_content = self._load_template(template)
        return self._fill_template(template_content, data)
```

### 模式4: Reviewer（审查器）

分离"检查什么"和"如何检查"。

```python
class DataQualitySkill:
    """数据质量检查 Skill"""
    
    def review(self, file_path: str, checks: List[str]) -> DataAnalysisResult:
        """
        执行数据质量检查
        
        checks: ["completeness", "uniqueness", "consistency", "validity"]
        """
        results = {}
        for check in checks:
            results[check] = getattr(self, f"_check_{check}")(file_path)
        return DataAnalysisResult(success=True, statistics=results)
```

---

## 创建新 Skill

### 步骤1: 创建目录结构

```bash
# 使用脚本创建标准结构
mkdir -p src/skills/my_skill/{references,assets}
touch src/skills/my_skill/{SKILL.md,__init__.py,my_skill.py,tools.py}
```

### 步骤2: 编写 SKILL.md

```markdown
---
name: my-skill
description: |
  清晰描述 Skill 的功能，这是 LLM 选择 Skill 的关键依据。
  描述应包含：功能、适用场景、输入输出。
metadata:
  version: "1.0.0"
  author: "Your Name"
  category: "data_processing"
  adk_additional_tools:
    - "tool1"
    - "tool2"
  tags:
    - "data"
    - "processing"
---

# My Skill

## 功能概述

本 Skill 提供 XXX 能力，可以：
1. 功能点1
2. 功能点2
3. 功能点3

## 使用场景

- 场景1: XXX
- 场景2: XXX

## 使用步骤

### Step 1: 准备工作
```python
# 示例代码
```

### Step 2: 执行主流程
```python
# 示例代码
```

### Step 3: 处理结果
```python
# 示例代码
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| param1 | str | 是 | 参数1说明 |
| param2 | int | 否 | 参数2说明，默认0 |

## 最佳实践

1. 建议1
2. 建议2

## 参考资料

- [参考文档1](references/guide1.md)
- [参考文档2](references/guide2.md)
```

### 步骤3: 实现 Skill 类

```python
# src/skills/my_skill/my_skill.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from loguru import logger


@dataclass
class MySkillResult:
    """Skill 执行结果"""
    success: bool
    summary: str
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class MySkillInput(BaseModel):
    """输入参数模式"""
    param1: str = Field(..., description="参数1说明")
    param2: int = Field(default=0, description="参数2说明")


class MySkill:
    """
    My Skill 实现
    
    提供 XXX 能力，可用于 YYY 场景。
    
    Example:
        skill = MySkill()
        result = skill.process(param1="value")
        print(result.summary)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 Skill
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.context: Dict[str, Any] = {}
        logger.info("[MySkill] initialized")
    
    def _log(self, message: str):
        """记录执行日志"""
        self.context.setdefault("execution_log", []).append(message)
        logger.info(message)
    
    def process(self, param1: str, param2: int = 0) -> MySkillResult:
        """
        核心处理逻辑
        
        Args:
            param1: 参数1
            param2: 参数2
            
        Returns:
            MySkillResult 处理结果
        """
        self._log(f"Processing with param1={param1}, param2={param2}")
        
        try:
            # 实现核心逻辑
            result_data = {"key": "value"}
            
            return MySkillResult(
                success=True,
                summary="处理成功",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return MySkillResult(
                success=False,
                summary="",
                error_message=str(e)
            )
    
    def get_tools(self) -> List[StructuredTool]:
        """
        获取 LangChain Tools
        
        Returns:
            List[StructuredTool] 工具列表
        """
        return [
            StructuredTool.from_function(
                func=self._tool_process,
                name="my_skill_process",
                description="执行 XXX 处理，参数说明...",
                args_schema=MySkillInput,
            )
        ]
    
    def _tool_process(self, **kwargs) -> str:
        """Tool 包装器"""
        import json
        result = self.process(**kwargs)
        return json.dumps({
            "success": result.success,
            "summary": result.summary,
            "data": result.data,
            "error": result.error_message
        }, ensure_ascii=False)


# 便捷函数
def process_with_my_skill(param1: str, param2: int = 0) -> MySkillResult:
    """便捷函数：一键处理"""
    skill = MySkill()
    return skill.process(param1, param2)
```

### 步骤4: 实现 Tools（可选）

```python
# src/skills/my_skill/tools.py

from langchain_core.tools import tool, StructuredTool
from pydantic import BaseModel, Field


@tool
def my_tool_function(param1: str) -> str:
    """
    独立的 Tool 函数
    
    Args:
        param1: 参数说明
        
    Returns:
        结果说明
    """
    return f"Result for {param1}"


def get_my_tools() -> List[StructuredTool]:
    """获取所有 Tools"""
    return [
        StructuredTool.from_function(
            func=my_tool_function,
            name="my_tool",
            description="Tool 功能说明",
        )
    ]
```

### 步骤5: 更新 __init__.py

```python
# src/skills/my_skill/__init__.py

"""
My Skill 模块

提供 XXX 能力。

Usage:
    from src.skills.my_skill import MySkill, process_with_my_skill
    
    skill = MySkill()
    result = skill.process(param1="value")
    
    # 或便捷函数
    result = process_with_my_skill(param1="value")
"""

from .my_skill import MySkill, MySkillResult, process_with_my_skill
from .tools import my_tool_function, get_my_tools

__all__ = [
    "MySkill",
    "MySkillResult",
    "process_with_my_skill",
    "my_tool_function",
    "get_my_tools",
]

__version__ = "1.0.0"
```

### 步骤6: 添加 L3 Resources

```markdown
<!-- src/skills/my_skill/references/guide.md -->

# My Skill 使用指南

## 常见问题

### Q1: 如何处理 XXX 情况？
A: 使用 YYY 方法。

### Q2: 参数 ZZZ 的取值范围？
A: 建议取值 0-100。

## 代码示例

```python
# 示例代码
skill = MySkill()
result = skill.process(...)
```

## 相关链接

- [官方文档](https://example.com)
```

### 步骤7: 测试

```python
# tests/test_my_skill.py

import pytest
from src.skills.my_skill import MySkill


def test_my_skill_process():
    skill = MySkill()
    result = skill.process(param1="test")
    
    assert result.success is True
    assert result.summary is not None


def test_my_skill_error_handling():
    skill = MySkill()
    result = skill.process(param1="")  # 无效输入
    
    assert result.success is False
```

---

## 最佳实践

### 1. 设计原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **单一职责** | 每个 Skill 只做一件事 | data_analysis 只负责数据分析 |
| **渐进披露** | L1 精简，L2/L3 按需 | SKILL.md 前10行包含核心信息 |
| **类型安全** | 使用 Pydantic 定义模式 | 所有 Tool 都有 args_schema |
| **可观测性** | 详细日志记录 | 使用 loguru 记录执行过程 |
| **错误处理** | 优雅降级 | 返回错误信息而非抛出异常 |

### 2. 命名规范

```python
# Skill 名称: kebab-case
# SKILL.md frontmatter
name: data-analysis-skill

# 类名: PascalCase + Skill 后缀
class DataAnalysisSkill:
    pass

# 方法名: snake_case
def analyze_statistics(self, ...)

# Tool 名: snake_case，动词开头
def load_data_tool(...)
def clean_data_tool(...)

# 文件名: snake_case
data_analysis_skill.py
tools.py
```

### 3. 文档规范

```python
def my_method(self, param: str) -> Result:
    """
    简短描述（一句话）
    
    详细描述（多句话，说明功能、使用场景、注意事项）
    
    Args:
        param: 参数说明，包含类型和取值范围
        
    Returns:
        Result: 返回值说明
        
    Raises:
        ValueError: 何时抛出此异常
        
    Example:
        >>> skill = MySkill()
        >>> result = skill.my_method("value")
        >>> print(result.data)
    """
```

### 4. 性能优化

```python
# 1. 延迟加载
class MySkill:
    def __init__(self):
        self._heavy_resource = None  # 延迟加载
    
    @property
    def heavy_resource(self):
        if self._heavy_resource is None:
            self._heavy_resource = self._load_heavy_resource()
        return self._heavy_resource

# 2. 结果缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(self, key: str):
    return self._compute(key)

# 3. 批量处理
def process_batch(self, items: List[str]) -> List[Result]:
    """批量处理减少重复初始化开销"""
    return [self.process(item) for item in items]
```

### 5. 安全配置

```python
# 1. 输入验证
def process(self, file_path: str):
    # 验证路径
    if ".." in file_path or file_path.startswith("/"):
        raise ValueError("Invalid file path")
    
    # 验证文件类型
    allowed_extensions = {".csv", ".json"}
    ext = Path(file_path).suffix
    if ext not in allowed_extensions:
        raise ValueError(f"Unsupported file type: {ext}")

# 2. 资源限制
def execute_with_timeout(self, func, timeout: int = 30):
    import signal
    
    def handler(signum, frame):
        raise TimeoutError("Operation timed out")
    
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    
    try:
        result = func()
    finally:
        signal.alarm(0)
    
    return result

# 3. 敏感操作确认
for file_path in files_to_delete:
    if self._is_sensitive_operation(file_path):
        confirmed = self._request_user_confirmation(f"Delete {file_path}?")
        if not confirmed:
            continue
    self._delete(file_path)
```

---

## 故障排查

### 常见问题

#### Q1: Skill 导入失败

```python
# 错误: ModuleNotFoundError
from src.skills.my_skill import MySkill

# 解决: 确保项目根目录在 Python 路径
import sys
sys.path.insert(0, "/path/to/project")
```

#### Q2: Tool 调用返回格式错误

```python
# 错误: Tool 返回非字符串
return {"key": "value"}  # ❌

# 解决: 始终返回 JSON 字符串
import json
return json.dumps({"key": "value"}, ensure_ascii=False)  # ✅
```

#### Q3: LLM 无法正确选择 Tool

```python
# 问题: Tool 描述不清晰
# 解决: 提供详细的描述和使用场景

tool = StructuredTool.from_function(
    func=my_func,
    name="my_tool",
    description="""
    详细描述 Tool 的功能。
    
    使用场景:
    - 场景1: 当需要 XXX 时使用
    - 场景2: 当数据格式为 YYY 时使用
    
    参数:
    - param1: 参数1说明，示例: "example_value"
    - param2: 参数2说明，示例: 42
    """,
)
```

#### Q4: 可视化中文乱码

```python
# 解决: 设置中文字体
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
```

### 调试技巧

```python
# 1. 启用详细日志
from loguru import logger
logger.add("skill_debug.log", level="DEBUG")

# 2. 检查 Tool 注册
skill = DataAnalysisSkill()
tools = skill.get_tools()
for tool in tools:
    print(f"Tool: {tool.name}, Args: {tool.args}")

# 3. 直接测试 Tool
tool = tools[0]
result = tool.invoke({"file_path": "test.csv"})
print(result)
```

---

## 参考资源

### 官方文档
- [Google ADK Skills](https://google.github.io/adk-docs/skills/)
- [Agent Skill Specification](https://agentskills.io/)
- [LangChain Tools](https://python.langchain.com/docs/how_to/custom_tools/)

### 项目文档
- [data_analysis/SKILL.md](data_analysis/SKILL.md) - 示例 Skill 规范
- [examples/skills_demo/README.md](../examples/skills_demo/README.md) - 使用示例
- [docs/skills_integration_research.md](../docs/skills_integration_research.md) - 调研报告

### 社区资源
- [skills.sh](https://skills.sh/) - Agent Skills 市场
- [Google ADK Samples](https://github.com/google/adk-samples)

---

*文档版本: 1.0.0*
*最后更新: 2026-03-29*
