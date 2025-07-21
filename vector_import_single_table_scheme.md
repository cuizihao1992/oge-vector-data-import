# 矢量数据入库方案 - 单表模式

## 核心设计

**原则：每个矢量数据文件入库时单独生成一个表**

```
数据文件 → 分析结构 → 创建表 → 数据入库 → 注册产品
```

## 1. 基本流程

### 1.1 文件分析
```python
def analyze_vector_file(file_path):
    """分析矢量文件结构"""
    gdf = gpd.read_file(file_path)
    return {
        'geometry_types': gdf.geometry.geom_type.unique(),
        'columns': list(gdf.columns),
        'feature_count': len(gdf),
        'crs': str(gdf.crs),
        'bbox': gdf.total_bounds
    }
```

### 1.2 表名生成规则
```python
def generate_table_name(file_path, layer_name=None):
    """生成表名"""
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    if layer_name:
        return f"{base_name}_{layer_name}".lower().replace('-', '_')
    return base_name.lower().replace('-', '_')
```

## 2. 不同格式处理

### 2.1 Shapefile (.shp)
```python
# 单图层，直接处理
table_name = generate_table_name("roads.shp")  # -> roads
```

### 2.2 GeoJSON (.geojson)
```python
# 可能包含多种几何类型
gdf = gpd.read_file("mixed_features.geojson")
geometry_types = gdf.geometry.geom_type.unique()

if len(geometry_types) > 1:
    # 按几何类型分表
    for geom_type in geometry_types:
        subset = gdf[gdf.geometry.geom_type == geom_type]
        table_name = f"{base_name}_{geom_type.lower()}"
        create_and_populate_table(table_name, subset)
else:
    # 单一几何类型
    table_name = generate_table_name("mixed_features.geojson")
    create_and_populate_table(table_name, gdf)
```

### 2.3 GDB文件 (.gdb)
```python
# 多图层处理
import fiona
layers = fiona.listlayers("data.gdb")

for layer in layers:
    gdf = gpd.read_file("data.gdb", layer=layer)
    table_name = generate_table_name("data.gdb", layer)
    create_and_populate_table(table_name, gdf)
```

## 3. 数据库表创建

### 3.1 表结构生成
```python
def create_vector_table(table_name, gdf, target_crs="EPSG:4326"):
    """创建矢量数据表"""
    
    # 确定几何类型
    geometry_types = gdf.geometry.geom_type.unique()
    if len(geometry_types) == 1:
        geom_type = geometry_types[0].upper()
    else:
        geom_type = "GEOMETRY"  # 混合类型
    
    # 生成字段定义
    columns = []
    for col in gdf.columns:
        if col == 'geometry':
            continue
        dtype = gdf[col].dtype
        pg_type = map_pandas_to_postgres(dtype)
        columns.append(f'"{col}" {pg_type}')
    
    # 创建表SQL
    sql = f"""
    CREATE TABLE {table_name} (
        id SERIAL PRIMARY KEY,
        geom geometry({geom_type}, {target_crs.split(':')[1]}),
        {', '.join(columns)}
    );
    """
    
    return sql
```

### 3.2 数据类型映射
```python
def map_pandas_to_postgres(dtype):
    """Pandas数据类型映射到PostgreSQL"""
    mapping = {
        'object': 'TEXT',
        'int64': 'BIGINT',
        'int32': 'INTEGER',
        'float64': 'DOUBLE PRECISION',
        'float32': 'REAL',
        'bool': 'BOOLEAN',
        'datetime64[ns]': 'TIMESTAMP'
    }
    return mapping.get(str(dtype), 'TEXT')
```

## 4. 特殊情况处理

### 4.1 GDB多图层
```python
def process_gdb_file(gdb_path):
    """处理GDB文件的多图层"""
    layers = fiona.listlayers(gdb_path)
    
    for layer in layers:
        try:
            gdf = gpd.read_file(gdb_path, layer=layer)
            table_name = generate_table_name(gdb_path, layer)
            
            # 创建表并入库
            create_and_populate_table(table_name, gdf)
            
            # 注册到产品表
            register_product(table_name, gdb_path, layer)
            
        except Exception as e:
            logger.error(f"处理图层 {layer} 失败: {e}")
```

