# 矢量数据入库系统表关系图

## 表关系概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        oge_data_resource_product                            │
│                           (产品元数据表)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK: id (SERIAL)                                                             │
│ name (VARCHAR(255)) - 产品名称                                              │
│ product_type (VARCHAR(30)) - 产品类型 (vector/raster/image)                │
│ owner (VARCHAR(32)) - 所有者                                                │
│ registertime (TIMESTAMP) - 注册时间                                         │
│ updatetime (TIMESTAMP) - 更新时间                                           │
│ status (INTEGER) - 状态                                                     │
│ is_publish (BOOLEAN) - 是否发布                                             │
│ lower_right_lat (FLOAT8) - 右下角纬度                                       │
│ lower_right_long (FLOAT8) - 右下角经度                                      │
│ upper_left_lat (FLOAT8) - 左上角纬度                                        │
│ upper_left_long (FLOAT8) - 左上角经度                                       │
│ ... (其他通用字段)                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ 1:N
                                        │ (一个产品可以有多个矢量数据表)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           oge_vector_fact                                   │
│                          (矢量数据索引表)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK: id (SERIAL)                                                             │
│ FK: product_id (INTEGER) → oge_data_resource_product.id                     │
│ table_name (VARCHAR(255)) - 数据表名                                        │
│ layer_name (VARCHAR(100)) - 图层名称                                        │
│ geometry_type (VARCHAR(50)) - 几何类型                                      │
│ feature_count (INTEGER) - 要素数量                                          │
│ attribute_count (INTEGER) - 属性字段数量                                    │
│ bbox_minx, bbox_miny, bbox_maxx, bbox_maxy (FLOAT8) - 边界框                │
│ source_crs, target_crs (VARCHAR(100)) - 坐标系                              │
│ file_format (VARCHAR(30)) - 文件格式                                        │
│ storage_path (TEXT) - 存储路径                                              │
│ table_create_time (TIMESTAMP) - 表创建时间                                  │
│ table_uuid (VARCHAR(10)) - 表UUID                                           │
│ attribute_schema (JSONB) - 属性字段结构                                     │
│ quality_metrics (JSONB) - 数据质量指标                                      │
│ processing_info (JSONB) - 处理信息                                          │
│ created_at, updated_at (TIMESTAMP) - 创建/更新时间                          │
│ status (INTEGER) - 状态                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ 1:1
                                        │ (一个事实记录对应一个数据表)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    {timestamp}_{filename}_{layer}_{uuid}                    │
│                          (动态矢量数据表)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ PK: id (SERIAL)                                                             │
│ geom (geometry) - 几何数据                                                  │
│ created_at (TIMESTAMP) - 创建时间                                           │
│ updated_at (TIMESTAMP) - 更新时间                                           │
│ ... (动态属性字段)                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 关系说明

### 1. oge_data_resource_product ↔ oge_vector_fact
- **关系类型**: 一对多 (1:N)
- **外键**: `oge_vector_fact.product_id` → `oge_data_resource_product.id`
- **说明**: 一个产品可以有多个矢量数据表
- **示例**: 
  - 产品 "city_data.gdb" → 3个表 (buildings, roads, boundaries)
  - 产品 "mixed.geojson" → 3个表 (point, linestring, polygon)

### 2. oge_vector_fact ↔ 动态数据表
- **关系类型**: 一对一 (1:1)
- **关联字段**: `oge_vector_fact.table_name` = 动态表名
- **说明**: 一个事实记录对应一个实际的数据表
- **示例**: 
  - 事实记录: `20240101_143022_roads_a1b2c3`
  - 数据表: `20240101_143022_roads_a1b2c3`

## 数据流向

```
数据文件 → 产品表 → 事实表 → 数据表
   ↓         ↓        ↓        ↓
roads.shp → 产品记录 → 事实记录 → 实际数据
```

## 查询示例

