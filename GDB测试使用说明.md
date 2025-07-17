# GDB数据入库测试使用说明

## 概述

本测试套件用于将 `空间适配OGE数据资料.gdb` 文件入库到PostGIS数据库，并提供完整的数据验证功能。

## 文件说明

### 核心文件
- `vector_to_postgis.py` - 矢量数据入库工具（已修复数据完整性问题）
- `test_gdb_import.py` - 基础版GDB入库测试脚本
- `test_gdb_import_advanced.py` - 高级版GDB入库测试脚本（推荐使用）
- `gdb_test_config.json` - 配置文件
- `test_data_integrity.py` - 数据完整性验证脚本

### 数据文件
- `空间适配OGE数据资料.gdb/` - 待入库的GDB数据

## 数据特征

根据分析，该GDB数据具有以下特征：
- **记录数**: 1条
- **字段数**: 14个字段
- **坐标系**: EPSG:4527
- **几何类型**: MULTIPOLYGON
- **无空值**: 所有字段都没有空值

### 字段列表
1. BSM - 标识码
2. YSDM - 要素代码
3. XZQDM - 行政区代码
4. XZQMC - 行政区名称
5. DCMJ - 调查面积
6. JSMJ - 计算面积
7. MSSM - 描述信息
8. HDMC - 活动名称
9. BZ - 备注
10. 分市 - 分市标识
11. 分县 - 分县标识
12. SHAPE_Length - 几何长度
13. SHAPE_Area - 几何面积
14. geometry - 几何数据

## 使用步骤

### 1. 环境准备

确保已安装必要的依赖：
```bash
pip install geopandas pandas sqlalchemy psycopg2-binary
```

### 2. 数据库准备

确保PostgreSQL数据库已启动，并创建目标数据库：
```sql
CREATE DATABASE oge_vector_db;
```

### 3. 配置修改

编辑 `gdb_test_config.json` 文件，修改数据库连接参数：
```json
{
    "database": {
        "host": "localhost",
        "port": 5432,
        "database": "oge_vector_db",
        "username": "your_username",
        "password": "your_password"
    }
}
```

### 4. 运行测试

#### 方式一：使用高级版脚本（推荐）
```bash
# 完整测试（包括数据分析和入库）
python test_gdb_import_advanced.py

# 仅检查数据（不执行入库）
python test_gdb_import_advanced.py --check-only

# 仅验证已入库的数据
python test_gdb_import_advanced.py --verify-only
```

#### 方式二：使用基础版脚本
```bash
python test_gdb_import.py
```

#### 方式三：使用命令行工具
```bash
python vector_to_postgis.py \
    --file_path "空间适配OGE数据资料.gdb" \
    --source_crs "EPSG:4527" \
    --target_crs "EPSG:4326" \
    --db_host localhost \
    --db_port 5432 \
    --db_name oge_vector_db \
    --db_user your_username \
    --db_password your_password \
    --vector_table oge_gdb_data \
    --metadata_table oge_gdb_metadata
```

### 5. 数据验证

运行数据完整性验证：
```bash
python test_data_integrity.py "空间适配OGE数据资料.gdb"
```

## 预期结果

### 成功入库后，数据库中会创建以下表：

#### 1. oge_gdb_data（矢量数据表）
```sql
CREATE TABLE oge_gdb_data (
    id SERIAL PRIMARY KEY,
    geometry GEOMETRY(GEOMETRY, 4326),
    properties JSONB,
    metadata_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. oge_gdb_metadata（元数据表）
```sql
CREATE TABLE oge_gdb_metadata (
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

### 查询示例

```sql
-- 查看所有数据
SELECT * FROM oge_gdb_data;

-- 查看元数据
SELECT * FROM oge_gdb_metadata;

-- 查看属性数据
SELECT 
    id,
    properties->>'BSM' as bsm,
    properties->>'XZQMC' as xzqmc,
    properties->>'DCMJ' as dcmj,
    ST_AsText(geometry) as geom_text
FROM oge_gdb_data;

-- 空间查询
SELECT COUNT(*) 
FROM oge_gdb_data 
WHERE ST_IsValid(geometry) = true;
```

## 注意事项

1. **坐标系转换**: 数据从EPSG:4527转换到EPSG:4326（WGS84）
2. **数据完整性**: 修改后的代码会保留所有属性数据，包括空值
3. **日志记录**: 所有操作都会记录到logs目录下的日志文件
4. **错误处理**: 脚本包含完整的错误处理和回滚机制

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL服务是否启动
   - 验证数据库连接参数是否正确
   - 确认数据库用户权限

2. **GDB文件读取失败**
   - 确认文件路径正确
   - 检查文件权限
   - 验证GDB文件完整性

3. **坐标系转换失败**
   - 确认源坐标系参数正确
   - 检查目标坐标系是否支持

4. **数据入库失败**
   - 检查数据库表是否已存在
   - 确认数据库用户有创建表的权限
   - 查看日志文件获取详细错误信息

### 日志文件

所有操作日志保存在 `logs/` 目录下，文件名格式为：
```
vector_import_YYYYMMDD_HHMMSS.log
```

## 技术支持

如遇到问题，请：
1. 查看日志文件获取详细错误信息
2. 检查数据库连接和权限
3. 验证数据文件完整性
4. 确认所有依赖库已正确安装 