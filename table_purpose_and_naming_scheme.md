# 表作用说明与命名方案

## 1. 三个表的作用

### 1.1 oge_db_connection（数据库连接表）
```sql
-- 存储数据库连接信息
CREATE TABLE oge_db_connection (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),           -- 连接名称
    host VARCHAR(255),           -- 数据库主机
    port INTEGER,                -- 端口
    database VARCHAR(255),       -- 数据库名
    username VARCHAR(255),       -- 用户名
    password VARCHAR(255),       -- 密码（加密存储）
    connection_type VARCHAR(50), -- 连接类型：postgresql, mysql等
    status INTEGER DEFAULT 1,    -- 状态：0-禁用，1-启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**作用：** 管理多个数据库连接，支持分布式存储

### 1.2 oge_catalog_scheme（分类表）
```sql
-- 存储数据分类信息
CREATE TABLE oge_catalog_scheme (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),           -- 分类名称
    code VARCHAR(50),            -- 分类代码
    parent_id INTEGER,           -- 父分类ID
    level INTEGER DEFAULT 1,     -- 分类层级
    description TEXT,            -- 分类描述
    sort_order INTEGER DEFAULT 0, -- 排序
    status INTEGER DEFAULT 1,    -- 状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**作用：** 管理数据分类体系，如行政区划、土地利用、基础设施等

### 1.3 oge_sensor（传感器表）
```sql
-- 存储传感器信息（主要用于遥感数据）
CREATE TABLE oge_sensor (
    sensor_key SERIAL PRIMARY KEY,
    sensor_name VARCHAR(255),    -- 传感器名称
    satellite_name VARCHAR(255), -- 卫星名称
    sensor_type VARCHAR(100),    -- 传感器类型
    resolution VARCHAR(50),      -- 分辨率
    wavelength_range TEXT,       -- 波长范围
    launch_date DATE,            -- 发射日期
    status VARCHAR(50),          -- 状态
    description TEXT             -- 描述
);
```
**作用：** 管理遥感传感器信息，虽然主要用于栅格数据，但矢量数据也可能需要关联

## 2. 文件同名问题解决方案

### 2.1 问题描述
```
输入文件: roads.shp
时间1: 2024-01-01 → 生成表: roads
时间2: 2024-01-15 → 生成表: roads (冲突!)
```

### 2.2 解决方案：时间戳+UUID命名

#### 方案A：时间戳前缀
```python
def generate_table_name_with_timestamp(file_path, layer_name=None):
    """生成带时间戳的表名"""
    import time
    from datetime import datetime
    
    # 获取当前时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 生成基础表名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    if layer_name:
        table_name = f"{timestamp}_{base_name}_{layer_name}"
    else:
        table_name = f"{timestamp}_{base_name}"
    
    return table_name.lower().replace('-', '_')

# 示例输出:
# 20240101_143022_roads
# 20240115_091545_roads
```

#### 方案B：UUID后缀
```python
def generate_table_name_with_uuid(file_path, layer_name=None):
    """生成带UUID的表名"""
    import uuid
    
    # 生成短UUID（前8位）
    short_uuid = str(uuid.uuid4())[:8]
    
    # 生成基础表名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    if layer_name:
        table_name = f"{base_name}_{layer_name}_{short_uuid}"
    else:
        table_name = f"{base_name}_{short_uuid}"
    
    return table_name.lower().replace('-', '_')

# 示例输出:
# roads_a1b2c3d4
# roads_e5f6g7h8
```

#### 方案C：时间戳+UUID组合（推荐）
```python
def generate_table_name_combined(file_path, layer_name=None):
    """生成时间戳+UUID组合的表名"""
    import time
    import uuid
    from datetime import datetime
    
    # 时间戳（精确到秒）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 短UUID
    short_uuid = str(uuid.uuid4())[:6]
    
    # 生成基础表名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    if layer_name:
        table_name = f"{timestamp}_{base_name}_{layer_name}_{short_uuid}"
    else:
        table_name = f"{timestamp}_{base_name}_{short_uuid}"
    
    return table_name.lower().replace('-', '_')

# 示例输出:
# 20240101_143022_roads_a1b2c3
# 20240115_091545_roads_d4e5f6
```

### 2.3 表名解析功能

