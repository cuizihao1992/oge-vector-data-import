# 矢量数据入库流程

## 1. 入库处理流程

### 1.1 整体流程
```
数据文件 → 文件验证 → 文件分析 → 文件拆解 → 表名生成 → 表结构创建 → 坐标系转换 → 数据入库 → 索引创建 → 产品注册
```

### 1.2 详细步骤

| 步骤 | 操作 | 说明 | 是否必需 |
|------|------|------|----------|
| 1 | 文件验证 | 检查文件格式是否支持，文件是否存在 | 必需 |
| 2 | 文件分析 | 分析几何类型、字段结构、要素数量等 | 必需 |
| 3 | 文件拆解 | 将多图层文件拆解为单图层，将混合几何类型分离 | 可选 |
| 4 | 表名生成 | 根据文件和时间戳生成唯一表名 | 必需 |
| 5 | 表结构创建 | 根据数据特征创建PostgreSQL表 | 必需 |
| 6 | 坐标系转换 | 统一转换到WGS84坐标系 | 可选 |
| 7 | 数据入库 | 批量插入矢量数据 | 必需 |
| 8 | 索引创建 | 创建空间索引和属性索引 | 必需 |
| 9 | 产品注册 | 在产品表中注册元数据信息 | 必需 |

## 2. 文件验证

### 2.1 文件格式验证

| 支持格式 | 文件扩展名 | 验证方式 | 说明 |
|----------|------------|----------|------|
| ESRI Shapefile | .shp, .shx, .dbf | 检查必需文件是否存在 | 需要.shp、.shx、.dbf三个文件 |
| GeoJSON | .geojson, .json | 检查JSON格式有效性 | 验证JSON结构和几何数据 |
| GPKG | .gpkg | 检查SQLite数据库结构 | 验证GeoPackage规范 |
| OpenFileGDB | .gdb | 检查文件夹结构 | 验证GDB文件夹完整性 |

### 2.2 文件完整性验证

| 验证项目 | 验证内容 | 处理方式 | 示例 |
|----------|----------|----------|------|
| 文件存在性 | 检查文件是否存在 | 跳过不存在的文件 | 文件不存在 → 记录错误 |
| 文件大小 | 检查文件大小是否合理 | 跳过空文件或过大文件 | 文件大小0字节 → 跳过 |
| 文件权限 | 检查文件读取权限 | 跳过无权限文件 | 权限不足 → 记录错误 |
| 文件损坏 | 检查文件是否损坏 | 跳过损坏文件 | 文件损坏 → 记录错误 |

## 3. 文件分析

文件分析是矢量数据入库的关键环节，通过系统化的分析获取文件的完整信息，为后续处理提供依据。

### 3.1 分析层次结构

```
文件分析
├── 基础信息分析（文件级）
│   ├── 文件属性
│   ├── 格式验证
│   └── 完整性检查
├── 结构信息分析（数据级）
│   ├── 图层结构
│   ├── 字段结构
│   └── 几何类型
└── 内容信息分析（要素级）
    ├── 要素统计
    ├── 空间范围
    └── 质量评估
```

### 3.2 基础信息分析

**3.2.1 文件属性分析**
| 分析项目 | 获取方式 | 输出结果 | 示例 |
|----------|----------|----------|------|
| 文件大小 | 文件系统API | 字节数 | 1024000 bytes |
| 修改时间 | 文件系统API | 时间戳 | 2024-01-01 14:30:25 |
| 文件编码 | 编码检测库 | 编码类型 | UTF-8, GBK |
| 文件校验和 | MD5计算 | 哈希值 | a1b2c3d4... |

**3.2.2 格式验证分析**
| 验证项目 | 验证内容 | 验证方法 | 结果 |
|----------|----------|----------|------|
| 文件完整性 | 必需文件是否存在 | 文件系统检查 | 完整/缺失 |
| 格式规范性 | 文件格式是否符合标准 | 格式解析器 | 规范/异常 |
| 数据有效性 | 基础数据结构是否有效 | 数据读取测试 | 有效/无效 |

### 3.3 结构信息分析

