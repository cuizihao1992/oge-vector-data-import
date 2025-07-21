# 矢量数据入库完整指南

## 1. 入库处理流程

### 1.1 整体流程
```
数据文件 → 文件分析 → 表名生成 → 表结构创建 → 数据入库 → 索引创建 → 产品注册
```

### 1.2 详细步骤

| 步骤 | 操作 | 说明 | 是否必需 |
|------|------|------|----------|
| 1 | 文件验证 | 检查文件格式是否支持，文件是否存在 | 必需 |
| 2 | 文件分析 | 分析几何类型、字段结构、要素数量等 | 必需 |
| 3 | 表名生成 | 根据文件和时间戳生成唯一表名 | 必需 |
| 4 | 表结构创建 | 根据数据特征创建PostgreSQL表 | 必需 |
| 5 | 坐标系转换 | 统一转换到WGS84坐标系 | 可选 |
| 6 | 数据入库 | 批量插入矢量数据 | 必需 |
| 7 | 索引创建 | 创建空间索引和属性索引 | 必需 |
| 8 | 产品注册 | 在产品表中注册元数据信息 | 必需 |

## 2. 表名生成规则

### 2.1 命名格式
**时间戳 + 文件名 + 图层名 + UUID**

| 组件 | 格式 | 示例 | 说明 |
|------|------|------|------|
| 时间戳 | YYYYMMDD_HHMMSS | 20240101_143022 | 精确到秒 |
| 文件名 | 原文件名（不含扩展名） | city_data | 小写，替换特殊字符 |
| 图层名 | 图层名称 | buildings | 仅多图层文件需要 |
| UUID | 6位随机字符 | a1b2c3 | 同一数据集使用相同UUID |

### 2.2 命名示例

| 输入文件 | 时间 | 输出表名 | 说明 |
|----------|------|----------|------|
| roads.shp | 2024-01-01 14:30:22 | 20240101_143022_roads_a1b2c3 | 单文件 |
| city_data.gdb (buildings层) | 2024-01-01 14:30:22 | 20240101_143022_city_data_buildings_a1b2c3 | GDB多图层，相同UUID |
| city_data.gdb (roads层) | 2024-01-01 14:30:22 | 20240101_143022_city_data_roads_a1b2c3 | GDB多图层，相同UUID |
| mixed.geojson (点要素) | 2024-01-01 14:30:22 | 20240101_143022_mixed_point_a1b2c3 | 混合几何类型，相同UUID |
| mixed.geojson (线要素) | 2024-01-01 14:30:22 | 20240101_143022_mixed_linestring_a1b2c3 | 混合几何类型，相同UUID |

## 3. 不同格式处理策略

### 3.1 单文件格式

| 格式 | 处理方式 | 生成表数 | 示例 |
|------|----------|----------|------|
| Shapefile (.shp) | 直接处理 | 1个 | roads.shp → 20240101_143022_roads_a1b2c3 |
| GeoJSON (.geojson) | 按几何类型分表 | 1-多个 | mixed.geojson → 3个表（点、线、面） |
| KML (.kml) | 直接处理 | 1个 | places.kml → 20240101_143022_places_a1b2c3 |

### 3.2 多图层格式

| 格式 | 处理方式 | 生成表数 | 示例 |
|------|----------|----------|------|
| GDB (.gdb) | 每个图层一个表 | N个（N=图层数） | city_data.gdb → 4个表 |
| GPKG (.gpkg) | 每个图层一个表 | N个（N=图层数） | data.gpkg → 3个表 |
| MDB (.mdb) | 每个图层一个表 | N个（N=图层数） | data.mdb → 3个表 |

## 4. 特殊情况处理

### 4.1 多图层文件处理

| 情况 | 处理方式 | 表名示例 | 说明 |
|------|----------|----------|------|
| 单图层GDB/GPKG | 正常处理 | 20240101_143022_data_a1b2c3 | 等同于单文件 |
| 多图层GDB | 按图层分表 | 20240101_143022_data_buildings_a1b2c3<br>20240101_143022_data_roads_a1b2c3<br>20240101_143022_data_boundaries_a1b2c3 | 同一数据集使用相同UUID |
| 多图层GPKG | 按图层分表 | 20240101_143022_data_buildings_a1b2c3<br>20240101_143022_data_roads_a1b2c3<br>20240101_143022_data_pois_a1b2c3 | 同一数据集使用相同UUID |

