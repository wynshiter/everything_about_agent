"""
数据分析 Skill 演示脚本

展示如何将 Google ADK 风格的数据分析 Skill 集成到当前项目的 Agent 中。

运行方式:
    cd d:\code\python\everything_about_agent
    python examples/skills_demo/demo_data_analysis_skill.py

前置条件:
    1. Ollama 服务已启动 (ollama serve)
    2. 已拉取模型 (ollama pull qwen2.5:3b)
    3. 安装了依赖: pip install pandas matplotlib seaborn
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

# =============================================================================
# 演示1: 直接使用 Skill（无需 LLM）
# =============================================================================

def demo_direct_usage():
    """直接调用 Skill 方法，不依赖 LLM"""
    print("\n" + "="*70)
    print("演示1: 直接使用 DataAnalysisSkill（无需 LLM）")
    print("="*70)
    
    from src.skills.data_analysis import DataAnalysisSkill
    
    # 初始化 Skill
    skill = DataAnalysisSkill(output_dir="./output")
    
    # 示例数据路径
    data_path = Path(__file__).parent / "sample_sales_data.csv"
    
    print(f"\n[数据文件] {data_path}")
    
    # 1. 加载数据
    print("\n--- Step 1: 加载数据 ---", flush=True)
    result = skill.load_data(str(data_path))
    print(result.summary)
    
    # 2. 数据清洗
    print("\n--- Step 2: 数据清洗 ---")
    clean_result = skill.clean_data(
        str(data_path),
        operations=["drop_duplicates", "fillna_mean"]
    )
    print(clean_result.summary)
    
    # 3. 统计分析
    print("\n--- Step 3: 统计分析 ---")
    stats_result = skill.analyze_statistics(
        str(data_path),
        analysis_type="overview"
    )
    print(f"分析摘要: {stats_result.summary}")
    
    # 4. 相关性分析
    print("\n--- Step 4: 相关性分析 ---")
    corr_result = skill.analyze_statistics(
        str(data_path),
        analysis_type="correlation"
    )
    if "strong_correlations" in corr_result.statistics:
        print(f"强相关变量对: {corr_result.statistics['strong_correlations']}")
    
    # 5. 生成可视化
    print("\n--- Step 5: 生成可视化 ---")
    
    # 收入趋势图
    viz_result = skill.visualize(
        str(data_path),
        chart_type="line",
        x_column="date",
        y_column="revenue",
        title="每日收入趋势"
    )
    if viz_result.success:
        print(f"[OK] 趋势图已保存: {viz_result.artifacts[0]['path']}")
    
    # 产品销量对比
    viz_result = skill.visualize(
        str(data_path),
        chart_type="bar",
        x_column="product",
        y_column="sales_quantity",
        title="产品销量对比"
    )
    if viz_result.success:
        print(f"[OK] 对比图已保存: {viz_result.artifacts[0]['path']}")
    
    # 相关性热力图
    viz_result = skill.visualize(
        str(data_path),
        chart_type="heatmap",
        x_column="sales_quantity",
        title="数值变量相关性热力图"
    )
    if viz_result.success:
        print(f"[OK] 热力图已保存: {viz_result.artifacts[0]['path']}")
    
    print("\n[完成] 演示1完成！")


# =============================================================================
# 演示2: 一键智能分析
# =============================================================================

def demo_smart_analysis():
    """一键智能分析"""
    print("\n" + "="*70)
    print("演示2: 一键智能分析")
    print("="*70)
    
    from src.skills.data_analysis import analyze_data
    
    data_path = Path(__file__).parent / "sample_sales_data.csv"
    
    print(f"\n[目标] 分析目标: 全面了解销售数据特征")
    
    result = analyze_data(
        file_path=str(data_path),
        analysis_goal="全面了解销售数据特征，包括收入趋势、产品表现和地区分布",
        output_dir="./output"
    )
    
    if result.success:
        print("\n" + result.summary)
        print(f"\n[图表] 生成图表数量: {len(result.artifacts)}")
        for artifact in result.artifacts:
            print(f"   - {artifact['type']}: {artifact['path']}")
    else:
        print(f"[错误] 分析失败: {result.error_message}")
    
    print("\n[OK] 演示2完成！")


# =============================================================================
# 演示3: 集成到 LangChain Agent
# =============================================================================

def demo_agent_integration():
    """将 Skill 作为 Tools 集成到 LangChain Agent"""
    print("\n" + "="*70)
    print("演示3: 集成到 LangChain Agent（需要 LLM 后端）")
    print("="*70)
    
    try:
        from src.skills.data_analysis import get_data_tools
        from src.utils.model_loader import model_loader
        from langchain.agents import create_tool_calling_agent, AgentExecutor
        from langchain_core.prompts import ChatPromptTemplate
        
        # 加载模型
        print("\n[加载] 正在加载模型...")
        llm = model_loader.load_llm()
        print(f"[OK] 模型加载成功: {model_loader.active_model_id}")
        
        # 获取数据分析工具
        tools = get_data_tools()
        print(f"[OK] 加载了 {len(tools)} 个数据分析工具")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description[:40]}...")
        
        # 创建 Agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的数据分析助手。你可以使用以下工具帮助用户分析数据：

1. load_data - 加载数据文件，查看数据概览
2. clean_data - 清洗数据（去重、处理缺失值）
3. analyze_statistics - 执行统计分析
4. visualize_data - 生成可视化图表

请遵循以下原则：
- 先加载数据了解结构
- 根据数据特征选择合适的分析方法
- 使用可视化辅助数据理解
- 用中文回复用户
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
        
        # 运行查询
        data_path = Path(__file__).parent / "sample_sales_data.csv"
        
        queries = [
            f"请加载 {data_path} 文件，告诉我数据的基本情况",
            f"分析 {data_path} 中各产品的销量分布，并生成柱状图",
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n--- 查询 {i} ---")
            print(f"用户: {query}")
            print("Agent 思考中...\n")
            
            try:
                result = agent_executor.invoke({"input": query})
                print(f"\nAgent 回复: {result['output']}")
            except Exception as e:
                print(f"[错误] 查询失败: {e}")
        
        print("\n[OK] 演示3完成！")
        
    except Exception as e:
        print(f"\n[警告] 演示3需要 LLM 后端，当前不可用: {e}")
        print("请确保 Ollama 服务已启动: ollama serve")


# =============================================================================
# 演示4: Google ADK 风格对比
# =============================================================================

def demo_adk_comparison():
    """展示与 Google ADK 的对比"""
    print("\n" + "="*70)
    print("演示4: Google ADK 风格对比")
    print("="*70)
    
    print("""