**3.3.1 图层结构分析**
| 分析项目 | 分析内容 | 输出结果 | 示例 |
|----------|----------|----------|------|
| 图层数量 | 统计图层总数 | 数量统计 | 3个图层 |
| 图层名称 | 提取所有图层名 | 名称列表 | buildings, roads, pois |
| 图层类型 | 识别图层类型 | 类型分类 | 点图层、线图层、面图层 |
| 图层坐标系 | 识别各图层坐标系 | 坐标系信息 | 单图层: "EPSG:4490", 多图层: {"buildings": "EPSG:4490", "roads": "EPSG:4326"} |

**3.3.2 字段结构分析**
| 分析项目 | 分析内容 | 输出结果 | 示例 |
|----------|----------|----------|------|
| 字段名称 | 提取所有字段名 | 字段列表 | name, type, area |
| 字段类型 | 识别数据类型 | 类型映射 | text, integer, float |
| 字段约束 | 分析字段约束 | 约束信息 | 非空、唯一、主键 |

**3.3.3 几何类型分析**
| 分析项目 | 分析内容 | 输出结果 | 示例 |
|----------|----------|----------|------|
| 几何类型 | 识别几何类型 | 类型列表 | Point, LineString, Polygon |
| 几何有效性 | 检查几何有效性 | 有效性统计 | 95%有效 |
| 几何复杂度 | 分析几何复杂度 | 复杂度指标 | 平均顶点数 |

### 3.4 内容信息分析

**3.4.1 要素统计分析**
| 分析项目 | 分析内容 | 输出结果 | 示例 |
|----------|----------|----------|------|
| 总要素数 | 统计所有要素 | 数量统计 | 10000个要素 |
| 按图层统计 | 分图层统计 | 图层统计 | buildings: 5000, roads: 3000 |
| 按类型统计 | 分几何类型统计 | 类型统计 | Point: 2000, Line: 3000, Polygon: 5000 |

**3.4.2 空间范围分析**
| 分析项目 | 分析内容 | 输出结果 | 示例 |
|----------|----------|----------|------|
| 边界框 | 计算空间边界 | 坐标范围 | 116.0-117.0, 39.0-40.0 |
| 坐标系 | 识别各图层坐标系 | 坐标系信息 | 单图层: "EPSG:4490", 多图层: {"layer1": "EPSG:4326", "layer2": "EPSG:4490"} |

**3.4.3 质量评估分析**
| 分析项目 | 分析内容 | 输出结果 | 示例 |
|----------|----------|----------|------|
| 数据完整性 | 检查数据完整性 | 完整性指标 | 98%完整 |
| 数据准确性 | 评估数据准确性 | 准确性指标 | 95%准确 |
| 数据一致性 | 检查数据一致性 | 一致性指标 | 一致/不一致 |

### 3.5 分析结果汇总

**3.5.1 产品级信息汇总**

**多图层文件示例：**
```json
{
  "file_info": {
    "size": 1024000,
    "modified_time": "2024-01-01 14:30:25",
    "encoding": "UTF-8",
    "checksum": "a1b2c3d4..."
  },
  "data_info": {
    "total_layers": 3,
    "total_features": 10000,
    "geometry_types": ["Point", "LineString", "Polygon"],
    "layer_crs": {
      "buildings": "EPSG:4490",
      "roads": "EPSG:4326", 
      "pois": "EPSG:4490"
    },
    "spatial_extent": [116.0, 39.0, 117.0, 40.0]
  },
  "quality_info": {
    "completeness": 0.98,
    "accuracy": 0.95,
    "consistency": "consistent"
  }
}
```

**单图层文件示例：**
```json
{
  "file_info": {
    "size": 512000,
    "modified_time": "2024-01-01 14:30:25",
    "encoding": "UTF-8",
    "checksum": "e5f6g7h8..."
  },
  "data_info": {
    "total_layers": 1,
    "total_features": 5000,
    "geometry_types": ["Polygon"],
    "layer_crs": "EPSG:4490",
    "spatial_extent": [116.0, 39.0, 117.0, 40.0]
  },
  "quality_info": {
    "completeness": 0.99,
    "accuracy": 0.96,
    "consistency": "consistent"
  }
}
```

**3.5.2 分析结果应用**
- **入库决策**：根据分析结果决定是否继续入库
- **处理策略**：根据文件特征选择处理方式
- **资源配置**：根据数据规模分配处理资源
- **质量监控**：建立质量基线进行后续监控

## 4. 文件拆解
分析Shapefile、GeoPackage、GeoJSON、GDB等多类型文件格式特点，分别采取不同的数据处理策略：