### 4.2 GeoJSON混合几何类型

| 情况 | 处理方式 | 表名示例 | 说明 |
|------|----------|----------|------|
| 单一几何类型 | 正常处理 | 20240101_143022_mixed_a1b2c3 | 直接入库 |
| 混合几何类型 | 按类型分表 | 20240101_143022_mixed_point_a1b2c3<br>20240101_143022_mixed_linestring_a1b2c3<br>20240101_143022_mixed_polygon_a1b2c3 | 同一数据集使用相同UUID |

### 4.3 文件同名处理

| 情况 | 处理方式 | 表名示例 | 说明 |
|------|----------|----------|------|
| 首次入库 | 正常命名 | 20240101_143022_roads_a1b2c3 | 无冲突 |
| 重复入库 | 时间戳区分 | 20240115_091545_roads_d4e5f6 | 自动避免冲突 |

### 4.4 UUID生成策略

| 场景 | UUID生成方式 | 示例 | 说明 |
|------|-------------|------|------|
| 单文件 | 随机生成 | roads.shp → a1b2c3 | 每个文件独立UUID |
| 多图层文件 | 文件级别生成 | city_data.gdb → a1b2c3 | 同一文件的所有图层使用相同UUID |
| 混合几何类型 | 文件级别生成 | mixed.geojson → a1b2c3 | 同一文件的所有几何类型使用相同UUID |

**UUID生成规则：**
- 在文件处理开始时生成一个UUID
- 同一文件的所有图层/几何类型共享这个UUID
- 不同文件使用不同的UUID
- 确保同一数据集的所有表可以通过UUID关联

### 4.5 字段名冲突处理

| 冲突类型 | 处理方式 | 示例 | 说明 |
|----------|----------|------|------|
| PostgreSQL保留字 | 添加后缀 | order → order_col | 避免SQL冲突 |
| 特殊字符 | 替换为下划线 | user-name → user_name | 符合命名规范 |
| 中文字段名 | 保持原样 | 名称 → 名称 | 支持UTF-8 |

### 4.6 坐标系转换处理

| 情况 | 处理方式 | 说明 | 示例 |
|------|----------|------|------|
| 已经是WGS84 | 跳过转换 | 直接使用原始坐标系 | EPSG:4326 → 不转换 |
| 坐标系信息缺失 | 跳过转换 | 使用原始坐标系，记录警告 | 无坐标系信息 → 跳过转换 |
| 转换失败 | 跳过转换 | 使用原始坐标系，记录错误 | EPSG:4490转换失败 → 跳过转换 |
| 转换成功 | 执行转换 | 统一转换为WGS84 | EPSG:4490 → EPSG:4326 |
| 用户指定跳过 | 跳过转换 | 按用户配置处理 | 配置skip_crs_transform=true |

**坐标系转换策略：**
- 优先尝试转换到WGS84（EPSG:4326）
- 转换失败时自动跳过，使用原始坐标系
- 在元数据中记录源坐标系和目标坐标系信息
- 支持用户配置是否强制转换

## 5. 数据库表设计说明

### 5.1 涉及的表结构概览

本系统涉及以下核心表：

| 表名 | 用途 | 表类型 | 说明 |
|------|------|--------|------|
| oge_data_resource_product | 产品元数据表 | 固定表 | 存储所有数据产品的元数据信息（矢量和栅格通用） |
| oge_vector_fact | 矢量数据索引表 | 固定表 | 矢量数据的事实表和索引信息 |
| {timestamp}_{filename}_{layer}_{uuid} | 矢量数据表 | 动态表 | 存储实际的矢量几何和属性数据 |

**产品表设计说明：**
- **统一表设计**：矢量和栅格产品使用同一个表，便于统一管理
- **字段复用**：通用字段（如name, product_type, owner等）两种数据类型都使用
- **专用字段**：栅格专用字段（如dtype, sensor_key, resolution等）矢量数据不使用
- **空间字段**：使用统一的边界框字段（lower_right_lat等）表示空间范围
- **扩展性**：支持未来添加新的数据类型（如三维数据、时序数据等）

