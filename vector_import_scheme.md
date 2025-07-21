# 向量数据导入方案

## 1. 系统架构

### 1.1 整体架构
```
数据文件 → 文件分析 → 表名生成 → 表结构创建 → 数据入库 → 索引创建 → 产品注册
```

### 1.2 核心表设计
- **oge_vector_product**: 向量产品元数据表（固定表）
- **oge_vector_layer**: 向量图层索引表（固定表）
- **{timestamp}_{filename}_{layer}_{uuid}**: 向量数据表（动态表）

## 2. 数据库表设计

### 2.1 oge_vector_product（向量产品元数据表）

| 字段名 | 数据类型 | 约束 | 说明 | 示例 |
|--------|----------|------|------|------|
| id | SERIAL | PRIMARY KEY | 产品ID | 1, 2, 3... |
| name | VARCHAR(255) | NOT NULL | 产品名称 | roads, city_data |
| file_path | TEXT | NOT NULL | 原始文件路径 | /data/roads.shp |
| file_format | VARCHAR(30) | NOT NULL | 文件格式 | shp, geojson, gdb |
| file_size | BIGINT | NULL | 文件大小（字节） | 1024000 |
| file_count | INTEGER | NULL | 文件数量 | 1, 4（shp文件组） |
| coordinate_system | VARCHAR(100) | NULL | 坐标系 | EPSG:4326, EPSG:4490 |
| spatial_extent | geometry(POLYGON, 4326) | NULL | 空间范围 | 边界多边形 |
| bbox_minx | FLOAT8 | NOT NULL | 边界框最小X | 116.0 |
| bbox_miny | FLOAT8 | NOT NULL | 边界框最小Y | 39.0 |
| bbox_maxx | FLOAT8 | NOT NULL | 边界框最大X | 117.0 |
| bbox_maxy | FLOAT8 | NOT NULL | 边界框最大Y | 40.0 |
| total_features | INTEGER | NOT NULL | 总要素数量 | 10000 |
| geometry_types | VARCHAR(200) | NOT NULL | 几何类型列表 | POINT,LINESTRING,POLYGON |
| layer_count | INTEGER | NOT NULL | 图层数量 | 1, 3, 5 |
| description | TEXT | NULL | 描述信息 | 道路网络数据 |
| tags | TEXT | NULL | 标签 | 道路,交通,基础设施 |
| owner | VARCHAR(32) | NULL | 所有者 | admin, user1 |
| status | INTEGER | DEFAULT 1 | 状态 | 1（正常）, 0（删除） |
| create_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 | 2024-01-01 14:30:25 |
| update_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 | 2024-01-01 14:30:25 |

### 2.2 oge_vector_layer（向量图层索引表）

| 字段名 | 数据类型 | 约束 | 说明 | 示例 |
|--------|----------|------|------|------|
| id | SERIAL | PRIMARY KEY | 图层ID | 1, 2, 3... |
| product_id | INTEGER | NOT NULL, FOREIGN KEY | 关联产品ID | 1, 2, 3... |
| layer_name | VARCHAR(100) | NOT NULL | 图层名称 | buildings, roads, boundaries |
| table_name | VARCHAR(255) | NOT NULL | 数据表名 | 20240101_143022_roads_a1b2c3 |
| geometry_type | VARCHAR(50) | NOT NULL | 几何类型 | POINT, LINESTRING, POLYGON |
| feature_count | INTEGER | NOT NULL | 要素数量 | 1000, 500, 100 |
| spatial_extent | geometry(POLYGON, 4326) | NULL | 空间范围 | 边界多边形 |
| bbox_minx | FLOAT8 | NOT NULL | 边界框最小X | 116.0 |
| bbox_miny | FLOAT8 | NOT NULL | 边界框最小Y | 39.0 |
| bbox_maxx | FLOAT8 | NOT NULL | 边界框最大X | 117.0 |
| bbox_maxy | FLOAT8 | NOT NULL | 边界框最大Y | 40.0 |
| coordinate_system | VARCHAR(100) | NOT NULL | 坐标系 | EPSG:4326 |
| attribute_schema | JSONB | NULL | 属性字段结构 | {"name": "text", "type": "integer"} |
| quality_metrics | JSONB | NULL | 数据质量指标 | {"validity": 0.95, "completeness": 0.98} |
| processing_info | JSONB | NULL | 处理信息 | {"software": "GDAL", "version": "3.4.0"} |
| uuid | VARCHAR(10) | NOT NULL | 图层UUID | a1b2c3 |
| create_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 | 2024-01-01 14:30:25 |
| update_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 | 2024-01-01 14:30:25 |
| status | INTEGER | DEFAULT 1 | 状态 | 1（正常）, 0（删除） |

### 2.3 向量数据表（动态表）

每个向量数据表都包含以下基础字段：