### 4.1 拆解类型与策略

| 拆解类型 | 处理对象 | 处理方式 | 示例 |
|----------|----------|----------|------|
| 多图层拆解 | GDB、GPKG文件 | 按图层分离，每个图层独立处理 | city_data.gdb → buildings层、roads层、boundaries层 |
| 混合几何类型拆解 | GeoJSON文件 | 按几何类型分离，每种类型独立处理 | mixed.geojson → Point类型、LineString类型、Polygon类型 |
| 单图层文件 | Shapefile、GeoJSON等 | 跳过拆解，直接处理 | roads.shp → 直接处理 |

### 4.2 多图层/混合几何类型拆解示例

**拆解示例：**
```
输入：city_data.gdb
├── buildings (面要素，1000个)
├── roads (线要素，500个)
├── pois (点要素，200个)
└── boundaries (面要素，50个)

输出：
├── city_data_buildings (独立处理)
├── city_data_roads (独立处理)
├── city_data_pois (独立处理)
└── city_data_boundaries (独立处理)
```

**拆解示例：**
```
输入：mixed.geojson
├── Point要素 (300个)
├── LineString要素 (150个)
└── Polygon要素 (80个)

输出：
├── mixed_point (独立处理)
├── mixed_linestring (独立处理)
└── mixed_polygon (独立处理)
```

### 4.3 拆解后处理流程

拆解完成后，每个独立的数据集将按照以下流程处理：

```
独立数据集 → 表名生成 → 表结构创建 → 坐标系转换 → 数据入库 → 索引创建
```

**处理特点：**
- 每个拆解后的数据集使用相同的UUID
- 表名中包含几何类型标识（仅混合几何类型）
- 独立创建表结构和索引
- 独立进行坐标系转换

## 5. 表名生成

### 5.1 命名格式
**前缀 + 文件名 + 图层名 + 时间戳 + UUID（推荐）**
```
oge_vec_roads_buildings_20240101_143022_a1b2c3
```

| 组件 | 格式 | 示例 | 说明 |
|------|------|------|------|
| 前缀 | oge_vec_ | oge_vec_ | 统一前缀，便于识别和管理 |
| 文件名 | 原文件名（不含扩展名） | roads | 小写，替换特殊字符 |
| 图层名 | 图层名称 | buildings | 仅多图层文件需要 |
| 时间戳 | YYYYMMDD_HHMMSS | 20240101_143022 | 精确到秒 |
| UUID | 6位随机字符 | a1b2c3 | 同一数据集使用相同UUID |

**前缀设计说明：**
- **oge_vec_**：OGE矢量数据表统一前缀
- 便于数据库管理员识别和管理矢量数据表
- 支持按前缀进行表分组和权限控制
- 避免与系统表或其他业务表名冲突

### 5.2 命名示例

| 输入文件 | 时间 | 输出表名 | 说明 |
|----------|------|----------|------|
| roads.shp | 2024-01-01 14:30:22 | oge_vec_roads_20240101_143022_a1b2c3 | 单文件 |
| city_data.gdb (buildings层) | 2024-01-01 14:30:22 | oge_vec_city_data_buildings_20240101_143022_a1b2c3 | GDB多图层，相同UUID |
| city_data.gdb (roads层) | 2024-01-01 14:30:22 | oge_vec_city_data_roads_20240101_143022_a1b2c3 | GDB多图层，相同UUID |
| mixed.geojson (点要素) | 2024-01-01 14:30:22 | oge_vec_mixed_point_20240101_143022_a1b2c3 | 混合几何类型，相同UUID |
| mixed.geojson (线要素) | 2024-01-01 14:30:22 | oge_vec_mixed_linestring_20240101_143022_a1b2c3 | 混合几何类型，相同UUID |

### 5.3 UUID生成策略

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

### 5.4 文件同名处理

| 情况 | 处理方式 | 表名示例 | 说明 |
|------|----------|----------|------|
| 首次入库 | 正常命名 | oge_vec_roads_20240101_143022_a1b2c3 | 无冲突 |
| 重复入库 | 时间戳区分 | oge_vec_roads_20240115_091545_d4e5f6 | 自动避免冲突 |

**处理策略：**
- 使用精确到秒的时间戳确保唯一性
- 不同时间入库的同名文件自动区分
- 支持同一文件的多版本管理

## 6. 表结构创建

