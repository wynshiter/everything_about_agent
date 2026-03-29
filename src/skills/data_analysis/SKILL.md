---
name: data-analysis-skill
description: |
  专业的数据分析 Skill，支持 CSV/Excel 数据加载、数据清洗、
  探索性数据分析(EDA)、统计计算和数据可视化。能够根据自然语言
  指令自动执行数据分析任务并生成图表和报告。
metadata:
  version: "1.0.0"
  author: "Everything About Agent Project"
  category: "data_science"
  adk_additional_tools:
    - "load_data"
    - "clean_data"
    - "analyze_data"
    - "visualize_data"
    - "generate_report"
  supported_formats:
    - "csv"
    - "excel"
    - "json"
  required_packages:
    - "pandas>=2.0.0"
    - "numpy>=1.24.0"
    - "matplotlib>=3.7.0"
    - "seaborn>=0.12.0"
    - "openpyxl>=3.0.0"
---

# 数据分析 Skill (Data Analysis Skill)

## 功能概述

本 Skill 提供端到端的数据分析能力，帮助用户快速理解数据、发现洞察。

### 核心能力

1. **数据加载** - 支持 CSV、Excel、JSON 格式
2. **数据清洗** - 缺失值处理、重复值处理、类型转换
3. **探索性分析** - 描述性统计、分布分析、相关性分析
4. **数据可视化** - 折线图、柱状图、散点图、热力图
5. **报告生成** - 自动化的分析摘要和图表报告

## 使用步骤

### Step 1: 数据加载

使用 `load_data` 工具加载数据文件：

```python
load_data(
    file_path="data/sales.csv",
    file_type="csv",
    encoding="utf-8"
)
```

### Step 2: 数据概览

获取数据基本信息：
- 行列数
- 列名和数据类型
- 缺失值统计
- 重复行统计

### Step 3: 数据清洗（可选）

根据数据质量问题执行清洗：
- 删除/填充缺失值
- 删除重复行
- 数据类型转换

### Step 4: 数据分析

根据分析目标选择分析方法：
- **描述性分析**: 统计摘要、分组聚合
- **相关性分析**: 变量间相关性矩阵
- **趋势分析**: 时间序列趋势

### Step 5: 可视化

生成图表：
- `line_chart`: 趋势图
- `bar_chart`: 对比图
- `scatter_plot`: 散点图
- `heatmap`: 热力图
- `histogram`: 分布直方图

### Step 6: 生成报告

输出包含文字摘要和图表路径的完整报告。

## 最佳实践

1. **始终先查看数据概览** - 了解数据结构和质量问题
2. **分步骤执行** - 先清洗再分析，避免错误传播
3. **选择合适图表** - 趋势用折线图，对比用柱状图，关系用散点图
4. **保存中间结果** - 清洗后的数据可以导出供后续使用

## 安全提示

- 数据文件路径需要正确权限
- 大数据集可能消耗较多内存
- 可视化输出保存在 `assets/` 目录

## 示例场景

### 场景1: 销售数据分析
```
输入: "分析 sales.csv 文件，查看月度销售趋势，并找出销量最高的产品"
输出: 趋势图 + 产品排名表 + 关键洞察
```

### 场景2: 用户行为分析
```
输入: "分析用户注册数据，查看用户增长趋势和地区分布"
输出: 增长曲线 + 地区分布图 + 增长洞察
```

### 场景3: 数据质量检查
```
输入: "检查 data.csv 的数据质量，列出所有问题"
输出: 质量报告（缺失值、异常值、重复值统计）
```

## 参考资料

- [Pandas 文档](references/pandas_guide.md)
- [数据可视化指南](references/visualization_guide.md)
- [统计分析速查](references/statistics_cheatsheet.md)
