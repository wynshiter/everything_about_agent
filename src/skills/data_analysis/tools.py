"""
数据分析工具 - LangChain Tool 封装

提供可直接集成到 LangChain Agent 的数据分析工具。
每个工具都遵循 Google ADK 的渐进式披露原则。
"""

from typing import List, Optional
from langchain_core.tools import tool, StructuredTool
from pydantic import BaseModel, Field
import pandas as pd
import json


# =============================================================================
# 工具输入模式定义
# =============================================================================

class LoadDataInput(BaseModel):
    """数据加载工具输入模式"""
    file_path: str = Field(
        ...,
        description="数据文件的绝对或相对路径，例如: 'data/sales.csv'"
    )
    file_type: str = Field(
        default="csv",
        description="文件类型，可选: csv, excel, json"
    )
    encoding: str = Field(
        default="utf-8",
        description="文件编码，默认utf-8，中文数据可尝试'gbk'"
    )


class CleanDataInput(BaseModel):
    """数据清洗工具输入模式"""
    file_path: str = Field(
        ...,
        description="原始数据文件路径"
    )
    operations: List[str] = Field(
        default=["drop_duplicates"],
        description="清洗操作列表，可选: drop_duplicates(去重), dropna(删缺失值), fillna_mean(均值填充), fillna_mode(众数填充)"
    )
    output_path: Optional[str] = Field(
        None,
        description="清洗后数据保存路径，不指定则不保存"
    )


class AnalyzeStatisticsInput(BaseModel):
    """统计分析工具输入模式"""
    file_path: str = Field(
        ...,
        description="数据文件路径"
    )
    analysis_type: str = Field(
        default="overview",
        description="分析类型，可选: overview(概览), correlation(相关性), distribution(分布)"
    )
    columns: Optional[List[str]] = Field(
        None,
        description="要分析的列名列表，None表示分析所有列"
    )


class VisualizeInput(BaseModel):
    """可视化工具输入模式"""
    file_path: str = Field(
        ...,
        description="数据文件路径"
    )
    chart_type: str = Field(
        ...,
        description="图表类型，可选: line(折线), bar(柱状), scatter(散点), histogram(直方), heatmap(热力), pie(饼图)"
    )
    x_column: str = Field(
        ...,
        description="X轴列名，用于横坐标或分类"
    )
    y_column: Optional[str] = Field(
        None,
        description="Y轴列名，用于数值，可选"
    )
    title: str = Field(
        default="数据可视化",
        description="图表标题"
    )


# =============================================================================
# 工具实现
# =============================================================================

