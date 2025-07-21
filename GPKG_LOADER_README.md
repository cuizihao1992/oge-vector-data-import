# GPKG文件加载脚本使用说明

## 功能说明

这个脚本用于将GPKG（GeoPackage）文件加载到PostgreSQL数据库中，使用config.json中的数据库配置。

## 文件结构

```
├── simple_gpkg_loader.py    # 主要的加载脚本
├── config.json              # 数据库配置文件
├── testGdb.gpkg            # 要加载的GPKG文件
├── requirements_gpkg.txt    # Python依赖包
└── logs/                   # 日志文件目录
```

## 安装依赖

```bash
pip install -r requirements_gpkg.txt
```

## 使用方法

### 1. 准备文件
确保以下文件存在：
- `testGdb.gpkg` - 要加载的GPKG文件
- `config.json` - 数据库配置文件

### 2. 运行脚本
```bash
python simple_gpkg_loader.py
```

## 脚本功能

### 1. 文件分析
- 自动检测GPKG文件中的所有图层
- 分析每个图层的几何类型、要素数量、坐标系等信息
- 输出分析结果到日志

### 2. 数据表创建
- 为每个图层创建独立的数据表
- 表名格式：`{时间戳}_{文件名}_{图层名}_{UUID}`
- 自动转换坐标系到WGS84（EPSG:4326）
- 将属性数据存储为JSONB格式

### 3. 索引创建
- **空间索引**：为几何字段创建GIST索引
- **时间索引**：为创建时间字段创建B-tree索引
- **属性索引**：为JSONB属性字段创建GIN索引

### 4. 元数据管理
- 创建 `oge_vector_product` 表存储产品级元数据
- 创建 `oge_vector_layer` 表存储图层级元数据
- 自动记录文件信息、空间范围、要素数量等

## 数据库表结构

### 动态数据表
每个图层会创建一个数据表，包含以下字段：
- `id`: 自增主键
- `geom`: 几何数据（PostGIS geometry类型）
- `attributes`: 属性数据（JSONB格式）
- `create_time`: 创建时间
- `update_time`: 更新时间

### 元数据表

#### oge_vector_product（产品元数据表）
- `id`: 产品ID
- `name`: 产品名称
- `file_path`: 文件路径
- `file_format`: 文件格式
- `total_features`: 总要素数量
- `geometry_types`: 几何类型列表
- `layer_count`: 图层数量
- `bbox_minx/maxy/maxx/maxy`: 空间范围

#### oge_vector_layer（图层索引表）
- `id`: 图层ID
- `product_id`: 关联的产品ID
- `layer_name`: 图层名称
- `table_name`: 对应的数据表名
- `geometry_type`: 几何类型
- `feature_count`: 要素数量
- `uuid`: 图层UUID

## 日志输出

脚本会生成详细的日志文件，包含：
- 文件分析结果
- 数据库操作状态
- 错误信息和警告
- 创建的表信息

日志文件位置：`logs/gpkg_import_YYYYMMDD_HHMMSS.log`

## 错误处理

### 常见错误及解决方案

1. **文件不存在**
   ```
   错误：GPKG文件不存在: testGdb.gpkg
   解决：确保testGdb.gpkg文件在当前目录
   ```

2. **数据库连接失败**
   ```
   错误：数据库连接失败
   解决：检查config.json中的数据库配置是否正确
   ```

3. **坐标系转换失败**
   ```
   警告：坐标系转换失败，使用原始坐标系
   解决：脚本会自动使用原始坐标系，不影响数据导入
   ```

4. **内存不足**
   ```
   错误：大文件处理时内存溢出
   解决：脚本使用分批处理，默认每批1000条记录
   ```

## 性能优化

### 批处理
- 默认批处理大小：1000条记录
- 可通过修改代码中的`chunksize`参数调整

### 索引优化
- 空间索引：加速空间查询
- 时间索引：加速时间范围查询
- 属性索引：加速JSONB属性查询

### 存储优化
- 使用JSONB存储属性数据，节省存储空间
- 自动压缩几何数据
- 批量插入减少数据库交互

## 查询示例

### 查询所有产品
```sql
SELECT name, file_format, total_features, layer_count 
FROM oge_vector_product 
WHERE status = 1;
```

### 查询产品图层
```sql
SELECT layer_name, table_name, geometry_type, feature_count 
FROM oge_vector_layer 
WHERE product_id = 1;
```

### 空间查询
```sql
SELECT * FROM 20240101_143022_testgdb_buildings_a1b2c3 
WHERE ST_Intersects(geom, ST_GeomFromText('POLYGON((...))', 4326));
```

### 属性查询
```sql
SELECT * FROM 20240101_143022_testgdb_roads_a1b2c3 
WHERE attributes->>'road_name' = '主干道';
```

## 注意事项

1. **文件格式支持**：仅支持GPKG格式文件
2. **坐标系转换**：自动尝试转换到WGS84，失败时使用原始坐标系
3. **表名唯一性**：使用时间戳和UUID确保表名唯一
4. **数据完整性**：自动创建索引和约束保证数据完整性
5. **日志记录**：详细记录所有操作过程，便于问题排查

## 扩展功能

如需支持其他格式（如Shapefile、GeoJSON等），可以修改脚本中的文件读取部分，使用相应的GeoPandas读取函数。 