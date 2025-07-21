# 矢量数据存储设计详解

## 1. 是否需要关联表？

### 当前项目的设计模式

从项目代码可以看出，当前采用**三层架构**：

```
产品表 (oge_vector_data_product) 
    ↓ (product_key)
事实表 (oge_vector_fact) 
    ↓ (table_name)
存储表 (shp_chengzhenkaifa, nature_reserve_data等)
```

### 关联表的必要性

**是的，需要关联表**，原因如下：

1. **统一管理**：通过产品表统一管理所有矢量数据产品
2. **灵活存储**：每个数据集可以存储在不同的表中
3. **元数据管理**：集中管理产品元数据
4. **查询便利**：通过关联表快速定位数据位置

## 2. 每个矢量数据入库时创建表的策略

### 方案一：每个数据集一个表（当前项目采用）

```sql
-- 示例：每个数据集独立表
CREATE TABLE shp_chengzhenkaifa (
    id SERIAL PRIMARY KEY,
    geom geometry(MULTIPOLYGON, 4490),
    objectid_1 numeric,
    bsm varchar(18),
    -- ... 其他属性字段
);

CREATE TABLE nature_reserve_data (
    id SERIAL PRIMARY KEY,
    geometry geometry(GEOMETRY, 4326),
    properties jsonb,
    metadata_id integer
);
```

**优点：**
- 表结构完全匹配数据特征
- 查询性能好（字段类型明确）
- 便于数据维护

**缺点：**
- 表数量会快速增长
- 管理复杂

### 方案二：统一表结构（推荐）

```sql
-- 统一的矢量数据表
CREATE TABLE vector_features (
    id SERIAL PRIMARY KEY,
    product_id INTEGER,           -- 关联产品表
    geometry_type VARCHAR(50),    -- 几何类型
    geometry GEOMETRY(GEOMETRY, 4326),
    properties JSONB,             -- 属性数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**优点：**
- 表结构统一，管理简单
- 支持混合几何类型
- 便于全局查询

**缺点：**
- 查询性能可能略低
- 需要额外的几何类型字段

## 3. 几何类型处理策略

### PostGIS几何字段的几何类型检测

**是的，geom字段能看出几何类型**，PostGIS提供了多种方法：

```sql
-- 方法1：使用ST_GeometryType()
SELECT ST_GeometryType(geometry) FROM vector_data;

-- 方法2：使用ST_Dimension()
SELECT ST_Dimension(geometry) FROM vector_data;

-- 方法3：使用PostGIS内置函数
SELECT 
    CASE 
        WHEN ST_GeometryType(geometry) = 'ST_Point' THEN 'POINT'
        WHEN ST_GeometryType(geometry) = 'ST_LineString' THEN 'LINESTRING'
        WHEN ST_GeometryType(geometry) = 'ST_Polygon' THEN 'POLYGON'
        WHEN ST_GeometryType(geometry) = 'ST_MultiPoint' THEN 'MULTIPOINT'
        WHEN ST_GeometryType(geometry) = 'ST_MultiLineString' THEN 'MULTILINESTRING'
        WHEN ST_GeometryType(geometry) = 'ST_MultiPolygon' THEN 'MULTIPOLYGON'
        ELSE 'GEOMETRYCOLLECTION'
    END as geometry_type
FROM vector_data;
```

### 混合几何类型的处理

#### 方案一：统一存储（推荐）

```sql
-- 使用GEOMETRY类型存储所有几何类型
CREATE TABLE vector_features (
    id SERIAL PRIMARY KEY,
    geometry GEOMETRY(GEOMETRY, 4326),  -- 支持所有几何类型
    geometry_type VARCHAR(50),          -- 显式记录几何类型
    properties JSONB
);

-- 创建几何类型索引
CREATE INDEX idx_geometry_type ON vector_features(geometry_type);
CREATE INDEX idx_geometry_spatial ON vector_features USING GIST(geometry);
```

#### 方案二：按几何类型分表

```sql
-- 点要素表
CREATE TABLE vector_points (
    id SERIAL PRIMARY KEY,
    geometry GEOMETRY(POINT, 4326),
    properties JSONB
);

-- 线要素表
CREATE TABLE vector_lines (
    id SERIAL PRIMARY KEY,
    geometry GEOMETRY(LINESTRING, 4326),
    properties JSONB
);

-- 面要素表
CREATE TABLE vector_polygons (
    id SERIAL PRIMARY KEY,
    geometry GEOMETRY(POLYGON, 4326),
    properties JSONB
);
```

## 4. 不同要素属性数据的存储

### 方案一：JSONB存储（当前项目采用）

```sql
-- 使用JSONB存储所有属性
CREATE TABLE vector_features (
    id SERIAL PRIMARY KEY,
    geometry GEOMETRY(GEOMETRY, 4326),
    properties JSONB,  -- 存储所有属性
    product_id INTEGER
);