本节所述的表结构创建，专指针对每个实际入库的矢量数据表（如 oge_vec_{filename}_{layer}_{timestamp}_{uuid} ）。表结构会根据源数据的属性表字段（自动识别字段名和类型）和空间几何字段（geometry）综合自动生成，确保每个要素的属性和空间信息都能完整存储。

**PostgreSQL预留字段考虑：**
在创建表结构时，需要避免使用PostgreSQL系统预留字段名，确保数据字段与系统字段不冲突。

### 6.1 基础表结构

每个矢量数据表都包含以下基础字段：

| 字段名 | 数据类型 | 约束 | 说明 | 示例 |
|--------|----------|------|------|------|
| id | SERIAL | PRIMARY KEY | 自增主键 | 1, 2, 3... |
| geom | geometry | NOT NULL | 几何数据，类型根据数据自动确定 | 见几何类型映射表 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 | 2024-01-01 14:30:25 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 | 2024-01-01 14:30:25 |

**PostgreSQL系统预留字段（避免使用）：**
- `oid`：对象标识符
- `tableoid`：表OID
- `xmin`、`xmax`：事务ID
- `cmin`、`cmax`：命令ID
- `ctid`：行物理位置
- `oid`：对象标识符（如果启用）
- 其他以`pg_`开头的字段名

**字段名冲突处理策略：**
- 检测到冲突时，自动在字段名前添加`attr_`前缀
- 例如：`oid` → `attr_oid`，`xmin` → `attr_xmin`
- 在元数据中记录原始字段名和映射后的字段名

### 6.2 几何类型映射

| 几何类型 | PostGIS类型 | 说明 | 示例表名 |
|----------|-------------|------|----------|
| Point | geometry(POINT, 4326) | 点要素 | oge_vec_pois_20240101_143022_a1b2c3 |
| LineString | geometry(LINESTRING, 4326) | 线要素 | oge_vec_roads_20240101_143022_a1b2c3 |
| Polygon | geometry(POLYGON, 4326) | 面要素 | oge_vec_buildings_20240101_143022_a1b2c3 |
| MultiPoint | geometry(MULTIPOINT, 4326) | 多点要素 | oge_vec_points_20240101_143022_a1b2c3 |
| MultiLineString | geometry(MULTILINESTRING, 4326) | 多线要素 | oge_vec_lines_20240101_143022_a1b2c3 |
| MultiPolygon | geometry(MULTIPOLYGON, 4326) | 多面要素 | oge_vec_areas_20240101_143022_a1b2c3 |
| 混合类型 | geometry(GEOMETRY, 4326) | 支持所有几何类型 | oge_vec_mixed_20240101_143022_a1b2c3 |

**坐标系说明：**
- **默认情况**：统一转换为WGS84（EPSG:4326）坐标系
- **保留原始坐标系**：如果转换失败或用户指定跳过，保留原始坐标系
- **其他目标坐标系**：支持转换为其他坐标系（如EPSG:3857、EPSG:4490等）
- **实际存储**：几何字段类型会根据实际坐标系动态调整，如 `geometry(POINT, 4490)`

**示例：**
```sql
-- 默认WGS84坐标系
geom geometry(POINT, 4326)

-- 保留原始坐标系（如CGCS2000）
geom geometry(POINT, 4490)

-- 转换为Web Mercator投影
geom geometry(POINT, 3857)
```

### 6.3 属性字段映射

| Pandas类型 | PostgreSQL类型 | 说明 | 示例 |
|------------|----------------|------|------|
| object | TEXT | 字符串类型 | 名称, 类型, 描述 |
| int64 | BIGINT | 64位整数 | 面积, 长度, 数量 |
| int32 | INTEGER | 32位整数 | 楼层数, 车道数 |
| float64 | DOUBLE PRECISION | 64位浮点数 | 坐标, 高程 |
| float32 | REAL | 32位浮点数 | 精度, 比例 |
| bool | BOOLEAN | 布尔类型 | 是否启用, 是否可见 |
| datetime64[ns] | TIMESTAMP | 时间戳类型 | 创建时间, 更新时间 |

## 7. 坐标系转换

### 7.1 转换策略

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

## 8. 数据库表设计

### 8.1 涉及的表结构概览

