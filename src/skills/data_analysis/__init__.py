"""
数据分析 Skill - Data Analysis Skill

参考 Google ADK Skill 规范实现的模块化数据分析能力。
可与 LangChain Agent 无缝集成。

Usage:
    from src.skills.data_analysis import DataAnalysisSkill
    
    skill = DataAnalysisSkill()
    result = skill.analyze(
        file_path="data.csv",
        analysis_goal="分析销售趋势"
    )
"""

from .data_analysis_skill import DataAnalysisSkill, DataAnalysisResult
from .tools import (
    load_data_tool,
    clean_data_tool,
    analyze_statistics_tool,
    visualize_tool,
    get_data_tools,
)

__all__ = [
    "DataAnalysisSkill",
    "DataAnalysisResult",
    "load_data_tool",
    "clean_data_tool",
    "analyze_statistics_tool",
    "visualize_tool",
    "get_data_tools",
]

__version__ = "1.0.0"