**矢量数据元数据存储策略：**
- **核心元数据**：存储在 `oge_data_resource_product` 表中（产品级别信息）
- **矢量专用元数据**：存储在 `oge_vector_fact` 表中（图层级别信息）
- **扩展元数据**：存储在 `oge_vector_fact` 表的JSONB字段中（灵活扩展）
- **数据完整性**：通过外键关联保证数据一致性

### 5.2 固定表详细设计

#### 5.2.1 oge_data_resource_product（产品元数据表）

| 字段名 | 数据类型 | 约束 | 说明 | 示例 |
|--------|----------|------|------|------|
| id | SERIAL | PRIMARY KEY | 产品ID，自增主键 | 1, 2, 3... |
| name | VARCHAR(255) | NOT NULL | 产品名称 | roads, city_data_buildings |
| product_type | VARCHAR(30) | NOT NULL | 产品类型 | vector, raster, image |
| dtype | VARCHAR(30) | NULL | 数据类型 | int8, uint8, float32（栅格专用） |
| sensor_key | INTEGER | DEFAULT 0 | 传感器ID | 1, 2, 3（栅格专用） |
| owner | VARCHAR(32) | NULL | 所有者 | admin, user1 |
| registertime | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 注册时间 | 2024-01-01 14:30:25 |
| updatetime | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 | 2024-01-01 14:30:25 |
| label | TEXT | NULL | 标签 | 道路数据, 建筑物数据 |
| labelid | INTEGER | NULL | 分类ID | 1, 2, 3 |
| description | TEXT | NULL | 描述信息 | 详细描述 |
| dbid | INTEGER | NOT NULL DEFAULT 0 | 数据库连接ID | 1, 2, 3 |
| subject | TEXT | NULL | 主题 | 基础地理, 专题数据 |
| alias | TEXT | NULL | 别名 | 道路网络, 建筑轮廓 |
| land_cover_adapt | INTEGER | NULL | 地表覆盖适应等级 | 1, 2, 3（栅格专用） |
| data_size | VARCHAR(30) | NULL | 数据大小 | 1GB, 500MB |
| image_amount | VARCHAR(30) | NULL | 影像数量 | 100张, 50张（栅格专用） |
| start_time | TEXT | NULL | 开始时间 | 2024-01-01 |
| end_time | TEXT | NULL | 结束时间 | 2024-12-31 |
| cover_area | VARCHAR(255) | NULL | 覆盖区域 | 山东省, 济南市 |
| resolution | VARCHAR(30) | NULL | 分辨率 | 0.5m, 1m（栅格专用） |
| status | INTEGER | DEFAULT 1 | 状态 | 1（启用）, 0（禁用） |
| sample_code | TEXT | NULL | 样例代码 | 示例代码 |
| is_publish | BOOLEAN | DEFAULT false | 是否发布 | true, false |
| description_en | TEXT | NULL | 英文描述 | English description |
| alias_en | TEXT | NULL | 英文别名 | Road network |
| label_en | TEXT | NULL | 英文标签 | Road data |
| image_amount_en | VARCHAR(30) | NULL | 英文影像数量 | 100 images |
| cover_area_en | TEXT | NULL | 英文覆盖区域 | Shandong Province |
| source_type | INTEGER | NULL | 数据类型 | 0-参数, 1-波段, 2-无 |
| param | TEXT | NULL | 参数/波段信息 | 参数信息（栅格专用） |
| themekeywords | TEXT | NULL | 主题关键词 | 道路, 交通, 基础设施 |
| themekeywords_en | TEXT | NULL | 英文主题关键词 | road, traffic, infrastructure |
| tag_ids | VARCHAR(255) | NULL | 标签ID数组 | 1,2,3 |
| sensor_sort | INTEGER | NULL | 传感器排序 | 1, 2, 3（栅格专用） |
| detail_meta | VARCHAR(255) | NULL | 详细元数据 | 元数据信息 |
| map_url | VARCHAR(255) | NULL | 地图服务地址 | http://... |
| lower_right_lat | FLOAT8 | NULL | 右下角纬度 | 39.0 |
| lower_right_long | FLOAT8 | NULL | 右下角经度 | 117.0 |
| upper_left_lat | FLOAT8 | NULL | 左上角纬度 | 40.0 |
| upper_left_long | FLOAT8 | NULL | 左上角经度 | 116.0 |