本系统矢量数据部分涉及三类核心表，三表通过外键关联保证数据一致性和完整性：
- **oge_vector_product**：存储矢量产品级别的核心元数据。
- **oge_vector_layer**：矢量数据索引表，存储矢量专用元数据、所属产品ID、属性结构等。
- **oge_vec_{filename}_{layer}_{timestamp}_{uuid}**：矢量数据表，实际存储每个图层/几何类型的要素数据。

表间关系：oge_vector_layer.product_id 外键关联 oge_vector_product.id，oge_vector_layer.table_name 与实际矢量数据表一一对应。

| 表名 | 用途 | 表类型 | 说明 |
|------|------|--------|------|
| oge_vector_product | 矢量产品元数据表 | 固定表 | 存储所有矢量产品的元数据信息 |
| oge_vector_layer | 矢量数据索引表 | 固定表 | 存储矢量数据表的结构、空间范围、属性等索引信息 |
| oge_vec_{filename}_{layer}_{timestamp}_{uuid} | 矢量数据表 | 动态表 | 存储实际的矢量几何和属性数据 |

### 8.2 固定表详细设计

#### 8.2.1 oge_vector_product（矢量产品元数据表）

该表用于存储每个矢量产品的核心元数据，支持文件追溯、空间范围、国际化描述、发布控制等多场景。

| 字段名           | 数据类型      | 约束                  | 说明                | 示例                      |
|------------------|--------------|-----------------------|---------------------|---------------------------|
| id               | SERIAL       | PRIMARY KEY           | 产品ID              | 1, 2, 3...                |
| name             | VARCHAR(255) | NOT NULL              | 产品名称            | roads, city_data_buildings|
| file_name        | VARCHAR(255) |                       | 原始文件名          | roads.shp                 |
| file_path        | TEXT         |                       | 文件存储路径        | /data/roads.shp           |
| file_format      | VARCHAR(30)  |                       | 文件格式            | shp, geojson, gdb         |
| file_size        | BIGINT       |                       | 文件大小（字节）    | 1024000                   |
| file_modified    | TIMESTAMP    |                       | 文件修改时间        | 2024-01-01 14:30:25       |
| file_encoding    | VARCHAR(20)  |                       | 文件编码            | UTF-8, GBK                |
| file_checksum    | VARCHAR(64)  |                       | 文件校验和          | a1b2c3d4...               |
| total_layers     | INTEGER      |                       | 总图层数            | 3                         |
| total_features   | INTEGER      |                       | 总要素数            | 10000                     |
| geometry_types   | TEXT[]       |                       | 几何类型列表        | {Point,LineString,Polygon}|
| source_crs       | JSONB        |                       | 源坐标系映射        | {"layer1": "EPSG:4490", "layer2": "EPSG:4326"} 或 "EPSG:4490" |
| target_crs       | VARCHAR(100) |                       | 目标坐标系          | EPSG:4326                 |
| crs_transform    | BOOLEAN      | DEFAULT false         | 是否进行坐标转换    | true, false               |
| lower_right_lat  | FLOAT8       |                       | 右下角纬度          | 39.0                      |
| lower_right_long | FLOAT8       |                       | 右下角经度          | 117.0                     |
| upper_left_lat   | FLOAT8       |                       | 左上角纬度          | 40.0                      |
| upper_left_long  | FLOAT8       |                       | 左上角经度          | 116.0                     |
| processing_time  | INTEGER      |                       | 处理时间（秒）      | 120                       |
| error_count      | INTEGER      | DEFAULT 0             | 错误数量            | 5                         |
| warning_count    | INTEGER      | DEFAULT 0             | 警告数量            | 10                        |
| owner            | VARCHAR(32)  |                       | 所有者              | admin, user1              |
| registertime     | TIMESTAMP    | DEFAULT CURRENT_TIMESTAMP | 注册时间        | 2024-01-01 14:30:25       |
| updatetime       | TIMESTAMP    | DEFAULT CURRENT_TIMESTAMP | 更新时间        | 2024-01-01 14:30:25       |
| description      | TEXT         |                       | 产品描述（中文）    | 详细描述                  |
| description_en   | TEXT         |                       | 产品描述（英文）    | English description       |
| cover_area       | VARCHAR(255) |                       | 所属区域（中文）    | 山东省, 济南市            |
| cover_area_en    | TEXT         |                       | 所属区域（英文）    | Shandong Province         |
| tags             | TEXT         |                       | 标签                | 道路, 建筑物              |
| sample_code      | TEXT         |                       | 示例代码            | ...                       |
| is_publish       | BOOLEAN      | DEFAULT false         | 是否发布            | true, false               |
| status           | INTEGER      | DEFAULT 1             | 状态                | 1（启用）, 0（禁用）       |

