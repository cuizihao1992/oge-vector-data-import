#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然保护地数据入库脚本
专门用于入库 Data/自然保护地.gpkg 数据
"""

import os
import sys
import json
import logging
from datetime import datetime
from vector_to_postgis import VectorToPostGIS


def load_config(config_file="nature_reserve_config.json"):
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ 配置文件加载成功: {config_file}")
        return config
    except FileNotFoundError:
        print(f"✗ 配置文件不存在: {config_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ 配置文件格式错误: {e}")
        return None


def analyze_nature_reserve_data(gpkg_file_path):
    """分析自然保护地数据"""
    try:
        import geopandas as gpd
        
        print(f"\n开始分析自然保护地数据: {gpkg_file_path}")
        
        # 读取数据
        gdf = gpd.read_file(gpkg_file_path)
        
        print(f"✓ 数据读取成功")
        print(f"  记录数: {len(gdf)}")
        print(f"  字段数: {len(gdf.columns)}")
        print(f"  坐标系: {gdf.crs}")
        
        # 字段信息
        print(f"\n字段信息:")
        for i, col in enumerate(gdf.columns, 1):
            dtype = str(gdf[col].dtype)
            null_count = gdf[col].isnull().sum()
            print(f"  {i:2d}. {col:<20} {dtype:<15} 空值: {null_count}")
        
        # 几何信息
        print(f"\n几何信息:")
        geometry_types = gdf.geometry.geom_type.unique()
        print(f"  几何类型: {geometry_types}")
        
        bbox = gdf.total_bounds
        print(f"  边界框: [{bbox[0]:.6f}, {bbox[1]:.6f}, {bbox[2]:.6f}, {bbox[3]:.6f}]")
        
        # 面积统计
        if 'mj' in gdf.columns:
            print(f"\n面积统计 (mj字段):")
            print(f"  总面积: {gdf['mj'].sum():.6f}")
            print(f"  平均面积: {gdf['mj'].mean():.6f}")
            print(f"  最大面积: {gdf['mj'].max():.6f}")
            print(f"  最小面积: {gdf['mj'].min():.6f}")
        
        # 数据预览
        print(f"\n数据预览:")
        print(gdf.head())
        
        return gdf
        
    except Exception as e:
        print(f"✗ 自然保护地数据分析失败: {e}")
        return None


def check_database_connection(config):
    """检查数据库连接"""
    try:
        from sqlalchemy import create_engine, text
        
        connection_string = (
            f"postgresql://{config['database']['username']}:{config['database']['password']}"
            f"@{config['database']['host']}:{config['database']['port']}/{config['database']['database']}"
        )
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✓ 数据库连接成功")
            print(f"  数据库版本: {version}")
            return True
            
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False


def import_nature_reserve_data(config):
    """导入自然保护地数据"""
    
    test_data = config['test_data']
    gpkg_file_path = test_data['gdb_file_path']
    
    # 检查文件是否存在
    if not os.path.exists(gpkg_file_path):
        print(f"✗ GPKG文件不存在: {gpkg_file_path}")
        return False
    
    # 分析数据
    gdf = analyze_nature_reserve_data(gpkg_file_path)
    if gdf is None:
        return False
    
    # 创建工具实例
    try:
        tool_config = {
            'database': config['database'],
            'log_level': config['logging']['log_level'],
            'log_dir': config['logging']['log_dir']
        }
        tool = VectorToPostGIS(tool_config)
        print("✓ 工具初始化成功")
    except Exception as e:
        print(f"✗ 工具初始化失败: {e}")
        return False
    
    # 执行数据入库
    try:
        print(f"\n开始数据入库...")
        print(f"源坐标系: {test_data['source_crs']}")
        print(f"目标坐标系: {test_data['target_crs']}")
        print(f"矢量表: {test_data['vector_table']}")
        print(f"元数据表: {test_data['metadata_table']}")
        
        tool.process_vector_data(
            file_path=gpkg_file_path,
            source_crs=test_data['source_crs'],
            target_crs=test_data['target_crs'],
            vector_table=test_data['vector_table'],
            metadata_table=test_data['metadata_table'],
            encoding=test_data['encoding'],
            batch_size=test_data['batch_size']
        )
        
        print("✓ 数据入库成功！")
        return True
        
    except Exception as e:
        print(f"✗ 数据入库失败: {e}")
        return False


def verify_imported_data(config):
    """验证入库后的数据"""
    print("\n" + "=" * 60)
    print("验证入库数据")
    print("=" * 60)
    
    test_data = config['test_data']
    vector_table = test_data['vector_table']
    metadata_table = test_data['metadata_table']
    
    try:
        from sqlalchemy import create_engine, text
        
        # 连接数据库
        connection_string = (
            f"postgresql://{config['database']['username']}:{config['database']['password']}"
            f"@{config['database']['host']}:{config['database']['port']}/{config['database']['database']}"
        )
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            # 1. 检查矢量数据表
            print("1. 矢量数据表检查:")
            vector_query = f"SELECT COUNT(*) as count FROM {vector_table}"
            result = conn.execute(text(vector_query))
            vector_count = result.fetchone()[0]
            print(f"   ✓ 记录数: {vector_count}")
            
            # 2. 检查元数据表
            print("\n2. 元数据表检查:")
            metadata_query = f"SELECT * FROM {metadata_table} ORDER BY id DESC LIMIT 1"
            result = conn.execute(text(metadata_query))
            metadata = result.fetchone()
            
            if metadata:
                print(f"   ✓ 文件名称: {metadata.file_name}")
                print(f"   ✓ 记录数量: {metadata.feature_count}")
                print(f"   ✓ 几何类型: {metadata.geometry_type}")
                print(f"   ✓ 源坐标系: {metadata.source_crs}")
                print(f"   ✓ 目标坐标系: {metadata.target_crs}")
                
                # 解析属性模式
                if metadata.properties_schema:
                    if isinstance(metadata.properties_schema, str):
                        schema = json.loads(metadata.properties_schema)
                    else:
                        schema = metadata.properties_schema
                    print(f"   ✓ 属性字段数: {len(schema)}")
            
            # 3. 检查样本数据
            print("\n3. 样本数据检查:")
            sample_query = f"SELECT properties, ST_AsText(geometry) as geom_text FROM {vector_table} LIMIT 3"
            result = conn.execute(text(sample_query))
            samples = result.fetchall()
            
            for i, sample in enumerate(samples, 1):
                properties = json.loads(sample.properties)
                print(f"   ✓ 样本 {i}:")
                print(f"     属性字段数: {len(properties)}")
                print(f"     属性字段: {list(properties.keys())}")
                print(f"     几何数据: {sample.geom_text[:100]}...")
                
                # 显示属性值
                for key, value in properties.items():
                    print(f"     {key}: {value}")
                print()
            
            # 4. 面积统计查询
            print("4. 面积统计:")
            area_query = f"""
            SELECT 
                COUNT(*) as count,
                SUM(CAST(properties->>'mj' AS FLOAT)) as total_area,
                AVG(CAST(properties->>'mj' AS FLOAT)) as avg_area,
                MAX(CAST(properties->>'mj' AS FLOAT)) as max_area,
                MIN(CAST(properties->>'mj' AS FLOAT)) as min_area
            FROM {vector_table}
            """
            result = conn.execute(text(area_query))
            area_stats = result.fetchone()
            
            if area_stats:
                print(f"   ✓ 记录数: {area_stats.count}")
                print(f"   ✓ 总面积: {area_stats.total_area:.6f}")
                print(f"   ✓ 平均面积: {area_stats.avg_area:.6f}")
                print(f"   ✓ 最大面积: {area_stats.max_area:.6f}")
                print(f"   ✓ 最小面积: {area_stats.min_area:.6f}")
            
            # 5. 空间查询测试
            print("\n5. 空间查询测试:")
            spatial_query = f"""
            SELECT COUNT(*) as count 
            FROM {vector_table} 
            WHERE ST_IsValid(geometry) = true
            """
            result = conn.execute(text(spatial_query))
            valid_count = result.fetchone()[0]
            print(f"   ✓ 有效几何数: {valid_count}")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据验证失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 70)
    print("自然保护地数据入库脚本")
    print("=" * 70)
    
    # 检查依赖
    try:
        import geopandas as gpd
        import pandas as pd
        from sqlalchemy import create_engine
        print("✓ 依赖库检查通过")
    except ImportError as e:
        print(f"✗ 缺少依赖库: {e}")
        print("请安装: pip install geopandas pandas sqlalchemy psycopg2-binary")
        return False
    
    # 加载配置
    config = load_config()
    if config is None:
        return False
    
    # 检查数据库连接
    if not check_database_connection(config):
        return False
    
    # 执行数据入库
    success = import_nature_reserve_data(config)
    
    if success:
        # 验证入库数据
        verify_imported_data(config)
        
        print("\n" + "=" * 70)
        print("入库完成！")
        print("=" * 70)
        print("自然保护地数据已成功入库到PostGIS数据库")
        print(f"表名:")
        print(f"  - 矢量数据: {config['test_data']['vector_table']}")
        print(f"  - 元数据: {config['test_data']['metadata_table']}")
        print(f"\n可以使用以下SQL查询数据:")
        print(f"  SELECT * FROM {config['test_data']['vector_table']} LIMIT 5;")
        print(f"  SELECT * FROM {config['test_data']['metadata_table']};")
        print(f"\n面积统计查询:")
        print(f"  SELECT properties->>'mj' as area FROM {config['test_data']['vector_table']};")
    else:
        print("\n" + "=" * 70)
        print("入库失败！")
        print("=" * 70)
        return False
    
    return True


if __name__ == '__main__':
    main() 