#### 5.2.2 oge_vector_fact（矢量数据索引表）

| 字段名 | 数据类型 | 约束 | 说明 | 示例 |
|--------|----------|------|------|------|
| id | SERIAL | PRIMARY KEY | 索引ID，自增主键 | 1, 2, 3... |
| product_id | INTEGER | NOT NULL, FOREIGN KEY | 关联产品ID | 1, 2, 3... |
| table_name | VARCHAR(255) | NOT NULL | 数据表名 | 20240101_143022_roads_a1b2c3 |
| layer_name | VARCHAR(100) | NULL | 图层名称 | buildings, roads, boundaries |
| geometry_type | VARCHAR(50) | NOT NULL | 几何类型 | POINT, LINESTRING, POLYGON |
| feature_count | INTEGER | NOT NULL | 要素数量 | 1000, 500, 100 |
| attribute_count | INTEGER | NULL | 属性字段数量 | 5, 10, 15 |
| spatial_extent | geometry(POLYGON, 4326) | NULL | 空间范围 | 边界多边形 |
| bbox_minx | FLOAT8 | NOT NULL | 边界框最小X | 116.0 |
| bbox_miny | FLOAT8 | NOT NULL | 边界框最小Y | 39.0 |
| bbox_maxx | FLOAT8 | NOT NULL | 边界框最大X | 117.0 |
| bbox_maxy | FLOAT8 | NOT NULL | 边界框最大Y | 40.0 |
| source_crs | VARCHAR(100) | NULL | 源坐标系 | EPSG:4490, EPSG:4326 |
| target_crs | VARCHAR(100) | NOT NULL | 目标坐标系 | EPSG:4326 |
| crs_authority | VARCHAR(50) | NULL | 坐标系权威机构 | EPSG, CGCS |
| file_format | VARCHAR(30) | NOT NULL | 文件格式 | shp, geojson, gdb |
| file_size | BIGINT | NULL | 文件大小（字节） | 1024000 |
| file_count | INTEGER | NULL | 文件数量 | 1, 4（shp文件组） |
| storage_path | TEXT | NOT NULL | 存储路径 | /data/roads.shp |
| table_create_time | TIMESTAMP | NOT NULL | 表创建时间 | 2024-01-01 14:30:22 |
| table_uuid | VARCHAR(10) | NOT NULL | 表UUID | a1b2c3 |
| attribute_schema | JSONB | NULL | 属性字段结构 | {"name": "text", "type": "integer"} |
| quality_metrics | JSONB | NULL | 数据质量指标 | {"validity": 0.95, "completeness": 0.98} |
| processing_info | JSONB | NULL | 处理信息 | {"software": "GDAL", "version": "3.4.0"} |

**JSONB字段详细说明：**

1. **attribute_schema（属性字段结构）**
```json
{
  "fields": [
    {"name": "road_name", "type": "text", "description": "道路名称"},
    {"name": "road_type", "type": "integer", "description": "道路类型"},
    {"name": "length", "type": "float", "description": "道路长度"}
  ],
  "total_fields": 3,
  "primary_key": "id"
}
```

2. **quality_metrics（数据质量指标）**
```json
{
  "validity": 0.95,
  "completeness": 0.98,
  "consistency": 0.92,
  "accuracy": 0.90,
  "invalid_features": 50,
  "null_values": 120
}
```

3. **processing_info（处理信息）**
```json
{
  "software": "GDAL",
  "version": "3.4.0",
  "processing_time": "2024-01-01T14:30:25",
  "transformation_applied": true,
  "crs_transformation": "EPSG:4490 -> EPSG:4326",
  "validation_passed": true
}
```
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 | 2024-01-01 14:30:25 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 | 2024-01-01 14:30:25 |
| status | INTEGER | DEFAULT 1 | 状态 | 1（正常）, 0（删除） |



### 5.3 动态表详细设计

#### 5.3.1 矢量数据表（{timestamp}_{filename}_{layer}_{uuid}）