## 架构对比

### Google ADK 原生写法:
```python
from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset

# 从目录加载 Skill
skill = load_skill_from_dir("./skills/data_analysis")
toolset = skill_toolset.SkillToolset(skills=[skill])

# 创建 Agent
agent = Agent(
    model="gemini-2.5-flash",
    tools=[toolset],
)
```

### 本项目适配写法 (LangChain + 多后端):
```python
from src.skills.data_analysis import DataAnalysisSkill, get_data_tools

# 方式1: 直接使用 Skill
skill = DataAnalysisSkill()
result = skill.analyze("data.csv", "分析销售趋势")

# 方式2: 获取 Tools 集成到 Agent
tools = get_data_tools()
agent = create_tool_calling_agent(llm, tools, prompt)
```

## 核心特点对比

| 特性 | Google ADK | 本项目实现 |
|------|-----------|-----------|
| Skill 规范 | SKILL.md + L1/L2/L3 | SKILL.md + 模块化代码 |
| 渐进式披露 | [OK] 原生支持 | [OK] 通过 Tool 描述实现 |
| 多后端支持 | Google/Vertex AI | Ollama/vLLM |
| Agent 框架 | ADK Agents | LangChain |
| 工具集成 | SkillToolset | LangChain Tools |

## 本项目优势

1. **本地优先**: 支持 Ollama 本地模型，无需云端 API
2. **多后端**: 可在 Ollama 和 vLLM 间无缝切换
3. **渐进式**: 采用相同的三层架构思想（L1 Metadata, L2 Instructions, L3 Resources）
4. **可扩展**: 易于添加新的 Skill，遵循相同目录结构
""")


# =============================================================================
# 主函数
# =============================================================================

def main():
    """主入口"""
    print("="*70)
    print("数据分析 Skill 演示")
    print("="*70)
    print("\n本演示展示如何将 Google ADK 风格的 Skill 集成到当前项目")
    
    # 运行演示
    demo_direct_usage()       # 演示1: 直接使用
    demo_smart_analysis()     # 演示2: 一键分析
    demo_agent_integration()  # 演示3: Agent 集成
    demo_adk_comparison()     # 演示4: ADK 对比
    
    print("\n" + "="*70)
    print("所有演示完成！")
    print("="*70)
    print("\n生成文件:")
    print("  - output/*.png - 数据可视化图表")
    print("\n下一步:")
    print("  1. 查看 output 目录中的图表")
    print("  2. 参考 src/skills/data_analysis/ 实现你自己的 Skill")
    print("  3. 将 Skill 集成到你的 Agent 项目中")


if __name__ == "__main__":
    main()