### 1. 查询产品的所有数据表
```sql
SELECT 
    p.name as product_name,
    f.table_name,
    f.layer_name,
    f.geometry_type,
    f.feature_count
FROM oge_data_resource_product p
JOIN oge_vector_fact f ON p.id = f.product_id
WHERE p.name = 'city_data';
```

### 2. 查询特定表的数据
```sql
-- 先查询表名
SELECT f.table_name 
FROM oge_vector_fact f
JOIN oge_data_resource_product p ON f.product_id = p.id
WHERE p.name = 'roads' AND f.layer_name = 'main_roads';

-- 再查询实际数据
SELECT * FROM 20240101_143022_roads_a1b2c3 
WHERE ST_Intersects(geom, ST_GeomFromText('POLYGON(...)', 4326));
```

### 3. 跨表查询同一产品的数据
```sql
-- 查询city_data产品的所有图层数据
WITH product_tables AS (
    SELECT f.table_name, f.layer_name
    FROM oge_vector_fact f
    JOIN oge_data_resource_product p ON f.product_id = p.id
    WHERE p.name = 'city_data'
)
SELECT 
    pt.layer_name,
    CASE pt.layer_name
        WHEN 'buildings' THEN (SELECT COUNT(*) FROM 20240101_143022_city_data_buildings_a1b2c3)
        WHEN 'roads' THEN (SELECT COUNT(*) FROM 20240101_143022_city_data_roads_a1b2c3)
        WHEN 'boundaries' THEN (SELECT COUNT(*) FROM 20240101_143022_city_data_boundaries_a1b2c3)
    END as feature_count
FROM product_tables pt;
```

## 索引设计

### 1. 产品表索引
```sql
CREATE INDEX idx_product_name ON oge_data_resource_product(name);
CREATE INDEX idx_product_type ON oge_data_resource_product(product_type);
CREATE INDEX idx_product_registertime ON oge_data_resource_product(registertime);
```

### 2. 事实表索引
```sql
CREATE INDEX idx_fact_product_id ON oge_vector_fact(product_id);
CREATE INDEX idx_fact_table_name ON oge_vector_fact(table_name);
CREATE INDEX idx_fact_geometry_type ON oge_vector_fact(geometry_type);
CREATE INDEX idx_fact_spatial ON oge_vector_fact USING GIST(spatial_extent);
CREATE INDEX idx_fact_attribute_schema ON oge_vector_fact USING GIN(attribute_schema);
CREATE INDEX idx_fact_quality_metrics ON oge_vector_fact USING GIN(quality_metrics);
```

### 3. 动态表索引
```sql
-- 每个动态表都会自动创建
CREATE INDEX idx_{table_name}_geom ON {table_name} USING GIST(geom);
CREATE INDEX idx_{table_name}_created ON {table_name}(created_at);
```

## 数据完整性约束

### 1. 外键约束
```sql
ALTER TABLE oge_vector_fact 
ADD CONSTRAINT fk_fact_product 
FOREIGN KEY (product_id) REFERENCES oge_data_resource_product(id);
```

### 2. 唯一约束
```sql
ALTER TABLE oge_data_resource_product 
ADD CONSTRAINT uk_product_name_time 
UNIQUE (name, registertime);

ALTER TABLE oge_vector_fact 
ADD CONSTRAINT uk_fact_table_name 
UNIQUE (table_name);
```

### 3. 检查约束
```sql
ALTER TABLE oge_data_resource_product 
ADD CONSTRAINT chk_product_type 
CHECK (product_type IN ('vector', 'raster', 'image'));

ALTER TABLE oge_vector_fact 
ADD CONSTRAINT chk_geometry_type 
CHECK (geometry_type IN ('POINT', 'LINESTRING', 'POLYGON', 'MULTIPOINT', 'MULTILINESTRING', 'MULTIPOLYGON', 'GEOMETRY'));
```

这个设计确保了数据的完整性、查询的效率和系统的可扩展性。 