-- 查询示例
SELECT 
    id,
    properties->>'name' as name,
    properties->>'area' as area,
    properties->>'type' as type
FROM vector_features 
WHERE properties->>'type' = 'building';
```

**优点：**
- 灵活性高，支持任意属性结构
- 支持复杂嵌套数据
- 便于扩展

**缺点：**
- 查询性能相对较低
- 需要额外的JSONB索引

### 方案二：混合存储

```sql
-- 常用属性用固定字段，其他用JSONB
CREATE TABLE vector_features (
    id SERIAL PRIMARY KEY,
    geometry GEOMETRY(GEOMETRY, 4326),
    name VARCHAR(255),           -- 常用字段
    type VARCHAR(50),            -- 常用字段
    area NUMERIC,                -- 常用字段
    properties JSONB,            -- 其他属性
    product_id INTEGER
);
```

## 5. 关联关系设计

### 完整的关联关系

```sql
-- 1. 产品表
CREATE TABLE oge_vector_data_product (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    product_type VARCHAR(30) DEFAULT 'vector',
    geometry_type VARCHAR(50),
    feature_count INTEGER,
    -- ... 其他字段
);

-- 2. 事实表（关联表）
CREATE TABLE oge_vector_fact (
    id SERIAL PRIMARY KEY,
    product_key INTEGER REFERENCES oge_vector_data_product(id),
    table_name VARCHAR(255),     -- 存储表名
    fact_data_ids TEXT,          -- 数据ID列表
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 存储表（实际数据）
CREATE TABLE vector_features (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES oge_vector_data_product(id),
    geometry GEOMETRY(GEOMETRY, 4326),
    geometry_type VARCHAR(50),
    properties JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 查询关联示例

```sql
-- 通过产品查询数据
SELECT 
    p.name as product_name,
    p.geometry_type,
    vf.geometry,
    vf.properties
FROM oge_vector_data_product p
JOIN vector_features vf ON p.id = vf.product_id
WHERE p.name = '山东省城镇开发边界';

-- 通过几何类型查询
SELECT 
    p.name,
    COUNT(*) as feature_count
FROM oge_vector_data_product p
JOIN vector_features vf ON p.id = vf.product_id
WHERE vf.geometry_type = 'POLYGON'
GROUP BY p.name;

-- 空间查询
SELECT 
    p.name,
    vf.properties->>'name' as feature_name
FROM oge_vector_data_product p
JOIN vector_features vf ON p.id = vf.product_id
WHERE ST_Intersects(vf.geometry, ST_GeomFromText('POLYGON((...))', 4326));
```

## 6. 推荐的设计方案

### 方案A：统一表 + JSONB（推荐）

```sql
-- 产品表
CREATE TABLE vector_products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    data_category VARCHAR(50),
    geometry_type VARCHAR(50),
    feature_count INTEGER DEFAULT 0,
    attribute_schema JSONB,
    spatial_extent GEOMETRY(POLYGON, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 要素表
CREATE TABLE vector_features (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES vector_products(id),
    geometry GEOMETRY(GEOMETRY, 4326),
    geometry_type VARCHAR(50),
    properties JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_vector_features_product ON vector_features(product_id);
CREATE INDEX idx_vector_features_geometry ON vector_features USING GIST(geometry);
CREATE INDEX idx_vector_features_geometry_type ON vector_features(geometry_type);
CREATE INDEX idx_vector_features_properties ON vector_features USING GIN(properties);
```

### 方案B：按几何类型分表

```sql
-- 点要素表
CREATE TABLE vector_points (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES vector_products(id),
    geometry GEOMETRY(POINT, 4326),
    properties JSONB
);

-- 线要素表
CREATE TABLE vector_lines (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES vector_products(id),
    geometry GEOMETRY(LINESTRING, 4326),
    properties JSONB
);

-- 面要素表
CREATE TABLE vector_polygons (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES vector_products(id),
    geometry GEOMETRY(POLYGON, 4326),
    properties JSONB
);
```

## 7. 实施建议

1. **选择方案A**：统一表结构，便于管理和查询
2. **使用JSONB**：存储属性数据，保持灵活性
3. **建立索引**：空间索引和属性索引都要建立
4. **产品表管理**：通过产品表统一管理所有数据集
5. **版本控制**：考虑数据版本管理需求

这样的设计既保持了灵活性，又便于统一管理和查询。 