| 字段名 | 数据类型 | 约束 | 说明 | 示例 |
|--------|----------|------|------|------|
| id | SERIAL | PRIMARY KEY | 自增主键 | 1, 2, 3... |
| geom | geometry | NOT NULL | 几何数据 | 见几何类型映射表 |
| attributes | JSONB | NULL | 属性数据 | {"name": "道路1", "type": 1} |
| create_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 | 2024-01-01 14:30:25 |
| update_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 | 2024-01-01 14:30:25 |

## 3. 导入处理流程

### 3.1 文件验证
- 检查文件格式是否支持
- 验证文件完整性
- 检查文件权限

### 3.2 文件分析
- 分析几何类型和数量
- 提取属性字段结构
- 计算空间范围
- 识别坐标系信息

### 3.3 表名生成
**命名格式：时间戳_文件名_图层名_UUID**

| 组件 | 格式 | 示例 | 说明 |
|------|------|------|------|
| 时间戳 | YYYYMMDD_HHMMSS | 20240101_143022 | 精确到秒 |
| 文件名 | 原文件名（不含扩展名） | city_data | 小写，替换特殊字符 |
| 图层名 | 图层名称 | buildings | 仅多图层文件需要 |
| UUID | 6位随机字符 | a1b2c3 | 同一数据集使用相同UUID |

### 3.4 表结构创建
- 根据几何类型创建对应的PostGIS表
- 设置坐标系和空间索引
- 创建必要的约束和索引

### 3.5 坐标系转换（可选）
- 优先尝试转换到WGS84（EPSG:4326）
- 转换失败时使用原始坐标系
- 记录转换过程和结果

### 3.6 数据入库
- 批量插入向量数据
- 处理属性字段映射
- 验证数据完整性

### 3.7 索引创建
- 创建空间索引（GIST）
- 创建时间索引（B-tree）
- 创建属性索引（GIN，用于JSONB）

### 3.8 产品注册
- 在产品表中注册元数据
- 在图层表中注册索引信息
- 更新统计信息

## 4. 不同格式处理策略

### 4.1 单文件格式

| 格式 | 处理方式 | 生成表数 | 示例 |
|------|----------|----------|------|
| Shapefile (.shp) | 直接处理 | 1个 | roads.shp → 20240101_143022_roads_a1b2c3 |
| GeoJSON (.geojson) | 按几何类型分表 | 1-多个 | mixed.geojson → 3个表（点、线、面） |
| KML (.kml) | 直接处理 | 1个 | places.kml → 20240101_143022_places_a1b2c3 |

### 4.2 多图层格式

| 格式 | 处理方式 | 生成表数 | 示例 |
|------|----------|----------|------|
| GDB (.gdb) | 每个图层一个表 | N个（N=图层数） | city_data.gdb → 4个表 |
| GPKG (.gpkg) | 每个图层一个表 | N个（N=图层数） | data.gpkg → 3个表 |

## 5. 特殊情况处理

### 5.1 多图层文件处理
- 同一文件的所有图层使用相同UUID
- 每个图层创建独立的数据表
- 在产品表中记录总图层数

### 5.2 GeoJSON混合几何类型
- 按几何类型分别创建表
- 同一文件的所有几何类型使用相同UUID
- 在图层表中记录每个几何类型的要素数量

### 5.3 文件同名处理
- 使用时间戳和UUID避免冲突
- 支持同一文件多次入库
- 保留历史版本信息

### 5.4 坐标系转换处理
- 转换成功：使用转换后的坐标系
- 转换失败：使用原始坐标系，记录警告
- 用户可配置是否强制转换

## 6. 索引和约束设计

### 6.1 主键和外键关系

| 关系类型 | 主表 | 主键 | 从表 | 外键 | 说明 |
|----------|------|------|------|------|------|
| 一对多 | oge_vector_product | id | oge_vector_layer | product_id | 一个产品可以有多个图层 |

### 6.2 索引设计

| 表名 | 索引名 | 索引类型 | 字段 | 说明 |
|------|--------|----------|------|------|
| oge_vector_product | idx_product_name | B-tree | name | 产品名称查询 |
| oge_vector_product | idx_product_create_time | B-tree | create_time | 创建时间查询 |
| oge_vector_product | idx_product_spatial | GIST | spatial_extent | 空间范围查询 |
| oge_vector_layer | idx_layer_product_id | B-tree | product_id | 产品关联查询 |
| oge_vector_layer | idx_layer_table_name | B-tree | table_name | 表名查询 |
| oge_vector_layer | idx_layer_geometry_type | B-tree | geometry_type | 几何类型查询 |
| oge_vector_layer | idx_layer_spatial | GIST | spatial_extent | 空间范围查询 |
| 动态表 | idx_{table_name}_geom | GIST | geom | 空间索引 |
| 动态表 | idx_{table_name}_created | B-tree | create_time | 时间索引 |
| 动态表 | idx_{table_name}_attributes | GIN | attributes | JSONB属性索引 |