#### 解析表名获取信息
```python
def parse_table_name(table_name):
    """解析表名获取创建时间等信息"""
    import re
    from datetime import datetime
    
    # 匹配模式: YYYYMMDD_HHMMSS_filename_layer_uuid
    pattern = r'(\d{8}_\d{6})_(.+?)(?:_([^_]+))?_(.{6})$'
    match = re.match(pattern, table_name)
    
    if match:
        timestamp_str, filename, layer, uuid_part = match.groups()
        
        # 解析时间戳
        create_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        
        return {
            'create_time': create_time,
            'filename': filename,
            'layer': layer,
            'uuid': uuid_part,
            'original_name': f"{filename}{'_' + layer if layer else ''}"
        }
    
    return None

# 使用示例
table_name = "20240101_143022_roads_a1b2c3"
info = parse_table_name(table_name)
# 输出: {
#     'create_time': datetime(2024, 1, 1, 14, 30, 22),
#     'filename': 'roads',
#     'layer': None,
#     'uuid': 'a1b2c3',
#     'original_name': 'roads'
# }
```

### 2.4 产品表记录更新

#### 更新产品表结构
```sql
-- 在产品表中添加时间戳字段
ALTER TABLE oge_vector_data_product ADD COLUMN table_create_time TIMESTAMP;
ALTER TABLE oge_vector_data_product ADD COLUMN table_uuid VARCHAR(10);

-- 更新产品注册函数
def register_product_with_timestamp(table_name, file_path, layer_name=None):
    """注册产品到产品表（带时间戳）"""
    
    # 解析表名
    table_info = parse_table_name(table_name)
    
    sql = """
    INSERT INTO oge_vector_data_product (
        name, product_type, data_category, geometry_type,
        feature_count, file_format, table_name, storage_path,
        table_create_time, table_uuid, registertime
    ) VALUES (
        :name, 'vector', :category, :geom_type,
        :feature_count, :file_format, :table_name, :file_path,
        :table_create_time, :table_uuid, :registertime
    );
    """
    
    params = {
        'name': table_info['original_name'],
        'category': 'auto_detected',
        'geom_type': 'auto_detected',
        'feature_count': 0,
        'file_format': os.path.splitext(file_path)[1],
        'table_name': table_name,
        'file_path': file_path,
        'table_create_time': table_info['create_time'],
        'table_uuid': table_info['uuid'],
        'registertime': datetime.now()
    }
    
    execute_sql(sql, params)
```

## 3. 完整示例

### 3.1 GDB多图层处理
```python
# 输入: city_data.gdb (包含3个图层)
# 时间: 2024-01-01 14:30:22

layers = fiona.listlayers("city_data.gdb")
for layer in layers:
    # 生成表名
    table_name = generate_table_name_combined("city_data.gdb", layer)
    
    # 示例输出:
    # 20240101_143022_city_data_buildings_a1b2c3
    # 20240101_143022_city_data_roads_d4e5f6
    # 20240101_143022_city_data_boundaries_g7h8i9
    
    # 创建表并注册产品
    create_table(table_name, layer_data)
    register_product_with_timestamp(table_name, "city_data.gdb", layer)
```

### 3.2 查询示例

#### 查询某个文件的所有版本
```sql
-- 查询roads.shp的所有版本
SELECT 
    table_name,
    table_create_time,
    table_uuid,
    feature_count,
    registertime
FROM oge_vector_data_product 
WHERE name = 'roads' 
ORDER BY table_create_time DESC;
```

#### 查询最新版本
```sql
-- 查询roads.shp的最新版本
SELECT 
    table_name,
    table_create_time,
    feature_count
FROM oge_vector_data_product 
WHERE name = 'roads' 
ORDER BY table_create_time DESC 
LIMIT 1;
```

#### 查询某个时间范围的数据
```sql
-- 查询2024年1月创建的所有表
SELECT 
    name,
    table_name,
    table_create_time,
    feature_count
FROM oge_vector_data_product 
WHERE table_create_time >= '2024-01-01' 
  AND table_create_time < '2024-02-01'
ORDER BY table_create_time;
```

## 4. 优势总结

### 4.1 时间戳优势
- ✅ **可读性强**：表名包含创建时间
- ✅ **排序方便**：按时间戳排序
- ✅ **版本管理**：支持多版本数据

### 4.2 UUID优势
- ✅ **唯一性保证**：避免冲突
- ✅ **短小精悍**：6位字符
- ✅ **随机性**：增加安全性

### 4.3 组合方案优势
- ✅ **信息完整**：时间+文件+UUID
- ✅ **易于解析**：可提取所有信息
- ✅ **向后兼容**：支持历史数据
- ✅ **查询高效**：支持多种查询方式

这样的命名方案既解决了文件同名问题，又保留了创建时间信息，便于数据管理和版本控制。 