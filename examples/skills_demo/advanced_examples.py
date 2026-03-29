"""
Skills 高级使用示例

展示数据分析 Skill 的高级用法和最佳实践。
"""

import sys
from pathlib import Path
from typing import List, Dict
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.skills.data_analysis import DataAnalysisSkill, analyze_data


# =============================================================================
# 示例1: 自定义分析流程
# =============================================================================

def custom_analysis_workflow():
    """
    自定义分析流程
    
    展示如何组合多个分析步骤，构建自定义分析流程。
    """
    print("=" * 70)
    print("示例1: 自定义分析流程")
    print("=" * 70)
    
    skill = DataAnalysisSkill(output_dir="./output/custom")
    data_path = "examples/skills_demo/sample_sales_data.csv"
    
    # Step 1: 数据质量评估
    print("\n[Step 1] 数据质量评估...")
    load_result = skill.load_data(data_path)
    
    quality_score = 100
    issues = []
    
    # 检查缺失值
    missing = load_result.statistics.get('missing_values', {})
    if any(v > 0 for v in missing.values()):
        quality_score -= 20
        issues.append(f"存在缺失值: {missing}")
    
    # 检查数据量
    if load_result.statistics['rows'] < 10:
        quality_score -= 10
        issues.append("数据量较小")
    
    print(f"  数据质量评分: {quality_score}/100")
    if issues:
        for issue in issues:
            print(f"  ⚠ {issue}")
    
    # Step 2: 关键指标计算
    print("\n[Step 2] 关键指标计算...")
    
    import pandas as pd
    df = pd.read_csv(data_path)
    
    metrics = {
        "总销售额": df['revenue'].sum(),
        "平均订单额": df['revenue'].mean(),
        "总销量": df['sales_quantity'].sum(),
        "平均客户数": df['customer_count'].mean(),
        "最高单价": df['unit_price'].max(),
        "最低单价": df['unit_price'].min(),
    }
    
    for name, value in metrics.items():
        if isinstance(value, float):
            print(f"  {name}: {value:,.2f}")
        else:
            print(f"  {name}: {value:,}")
    
    # Step 3: 产品排名
    print("\n[Step 3] 产品排名...")
    product_ranking = df.groupby('product').agg({
        'revenue': 'sum',
        'sales_quantity': 'sum'
    }).sort_values('revenue', ascending=False)
    
    print("  收入排名:")
    for i, (product, row) in enumerate(product_ranking.iterrows(), 1):
        print(f"    {i}. {product}: ${row['revenue']:,.2f}")
    
    # Step 4: 趋势分析
    print("\n[Step 4] 趋势分析...")
    df['date'] = pd.to_datetime(df['date'])
    daily_revenue = df.groupby('date')['revenue'].sum()
    
    # 计算增长趋势
    if len(daily_revenue) > 1:
        first_week = daily_revenue.head(7).mean()
        last_week = daily_revenue.tail(7).mean()
        growth = (last_week - first_week) / first_week * 100
        
        print(f"  首周平均收入: ${first_week:,.2f}")
        print(f"  末周平均收入: ${last_week:,.2f}")
        print(f"  增长率: {growth:+.1f}%")
        
        if growth > 0:
            print("  📈 上升趋势")
        elif growth < 0:
            print("  📉 下降趋势")
        else:
            print("  ➡️ 平稳")
    
    # Step 5: 生成可视化
    print("\n[Step 5] 生成可视化...")
    
    # 收入趋势
    skill.visualize(
        data_path,
        chart_type="line",
        x_column="date",
        y_column="revenue",
        title="收入趋势分析"
    )
    
    # 产品对比
    skill.visualize(
        data_path,
        chart_type="bar",
        x_column="product",
        y_column="revenue",
        title="产品收入对比"
    )
    
    print("\n✅ 自定义分析流程完成！")


# =============================================================================
# 示例2: 批量数据处理
# =============================================================================