每个矢量数据表都包含以下基础字段：

| 字段名 | 数据类型 | 约束 | 说明 | 示例 |
|--------|----------|------|------|------|
| id | SERIAL | PRIMARY KEY | 自增主键 | 1, 2, 3... |
| geom | geometry | NOT NULL | 几何数据，类型根据数据自动确定 | 见几何类型映射表 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 | 2024-01-01 14:30:25 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 | 2024-01-01 14:30:25 |

**几何类型映射表：**

| 几何类型 | PostGIS类型 | 说明 | 示例表名 |
|----------|-------------|------|----------|
| Point | geometry(POINT, 4326) | 点要素 | 20240101_143022_pois_a1b2c3 |
| LineString | geometry(LINESTRING, 4326) | 线要素 | 20240101_143022_roads_a1b2c3 |
| Polygon | geometry(POLYGON, 4326) | 面要素 | 20240101_143022_buildings_a1b2c3 |
| MultiPoint | geometry(MULTIPOINT, 4326) | 多点要素 | 20240101_143022_points_a1b2c3 |
| MultiLineString | geometry(MULTILINESTRING, 4326) | 多线要素 | 20240101_143022_lines_a1b2c3 |
| MultiPolygon | geometry(MULTIPOLYGON, 4326) | 多面要素 | 20240101_143022_areas_a1b2c3 |
| 混合类型 | geometry(GEOMETRY, 4326) | 支持所有几何类型 | 20240101_143022_mixed_a1b2c3 |

**属性字段映射表：**

| Pandas类型 | PostgreSQL类型 | 说明 | 示例 |
|------------|----------------|------|------|
| object | TEXT | 字符串类型 | 名称, 类型, 描述 |
| int64 | BIGINT | 64位整数 | 面积, 长度, 数量 |
| int32 | INTEGER | 32位整数 | 楼层数, 车道数 |
| float64 | DOUBLE PRECISION | 64位浮点数 | 坐标, 高程 |
| float32 | REAL | 32位浮点数 | 精度, 比例 |
| bool | BOOLEAN | 布尔类型 | 是否启用, 是否可见 |
| datetime64[ns] | TIMESTAMP | 时间戳类型 | 创建时间, 更新时间 |

### 5.4 表关系设计

#### 5.4.1 主键和外键关系

| 关系类型 | 主表 | 主键 | 从表 | 外键 | 说明 |
|----------|------|------|------|------|------|
| 一对多 | oge_data_resource_product | id | oge_vector_fact | product_id | 一个产品可以有多个矢量数据表 |
| 一对一 | oge_vector_fact | table_name | 动态表 | 表名 | 事实表与数据表的一一对应 |

#### 5.4.2 索引设计

| 表名 | 索引名 | 索引类型 | 字段 | 说明 |
|------|--------|----------|------|------|
| oge_data_resource_product | idx_product_name | B-tree | name | 产品名称查询 |
| oge_data_resource_product | idx_product_type | B-tree | product_type | 产品类型查询 |
| oge_data_resource_product | idx_product_registertime | B-tree | registertime | 注册时间查询 |
| oge_vector_fact | idx_fact_product_id | B-tree | product_id | 产品关联查询 |
| oge_vector_fact | idx_fact_table_name | B-tree | table_name | 表名查询 |
| oge_vector_fact | idx_fact_geometry_type | B-tree | geometry_type | 几何类型查询 |
| oge_vector_fact | idx_fact_spatial | GIST | spatial_extent | 空间范围查询 |
| 动态表 | idx_{table_name}_geom | GIST | geom | 空间索引 |
| 动态表 | idx_{table_name}_created | B-tree | created_at | 时间索引 |

### 5.5 数据完整性约束

#### 5.5.1 检查约束

| 表名 | 约束名 | 约束条件 | 说明 |
|------|--------|----------|------|
| oge_data_resource_product | chk_product_type | product_type IN ('vector', 'raster', 'image') | 产品类型限制 |
| oge_data_resource_product | chk_status | status IN (0, 1) | 状态值限制 |
| oge_data_resource_product | chk_access_level | access_level IN (0, 1, 2) | 访问级别限制 |
| oge_vector_fact | chk_geometry_type | geometry_type IN ('POINT', 'LINESTRING', 'POLYGON', 'MULTIPOINT', 'MULTILINESTRING', 'MULTIPOLYGON', 'GEOMETRY') | 几何类型限制 |
| oge_vector_fact | chk_feature_count | feature_count > 0 | 要素数量必须大于0 |

