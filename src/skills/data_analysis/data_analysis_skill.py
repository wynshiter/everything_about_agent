"""
数据分析 Skill 核心实现

基于 Google ADK Skill 规范设计，采用渐进式披露架构：
- L1 (Metadata): SKILL.md frontmatter - 启动时加载
- L2 (Instructions): SKILL.md body - Skill 触发时加载  
- L3 (Resources): references/, assets/ - 按需加载

集成到 LangChain Agent 中使用 Tool 封装。
"""

import os
import json
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
import numpy as np
from langchain_core.tools import tool, StructuredTool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from pydantic import BaseModel, Field
from loguru import logger

from src.utils.model_loader import model_loader


# =============================================================================
# 数据模型定义
# =============================================================================

@dataclass
class DataAnalysisResult:
    """数据分析结果容器"""
    success: bool
    summary: str
    statistics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, str]] = field(default_factory=list)
    execution_log: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


class LoadDataInput(BaseModel):
    """数据加载工具输入模式"""
    file_path: str = Field(..., description="数据文件的绝对或相对路径")
    file_type: str = Field(default="csv", description="文件类型: csv, excel, json")
    encoding: str = Field(default="utf-8", description="文件编码，默认utf-8")


class CleanDataInput(BaseModel):
    """数据清洗工具输入模式"""
    file_path: str = Field(..., description="原始数据文件路径")
    operations: List[str] = Field(
        default=["drop_duplicates", "fillna_mean"],
        description="清洗操作列表: drop_duplicates, dropna, fillna_mean, fillna_mode"
    )
    output_path: Optional[str] = Field(None, description="清洗后数据保存路径")


class AnalyzeInput(BaseModel):
    """数据分析工具输入模式"""
    file_path: str = Field(..., description="数据文件路径")
    analysis_type: str = Field(
        default="overview",
        description="分析类型: overview, correlation, distribution, trend"
    )
    columns: Optional[List[str]] = Field(None, description="要分析的列名列表")
    group_by: Optional[str] = Field(None, description="分组列名")


class VisualizeInput(BaseModel):
    """数据可视化工具输入模式"""
    file_path: str = Field(..., description="数据文件路径")
    chart_type: str = Field(
        ...,
        description="图表类型: line, bar, scatter, histogram, heatmap, pie"
    )
    x_column: str = Field(..., description="X轴列名")
    y_column: Optional[str] = Field(None, description="Y轴列名（可选）")
    title: str = Field(default="Chart", description="图表标题")
    output_path: Optional[str] = Field(None, description="图表保存路径")


# =============================================================================
# Skill 核心类
# =============================================================================