@tool
def load_data_tool(
    file_path: str,
    file_type: str = "csv",
    encoding: str = "utf-8"
) -> str:
    """
    加载数据文件，返回数据概览信息。
    
    使用场景:
    - 分析开始前加载数据
    - 查看数据结构和基本信息
    - 检查数据质量和缺失值
    
    返回信息包括:
    - 行列数
    - 列名和数据类型
    - 缺失值统计
    - 内存占用
    
    Example:
        load_data_tool("data/sales.csv", "csv")
    """
    try:
        import pandas as pd
        from pathlib import Path
        
        path = Path(file_path)
        if not path.exists():
            return f"错误: 文件不存在 - {file_path}"
        
        # 加载数据
        if file_type.lower() == "csv":
            df = pd.read_csv(file_path, encoding=encoding)
        elif file_type.lower() in ["excel", "xlsx", "xls"]:
            df = pd.read_excel(file_path)
        elif file_type.lower() == "json":
            df = pd.read_json(file_path)
        else:
            return f"错误: 不支持的文件类型 - {file_type}"
        
        # 生成概览
        info = {
            "文件路径": file_path,
            "行数": len(df),
            "列数": len(df.columns),
            "列名": df.columns.tolist(),
            "数据类型": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "缺失值": df.isnull().sum().to_dict(),
            "内存占用(MB)": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        }
        
        return json.dumps(info, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"加载数据失败: {str(e)}"


@tool
def clean_data_tool(
    file_path: str,
    operations: List[str] = None,
    output_path: Optional[str] = None
) -> str:
    """
    清洗数据，处理质量问题。
    
    使用场景:
    - 删除重复数据
    - 处理缺失值
    - 数据标准化
    
    支持的清洗操作:
    - drop_duplicates: 删除重复行
    - dropna: 删除含缺失值的行
    - fillna_mean: 用均值填充数值列缺失值
    - fillna_mode: 用众数填充分类列缺失值
    
    Example:
        clean_data_tool("data.csv", ["drop_duplicates", "fillna_mean"], "cleaned.csv")
    """
    try:
        import pandas as pd
        import numpy as np
        
        operations = operations or ["drop_duplicates"]
        
        # 加载数据
        df = pd.read_csv(file_path)
        original_rows = len(df)
        
        results = {
            "原始行数": original_rows,
            "操作记录": []
        }
        
        # 执行清洗
        for op in operations:
            if op == "drop_duplicates":
                before = len(df)
                df = df.drop_duplicates()
                removed = before - len(df)
                results["操作记录"].append(f"去重: 删除 {removed} 行")
                
            elif op == "dropna":
                before = len(df)
                df = df.dropna()
                removed = before - len(df)
                results["操作记录"].append(f"删缺失值: 删除 {removed} 行")
                
            elif op == "fillna_mean":
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                filled_count = df[numeric_cols].isnull().sum().sum()
                df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                results["操作记录"].append(f"均值填充: 填充 {filled_count} 个数值缺失值")
                
            elif op == "fillna_mode":
                categorical_cols = df.select_dtypes(include=["object"]).columns
                filled_count = 0
                for col in categorical_cols:
                    mode = df[col].mode()
                    if len(mode) > 0:
                        na_count = df[col].isnull().sum()
                        df[col] = df[col].fillna(mode[0])
                        filled_count += na_count
                results["操作记录"].append(f"众数填充: 填充 {filled_count} 个分类缺失值")
        
        results["清洗后行数"] = len(df)
        results["删除总行数"] = original_rows - len(df)
        
        # 保存
        if output_path:
            df.to_csv(output_path, index=False, encoding="utf-8")
            results["保存路径"] = output_path
        
        return json.dumps(results, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"数据清洗失败: {str(e)}"


@tool
def analyze_statistics_tool(
    file_path: str,
    analysis_type: str = "overview",
    columns: Optional[List[str]] = None
) -> str:
    """
    执行统计分析，发现数据洞察。
    
    使用场景:
    - 获取数据的描述性统计
    - 分析变量间的相关性
    - 了解数据分布特征
    
    分析类型:
    - overview: 描述性统计（均值、标准差、分位数等）
    - correlation: 相关性分析（相关系数矩阵）
    - distribution: 分布分析（偏度、峰度等）
    
    Example:
        analyze_statistics_tool("data.csv", "correlation", ["sales", "profit"])
    """
    try:
        import pandas as pd
        import numpy as np
        
        df = pd.read_csv(file_path)
        
        if columns:
            df = df[columns]
        
        results = {"分析类型": analysis_type}
        
        if analysis_type == "overview":
            # 描述性统计
            numeric_df = df.select_dtypes(include=[np.number])
            if not numeric_df.empty:
                desc = numeric_df.describe()
                results["描述统计"] = desc.to_dict()
                
            # 分类变量
            categorical_df = df.select_dtypes(include=["object"])
            if not categorical_df.empty:
                results["分类统计"] = {
                    col: df[col].value_counts().head(5).to_dict()
                    for col in categorical_df.columns
                }
                
        elif analysis_type == "correlation":
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) >= 2:
                corr = numeric_df.corr()
                results["相关系数"] = corr.to_dict()
                
                # 强相关对
                strong = []
                for i in range(len(corr.columns)):
                    for j in range(i+1, len(corr.columns)):
                        val = corr.iloc[i, j]
                        if abs(val) > 0.7:
                            strong.append({
                                "变量1": corr.columns[i],
                                "变量2": corr.columns[j],
                                "相关系数": round(val, 3)
                            })
                results["强相关对(|r|>0.7)"] = strong
            else:
                results["警告"] = "数值列不足2个，无法计算相关性"
                
        elif analysis_type == "distribution":
            numeric_df = df.select_dtypes(include=[np.number])
            results["分布特征"] = {
                col: {
                    "均值": float(df[col].mean()),
                    "中位数": float(df[col].median()),
                    "标准差": float(df[col].std()),
                    "最小值": float(df[col].min()),
                    "最大值": float(df[col].max()),
                    "偏度": float(df[col].skew()),
                    "峰度": float(df[col].kurtosis()),
                }
                for col in numeric_df.columns
            }
        
        return json.dumps(results, ensure_ascii=False, indent=2, default=str)
        
    except Exception as e:
        return f"统计分析失败: {str(e)}"


@tool
def visualize_tool(
    file_path: str,
    chart_type: str,
    x_column: str,
    y_column: Optional[str] = None,
    title: str = "数据可视化"
) -> str:
    """
    生成数据可视化图表。
    
    使用场景:
    - 展示数据趋势
    - 对比不同类别
    - 展示变量关系
    - 展示数据分布
    
    支持的图表类型:
    - line: 折线图（展示趋势）
    - bar: 柱状图（展示对比）
    - scatter: 散点图（展示关系）
    - histogram: 直方图（展示分布）
    - heatmap: 热力图（展示相关性）
    - pie: 饼图（展示占比）
    
    Example:
        visualize_tool("sales.csv", "line", "month", "revenue", "月度收入趋势")
    """
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
        from pathlib import Path
        
        df = pd.read_csv(file_path)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 生成输出路径
        output_dir = Path("./output")
        output_dir.mkdir(exist_ok=True)
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f"{chart_type}_{timestamp}.png"
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == "line":
            if y_column and y_column in df.columns:
                df.plot(x=x_column, y=y_column, kind="line", ax=ax, marker='o')
            else:
                df[x_column].plot(kind="line", ax=ax, marker='o')
                
        elif chart_type == "bar":
            if y_column and y_column in df.columns:
                df.plot(x=x_column, y=y_column, kind="bar", ax=ax)
            else:
                df[x_column].value_counts().plot(kind="bar", ax=ax)
                
        elif chart_type == "scatter":
            if y_column and y_column in df.columns:
                df.plot.scatter(x=x_column, y=y_column, ax=ax, alpha=0.6)
            else:
                return "散点图需要提供 y_column 参数"
                
        elif chart_type == "histogram":
            df[x_column].plot(kind="hist", ax=ax, bins=20, edgecolor='black')
            ax.axvline(df[x_column].mean(), color='red', linestyle='--', label='Mean')
            ax.legend()
            
        elif chart_type == "heatmap":
            import seaborn as sns
            numeric_df = df.select_dtypes(include=[np.number])
            sns.heatmap(numeric_df.corr(), annot=True, fmt=".2f", ax=ax, cmap="coolwarm", center=0)
            
        elif chart_type == "pie":
            df[x_column].value_counts().plot(kind="pie", ax=ax, autopct='%1.1f%%')
            ax.set_ylabel('')
        else:
            return f"不支持的图表类型: {chart_type}"
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return json.dumps({
            "状态": "成功",
            "图表类型": chart_type,
            "保存路径": str(output_path),
            "标题": title,
            "X轴": x_column,
            "Y轴": y_column or "N/A"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"生成图表失败: {str(e)}"


# =============================================================================
# 工具集合
# =============================================================================

def get_data_tools() -> List[StructuredTool]:
    """
    获取所有数据分析工具列表
    
    用于集成到 LangChain Agent:
        from src.skills.data_analysis import get_data_tools
        
        tools = get_data_tools()
        agent = create_tool_calling_agent(llm, tools, prompt)
    
    Returns:
        List[StructuredTool]: 数据分析工具列表
    """
    return [
        StructuredTool.from_function(
            func=load_data_tool,
            name="load_data",
            description="加载 CSV/Excel/JSON 数据文件，返回数据概览、列信息、缺失值统计",
        ),
        StructuredTool.from_function(
            func=clean_data_tool,
            name="clean_data",
            description="清洗数据：删除重复值、处理缺失值（支持均值/众数填充）",
        ),
        StructuredTool.from_function(
            func=analyze_statistics_tool,
            name="analyze_statistics",
            description="执行统计分析：描述统计、相关性分析、分布分析",
        ),
        StructuredTool.from_function(
            func=visualize_tool,
            name="visualize_data",
            description="生成数据可视化：折线图、柱状图、散点图、直方图、热力图、饼图",
        ),
    ]
