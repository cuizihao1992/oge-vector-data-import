#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GDB数据入库测试脚本（高级版）
支持配置文件读取，提供详细的测试和验证功能
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from vector_to_postgis import VectorToPostGIS


def load_config(config_file="gdb_test_config.json"):
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


def analyze_gdb_data(gdb_file_path):
    """分析GDB数据"""
    try:
        import geopandas as gpd
        
        print(f"\n开始分析GDB数据: {gdb_file_path}")
        
        # 读取数据
        gdf = gpd.read_file(gdb_file_path)
        
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
        
        # 数据预览
        print(f"\n数据预览:")
        print(gdf.head())
        
        return gdf
        
    except Exception as e:
        print(f"✗ GDB数据分析失败: {e}")
        return None


def test_gdb_import(config):
    """测试GDB数据入库"""
    
    test_data = config['test_data']
    gdb_file_path = test_data['gdb_file_path']
    
    # 检查文件是否存在
    if not os.path.exists(gdb_file_path):
        print(f"✗ GDB文件不存在: {gdb_file_path}")
        return False
    
    # 分析GDB数据
    gdf = analyze_gdb_data(gdb_file_path)
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
            file_path=gdb_file_path,
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
                    schema = json.loads(metadata.properties_schema)
                    print(f"   ✓ 属性字段数: {len(schema)}")
            
            # 3. 检查样本数据
            print("\n3. 样本数据检查:")
            sample_query = f"SELECT properties, ST_AsText(geometry) as geom_text FROM {vector_table} LIMIT 1"
            result = conn.execute(text(sample_query))
            sample = result.fetchone()
            
            if sample:
                properties = json.loads(sample.properties)
                print(f"   ✓ 属性字段数: {len(properties)}")
                print(f"   ✓ 几何数据: {sample.geom_text[:100]}...")
                
                # 显示属性字段
                print("   ✓ 属性字段:")
                for key, value in list(properties.items())[:5]:
                    print(f"      {key}: {value}")
            
            # 4. 空间查询测试
            print("\n4. 空间查询测试:")
            spatial_query = f"""
            SELECT COUNT(*) as count 
            FROM {vector_table} 
            WHERE ST_IsValid(geometry) = true
            """
            result = conn.execute(text(spatial_query))
            valid_count = result.fetchone()[0]
            print(f"   ✓ 有效几何数: {valid_count}")
            
            # 5. 属性查询测试
            print("\n5. 属性查询测试:")
            prop_query = f"""
            SELECT properties->>'BSM' as bsm, properties->>'XZQMC' as xzqmc
            FROM {vector_table} 
            LIMIT 3
            """
            result = conn.execute(text(prop_query))
            props = result.fetchall()
            print(f"   ✓ 属性查询结果:")
            for prop in props:
                print(f"      BSM: {prop.bsm}, 行政区: {prop.xzqmc}")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据验证失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GDB数据入库测试脚本')
    parser.add_argument('--config', default='gdb_test_config.json', help='配置文件路径')
    parser.add_argument('--check-only', action='store_true', help='仅检查数据库连接和数据')
    parser.add_argument('--verify-only', action='store_true', help='仅验证已入库的数据')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("GDB数据入库测试脚本（高级版）")
    print("=" * 70)
    
    # 加载配置
    config = load_config(args.config)
    if config is None:
        return False
    
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
    
    # 检查数据库连接
    if not check_database_connection(config):
        return False
    
    if args.verify_only:
        # 仅验证数据
        return verify_imported_data(config)
    
    if args.check_only:
        # 仅检查数据
        gdb_file_path = config['test_data']['gdb_file_path']
        if os.path.exists(gdb_file_path):
            analyze_gdb_data(gdb_file_path)
        else:
            print(f"✗ GDB文件不存在: {gdb_file_path}")
        return True
    
    # 执行完整测试流程
    success = test_gdb_import(config)
    
    if success:
        # 验证入库数据
        verify_imported_data(config)
        
        print("\n" + "=" * 70)
        print("测试完成！")
        print("=" * 70)
        print("数据已成功入库到PostGIS数据库")
        print(f"表名:")
        print(f"  - 矢量数据: {config['test_data']['vector_table']}")
        print(f"  - 元数据: {config['test_data']['metadata_table']}")
        print(f"\n可以使用以下SQL查询数据:")
        print(f"  SELECT * FROM {config['test_data']['vector_table']} LIMIT 5;")
        print(f"  SELECT * FROM {config['test_data']['metadata_table']};")
    else:
        print("\n" + "=" * 70)
        print("测试失败！")
        print("=" * 70)
        return False
    
    return True


if __name__ == '__main__':
    main() 