#### 8.2.2 oge_vector_layer（矢量数据索引表）

该表不仅存储矢量数据表的基本信息（如表名、几何类型、空间范围、产品ID等），还需存储矢量数据表的结构信息，便于系统自动化管理和元数据自描述。推荐通过 attribute_schema 字段（JSONB 类型）记录每个矢量数据表的属性字段名、类型、主键等结构。

- **attribute_schema 字段设计说明**：
  - 记录所有属性字段的名称、类型、可选描述、主键等。
  - 支持灵活扩展，便于后续字段变更或表结构演化。

- **attribute_schema 示例**：
```json
{
  "fields": [
    {"name": "name", "type": "text", "description": "名称"},
    {"name": "area", "type": "float", "description": "面积"},
    {"name": "type", "type": "integer", "description": "类型"}
  ],
  "primary_key": "id"
}
```

| 字段名 | 数据类型 | 约束 | 说明 | 示例 |
|--------|----------|------|------|------|
| id | SERIAL | PRIMARY KEY | 索引ID，自增主键 | 1, 2, 3... |
| product_id | INTEGER | NOT NULL, FOREIGN KEY | 关联产品ID | 1, 2, 3... |
| table_name | VARCHAR(255) | NOT NULL | 数据表名 | oge_vec_roads_20240101_143022_a1b2c3 |
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
| file_format | VARCHAR(30) | NOT NULL | 文件格式 | shp, geojson, gdb |
| storage_path | TEXT | NOT NULL | 存储路径 | /data/roads.shp |
| table_create_time | TIMESTAMP | NOT NULL | 表创建时间 | 2024-01-01 14:30:22 |
| table_uuid | VARCHAR(10) | NOT NULL | 表UUID | a1b2c3 |
| attribute_schema | JSONB | NULL | 属性字段结构 | 见上方示例 |
| quality_metrics | JSONB | NULL | 数据质量指标 | {"validity": 0.95, ...} |
| processing_info | JSONB | NULL | 处理信息 | {"software": "GDAL", ...} |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 | 2024-01-01 14:30:25 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 | 2024-01-01 14:30:25 |
| status | INTEGER | DEFAULT 1 | 状态 | 1（正常）, 0（删除） |

### 8.3 动态表详细设计

#### 8.3.1 矢量数据表（oge_vec_{layer}_{timestamp}_{uuid}）

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
| Point | geometry(POINT, 4326) | 点要素 | oge_vec_pois_20240101_143022_a1b2c3 |
| LineString | geometry(LINESTRING, 4326) | 线要素 | oge_vec_roads_20240101_143022_a1b2c3 |
| Polygon | geometry(POLYGON, 4326) | 面要素 | oge_vec_buildings_20240101_143022_a1b2c3 |
| MultiPoint | geometry(MULTIPOINT, 4326) | 多点要素 | oge_vec_points_20240101_143022_a1b2c3 |
| MultiLineString | geometry(MULTILINESTRING, 4326) | 多线要素 | oge_vec_lines_20240101_143022_a1b2c3 |
| MultiPolygon | geometry(MULTIPOLYGON, 4326) | 多面要素 | oge_vec_areas_20240101_143022_a1b2c3 |
| 混合类型 | geometry(GEOMETRY, 4326) | 支持所有几何类型 | oge_vec_mixed_20240101_143022_a1b2c3 |

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

### 8.4 表关系与约束

#### 8.4.1 主键和外键关系

| 关系类型 | 主表 | 主键 | 从表 | 外键 | 说明 |
|----------|------|------|------|------|------|
| 一对多 | oge_vector_product | id | oge_vector_layer | product_id | 一个产品可以有多个矢量数据表 |
| 逻辑关联 | oge_vector_layer | id | 动态表 | 无外键 | 通过表名与oge_vector_layer.table_name进行逻辑关联 |

**说明：**
- 动态表与oge_vector_layer之间为逻辑关联关系，依赖表名一致性，无数据库外键约束。
- 所有动态表的元数据和管理均通过oge_vector_layer表实现。


