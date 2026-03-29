"""
简单的 Skill 功能测试
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.skills.data_analysis import DataAnalysisSkill

# 初始化
skill = DataAnalysisSkill(output_dir="./output")

# 加载数据
data_path = Path(__file__).parent / "sample_sales_data.csv"
print(f"Loading: {data_path}")

result = skill.load_data(str(data_path))
print(f"Success: {result.success}")
print(f"Rows: {result.statistics.get('rows')}")
print(f"Columns: {result.statistics.get('columns')}")

# 生成可视化
viz_result = skill.visualize(
    str(data_path),
    chart_type="bar",
    x_column="product",
    y_column="sales_quantity",
    title="Product Sales"
)

print(f"Chart generated: {viz_result.success}")
if viz_result.artifacts:
    print(f"Chart path: {viz_result.artifacts[0]['path']}")

print("\nTest completed!")
