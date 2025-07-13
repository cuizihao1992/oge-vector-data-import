# 矢量数据入库PostGIS工具

这是一个用于将矢量数据导入PostGIS数据库的Python工具，支持多种矢量格式，具备坐标系转换功能。

## 功能特性

- ✅ 支持多种矢量格式：Shapefile, GeoJSON, KML, GML, CSV, GPKG等
- ✅ 坐标系转换功能
- ✅ 批量数据插入
- ✅ 完整的元数据记录
- ✅ 详细的日志记录
- ✅ 错误处理和回滚
- ✅ 空间索引自动创建

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行使用

```bash
python vector_to_postgis.py \
    --file_path /path/to/your/data.shp \
    --source_crs EPSG:4326 \
    --target_crs EPSG:3857 \
    --db_host localhost \
    --db_port 5432 \
    --db_name gis_db \
    --db_user postgres \
    --db_password your_password \
    --vector_table vector_data \
    --metadata_table vector_metadata \
    --encoding utf-8 \
    --batch_size 1000 \
    --log_level INFO
```

### 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--file_path` | ✅ | - | 矢量文件路径 |
| `--source_crs` | ✅ | - | 源坐标系 (如: EPSG:4326) |
| `--target_crs` | ✅ | - | 目标坐标系 (如: EPSG:4326) |
| `--db_host` | ❌ | localhost | 数据库主机 |
| `--db_port` | ❌ | 5432 | 数据库端口 |
| `--db_name` | ✅ | - | 数据库名 |
| `--db_user` | ✅ | - | 数据库用户名 |
| `--db_password` | ✅ | - | 数据库密码 |
| `--vector_table` | ❌ | vector_data | 矢量数据表名 |
| `--metadata_table` | ❌ | vector_metadata | 元数据表名 |
| `--encoding` | ❌ | utf-8 | 文件编码 |
| `--batch_size` | ❌ | 1000 | 批量插入大小 |
| `--log_level` | ❌ | INFO | 日志级别 |
| `--log_dir` | ❌ | logs | 日志目录 |

## 支持的文件格式

- **ESRI Shapefile** (.shp)
- **GeoJSON** (.geojson, .json)
- **KML** (.kml)
- **GML** (.gml)
- **CSV** (.csv) - 需要包含geometry列或longitude/latitude列
- **GeoPackage** (.gpkg)
- **File Geodatabase** (.gdb)

## 数据库表结构

### 矢量数据表 (vector_data)

```sql
CREATE TABLE vector_data (
    id SERIAL PRIMARY KEY,
    geometry GEOMETRY(GEOMETRY, 4326),
    properties JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 空间索引
CREATE INDEX idx_vector_data_geometry ON vector_data USING GIST (geometry);

-- JSONB索引
CREATE INDEX idx_vector_data_properties ON vector_data USING GIN (properties);
```

### 元数据表 (vector_metadata)

```sql
CREATE TABLE vector_metadata (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255),
    file_path TEXT,
    file_size BIGINT,
    file_format VARCHAR(50),
    source_crs VARCHAR(100),
    target_crs VARCHAR(100),
    feature_count INTEGER,
    geometry_type VARCHAR(50),
    bbox_minx DOUBLE PRECISION,
    bbox_miny DOUBLE PRECISION,
    bbox_maxx DOUBLE PRECISION,
    bbox_maxy DOUBLE PRECISION,
    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    properties_schema JSONB,
    additional_info JSONB
);
```

## 使用示例

### 示例1：导入Shapefile

```bash
python vector_to_postgis.py \
    --file_path /data/cities.shp \
    --source_crs EPSG:4326 \
    --target_crs EPSG:3857 \
    --db_name gis_db \
    --db_user postgres \
    --db_password mypassword \
    --vector_table cities \
    --metadata_table cities_metadata
```

### 示例2：导入GeoJSON

```bash
python vector_to_postgis.py \
    --file_path /data/rivers.geojson \
    --source_crs EPSG:4326 \
    --target_crs EPSG:4326 \
    --db_name gis_db \
    --db_user postgres \
    --db_password mypassword \
    --vector_table rivers \
    --metadata_table rivers_metadata \
    --batch_size 500
```

### 示例3：导入CSV文件

```bash
python vector_to_postgis.py \
    --file_path /data/points.csv \
    --source_crs EPSG:4326 \
    --target_crs EPSG:3857 \
    --db_name gis_db \
    --db_user postgres \
    --db_password mypassword \
    --vector_table points \
    --metadata_table points_metadata \
    --encoding gbk
```

## 日志输出

工具会生成详细的日志文件，包含：

- 文件读取进度
- 坐标系转换信息
- 数据插入进度
- 错误信息和堆栈跟踪
- 性能统计信息

日志文件位置：`logs/vector_import_YYYYMMDD_HHMMSS.log`

## 错误处理

工具具备完善的错误处理机制：

- 文件格式验证
- 坐标系转换错误处理
- 数据库连接错误处理
- 数据插入错误处理和回滚
- 内存不足处理

## 性能优化

- 批量插入减少数据库连接开销
- 空间索引提高查询性能
- JSONB索引优化属性查询
- 内存使用优化

## 注意事项

1. **PostGIS扩展**：确保PostgreSQL数据库已安装PostGIS扩展
2. **权限**：确保数据库用户有创建表和插入数据的权限
3. **内存**：大文件处理时注意内存使用情况
4. **坐标系**：确保指定的坐标系正确
5. **编码**：CSV文件注意编码格式设置

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否启动
   - 验证连接参数是否正确
   - 确认网络连接正常

2. **坐标系转换失败**
   - 检查坐标系代码是否正确
   - 确认pyproj库版本
   - 验证数据是否包含有效的几何信息

3. **文件读取失败**
   - 检查文件路径是否正确
   - 确认文件格式是否支持
   - 验证文件是否损坏

4. **内存不足**
   - 减小batch_size参数
   - 分批处理大文件
   - 增加系统内存

## 许可证

MIT License
