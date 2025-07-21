#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的GPKG文件加载脚本
使用config.json中的数据库配置加载testGdb.gpkg文件
"""

import json
import logging
import os
import sys
from datetime import datetime
import random
import string

import geopandas as gpd
from sqlalchemy import create_engine, text

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/gpkg_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config(config_path='config.json'):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logging.info(f"配置文件加载成功: {config_path}")
        return config
    except FileNotFoundError:
        logging.error(f"配置文件未找到: {config_path}")
        sys.exit(1)

def create_database_connection(config):
    """创建数据库连接"""
    db_config = config['database']
    try:
        connection_string = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        engine = create_engine(connection_string)
        
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logging.info("数据库连接成功")
        return engine
    except Exception as e:
        logging.error(f"数据库连接失败: {e}")
        sys.exit(1)

def analyze_gpkg_file(file_path):
    """分析GPKG文件"""
    try:
        # 读取GPKG文件的所有图层
        layers = gpd.read_file(file_path, layer=None)
        logging.info(f"GPKG文件分析完成: {file_path}")
        logging.info(f"发现 {len(layers)} 个图层")
        
        layer_info = {}
        for layer_name in layers:
            gdf = gpd.read_file(file_path, layer=layer_name)
            layer_info[layer_name] = {
                'feature_count': len(gdf),
                'geometry_type': str(gdf.geometry.geom_type.iloc[0]) if len(gdf) > 0 else 'Unknown',
                'crs': str(gdf.crs) if gdf.crs else 'Unknown',
                'columns': list(gdf.columns),
                'bbox': gdf.total_bounds.tolist() if len(gdf) > 0 else None
            }
            logging.info(f"图层 {layer_name}: {layer_info[layer_name]['feature_count']} 个要素, 几何类型: {layer_info[layer_name]['geometry_type']}")
        
        return layer_info
    except Exception as e:
        logging.error(f"GPKG文件分析失败: {e}")
        sys.exit(1)

def generate_table_name(filename, layer_name, timestamp):
    """生成表名"""
    # 清理文件名和图层名
    clean_filename = filename.replace('.gpkg', '').replace('.', '_').lower()
    clean_layer = layer_name.replace(' ', '_').lower()
    
    # 生成UUID
    uuid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    
    table_name = f"{timestamp}_{clean_filename}_{clean_layer}_{uuid}"
    return table_name

def create_vector_tables(engine, layer_info, filename, timestamp):
    """创建向量数据表"""
    tables_created = {}
    
    for layer_name, info in layer_info.items():
        table_name = generate_table_name(filename, layer_name, timestamp)
        
        logging.info(f"开始处理图层: {layer_name} -> 表名: {table_name}")
        
        # 读取图层数据
        gdf = gpd.read_file(f"testGdb.gpkg", layer=layer_name)
        
        # 转换坐标系到WGS84（如果需要）
        if gdf.crs and gdf.crs != 'EPSG:4326':
            try:
                gdf = gdf.to_crs('EPSG:4326')
                logging.info(f"坐标系转换成功: {layer_name} -> EPSG:4326")
            except Exception as e:
                logging.warning(f"坐标系转换失败，使用原始坐标系: {e}")
        
        # 准备属性数据
        if len(gdf) > 0:
            # 移除几何列，保留属性列
            attributes_df = gdf.drop(columns=['geometry'])
            
            # 将属性数据转换为JSONB格式
            attributes_json = attributes_df.to_dict('records')
            
            # 创建包含几何和属性的DataFrame
            import pandas as pd
            result_df = pd.DataFrame({
                'geom': gdf.geometry,
                'attributes': attributes_json,
                'create_time': datetime.now(),
                'update_time': datetime.now()
            })
            
            # 写入数据库
            try:
                result_df.to_sql(
                    table_name, 
                    engine, 
                    if_exists='replace', 
                    index=False,
                    method='multi',
                    chunksize=1000
                )
                
                # 创建索引
                with engine.connect() as conn:
                    # 空间索引
                    conn.execute(text(f"CREATE INDEX idx_{table_name}_geom ON {table_name} USING GIST (geom)"))
                    # 时间索引
                    conn.execute(text(f"CREATE INDEX idx_{table_name}_created ON {table_name} USING BTREE (create_time)"))
                    # 属性索引
                    conn.execute(text(f"CREATE INDEX idx_{table_name}_attributes ON {table_name} USING GIN (attributes)"))
                    conn.commit()
                
                tables_created[layer_name] = {
                    'table_name': table_name,
                    'feature_count': len(result_df),
                    'geometry_type': info['geometry_type']
                }
                
                logging.info(f"表 {table_name} 创建成功，包含 {len(result_df)} 个要素")
                
            except Exception as e:
                logging.error(f"表 {table_name} 创建失败: {e}")
                continue
    
    return tables_created

def create_metadata_tables(engine, layer_info, tables_created, filename, timestamp):
    """创建元数据表"""
    try:
        # 创建产品元数据表
        product_table_sql = """
        CREATE TABLE IF NOT EXISTS oge_vector_product (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            file_format VARCHAR(30) NOT NULL,
            file_size BIGINT,
            coordinate_system VARCHAR(100),
            bbox_minx FLOAT8,
            bbox_miny FLOAT8,
            bbox_maxx FLOAT8,
            bbox_maxy FLOAT8,
            total_features INTEGER NOT NULL,
            geometry_types VARCHAR(200) NOT NULL,
            layer_count INTEGER NOT NULL,
            description TEXT,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 创建图层索引表
        layer_table_sql = """
        CREATE TABLE IF NOT EXISTS oge_vector_layer (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL,
            layer_name VARCHAR(100) NOT NULL,
            table_name VARCHAR(255) NOT NULL,
            geometry_type VARCHAR(50) NOT NULL,
            feature_count INTEGER NOT NULL,
            bbox_minx FLOAT8,
            bbox_miny FLOAT8,
            bbox_maxx FLOAT8,
            bbox_maxy FLOAT8,
            coordinate_system VARCHAR(100) NOT NULL,
            attribute_schema JSONB,
            uuid VARCHAR(10) NOT NULL,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        with engine.connect() as conn:
            conn.execute(text(product_table_sql))
            conn.execute(text(layer_table_sql))
            conn.commit()
        
        logging.info("元数据表创建成功")
        
        # 插入产品元数据
        total_features = sum(info['feature_count'] for info in layer_info.values())
        geometry_types = ','.join(set(info['geometry_type'] for info in layer_info.values()))
        
        # 计算总体边界框
        all_bboxes = [info['bbox'] for info in layer_info.values() if info['bbox']]
        if all_bboxes:
            minx = min(bbox[0] for bbox in all_bboxes)
            miny = min(bbox[1] for bbox in all_bboxes)
            maxx = max(bbox[2] for bbox in all_bboxes)
            maxy = max(bbox[3] for bbox in all_bboxes)
        else:
            minx = miny = maxx = maxy = 0
        
        product_insert_sql = """
        INSERT INTO oge_vector_product 
        (name, file_path, file_format, file_size, coordinate_system, bbox_minx, bbox_miny, bbox_maxx, bbox_maxy, 
         total_features, geometry_types, layer_count, description, create_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(product_insert_sql), (
                filename,
                f"testGdb.gpkg",
                "GPKG",
                os.path.getsize("testGdb.gpkg") if os.path.exists("testGdb.gpkg") else 0,
                "EPSG:4326",
                minx, miny, maxx, maxy,
                total_features,
                geometry_types,
                len(layer_info),
                f"GPKG文件导入: {filename}",
                datetime.now()
            ))
            product_id = result.fetchone()[0]
            conn.commit()
        
        # 插入图层元数据
        for layer_name, table_info in tables_created.items():
            layer_info_data = layer_info[layer_name]
            uuid = table_info['table_name'].split('_')[-1]
            
            layer_insert_sql = """
            INSERT INTO oge_vector_layer 
            (product_id, layer_name, table_name, geometry_type, feature_count, bbox_minx, bbox_miny, bbox_maxx, bbox_maxy,
             coordinate_system, attribute_schema, uuid, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            
            bbox = layer_info_data.get('bbox', [0, 0, 0, 0])
            attribute_schema = json.dumps({col: 'text' for col in layer_info_data.get('columns', []) if col != 'geometry'})
            
            with engine.connect() as conn:
                conn.execute(text(layer_insert_sql), (
                    product_id,
                    layer_name,
                    table_info['table_name'],
                    layer_info_data['geometry_type'],
                    layer_info_data['feature_count'],
                    bbox[0], bbox[1], bbox[2], bbox[3],
                    layer_info_data['crs'],
                    attribute_schema,
                    uuid,
                    datetime.now()
                ))
                conn.commit()
        
        logging.info(f"元数据插入成功，产品ID: {product_id}")
        
    except Exception as e:
        logging.error(f"元数据表创建失败: {e}")

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 创建日志目录
    os.makedirs('logs', exist_ok=True)
    
    # 检查文件是否存在
    gpkg_file = "testGdb.gpkg"
    if not os.path.exists(gpkg_file):
        logging.error(f"GPKG文件不存在: {gpkg_file}")
        sys.exit(1)
    
    # 加载配置
    config = load_config()
    
    # 创建数据库连接
    engine = create_database_connection(config)
    
    # 分析GPKG文件
    logging.info("开始分析GPKG文件...")
    layer_info = analyze_gpkg_file(gpkg_file)
    
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 创建向量数据表
    logging.info("开始创建向量数据表...")
    tables_created = create_vector_tables(engine, layer_info, "testGdb", timestamp)
    
    # 创建元数据表
    logging.info("开始创建元数据表...")
    create_metadata_tables(engine, layer_info, tables_created, "testGdb", timestamp)
    
    # 输出结果
    logging.info("GPKG文件导入完成!")
    logging.info(f"创建的表:")
    for layer_name, table_info in tables_created.items():
        logging.info(f"  - {layer_name}: {table_info['table_name']} ({table_info['feature_count']} 个要素)")

if __name__ == "__main__":
    main() 