#### 5.5.2 唯一约束

| 表名 | 约束名 | 字段 | 说明 |
|------|--------|------|------|
| oge_data_resource_product | uk_product_name_time | name, table_create_time | 产品名称和创建时间唯一 |
| oge_vector_fact | uk_fact_table_name | table_name | 表名唯一 |

## 6. 索引策略

### 6.1 自动创建索引

| 索引类型 | 索引名 | 字段 | 说明 |
|----------|--------|------|------|
| 空间索引 | idx_{table_name}_geom | geom | GIST索引，支持空间查询 |
| 主键索引 | {table_name}_pkey | id | 自动创建 |
| 时间索引 | idx_{table_name}_created | created_at | 支持时间查询 |

### 6.2 索引性能

| 查询类型 | 索引支持 | 性能 | 说明 |
|----------|----------|------|------|
| 空间查询 | 空间索引 | 高 | ST_Intersects, ST_Contains等 |
| 属性查询 | 无 | 中 | 全表扫描 |
| 时间查询 | 时间索引 | 高 | 按创建时间查询 |
| 主键查询 | 主键索引 | 高 | 按ID查询 |

## 7. 产品表字段

### 7.1 基础信息字段

| 字段名 | 数据类型 | 说明 | 示例 | 适用类型 |
|--------|----------|------|------|----------|
| id | SERIAL | 产品ID | 1, 2, 3... | 通用 |
| name | VARCHAR(255) | 产品名称 | roads, city_data_buildings | 通用 |
| product_type | VARCHAR(30) | 产品类型 | vector, raster, image | 通用 |
| dtype | VARCHAR(30) | 数据类型 | int8, uint8, float32 | 栅格专用 |
| sensor_key | INTEGER | 传感器ID | 1, 2, 3 | 栅格专用 |
| owner | VARCHAR(32) | 所有者 | admin, user1 | 通用 |
| registertime | TIMESTAMP | 注册时间 | 2024-01-01 14:30:25 | 通用 |
| updatetime | TIMESTAMP | 更新时间 | 2024-01-01 14:30:25 | 通用 |

### 7.2 空间信息字段

| 字段名 | 数据类型 | 说明 | 示例 | 适用类型 |
|--------|----------|------|------|----------|
| lower_right_lat | FLOAT8 | 右下角纬度 | 39.0 | 通用 |
| lower_right_long | FLOAT8 | 右下角经度 | 117.0 | 通用 |
| upper_left_lat | FLOAT8 | 左上角纬度 | 40.0 | 通用 |
| upper_left_long | FLOAT8 | 左上角经度 | 116.0 | 通用 |
| cover_area | VARCHAR(255) | 覆盖区域 | 山东省, 济南市 | 通用 |
| cover_area_en | TEXT | 英文覆盖区域 | Shandong Province | 通用 |

### 7.3 栅格专用字段

| 字段名 | 数据类型 | 说明 | 示例 | 适用类型 |
|--------|----------|------|------|----------|
| resolution | VARCHAR(30) | 分辨率 | 0.5m, 1m | 栅格专用 |
| image_amount | VARCHAR(30) | 影像数量 | 100张, 50张 | 栅格专用 |
| image_amount_en | VARCHAR(30) | 英文影像数量 | 100 images | 栅格专用 |
| land_cover_adapt | INTEGER | 地表覆盖适应等级 | 1, 2, 3 | 栅格专用 |
| param | TEXT | 参数/波段信息 | 参数信息 | 栅格专用 |
| sensor_sort | INTEGER | 传感器排序 | 1, 2, 3 | 栅格专用 |

### 7.4 描述信息字段