### 4.2 GeoJSON混合几何类型
```python
def process_mixed_geojson(file_path):
    """处理包含多种几何类型的GeoJSON"""
    gdf = gpd.read_file(file_path)
    geometry_types = gdf.geometry.geom_type.unique()
    
    if len(geometry_types) == 1:
        # 单一类型，正常处理
        table_name = generate_table_name(file_path)
        create_and_populate_table(table_name, gdf)
    else:
        # 混合类型，按类型分表
        base_name = generate_table_name(file_path)
        
        for geom_type in geometry_types:
            subset = gdf[gdf.geometry.geom_type == geom_type]
            table_name = f"{base_name}_{geom_type.lower()}"
            create_and_populate_table(table_name, subset)
```

### 4.3 字段名冲突处理
```python
def sanitize_column_name(col_name):
    """处理字段名冲突"""
    # PostgreSQL保留字
    reserved_words = ['order', 'group', 'table', 'user', 'index', 'primary']
    
    if col_name.lower() in reserved_words:
        return f"{col_name}_col"
    
    # 特殊字符处理
    return col_name.replace(' ', '_').replace('-', '_')
```

## 5. 产品注册

### 5.1 产品表记录
```python
def register_product(table_name, file_path, layer_name=None):
    """注册产品到产品表"""
    
    sql = """
    INSERT INTO oge_vector_data_product (
        name, product_type, data_category, geometry_type,
        feature_count, file_format, table_name, storage_path
    ) VALUES (
        :name, 'vector', :category, :geom_type,
        :feature_count, :file_format, :table_name, :file_path
    );
    """
    
    # 执行插入
    execute_sql(sql, params)
```

## 6. 完整示例

### 6.1 处理Shapefile
```python
# 输入: roads.shp
# 输出: roads表
table_name = "roads"
sql = """
CREATE TABLE roads (
    id SERIAL PRIMARY KEY,
    geom geometry(LINESTRING, 4326),
    "name" TEXT,
    "type" TEXT,
    "length" DOUBLE PRECISION
);
"""
```

### 6.2 处理GDB文件
```python
# 输入: data.gdb (包含 layers: buildings, roads, boundaries)
# 输出: data_buildings, data_roads, data_boundaries 三个表

# data_buildings表
CREATE TABLE data_buildings (
    id SERIAL PRIMARY KEY,
    geom geometry(POLYGON, 4326),
    "name" TEXT,
    "height" DOUBLE PRECISION
);

# data_roads表  
CREATE TABLE data_roads (
    id SERIAL PRIMARY KEY,
    geom geometry(LINESTRING, 4326),
    "name" TEXT,
    "width" DOUBLE PRECISION
);
```

### 6.3 处理混合GeoJSON
```python
# 输入: mixed.geojson (包含 POINT, LINESTRING, POLYGON)
# 输出: mixed_point, mixed_linestring, mixed_polygon 三个表

# mixed_point表
CREATE TABLE mixed_point (
    id SERIAL PRIMARY KEY,
    geom geometry(POINT, 4326),
    "name" TEXT
);

# mixed_linestring表
CREATE TABLE mixed_linestring (
    id SERIAL PRIMARY KEY,
    geom geometry(LINESTRING, 4326),
    "name" TEXT
);
```

## 7. 索引创建

```python
def create_indexes(table_name):
    """为表创建索引"""
    indexes = [
        f"CREATE INDEX idx_{table_name}_geom ON {table_name} USING GIST (geom);",
        f"CREATE INDEX idx_{table_name}_id ON {table_name} (id);"
    ]
    
    for index_sql in indexes:
        execute_sql(index_sql)
```

## 8. 查询示例

```sql
-- 查询所有产品
SELECT name, geometry_type, feature_count, table_name 
FROM oge_vector_data_product 
WHERE product_type = 'vector';

-- 查询特定表的数据
SELECT * FROM roads WHERE ST_Intersects(geom, ST_GeomFromText('POLYGON((...))', 4326));

-- 查询所有道路
SELECT * FROM data_roads WHERE "type" = 'highway';
```

## 9. 优势与限制

### 优势
- ✅ 表结构完全匹配数据特征
- ✅ 查询性能好（字段类型明确）
- ✅ 便于数据维护和更新
- ✅ 支持复杂属性结构

### 限制
- ❌ 表数量会快速增长
- ❌ 跨表查询复杂
- ❌ 需要额外的产品表管理

## 10. 实施建议

1. **命名规范**：使用统一的表名生成规则
2. **索引优化**：为每个表创建空间索引
3. **产品管理**：通过产品表统一管理所有表
4. **错误处理**：对特殊情况进行异常处理
5. **日志记录**：记录每个表的创建和入库过程 