## 7. 查询示例

### 7.1 基础查询

| 查询类型 | SQL示例 | 说明 |
|----------|---------|------|
| 查询所有产品 | SELECT p.name, p.file_format, p.total_features, p.layer_count FROM oge_vector_product p WHERE p.status = 1 | 获取所有正常状态的产品 |
| 查询产品图层 | SELECT l.layer_name, l.table_name, l.geometry_type, l.feature_count FROM oge_vector_layer l WHERE l.product_id = 1 | 获取指定产品的所有图层 |
| 查询最新版本 | SELECT l.table_name FROM oge_vector_layer l WHERE l.product_id = 1 ORDER BY l.create_time DESC LIMIT 1 | 获取最新版本表名 |
| 查询属性结构 | SELECT l.attribute_schema FROM oge_vector_layer l WHERE l.table_name = '20240101_143022_roads_a1b2c3' | 获取表的属性字段结构 |

### 7.2 空间查询

| 查询类型 | SQL示例 | 说明 |
|----------|---------|------|
| 空间相交 | SELECT * FROM 20240101_143022_roads_a1b2c3 WHERE ST_Intersects(geom, ST_GeomFromText('POLYGON((...))', 4326)) | 查询与指定区域相交的要素 |
| 空间包含 | SELECT * FROM 20240101_143022_buildings_a1b2c3 WHERE ST_Contains(ST_GeomFromText('POLYGON((...))', 4326), geom) | 查询包含在指定区域内的要素 |
| 距离查询 | SELECT * FROM 20240101_143022_points_a1b2c3 WHERE ST_DWithin(geom, ST_GeomFromText('POINT(116.0 39.0)', 4326), 1000) | 查询距离指定点1000米内的要素 |

### 7.3 跨表查询

| 查询类型 | SQL示例 | 说明 |
|----------|---------|------|
| 查询GDB所有图层 | SELECT p.name, l.layer_name, l.table_name, l.feature_count FROM oge_vector_product p JOIN oge_vector_layer l ON p.id = l.product_id WHERE p.file_path = 'city_data.gdb' | 获取多图层文件的所有图层 |
| 跨表空间查询 | WITH area AS (SELECT ST_GeomFromText('POLYGON((...))', 4326) as geom)<br>SELECT 'buildings' as layer, id, geom FROM 20240101_143022_city_data_buildings_a1b2c3, area WHERE ST_Intersects(geom, area.geom)<br>UNION ALL<br>SELECT 'roads' as layer, id, geom FROM 20240101_143022_city_data_roads_a1b2c3, area WHERE ST_Intersects(geom, area.geom) | 查询多个表的空间数据 |

## 8. 性能优化

### 8.1 索引优化
- 空间索引：为geom字段创建GIST索引
- 时间索引：为create_time字段创建B-tree索引
- 属性索引：为attributes字段创建GIN索引

### 8.2 查询优化
- 使用空间索引进行空间查询
- 限制查询范围减少扫描数据量
- 使用批量操作减少数据库交互

### 8.3 存储优化
- 选择合适的数据类型
- 使用PostgreSQL压缩功能
- 按时间或空间分区

## 9. 错误处理

### 9.1 常见错误及处理

| 错误类型 | 错误描述 | 处理方式 | 预防措施 |
|----------|----------|----------|----------|
| 文件格式不支持 | 无法读取文件格式 | 跳过该文件，记录错误日志 | 预先检查文件格式 |
| 坐标系转换失败 | 坐标系转换出错 | 跳过转换，使用原始坐标系，记录警告 | 验证坐标系信息 |
| 字段名冲突 | 字段名与保留字冲突 | 自动添加后缀 | 预先检查字段名 |
| 内存不足 | 大文件处理时内存溢出 | 分批处理数据 | 设置合理的批处理大小 |
| 数据库连接失败 | 无法连接数据库 | 重试连接，记录错误 | 检查数据库状态 |

### 9.2 日志记录

| 日志级别 | 记录内容 | 示例 |
|----------|----------|------|
| INFO | 正常操作信息 | 文件roads.shp入库成功，生成表20240101_143022_roads_a1b2c3 |
| WARNING | 警告信息 | 坐标系转换警告，使用原始坐标系EPSG:4490 |
| ERROR | 错误信息 | 文件data.gdb读取失败：文件损坏 |
| DEBUG | 调试信息 | 处理第1000条记录，内存使用：50MB |

## 10. 监控和维护

### 10.1 性能监控
- 入库速度：记录处理时间
- 内存使用：监控内存占用
- 磁盘空间：监控存储空间
- 查询响应时间：记录查询时间

### 10.2 数据质量检查
- 几何有效性：使用ST_IsValid()检查
- 属性完整性：统计空值比例
- 坐标系一致性：检查坐标系是否正确
- 数据范围：检查数据空间范围 