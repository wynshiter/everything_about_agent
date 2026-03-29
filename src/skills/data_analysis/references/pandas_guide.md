# Pandas 数据分析指南

## 常用操作速查

### 数据加载
```python
import pandas as pd

# CSV
df = pd.read_csv('file.csv', encoding='utf-8')

# Excel
df = pd.read_excel('file.xlsx', sheet_name='Sheet1')

# JSON
df = pd.read_json('file.json')
```

### 数据查看
```python
df.head()           # 前5行
df.tail()           # 后5行
df.info()           # 数据信息
df.describe()       # 统计摘要
df.columns          # 列名
df.dtypes           # 数据类型
```

### 数据清洗
```python
# 处理缺失值
df.dropna()                              # 删除含缺失值的行
df.fillna(0)                             # 用0填充
df.fillna(df.mean())                     # 用均值填充
df.fillna(df.mode().iloc[0])             # 用众数填充

# 处理重复值
df.drop_duplicates()                     # 删除重复行

# 类型转换
df['col'] = df['col'].astype('float')    # 转浮点数
df['col'] = pd.to_datetime(df['col'])    # 转日期
```

### 数据分析
```python
# 分组统计
df.groupby('category').agg({'sales': 'sum', 'quantity': 'mean'})

# 透视表
pd.pivot_table(df, values='sales', index='category', columns='month', aggfunc='sum')

# 排序
df.sort_values('sales', ascending=False)

# 筛选
df[df['sales'] > 1000]
df.query('sales > 1000 and category == "A"')
```