def batch_processing_example():
    """
    批量数据处理示例
    
    展示如何批量处理多个数据文件。
    """
    print("\n" + "=" * 70)
    print("示例2: 批量数据处理")
    print("=" * 70)
    
    # 模拟多个数据文件
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建多个测试文件
        files = []
        for i in range(3):
            file_path = Path(tmpdir) / f"data_{i+1}.csv"
            with open(file_path, 'w') as f:
                f.write("product,sales\n")
                f.write(f"A,{100 + i * 20}\n")
                f.write(f"B,{150 + i * 15}\n")
                f.write(f"C,{200 + i * 10}\n")
            files.append(str(file_path))
        
        print(f"\n创建了 {len(files)} 个测试文件")
        
        # 批量分析
        results = []
        for file_path in files:
            print(f"\n处理: {Path(file_path).name}")
            
            result = analyze_data(
                file_path=file_path,
                analysis_goal=f"分析 {Path(file_path).stem} 数据",
                output_dir=f"./output/batch/{Path(file_path).stem}"
            )
            
            results.append({
                "file": Path(file_path).name,
                "success": result.success,
                "summary": result.summary[:100] + "..."
            })
        
        # 汇总报告
        print("\n" + "-" * 70)
        print("批量处理结果汇总:")
        for r in results:
            status = "✅" if r['success'] else "❌"
            print(f"  {status} {r['file']}")


# =============================================================================
# 示例3: 报告生成
# =============================================================================

def generate_analysis_report():
    """
    生成完整分析报告
    
    展示如何生成结构化的 Markdown 分析报告。
    """
    print("\n" + "=" * 70)
    print("示例3: 生成分析报告")
    print("=" * 70)
    
    data_path = "examples/skills_demo/sample_sales_data.csv"
    output_dir = "./output/report"
    
    # 执行分析
    print("\n执行数据分析...")
    result = analyze_data(
        file_path=data_path,
        analysis_goal="生成完整的销售数据分析报告",
        output_dir=output_dir
    )
    
    if not result.success:
        print(f"分析失败: {result.error_message}")
        return
    
    # 构建报告
    report = f"""# 销售数据分析报告

生成时间: 2026-03-29

## 执行摘要

{result.summary}

## 数据概览

- **数据规模**: {result.statistics.get('load', {}).get('rows', 'N/A')} 行
- **数据列数**: {result.statistics.get('load', {}).get('columns', 'N/A')} 列
- **清洗情况**: {result.statistics.get('clean', {}).get('removed_rows', 0)} 行被清理

## 详细统计

### 描述性统计
```
{json.dumps(result.statistics.get('analysis', {}), indent=2, ensure_ascii=False)}
```

## 生成图表

"""
    
    # 添加图表引用
    for i, artifact in enumerate(result.artifacts, 1):
        report += f"{i}. {artifact['type'].upper()}: `{artifact['path']}`\n"
    
    report += """

## 关键发现

1. **销售趋势**: 基于数据分析，收入呈现稳定趋势
2. **产品表现**: 不同产品间存在显著差异
3. **地区分布**: 各地区销售表现均衡

## 建议行动

1. 重点关注高价值产品
2. 优化低销量产品的营销策略
3. 持续监控关键指标变化

---
*报告由 DataAnalysisSkill 自动生成*
"""
    
    # 保存报告
    report_path = Path(output_dir) / "analysis_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    
    print(f"\n✅ 报告已生成: {report_path}")
    print(f"\n报告预览:")
    print("-" * 70)
    print(report[:500] + "...")


# =============================================================================
# 示例4: 数据质量检查框架
# =============================================================================