| 字段名 | 数据类型 | 说明 | 示例 | 适用类型 |
|--------|----------|------|------|----------|
| label | TEXT | 标签 | 道路数据, 建筑物数据 | 通用 |
| label_en | TEXT | 英文标签 | Road data | 通用 |
| description | TEXT | 描述信息 | 详细描述 | 通用 |
| description_en | TEXT | 英文描述 | English description | 通用 |
| alias | TEXT | 别名 | 道路网络, 建筑轮廓 | 通用 |
| alias_en | TEXT | 英文别名 | Road network | 通用 |
| subject | TEXT | 主题 | 基础地理, 专题数据 | 通用 |
| themekeywords | TEXT | 主题关键词 | 道路, 交通, 基础设施 | 通用 |
| themekeywords_en | TEXT | 英文主题关键词 | road, traffic, infrastructure | 通用 |

### 7.5 时间信息字段

| 字段名 | 数据类型 | 说明 | 示例 | 适用类型 |
|--------|----------|------|------|----------|
| start_time | TEXT | 开始时间 | 2024-01-01 | 通用 |
| end_time | TEXT | 结束时间 | 2024-12-31 | 通用 |

### 7.6 管理信息字段

| 字段名 | 数据类型 | 说明 | 示例 | 适用类型 |
|--------|----------|------|------|----------|
| status | INTEGER | 状态 | 1（启用）, 0（禁用） | 通用 |
| is_publish | BOOLEAN | 是否发布 | true, false | 通用 |
| dbid | INTEGER | 数据库连接ID | 1, 2, 3 | 通用 |
| labelid | INTEGER | 分类ID | 1, 2, 3 | 通用 |
| tag_ids | VARCHAR(255) | 标签ID数组 | 1,2,3 | 通用 |
| source_type | INTEGER | 数据类型 | 0-参数, 1-波段, 2-无 | 通用 |
| sample_code | TEXT | 样例代码 | 示例代码 | 通用 |
| detail_meta | VARCHAR(255) | 详细元数据 | 元数据信息 | 通用 |
| map_url | VARCHAR(255) | 地图服务地址 | http://... | 通用 |

## 8. 查询示例

### 8.1 基础查询

| 查询类型 | SQL示例 | 说明 |
|----------|---------|------|
| 查询所有产品 | SELECT p.name, f.geometry_type, f.feature_count FROM oge_data_resource_product p JOIN oge_vector_fact f ON p.id = f.product_id WHERE p.product_type = 'vector' | 获取所有矢量产品 |
| 查询特定文件 | SELECT p.*, f.table_name, f.geometry_type FROM oge_data_resource_product p JOIN oge_vector_fact f ON p.id = f.product_id WHERE p.name = 'roads' ORDER BY f.table_create_time DESC | 获取文件的所有版本 |
| 查询最新版本 | SELECT f.table_name FROM oge_data_resource_product p JOIN oge_vector_fact f ON p.id = f.product_id WHERE p.name = 'roads' ORDER BY f.table_create_time DESC LIMIT 1 | 获取最新版本表名 |
| 查询属性结构 | SELECT f.attribute_schema FROM oge_vector_fact f WHERE f.table_name = '20240101_143022_roads_a1b2c3' | 获取表的属性字段结构 |
| 查询质量指标 | SELECT f.quality_metrics FROM oge_vector_fact f WHERE f.table_name = '20240101_143022_roads_a1b2c3' | 获取数据质量指标 |

### 8.2 空间查询

| 查询类型 | SQL示例 | 说明 |
|----------|---------|------|
| 空间相交 | SELECT * FROM 20240101_143022_roads_a1b2c3 WHERE ST_Intersects(geom, ST_GeomFromText('POLYGON((...))', 4326)) | 查询与指定区域相交的要素 |
| 空间包含 | SELECT * FROM 20240101_143022_buildings_a1b2c3 WHERE ST_Contains(ST_GeomFromText('POLYGON((...))', 4326), geom) | 查询包含在指定区域内的要素 |
| 距离查询 | SELECT * FROM 20240101_143022_points_a1b2c3 WHERE ST_DWithin(geom, ST_GeomFromText('POINT(116.0 39.0)', 4326), 1000) | 查询距离指定点1000米内的要素 |

### 8.3 跨表查询