class DataAnalysisSkill:
    """
    数据分析 Skill - 参考 Google ADK 规范实现
    
    提供端到端的数据分析能力：
    1. 数据加载 (CSV/Excel/JSON)
    2. 数据清洗 (缺失值、重复值处理)
    3. 探索性分析 (统计摘要、相关性)
    4. 数据可视化 (多种图表类型)
    5. 报告生成 (综合分析报告)
    
    架构特点：
    - 模块化设计：每个功能封装为独立 Tool
    - 渐进式披露：根据任务动态加载能力
    - 可观测性：详细的执行日志
    
    Example:
        skill = DataAnalysisSkill()
        
        # 方式1: 直接调用 Skill 方法
        result = skill.analyze("data.csv", "分析销售趋势")
        
        # 方式2: 获取 Tools 集成到 Agent
        tools = skill.get_tools()
        agent = create_tool_calling_agent(llm, tools, prompt)
    """
    
    def __init__(self, output_dir: str = "./output"):
        """
        初始化数据分析 Skill
        
        Args:
            output_dir: 输出文件保存目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 执行上下文，用于在工具间共享数据
        self.context: Dict[str, Any] = {
            "loaded_data": None,
            "current_df": None,
            "execution_log": [],
        }
        
        logger.info(f"📊 DataAnalysisSkill initialized (output: {output_dir})")
    
    def _log(self, message: str):
        """记录执行日志"""
        self.context["execution_log"].append(message)
        logger.info(message)
    
    # =====================================================================
    # L2 能力层 - 核心分析功能
    # =====================================================================
    
    def load_data(
        self,
        file_path: str,
        file_type: str = "csv",
        encoding: str = "utf-8"
    ) -> DataAnalysisResult:
        """
        加载数据文件到 DataFrame
        
        Args:
            file_path: 数据文件路径
            file_type: 文件类型 (csv/excel/json)
            encoding: 文件编码
            
        Returns:
            DataAnalysisResult 包含加载的数据和元信息
        """
        self._log(f"📥 Loading data from: {file_path}")
        
        try:
            path = Path(file_path)
            if not path.exists():
                return DataAnalysisResult(
                    success=False,
                    summary="",
                    error_message=f"File not found: {file_path}"
                )
            
            # 根据类型加载数据
            if file_type.lower() == "csv":
                df = pd.read_csv(file_path, encoding=encoding)
            elif file_type.lower() in ["excel", "xlsx", "xls"]:
                df = pd.read_excel(file_path)
            elif file_type.lower() == "json":
                df = pd.read_json(file_path)
            else:
                return DataAnalysisResult(
                    success=False,
                    summary="",
                    error_message=f"Unsupported file type: {file_type}"
                )
            
            # 保存到上下文
            self.context["current_df"] = df
            self.context["loaded_data"] = {
                "path": file_path,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
            }
            
            # 生成数据概览
            summary = self._generate_data_overview(df)
            
            self._log(f"✅ Loaded {len(df)} rows x {len(df.columns)} columns")
            
            return DataAnalysisResult(
                success=True,
                summary=summary,
                statistics={
                    "rows": len(df),
                    "columns": len(df.columns),
                    "dtypes": df.dtypes.to_dict(),
                    "missing_values": df.isnull().sum().to_dict(),
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return DataAnalysisResult(
                success=False,
                summary="",
                error_message=str(e)
            )
    
    def clean_data(
        self,
        file_path: str,
        operations: List[str] = None,
        output_path: Optional[str] = None
    ) -> DataAnalysisResult:
        """
        清洗数据
        
        Args:
            file_path: 原始数据文件路径
            operations: 清洗操作列表
                - drop_duplicates: 删除重复行
                - dropna: 删除含缺失值行
                - fillna_mean: 用均值填充数值缺失值
                - fillna_mode: 用众数填充分类缺失值
            output_path: 清洗后数据保存路径
            
        Returns:
            DataAnalysisResult 包含清洗后的数据统计
        """
        operations = operations or ["drop_duplicates"]
        self._log(f"🧹 Cleaning data with operations: {operations}")
        
        try:
            # 加载数据
            result = self.load_data(file_path)
            if not result.success:
                return result
            
            df = self.context["current_df"].copy()
            original_rows = len(df)
            
            # 执行清洗操作
            for op in operations:
                if op == "drop_duplicates":
                    df = df.drop_duplicates()
                    self._log(f"  - Dropped {original_rows - len(df)} duplicate rows")
                elif op == "dropna":
                    df = df.dropna()
                    self._log(f"  - Rows after dropna: {len(df)}")
                elif op == "fillna_mean":
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                    self._log(f"  - Filled numeric NAs with mean")
                elif op == "fillna_mode":
                    categorical_cols = df.select_dtypes(include=["object"]).columns
                    for col in categorical_cols:
                        mode = df[col].mode()
                        if len(mode) > 0:
                            df[col] = df[col].fillna(mode[0])
                    self._log(f"  - Filled categorical NAs with mode")
            
            # 保存清洗后的数据
            if output_path:
                df.to_csv(output_path, index=False, encoding="utf-8")
                self._log(f"  - Saved cleaned data to: {output_path}")
            
            self.context["current_df"] = df
            
            return DataAnalysisResult(
                success=True,
                summary=f"Cleaned data: {original_rows} -> {len(df)} rows",
                statistics={
                    "original_rows": original_rows,
                    "cleaned_rows": len(df),
                    "removed_rows": original_rows - len(df),
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to clean data: {e}")
            return DataAnalysisResult(
                success=False,
                summary="",
                error_message=str(e)
            )
    
    def analyze_statistics(
        self,
        file_path: str,
        analysis_type: str = "overview",
        columns: Optional[List[str]] = None,
        group_by: Optional[str] = None
    ) -> DataAnalysisResult:
        """
        执行统计分析
        
        Args:
            file_path: 数据文件路径
            analysis_type: 分析类型
                - overview: 描述性统计概览
                - correlation: 相关性分析
                - distribution: 分布分析
            columns: 指定分析的列
            group_by: 分组列名
            
        Returns:
            DataAnalysisResult 包含统计结果
        """
        self._log(f"📈 Performing {analysis_type} analysis")
        
        try:
            result = self.load_data(file_path)
            if not result.success:
                return result
            
            df = self.context["current_df"]
            
            # 选择列
            if columns:
                df = df[columns]
            
            stats = {}
            summary_parts = []
            
            if analysis_type == "overview":
                # 描述性统计
                numeric_df = df.select_dtypes(include=[np.number])
                if not numeric_df.empty:
                    stats["describe"] = numeric_df.describe().to_dict()
                    summary_parts.append(f"分析 {len(numeric_df.columns)} 个数值列")
                
                # 分类变量统计
                categorical_df = df.select_dtypes(include=["object"])
                if not categorical_df.empty:
                    stats["categorical"] = {
                        col: df[col].value_counts().head(5).to_dict()
                        for col in categorical_df.columns
                    }
                    summary_parts.append(f"分析 {len(categorical_df.columns)} 个分类列")
                
            elif analysis_type == "correlation":
                # 相关性分析
                numeric_df = df.select_dtypes(include=[np.number])
                if len(numeric_df.columns) >= 2:
                    corr_matrix = numeric_df.corr()
                    stats["correlation"] = corr_matrix.to_dict()
                    # 找出强相关对
                    strong_corr = []
                    for i in range(len(corr_matrix.columns)):
                        for j in range(i+1, len(corr_matrix.columns)):
                            corr_val = corr_matrix.iloc[i, j]
                            if abs(corr_val) > 0.7:
                                strong_corr.append({
                                    "col1": corr_matrix.columns[i],
                                    "col2": corr_matrix.columns[j],
                                    "correlation": round(corr_val, 3)
                                })
                    stats["strong_correlations"] = strong_corr
                    summary_parts.append(f"发现 {len(strong_corr)} 对强相关变量")
                
            elif analysis_type == "distribution":
                # 分布分析
                numeric_df = df.select_dtypes(include=[np.number])
                stats["distribution"] = {
                    col: {
                        "mean": float(df[col].mean()),
                        "median": float(df[col].median()),
                        "std": float(df[col].std()),
                        "skew": float(df[col].skew()),
                        "kurt": float(df[col].kurtosis()),
                    }
                    for col in numeric_df.columns
                }
                summary_parts.append(f"分析 {len(numeric_df.columns)} 个数值列的分布")
            
            # 分组统计
            if group_by and group_by in df.columns:
                grouped = df.groupby(group_by).agg({
                    col: ["mean", "sum", "count"]
                    for col in df.select_dtypes(include=[np.number]).columns[:3]
                })
                stats["grouped"] = grouped.to_dict()
                summary_parts.append(f"按 {group_by} 分组统计")
            
            return DataAnalysisResult(
                success=True,
                summary="; ".join(summary_parts),
                statistics=stats
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return DataAnalysisResult(
                success=False,
                summary="",
                error_message=str(e)
            )
    
    def visualize(
        self,
        file_path: str,
        chart_type: str,
        x_column: str,
        y_column: Optional[str] = None,
        title: str = "Chart",
        output_path: Optional[str] = None
    ) -> DataAnalysisResult:
        """
        生成数据可视化图表
        
        Args:
            file_path: 数据文件路径
            chart_type: 图表类型 (line/bar/scatter/histogram/heatmap/pie)
            x_column: X轴列名
            y_column: Y轴列名（可选）
            title: 图表标题
            output_path: 图表保存路径
            
        Returns:
            DataAnalysisResult 包含图表路径
        """
        self._log(f"📊 Creating {chart_type} chart: {title}")
        
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            result = self.load_data(file_path)
            if not result.success:
                return result
            
            df = self.context["current_df"]
            
            # 生成输出路径
            if output_path is None:
                output_path = self.output_dir / f"chart_{chart_type}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if chart_type == "line":
                if y_column:
                    df.plot(x=x_column, y=y_column, kind="line", ax=ax, title=title)
                else:
                    df[x_column].plot(kind="line", ax=ax, title=title)
                    
            elif chart_type == "bar":
                if y_column:
                    df.plot(x=x_column, y=y_column, kind="bar", ax=ax, title=title)
                else:
                    df[x_column].value_counts().plot(kind="bar", ax=ax, title=title)
                    
            elif chart_type == "scatter":
                if y_column:
                    df.plot.scatter(x=x_column, y=y_column, ax=ax, title=title)
                else:
                    return DataAnalysisResult(
                        success=False,
                        summary="",
                        error_message="Scatter plot requires y_column"
                    )
                    
            elif chart_type == "histogram":
                df[x_column].plot(kind="hist", ax=ax, title=title, bins=20)
                
            elif chart_type == "heatmap":
                numeric_df = df.select_dtypes(include=[np.number])
                sns.heatmap(numeric_df.corr(), annot=True, fmt=".2f", ax=ax, cmap="coolwarm")
                ax.set_title(title)
                
            elif chart_type == "pie":
                df[x_column].value_counts().plot(kind="pie", ax=ax, title=title, autopct="%1.1f%%")
                ax.set_ylabel("")
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close()
            
            self._log(f"✅ Chart saved to: {output_path}")
            
            return DataAnalysisResult(
                success=True,
                summary=f"Generated {chart_type} chart",
                artifacts=[{
                    "type": "chart",
                    "format": "png",
                    "path": str(output_path)
                }]
            )
            
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
            return DataAnalysisResult(
                success=False,
                summary="",
                error_message=str(e)
            )
    
    # =====================================================================
    # 高级功能
    # =====================================================================
    
    def analyze(
        self,
        file_path: str,
        analysis_goal: str,
        auto_visualize: bool = True
    ) -> DataAnalysisResult:
        """
        智能分析入口 - 根据目标自动执行完整分析流程
        
        Args:
            file_path: 数据文件路径
            analysis_goal: 分析目标描述（自然语言）
            auto_visualize: 是否自动生成可视化
            
        Returns:
            DataAnalysisResult 完整分析结果
        """
        self._log(f"🎯 Starting analysis: {analysis_goal}")
        
        # 1. 加载数据
        result = self.load_data(file_path)
        if not result.success:
            return result
        
        df = self.context["current_df"]
        
        # 2. 自动清洗
        clean_result = self.clean_data(
            file_path,
            operations=["drop_duplicates", "fillna_mean", "fillna_mode"]
        )
        
        # 3. 全面分析
        stats_result = self.analyze_statistics(file_path, analysis_type="overview")
        
        # 4. 相关性分析（如果有多个数值列）
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        corr_result = None
        if len(numeric_cols) >= 2:
            corr_result = self.analyze_statistics(file_path, analysis_type="correlation")
        
        # 5. 自动生成可视化
        artifacts = []
        if auto_visualize and len(numeric_cols) > 0:
            # 分布图
            viz_result = self.visualize(
                file_path,
                chart_type="histogram",
                x_column=numeric_cols[0],
                title=f"Distribution of {numeric_cols[0]}"
            )
            if viz_result.success:
                artifacts.extend(viz_result.artifacts)
            
            # 热力图（多数值列）
            if len(numeric_cols) >= 2:
                viz_result = self.visualize(
                    file_path,
                    chart_type="heatmap",
                    x_column=numeric_cols[0],
                    title="Correlation Heatmap"
                )
                if viz_result.success:
                    artifacts.extend(viz_result.artifacts)
        
        # 整合结果
        summary = f"""