def data_quality_framework():
    """
    数据质量检查框架
    
    展示如何构建系统化的数据质量检查流程。
    """
    print("\n" + "=" * 70)
    print("示例4: 数据质量检查框架")
    print("=" * 70)
    
    class DataQualityChecker:
        """数据质量检查器"""
        
        def __init__(self):
            self.checks = []
            self.results = []
        
        def add_check(self, name: str, check_func, weight: float = 1.0):
            """添加检查项"""
            self.checks.append({
                "name": name,
                "func": check_func,
                "weight": weight
            })
        
        def run_checks(self, df) -> Dict:
            """执行所有检查"""
            total_score = 0
            total_weight = 0
            
            for check in self.checks:
                try:
                    passed, message = check["func"](df)
                    score = check["weight"] if passed else 0
                    
                    self.results.append({
                        "name": check["name"],
                        "passed": passed,
                        "score": score,
                        "message": message
                    })
                    
                    total_score += score
                    total_weight += check["weight"]
                    
                except Exception as e:
                    self.results.append({
                        "name": check["name"],
                        "passed": False,
                        "score": 0,
                        "message": f"检查失败: {e}"
                    })
                    total_weight += check["weight"]
            
            overall_score = (total_score / total_weight * 100) if total_weight > 0 else 0
            
            return {
                "overall_score": overall_score,
                "results": self.results
            }
    
    # 定义检查函数
    def check_completeness(df):
        """完整性检查"""
        missing_pct = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
        passed = missing_pct < 0.05  # 允许 5% 缺失
        return passed, f"缺失率: {missing_pct*100:.1f}%"
    
    def check_uniqueness(df):
        """唯一性检查"""
        dup_pct = df.duplicated().sum() / len(df)
        passed = dup_pct < 0.01  # 允许 1% 重复
        return passed, f"重复率: {dup_pct*100:.1f}%"
    
    def check_consistency(df):
        """一致性检查"""
        # 检查数据类型一致性
        issues = []
        for col in df.select_dtypes(include=['object']):
            if df[col].str.isnumeric().any():
                issues.append(f"{col} 可能包含数值数据但被识别为文本")
        
        passed = len(issues) == 0
        return passed, "; ".join(issues) if issues else "数据类型一致"
    
    def check_validity(df):
        """有效性检查"""
        issues = []
        
        # 检查数值列是否有负数（假设都不应为负）
        for col in df.select_dtypes(include=['number']):
            if (df[col] < 0).any():
                issues.append(f"{col} 包含负值")
        
        passed = len(issues) == 0
        return passed, "; ".join(issues) if issues else "所有数值有效"
    
    # 执行检查
    print("\n初始化数据质量检查器...")
    checker = DataQualityChecker()
    
    checker.add_check("完整性", check_completeness, weight=2.0)
    checker.add_check("唯一性", check_uniqueness, weight=1.5)
    checker.add_check("一致性", check_consistency, weight=1.0)
    checker.add_check("有效性", check_validity, weight=2.0)
    
    print(f"已添加 {len(checker.checks)} 个检查项")
    
    # 加载数据并检查
    import pandas as pd
    df = pd.read_csv("examples/skills_demo/sample_sales_data.csv")
    
    print("\n执行检查...")
    report = checker.run_checks(df)
    
    print(f"\n整体质量评分: {report['overall_score']:.1f}/100")
    print("-" * 70)
    
    for result in report['results']:
        status = "✅" if result['passed'] else "❌"
        print(f"{status} {result['name']}: {result['message']}")
    
    # 质量评级
    score = report['overall_score']
    if score >= 90:
        grade = "A (优秀)"
    elif score >= 80:
        grade = "B (良好)"
    elif score >= 70:
        grade = "C (合格)"
    else:
        grade = "D (需改进)"
    
    print(f"\n质量评级: {grade}")


# =============================================================================
# 示例5: 自定义 Skill 扩展示例
# =============================================================================

