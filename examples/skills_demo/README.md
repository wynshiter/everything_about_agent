# Skills 集成示例与最佳实践

本目录展示如何将 **Google ADK 风格的 Skills** 集成到当前项目中，以数据分析 Skill 为例。

## 目录

- [核心概念](#核心概念)
- [文件说明](#文件说明)
- [运行环境准备](#运行环境准备)
- [使用方式详解](#使用方式详解)
- [完整示例代码](#完整示例代码)
- [高级用法](#高级用法)
- [常见问题](#常见问题)
- [扩展阅读](#扩展阅读)

---

## 核心概念

### 什么是 Skill？

Skill 是一个**自包含的功能单元**，封装了特定领域的知识和能力。它遵循三层渐进式架构：

```
┌─────────────────────────────────────┐
│  L1 - Metadata                      │  ← 启动时加载
│  (名称、描述、版本)                  │
├─────────────────────────────────────┤
│  L2 - Instructions                  │  ← 激活时加载
│  (使用说明、步骤)                    │
├─────────────────────────────────────┤
│  L3 - Resources                     │  ← 按需加载
│  (参考资料、代码片段)                │
├─────────────────────────────────────┤
│  Implementation                     │
│  (Python 代码、Tools)                │
└─────────────────────────────────────┘
```

### 与 Google ADK 的关系

| 特性 | Google ADK 原生 | 本项目实现 |
|------|----------------|-----------|
| Skill 规范 | ✅ SKILL.md | ✅ 兼容 |
| 渐进披露 | ✅ L1/L2/L3 | ✅ 模拟实现 |
| 多后端支持 | Google/Vertex AI | ✅ Ollama/vLLM |
| Agent 框架 | ADK Agents | ✅ LangChain |
| 工具集成 | SkillToolset | ✅ LangChain Tools |

---

## 文件说明

```
skills_demo/
├── README.md                           # 本文档
├── demo_data_analysis_skill.py        # 完整演示脚本
├── test_skill_simple.py               # 简单测试脚本
└── sample_sales_data.csv              # 示例数据（30条销售记录）
```

### 示例数据说明

`sample_sales_data.csv` 包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | Date | 销售日期 (2024-01-01 ~ 2024-01-15) |
| `product` | String | 产品名称 (Product A ~ E) |
| `category` | String | 产品类别 (Electronics/Clothing/Food/Home) |
| `region` | String | 销售地区 (North/South/East/West) |
| `sales_quantity` | Integer | 销售数量 |
| `unit_price` | Float | 单价 |
| `revenue` | Float | 收入 (sales_quantity × unit_price) |
| `customer_count` | Integer | 客户数 |

---

## 运行环境准备

### 1. 安装依赖

```bash
# 进入项目目录
cd d:/code/python/everything_about_agent

# 安装数据分析依赖
pip install pandas matplotlib seaborn openpyxl

# 或使用 uv
uv pip install pandas matplotlib seaborn openpyxl
```

### 2. 启动 LLM 后端（可选）

如需运行 Agent 集成演示，需要启动 Ollama：

```bash
# 启动 Ollama 服务
ollama serve

# 拉取模型（首次使用）
ollama pull qwen2.5:3b
# 或
ollama pull qwen3:4b
```

### 3. 验证安装

```bash
# 运行简单测试
python examples/skills_demo/test_skill_simple.py
```

预期输出：
```
Loading: D:\code\python\everything_about_agent\examples\skills_demo\sample_sales_data.csv
Success: True
Rows: 30
Columns: 8
Chart generated: True
Chart path: output\chart_bar_xxxx.png
Test completed!
```

---

## 使用方式详解

### 方式1: 直接使用 Skill（无需 LLM）

适合数据处理脚本、批量分析任务。

#### 基础用法

```python
from src.skills.data_analysis import DataAnalysisSkill

# 初始化
skill = DataAnalysisSkill(output_dir="./output")

# 加载数据
result = skill.load_data("examples/skills_demo/sample_sales_data.csv")
print(result.summary)
```

输出示例：
```markdown
## 数据概览

- **行数**: 30
- **列数**: 8
- **列名**: date, product, category, region, sales_quantity, unit_price, revenue, customer_count

### 数据类型分布
- object: 4 列
- int64: 3 列
- float64: 1 列

### 缺失值统计
（无缺失值）
```

#### 数据清洗

```python
# 清洗数据
result = skill.clean_data(
    "examples/skills_demo/sample_sales_data.csv",
    operations=["drop_duplicates", "fillna_mean", "fillna_mode"],
    output_path="output/cleaned_data.csv"
)

print(f"清洗结果: {result.statistics}")
```

#### 统计分析

```python
# 描述性统计
result = skill.analyze_statistics(
    "examples/skills_demo/sample_sales_data.csv",
    analysis_type="overview"
)
print(result.statistics["describe"])

# 相关性分析
result = skill.analyze_statistics(
    "examples/skills_demo/sample_sales_data.csv",
    analysis_type="correlation"
)
print(result.statistics["strong_correlations"])
```

#### 数据可视化

```python
# 折线图 - 趋势
skill.visualize(
    "examples/skills_demo/sample_sales_data.csv",
    chart_type="line",
    x_column="date",
    y_column="revenue",
    title="每日收入趋势"
)

# 柱状图 - 对比
skill.visualize(
    "examples/skills_demo/sample_sales_data.csv",
    chart_type="bar",
    x_column="product",
    y_column="sales_quantity",
    title="产品销量对比"
)

# 散点图 - 关系
skill.visualize(
    "examples/skills_demo/sample_sales_data.csv",
    chart_type="scatter",
    x_column="customer_count",
    y_column="revenue",
    title="客户数与收入关系"
)

# 热力图 - 相关性
skill.visualize(
    "examples/skills_demo/sample_sales_data.csv",
    chart_type="heatmap",
    x_column="sales_quantity",
    title="数值变量相关性热力图"
)

# 饼图 - 占比
skill.visualize(
    "examples/skills_demo/sample_sales_data.csv",
    chart_type="pie",
    x_column="category",
    title="产品类别占比"
)
```

#### 一键智能分析

```python
from src.skills.data_analysis import analyze_data

# 一键分析
result = analyze_data(
    file_path="examples/skills_demo/sample_sales_data.csv",
    analysis_goal="分析销售趋势、产品表现和地区分布，找出关键洞察",
    output_dir="./output"
)

# 查看结果
print(result.summary)      # Markdown 格式报告
print(result.statistics)   # 详细统计数据
print(result.artifacts)    # 生成的图表路径
```

输出示例：
```markdown
## 数据分析报告

### 分析目标
分析销售趋势、产品表现和地区分布，找出关键洞察

### 数据概览
- 数据规模: 30 行 × 8 列
- 清洗结果: 0 行被清理

### 关键发现
分析 4 个数值列; 分析 4 个分类列

### 相关性洞察
发现 3 对强相关变量

### 生成图表
2 个可视化图表已生成
```

---

### 方式2: 集成到 LangChain Agent

让 LLM 自主决定如何使用数据分析能力。

#### 基础 Agent

```python
from src.skills.data_analysis import get_data_tools
from src.utils.model_loader import model_loader
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# 1. 加载模型（自动适配 Ollama/vLLM）
llm = model_loader.load_llm()

# 2. 获取数据分析工具（4个 Tools）
tools = get_data_tools()

# 3. 创建系统提示
system_prompt = """你是一个专业的数据分析师，擅长使用工具进行数据分析。

你可以使用的工具：
1. load_data - 加载 CSV/Excel/JSON 数据文件，返回数据概览
2. clean_data - 清洗数据：删除重复值、填充缺失值
3. analyze_statistics - 执行统计分析：描述统计、相关性、分布
4. visualize_data - 生成可视化图表：折线、柱状、散点、热力、饼图

工作流程：
1. 先用 load_data 加载数据，了解数据结构
2. 根据用户问题选择合适的分析方法
3. 必要时使用 clean_data 清洗数据
4. 使用 analyze_statistics 进行统计分析
5. 使用 visualize_data 生成图表辅助说明
6. 用中文回复，提供清晰的结论和建议

注意：
- 文件路径使用绝对路径或相对项目根目录的路径
- 生成图表后告诉用户图表保存位置
- 如果分析失败，说明可能的原因
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 4. 创建 Agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,           # 显示详细执行过程
    max_iterations=10,      # 最大迭代次数
    handle_parsing_errors=True
)

# 5. 执行查询
response = agent_executor.invoke({
    "input": "请分析 examples/skills_demo/sample_sales_data.csv，告诉我哪个产品销量最好，收入最高的是哪个产品？"
})

print(response["output"])
```

#### 多轮对话 Agent

```python
from langchain_core.messages import HumanMessage, AIMessage

# 维护对话历史
chat_history = []

while True:
    user_input = input("用户: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    
    # 构建带历史的输入
    response = agent_executor.invoke({
        "input": user_input,
        "chat_history": chat_history
    })
    
    # 更新历史
    chat_history.append(HumanMessage(content=user_input))
    chat_history.append(AIMessage(content=response["output"]))
    
    print(f"助手: {response['output']}")
```

#### 带记忆的 Agent

```python
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 消息历史存储
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# 包装带历史的 Agent
agent_with_history = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# 使用
response = agent_with_history.invoke(
    {"input": "分析销售数据"},
    config={"configurable": {"session_id": "user_123"}}
)
```

---

### 方式3: 在 Multi-Agent 系统中使用

结合其他 Agent 模式构建复杂系统。

#### 与 Routing 模式结合

```python
from src.skills.data_analysis import get_data_tools

# 定义不同类型的 Agent
data_agent = Agent(
    name="DataAnalyst",
    tools=get_data_tools(),
    system_message="你专门负责数据分析任务"
)

code_agent = Agent(
    name="CodeExpert",
    tools=[python_executor_tool],
    system_message="你专门负责代码执行和编程任务"
)

qa_agent = Agent(
    name="QASpecialist",
    tools=[search_tool],
    system_message="你专门负责问答和知识检索"
)

# 路由 Agent
router = RouterAgent(agents={
    "data_analysis": data_agent,
    "code_execution": code_agent,
    "question_answering": qa_agent
})

# 自动路由
result = router.route("分析销售数据")  # → 路由到 data_agent
result = router.route("写一个排序算法")  # → 路由到 code_agent
```

#### 与 Planning 模式结合

```python
from src.agents.patterns.planning import PlannerAgent

# 规划 Agent 制定执行计划
planner = PlannerAgent()
plan = planner.create_plan("全面分析销售数据并生成报告")

# 数据分析 Agent 执行具体步骤
for step in plan.steps:
    if step.type == "data_analysis":
        skill = DataAnalysisSkill()
        result = skill.analyze(step.file_path, step.goal)
    elif step.type == "visualization":
        skill.visualize(...)
```

#### 与 Reflection 模式结合

```python
# 分析师 Agent 执行分析
skill = DataAnalysisSkill()
result = skill.analyze("data.csv", "分析销售趋势")

# 审查员 Agent 检查分析质量
critic = CriticAgent()
review = critic.review(result.summary)

# 根据反馈改进
if review.score < 0.8:
    result = skill.analyze("data.csv", review.suggestions)
```

---

## 完整示例代码

### 示例1: 销售数据分析完整流程

```python
"""
销售数据分析完整示例

演示从数据加载到报告生成的完整流程
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.skills.data_analysis import DataAnalysisSkill

def main():
    # 配置
    data_path = "examples/skills_demo/sample_sales_data.csv"
    output_dir = "./output/sales_analysis"
    
    # 初始化 Skill
    skill = DataAnalysisSkill(output_dir=output_dir)
    
    print("=" * 60)
    print("销售数据分析示例")
    print("=" * 60)
    
    # Step 1: 加载数据
    print("\n[Step 1] 加载数据...")
    result = skill.load_data(data_path)
    if not result.success:
        print(f"加载失败: {result.error_message}")
        return
    print(f"✓ 数据规模: {result.statistics['rows']} 行 x {result.statistics['columns']} 列")
    
    # Step 2: 数据质量检查
    print("\n[Step 2] 数据质量检查...")
    missing = result.statistics.get('missing_values', {})
    missing_cols = {k: v for k, v in missing.items() if v > 0}
    if missing_cols:
        print(f"⚠ 发现缺失值: {missing_cols}")
        print("  执行数据清洗...")
        skill.clean_data(data_path, operations=["fillna_mean"])
    else:
        print("✓ 数据质量良好，无缺失值")
    
    # Step 3: 描述性统计
    print("\n[Step 3] 描述性统计...")
    result = skill.analyze_statistics(data_path, analysis_type="overview")
    print(f"✓ {result.summary}")
    
    # Step 4: 产品分析
    print("\n[Step 4] 产品销量分析...")
    skill.visualize(
        data_path,
        chart_type="bar",
        x_column="product",
        y_column="sales_quantity",
        title="各产品销量对比"
    )
    
    # Step 5: 收入趋势
    print("\n[Step 5] 收入趋势分析...")
    skill.visualize(
        data_path,
        chart_type="line",
        x_column="date",
        y_column="revenue",
        title="每日收入趋势"
    )
    
    # Step 6: 相关性分析
    print("\n[Step 6] 相关性分析...")
    result = skill.analyze_statistics(data_path, analysis_type="correlation")
    strong_corr = result.statistics.get("strong_correlations", [])
    print(f"✓ 发现 {len(strong_corr)} 对强相关变量")
    for pair in strong_corr:
        print(f"  - {pair['col1']} vs {pair['col2']}: r={pair['correlation']}")
    
    # Step 7: 生成热力图
    skill.visualize(
        data_path,
        chart_type="heatmap",
        x_column="sales_quantity",
        title="数值变量相关性热力图"
    )
    
    # Step 8: 类别占比
    print("\n[Step 7] 产品类别占比...")
    skill.visualize(
        data_path,
        chart_type="pie",
        x_column="category",
        title="产品类别销售占比"
    )
    
    print("\n" + "=" * 60)
    print("分析完成！")
    print(f"输出目录: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

### 示例2: 智能数据助手

```python
"""
智能数据助手 - 结合 LLM 的数据分析 Agent
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.skills.data_analysis import get_data_tools
from src.utils.model_loader import model_loader
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

def create_data_assistant():
    """创建智能数据助手"""
    
    # 加载模型
    llm = model_loader.load_llm()
    
    # 获取工具
    tools = get_data_tools()
    
    # 系统提示 - 专业数据分析师角色
    system_prompt = """你是一位资深数据分析师，拥有10年以上数据分析经验。

你的专长：
- 数据清洗和预处理
- 探索性数据分析（EDA）
- 统计分析和假设检验
- 数据可视化和洞察提炼
- 业务报告撰写

工作原则：
1. 数据质量优先：总是先检查数据质量
2. 方法论严谨：选择合适的统计方法
3. 可视化辅助：用图表支持结论
4. 业务导向：从数据中提取业务洞察
5. 清晰沟通：用非技术人员能理解的语言解释

工具使用指南：
- load_data: 第一步总是用它加载数据
- clean_data: 当发现缺失值或异常值时使用
- analyze_statistics: 根据问题选择 analysis_type
  * "overview" - 初次了解数据
  * "correlation" - 分析变量关系
  * "distribution" - 了解数据分布
- visualize_data: 根据数据类型选择 chart_type
  * "line" - 时间趋势
  * "bar" - 类别对比
  * "scatter" - 变量关系
  * "heatmap" - 相关性矩阵
  * "pie" - 占比构成

回复格式：
1. 分析结论（关键发现）
2. 数据支撑（具体数字）
3. 可视化说明（图表位置）
4. 行动建议（可落地的建议）
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    # 创建 Agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=15
    )
    
    return agent_executor

def main():
    print("=" * 70)
    print("智能数据助手")
    print("=" * 70)
    
    # 创建助手
    print("\n[初始化] 加载模型和工具...")
    assistant = create_data_assistant()
    print("[就绪] 请输入你的数据分析问题\n")
    
    # 示例查询
    queries = [
        "请加载 examples/skills_demo/sample_sales_data.csv 文件，给出数据的整体概况",
        "哪个产品的总收入最高？请计算并可视化",
        "分析不同地区的销售表现，找出表现最好的地区",
        "客户数量和收入之间有什么关系？用散点图展示",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n[查询 {i}] {query}")
        print("-" * 70)
        
        try:
            response = assistant.invoke({"input": query})
            print(f"\n[回复] {response['output']}")
        except Exception as e:
            print(f"[错误] {e}")
        
        input("\n按 Enter 继续...")
    
    print("\n" + "=" * 70)
    print("演示结束！")
    print("=" * 70)

if __name__ == "__main__":
    main()
```

---

## 高级用法

### 自定义分析流程

```python
from src.skills.data_analysis import DataAnalysisSkill
from typing import List, Dict

class CustomAnalyzer:
    """自定义分析器"""
    
    def __init__(self):
        self.skill = DataAnalysisSkill()
    
    def analyze_product_performance(
        self,
        file_path: str,
        product_col: str = "product",
        metrics: List[str] = ["revenue", "sales_quantity"]
    ) -> Dict:
        """分析产品表现"""
        
        import pandas as pd
        df = pd.read_csv(file_path)
        
        results = {}
        for metric in metrics:
            # 按产品分组统计
            product_stats = df.groupby(product_col)[metric].agg([
                ('total', 'sum'),
                ('mean', 'mean'),
                ('count', 'count')
            ]).sort_values('total', ascending=False)
            
            results[metric] = {
                'top_product': product_stats.index[0],
                'top_value': float(product_stats.iloc[0]['total']),
                'stats': product_stats.to_dict()
            }
        
        return results
    
    def generate_executive_summary(self, file_path: str) -> str:
        """生成高管摘要"""
        
        # 执行一键分析
        result = self.skill.analyze(
            file_path,
            analysis_goal="生成高管层面的业务洞察"
        )
        
        # 构建摘要
        summary = f"""
# 数据分析执行摘要

## 关键指标
{result.summary}

## 核心洞察
1. 数据质量良好，可直接用于决策
2. 建议关注强相关变量对
3. 详见附件图表

## 建议行动
- 基于数据分析结果制定策略
- 持续监控关键指标变化
        """
        
        return summary
```

### 批量数据处理

```python
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def batch_analyze(directory: str, output_dir: str):
    """批量分析目录中的所有 CSV 文件"""
    
    skill = DataAnalysisSkill(output_dir=output_dir)
    csv_files = list(Path(directory).glob("*.csv"))
    
    results = []
    for file_path in csv_files:
        print(f"Processing: {file_path.name}")
        result = skill.analyze(
            str(file_path),
            analysis_goal=f"分析 {file_path.stem} 数据"
        )
        results.append({
            "file": file_path.name,
            "success": result.success,
            "artifacts": result.artifacts
        })
    
    return results

# 并行处理
def parallel_analyze(directory: str, output_dir: str, max_workers: int = 4):
    """并行批量分析"""
    
    csv_files = list(Path(directory).glob("*.csv"))
    
    def process_file(file_path: Path):
        skill = DataAnalysisSkill(output_dir=output_dir)
        return skill.analyze(
            str(file_path),
            analysis_goal=f"分析 {file_path.stem} 数据"
        )
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file, csv_files))
    
    return results
```

### 与其他工具结合

```python
from src.skills.data_analysis import get_data_tools
from langchain_community.tools import DuckDuckGoSearchRun

# 组合多个技能的数据分析 Agent
def create_enhanced_data_agent():
    """创建增强型数据分析 Agent"""
    
    # 数据分析工具
    data_tools = get_data_tools()
    
    # 搜索工具（用于获取行业基准）
    search_tool = DuckDuckGoSearchRun()
    
    # 所有工具
    all_tools = data_tools + [search_tool]
    
    # 系统提示
    system_prompt = """你是增强型数据分析师。

特殊能力：
1. 不仅可以分析用户提供的数据
2. 还可以搜索行业基准进行对比
3. 提供行业洞察和最佳实践

工作流程：
1. 加载并分析用户数据
2. 搜索相关行业基准
3. 对比分析，找出差距和机会
4. 提供可执行的建议
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm, all_tools, prompt)
    return AgentExecutor(agent=agent, tools=all_tools)
```

---

## 常见问题

### Q1: 如何支持其他数据格式？

```python
# 扩展 load_data 支持更多格式
class ExtendedDataSkill(DataAnalysisSkill):
    def load_data(self, file_path: str, file_type: str = "csv", **kwargs):
        if file_type == "parquet":
            import pyarrow.parquet as pq
            df = pq.read_table(file_path).to_pandas()
        elif file_type == "feather":
            df = pd.read_feather(file_path)
        else:
            return super().load_data(file_path, file_type, **kwargs)
        
        # 保存到上下文
        self.context["current_df"] = df
        return DataAnalysisResult(...)
```

### Q2: 如何处理大数据集？

```python
# 使用分块处理
class BigDataSkill(DataAnalysisSkill):
    def analyze_large_file(self, file_path: str, chunksize: int = 10000):
        """分块分析大文件"""
        
        import pandas as pd
        
        # 统计信息累加
        total_rows = 0
        column_sums = None
        
        for chunk in pd.read_csv(file_path, chunksize=chunksize):
            total_rows += len(chunk)
            
            if column_sums is None:
                column_sums = chunk.sum(numeric_only=True)
            else:
                column_sums += chunk.sum(numeric_only=True)
        
        return {
            "total_rows": total_rows,
            "column_means": column_sums / total_rows
        }
```

### Q3: 如何自定义图表样式？

```python
# 扩展可视化方法
class StyledDataSkill(DataAnalysisSkill):
    def visualize_custom(
        self,
        file_path: str,
        chart_type: str,
        style_config: dict = None,
        **kwargs
    ):
        """自定义样式的可视化"""
        
        import matplotlib.pyplot as plt
        
        # 应用自定义样式
        style_config = style_config or {}
        plt.rcParams['figure.figsize'] = style_config.get('figsize', (12, 6))
        plt.rcParams['font.size'] = style_config.get('font_size', 12)
        
        # 调用父类方法
        return super().visualize(file_path, chart_type, **kwargs)
```

### Q4: 如何保存分析结果为报告？

```python
def save_report(result: DataAnalysisResult, output_path: str):
    """保存分析结果为 Markdown 报告"""
    
    report = f"""# 数据分析报告

## 执行摘要
{result.summary}

## 详细统计
```json
{json.dumps(result.statistics, indent=2, ensure_ascii=False)}
```

## 生成图表
"""
    
    for artifact in result.artifacts:
        report += f"- {artifact['type']}: {artifact['path']}\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"报告已保存: {output_path}")
```

---

## 扩展阅读

### 项目文档
- [完整调研报告](../../docs/skills_integration_research.md)
- [Skills API 参考](../../src/skills/README.md)
- [data_analysis/SKILL.md](../../src/skills/data_analysis/SKILL.md)

### 外部资源
- [Google ADK Skills](https://google.github.io/adk-docs/skills/)
- [LangChain Tools](https://python.langchain.com/docs/how_to/custom_tools/)
- [Pandas 文档](https://pandas.pydata.org/docs/)
- [Matplotlib 教程](https://matplotlib.org/stable/tutorials/index.html)

### 示例数据
- [sample_sales_data.csv](sample_sales_data.csv) - 销售数据示例

---

*文档版本: 1.0.0*
*最后更新: 2026-03-29*
