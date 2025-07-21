# 表数量与关联关系详解

## 1. 表数量统计

### 1.1 基础表（固定）
```
1. oge_vector_data_product    - 产品表（管理所有矢量产品）
2. oge_vector_fact           - 事实表（关联产品与存储表）
3. oge_db_connection         - 数据库连接表
4. oge_catalog_scheme        - 分类表
5. oge_sensor                - 传感器表
```

### 1.2 动态生成的表（根据数据文件）
```
每个矢量文件 → 1个或多个数据表
```

## 2. 表生成规则

### 2.1 单文件单图层
```
输入: roads.shp
输出: 1个表
- roads (存储道路数据)
```

### 2.2 单文件多图层（GDB）
```
输入: city_data.gdb (包含3个图层)
输出: 3个表
- city_data_buildings
- city_data_roads  
- city_data_boundaries
```

### 2.3 混合几何类型文件
```
输入: mixed_features.geojson (包含点、线、面)
输出: 3个表
- mixed_features_point
- mixed_features_linestring
- mixed_features_polygon
```

## 3. 表关联关系

### 3.1 关联架构图
```
oge_vector_data_product (产品表)
    ↓ (1:N)
oge_vector_fact (事实表)
    ↓ (1:1)
具体数据表 (如: city_data_buildings, roads等)
```

### 3.2 关联字段说明
```sql
-- 产品表
CREATE TABLE oge_vector_data_product (
    id SERIAL PRIMARY KEY,           -- 产品ID
    name VARCHAR(255),               -- 产品名称
    table_name VARCHAR(255),         -- 存储表名
    geometry_type VARCHAR(50),       -- 几何类型
    feature_count INTEGER            -- 要素数量
);

-- 事实表
CREATE TABLE oge_vector_fact (
    id SERIAL PRIMARY KEY,
    product_key INTEGER,             -- 关联产品表ID
    table_name VARCHAR(255),         -- 存储表名
    fact_data_ids TEXT               -- 数据ID列表
);

-- 具体数据表
CREATE TABLE city_data_buildings (
    id SERIAL PRIMARY KEY,           -- 要素ID
    geom geometry(POLYGON, 4326),    -- 几何数据
    name TEXT,                       -- 属性字段
    height DOUBLE PRECISION
);
```

## 4. GDB多图层处理详解

### 4.1 示例：城市数据GDB
```
输入文件: city_data.gdb
包含图层: buildings, roads, boundaries, parks

输出表:
1. city_data_buildings
2. city_data_roads  
3. city_data_boundaries
4. city_data_parks
```

### 4.2 产品表记录
```sql
-- 每个图层在产品表中有一条记录
INSERT INTO oge_vector_data_product VALUES
(1, '城市建筑物', 'vector', 'POLYGON', 1000, 'city_data_buildings', 'city_data.gdb'),
(2, '城市道路', 'vector', 'LINESTRING', 500, 'city_data_roads', 'city_data.gdb'),
(3, '城市边界', 'vector', 'POLYGON', 10, 'city_data_boundaries', 'city_data.gdb'),
(4, '城市公园', 'vector', 'POLYGON', 50, 'city_data_parks', 'city_data.gdb');
```

### 4.3 事实表记录
```sql
-- 每个图层在事实表中有一条记录
INSERT INTO oge_vector_fact VALUES
(1, 1, 'city_data_buildings', '1,2,3,...,1000'),
(2, 2, 'city_data_roads', '1,2,3,...,500'),
(3, 3, 'city_data_boundaries', '1,2,3,...,10'),
(4, 4, 'city_data_parks', '1,2,3,...,50');
```

## 5. 查询关联示例

### 5.1 查询某个GDB的所有图层
```sql
-- 查询city_data.gdb的所有图层
SELECT 
    p.name as layer_name,
    p.geometry_type,
    p.feature_count,
    p.table_name
FROM oge_vector_data_product p
WHERE p.storage_path = 'city_data.gdb'
ORDER BY p.name;
```

### 5.2 查询某个GDB的所有数据
```sql
-- 查询city_data.gdb的所有建筑物
SELECT * FROM city_data_buildings;

-- 查询city_data.gdb的所有道路
SELECT * FROM city_data_roads;

-- 查询city_data.gdb的所有边界
SELECT * FROM city_data_boundaries;
```

### 5.3 跨表空间查询
```sql
-- 查询某个区域内的所有要素（跨表查询）
WITH area AS (
    SELECT ST_GeomFromText('POLYGON((...))', 4326) as geom
)
SELECT 'buildings' as layer, id, geom FROM city_data_buildings, area 
WHERE ST_Intersects(city_data_buildings.geom, area.geom)
UNION ALL
SELECT 'roads' as layer, id, geom FROM city_data_roads, area 
WHERE ST_Intersects(city_data_roads.geom, area.geom)
UNION ALL
SELECT 'parks' as layer, id, geom FROM city_data_parks, area 
WHERE ST_Intersects(city_data_parks.geom, area.geom);
```

## 6. 表数量计算公式

### 6.1 总表数
```
总表数 = 基础表数 + 数据表数
基础表数 = 5 (固定)
数据表数 = Σ(每个文件的表数)
```

### 6.2 每个文件的表数
```
单图层文件: 1个表
多图层GDB: N个表 (N = 图层数)
混合几何类型: M个表 (M = 几何类型数)
```

### 6.3 示例计算
```
文件列表:
- roads.shp (单图层) → 1个表
- city_data.gdb (4个图层) → 4个表  
- mixed.geojson (3种几何类型) → 3个表

总表数 = 5 + 1 + 4 + 3 = 13个表
```

## 7. 关联关系总结

### 7.1 一对多关系
```
1个GDB文件 → N个图层 → N个数据表
1个产品 → 1个事实记录 → 1个数据表
```

### 7.2 查询路径
```
通过产品表 → 找到所有相关表
通过事实表 → 定位具体存储位置
通过数据表 → 获取实际数据
```

### 7.3 管理优势
```
- 统一管理：通过产品表管理所有数据
- 灵活存储：每个图层独立存储
- 高效查询：直接访问具体表
- 便于维护：表结构完全匹配数据特征
```

## 8. 实际应用示例

### 8.1 入库流程
```python
# 处理city_data.gdb
gdb_path = "city_data.gdb"
layers = fiona.listlayers(gdb_path)

for layer in layers:
    # 1. 创建数据表
    table_name = f"city_data_{layer}"
    create_table(table_name, layer_data)
    
    # 2. 注册产品
    product_id = register_product(table_name, gdb_path, layer)
    
    # 3. 创建事实记录
    create_fact_record(product_id, table_name)
```

### 8.2 查询流程
```python
# 查询city_data.gdb的所有数据
def query_gdb_data(gdb_path):
    # 1. 获取所有相关表
    tables = get_tables_by_gdb(gdb_path)
    
    # 2. 查询每个表
    results = {}
    for table in tables:
        results[table] = query_table(table)
    
    return results
```

这样的设计确保了：
- **清晰的数量关系**：每个文件生成确定数量的表
- **明确的关联关系**：通过产品表和事实表管理所有表
- **高效的查询性能**：直接访问具体数据表
- **灵活的管理方式**：支持复杂的多图层和多几何类型数据 