def custom_skill_extension_example():
    """
    自定义 Skill 扩展示例
    
    展示如何通过继承扩展 DataAnalysisSkill。
    """
    print("\n" + "=" * 70)
    print("示例5: 自定义 Skill 扩展")
    print("=" * 70)
    
    class AdvancedAnalysisSkill(DataAnalysisSkill):
        """高级分析 Skill - 扩展基础功能"""
        
        def __init__(self, output_dir: str = "./output"):
            super().__init__(output_dir)
            self.custom_config = {
                "confidence_level": 0.95,
                "outlier_threshold": 3.0
            }
        
        def detect_outliers(self, file_path: str, column: str) -> List[int]:
            """
            检测异常值
            
            使用 Z-score 方法检测异常值。
            """
            import pandas as pd
            import numpy as np
            
            df = pd.read_csv(file_path)
            
            if column not in df.columns:
                return []
            
            if not pd.api.types.is_numeric_dtype(df[column]):
                return []
            
            # 计算 Z-score
            z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
            
            # 找出异常值
            outliers = df[z_scores > self.custom_config["outlier_threshold"]].index.tolist()
            
            return outliers
        
        def calculate_growth_rate(self, file_path: str, date_col: str, value_col: str) -> Dict:
            """
            计算增长率
            """
            import pandas as pd
            
            df = pd.read_csv(file_path)
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.sort_values(date_col)
            
            # 计算日增长率
            df['growth_rate'] = df[value_col].pct_change() * 100
            
            return {
                "avg_growth": df['growth_rate'].mean(),
                "max_growth": df['growth_rate'].max(),
                "min_growth": df['growth_rate'].min(),
                "growth_rates": df[['date', 'growth_rate']].dropna().to_dict('records')
            }
        
        def generate_executive_summary(self, file_path: str) -> str:
            """
            生成高管摘要
            """
            # 执行基础分析
            base_result = self.analyze(file_path, "生成高管摘要")
            
            # 添加自定义洞察
            outliers = self.detect_outliers(file_path, 'revenue')
            growth = self.calculate_growth_rate(file_path, 'date', 'revenue')
            
            summary = f"""
# 高管数据分析摘要

## 关键指标
- 数据规模: {base_result.statistics.get('load', {}).get('rows')} 条记录
- 平均增长率: {growth['avg_growth']:+.2f}%
- 异常值数量: {len(outliers)} 个

## 核心洞察
1. 收入趋势 {'上升' if growth['avg_growth'] > 0 else '下降'}
2. 数据质量 {'良好' if len(outliers) < 5 else '需关注'}
3. 建议采取数据驱动的决策

## 下一步行动
1. 深入分析异常值原因
2. 制定增长策略
3. 持续监控关键指标
"""
            return summary
    
    # 使用扩展的 Skill
    print("\n初始化高级分析 Skill...")
    skill = AdvancedAnalysisSkill(output_dir="./output/advanced")
    
    data_path = "examples/skills_demo/sample_sales_data.csv"
    
    # 检测异常值
    print("\n检测异常值...")
    outliers = skill.detect_outliers(data_path, 'revenue')
    print(f"发现 {len(outliers)} 个异常值")
    if outliers:
        print(f"异常值索引: {outliers}")
    
    # 计算增长率
    print("\n计算增长率...")
    growth = skill.calculate_growth_rate(data_path, 'date', 'revenue')
    print(f"平均日增长率: {growth['avg_growth']:+.2f}%")
    print(f"最高日增长率: {growth['max_growth']:+.2f}%")
    print(f"最低日增长率: {growth['min_growth']:+.2f}%")
    
    # 生成高管摘要
    print("\n生成高管摘要...")
    summary = skill.generate_executive_summary(data_path)
    print(summary)


# =============================================================================
# 主函数
# =============================================================================

def main():
    """运行所有示例"""
    print("=" * 70)
    print("Skills 高级使用示例")
    print("=" * 70)
    
    examples = [
        ("自定义分析流程", custom_analysis_workflow),
        ("批量数据处理", batch_processing_example),
        ("生成分析报告", generate_analysis_report),
        ("数据质量检查", data_quality_framework),
        ("自定义 Skill 扩展", custom_skill_extension_example),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\n❌ {name} 失败: {e}")
        
        if i < len(examples):
            input("\n按 Enter 继续下一个示例...")
    
    print("\n" + "=" * 70)
    print("所有示例完成！")
    print("=" * 70)
    print("\n生成的文件:")
    print("  - output/custom/* - 自定义分析输出")
    print("  - output/batch/* - 批量处理输出")
    print("  - output/report/* - 分析报告")
    print("  - output/advanced/* - 高级分析输出")


if __name__ == "__main__":
    main()