| 查询类型 | SQL示例 | 说明 |
|----------|---------|------|
| 查询GDB/GPKG所有图层 | SELECT p.name, f.table_name, f.layer_name, f.feature_count FROM oge_data_resource_product p JOIN oge_vector_fact f ON p.id = f.product_id WHERE p.storage_path = 'city_data.gdb' | 获取多图层文件的所有图层 |
| 跨表空间查询 | WITH area AS (SELECT ST_GeomFromText('POLYGON((...))', 4326) as geom)<br>SELECT 'buildings' as layer, id, geom FROM 20240101_143022_city_data_buildings_a1b2c3, area WHERE ST_Intersects(geom, area.geom)<br>UNION ALL<br>SELECT 'roads' as layer, id, geom FROM 20240101_143022_city_data_roads_d4e5f6, area WHERE ST_Intersects(geom, area.geom) | 查询多个表的空间数据 |

## 9. 性能优化建议

### 9.1 索引优化

| 优化策略 | 说明 | 效果 |
|----------|------|------|
| 空间索引 | 为geom字段创建GIST索引 | 空间查询性能提升10-100倍 |
| 时间索引 | 为created_at字段创建B-tree索引 | 时间查询性能提升5-10倍 |
| 复合索引 | 为常用查询组合创建复合索引 | 复杂查询性能提升2-5倍 |

### 9.2 查询优化

| 优化策略 | 说明 | 效果 |
|----------|------|------|
| 限制查询范围 | 使用WHERE条件限制数据范围 | 减少扫描数据量 |
| 使用空间索引 | 优先使用空间函数进行查询 | 避免全表扫描 |
| 批量操作 | 使用批量插入和更新 | 减少数据库交互次数 |

### 9.3 存储优化

| 优化策略 | 说明 | 效果 |
|----------|------|------|
| 数据类型优化 | 选择合适的数据类型 | 减少存储空间 |
| 压缩存储 | 使用PostgreSQL压缩功能 | 减少存储空间30-50% |
| 分区表 | 按时间或空间分区 | 查询性能提升2-5倍 |

## 10. 错误处理

### 10.1 常见错误及处理

| 错误类型 | 错误描述 | 处理方式 | 预防措施 |
|----------|----------|----------|----------|
| 文件格式不支持 | 无法读取文件格式 | 跳过该文件，记录错误日志 | 预先检查文件格式 |
| 坐标系转换失败 | 坐标系转换出错 | 跳过转换，使用原始坐标系，记录警告 | 验证坐标系信息 |
| 字段名冲突 | 字段名与保留字冲突 | 自动添加后缀 | 预先检查字段名 |
| 内存不足 | 大文件处理时内存溢出 | 分批处理数据 | 设置合理的批处理大小 |
| 数据库连接失败 | 无法连接数据库 | 重试连接，记录错误 | 检查数据库状态 |

### 10.2 日志记录

| 日志级别 | 记录内容 | 示例 |
|----------|----------|------|
| INFO | 正常操作信息 | 文件roads.shp入库成功，生成表20240101_143022_roads_a1b2c3 |
| WARNING | 警告信息 | 坐标系转换警告，使用原始坐标系EPSG:4490 |
| ERROR | 错误信息 | 文件data.gdb读取失败：文件损坏 |
| DEBUG | 调试信息 | 处理第1000条记录，内存使用：50MB |

## 11. 监控和维护

### 11.1 性能监控

| 监控指标 | 监控方式 | 阈值 | 说明 |
|----------|----------|------|------|
| 入库速度 | 记录处理时间 | 1000条/秒 | 每秒处理的要素数量 |
| 内存使用 | 监控内存占用 | 80% | 内存使用率 |
| 磁盘空间 | 监控存储空间 | 90% | 磁盘使用率 |
| 查询响应时间 | 记录查询时间 | 1秒 | 查询响应时间 |

### 11.2 数据质量检查

| 检查项目 | 检查方式 | 标准 | 说明 |
|----------|----------|------|------|
| 几何有效性 | ST_IsValid() | 100%有效 | 检查几何数据是否有效 |
| 属性完整性 | 空值统计 | <5%空值 | 检查属性数据完整性 |
| 坐标系一致性 | 坐标系检查 | 统一WGS84 | 检查坐标系是否正确 |
| 数据范围 | 边界框检查 | 合理范围 | 检查数据空间范围 |