## 数据分析报告

### 分析目标
{analysis_goal}

### 数据概览
- 数据规模: {result.statistics.get('rows', 0)} 行 × {result.statistics.get('columns', 0)} 列
- 清洗结果: {clean_result.statistics.get('removed_rows', 0)} 行被清理

### 关键发现
{stats_result.summary}

{f"### 相关性洞察\n{corr_result.summary}" if corr_result else ""}

### 生成图表
{len(artifacts)} 个可视化图表已生成
"""
        
        return DataAnalysisResult(
            success=True,
            summary=summary,
            statistics={
                "load": result.statistics,
                "clean": clean_result.statistics,
                "analysis": stats_result.statistics,
            },
            artifacts=artifacts,
            execution_log=self.context["execution_log"]
        )
    
    # =====================================================================
    # 工具导出 - 用于 LangChain Agent 集成
    # =====================================================================
    
    def get_tools(self) -> List[StructuredTool]:
        """
        获取 LangChain 工具列表，用于集成到 Agent
        
        Returns:
            List[StructuredTool] 工具列表
        """
        return [
            StructuredTool.from_function(
                func=self._tool_load_data,
                name="load_data",
                description="加载 CSV/Excel/JSON 数据文件，返回数据概览信息",
                args_schema=LoadDataInput,
            ),
            StructuredTool.from_function(
                func=self._tool_clean_data,
                name="clean_data",
                description="清洗数据：删除重复值、填充缺失值",
                args_schema=CleanDataInput,
            ),
            StructuredTool.from_function(
                func=self._tool_analyze_statistics,
                name="analyze_statistics",
                description="执行统计分析：描述统计、相关性、分布分析",
                args_schema=AnalyzeInput,
            ),
            StructuredTool.from_function(
                func=self._tool_visualize,
                name="visualize_data",
                description="生成数据可视化图表：折线图、柱状图、散点图、热力图等",
                args_schema=VisualizeInput,
            ),
        ]
    
    def _tool_load_data(self, **kwargs) -> str:
        """Tool wrapper for load_data"""
        result = self.load_data(**kwargs)
        return json.dumps({
            "success": result.success,
            "summary": result.summary,
            "statistics": result.statistics,
            "error": result.error_message
        }, ensure_ascii=False, default=str)
    
    def _tool_clean_data(self, **kwargs) -> str:
        """Tool wrapper for clean_data"""
        result = self.clean_data(**kwargs)
        return json.dumps({
            "success": result.success,
            "summary": result.summary,
            "statistics": result.statistics,
            "error": result.error_message
        }, ensure_ascii=False, default=str)
    
    def _tool_analyze_statistics(self, **kwargs) -> str:
        """Tool wrapper for analyze_statistics"""
        result = self.analyze_statistics(**kwargs)
        return json.dumps({
            "success": result.success,
            "summary": result.summary,
            "statistics": result.statistics,
            "error": result.error_message
        }, ensure_ascii=False, default=str)
    
    def _tool_visualize(self, **kwargs) -> str:
        """Tool wrapper for visualize"""
        result = self.visualize(**kwargs)
        return json.dumps({
            "success": result.success,
            "summary": result.summary,
            "artifacts": result.artifacts,
            "error": result.error_message
        }, ensure_ascii=False, default=str)
    
    # =====================================================================
    # 辅助方法
    # =====================================================================
    
    def _generate_data_overview(self, df: pd.DataFrame) -> str:
        """生成数据概览文本"""
        lines = [
            f"## 数据概览",
            f"",
            f"- **行数**: {len(df)}",
            f"- **列数**: {len(df.columns)}",
            f"- **列名**: {', '.join(df.columns.tolist())}",
            f"",
            f"### 数据类型分布",
        ]
        
        dtype_counts = df.dtypes.value_counts()
        for dtype, count in dtype_counts.items():
            lines.append(f"- {dtype}: {count} 列")
        
        # 缺失值统计
        missing = df.isnull().sum()
        missing_cols = missing[missing > 0]
        if len(missing_cols) > 0:
            lines.extend([
                f"",
                f"### 缺失值统计",
            ])
            for col, count in missing_cols.head(5).items():
                lines.append(f"- {col}: {count} 个缺失值 ({count/len(df)*100:.1f}%)")
        
        return "\n".join(lines)


# =============================================================================
# 便捷函数
# =============================================================================

def analyze_data(
    file_path: str,
    analysis_goal: str,
    output_dir: str = "./output"
) -> DataAnalysisResult:
    """
    便捷函数：一键分析数据
    
    Args:
        file_path: 数据文件路径
        analysis_goal: 分析目标
        output_dir: 输出目录
        
    Returns:
        DataAnalysisResult 分析结果
    """
    skill = DataAnalysisSkill(output_dir=output_dir)
    return skill.analyze(file_path, analysis_goal)
