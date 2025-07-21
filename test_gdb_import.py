#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GDB数据入库测试脚本
专门用于测试空间适配OGE数据资料.gdb的入库功能
"""

import os
import sys
import json
import logging
from datetime import datetime
from vector_to_postgis import VectorToPostGIS


def setup_test_config():
    """设置测试配置"""
    config = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'oge_vector_db',  # 数据库名
            'username': 'postgres',       # 用户名
            'password': 'postgres'        # 密码
        },
        'log_level': 'INFO',
        'log_dir': 'logs'
    }
    return config


def test_gdb_import():
    """测试GDB数据入库"""
    
    # 文件路径
    gdb_file_path = "新建文件地理数据库.gdb"
    
    # 检查文件是否存在
    if not os.path.exists(gdb_file_path):
        print(f"错误: GDB文件不存在: {gdb_file_path}")
        return False
    
    # 设置配置
    config = setup_test_config()
    
    # 创建工具实例
    try:
        tool = VectorToPostGIS(config)
        print("✓ 工具初始化成功")
    except Exception as e:
        print(f"✗ 工具初始化失败: {e}")
        return False
    
    # 测试文件格式验证
    try:
        is_valid = tool.validate_file_format(gdb_file_path)
        if is_valid:
            print("✓ 文件格式验证通过")
        else:
            print("✗ 文件格式验证失败")
            return False
    except Exception as e:
        print(f"✗ 文件格式验证出错: {e}")
        return False
    
    # 测试数据读取
    try:
        print("\n开始读取GDB数据...")
        gdf = tool.read_vector_data(gdb_file_path)
        print(f"✓ 数据读取成功，共{len(gdf)}条记录")
        print(f"  字段数量: {len(gdf.columns)}")
        print(f"  字段列表: {list(gdf.columns)}")
        print(f"  坐标系: {gdf.crs}")
        
        # 显示数据预览
        print("\n数据预览:")
        print(gdf.head())
        
        # 显示空值统计
        print("\n空值统计:")
        null_counts = gdf.isnull().sum()
        for col, count in null_counts.items():
            if count > 0:
                print(f"  {col}: {count}")
        
    except Exception as e:
        print(f"✗ 数据读取失败: {e}")
        return False
    
    # 设置坐标系参数
    source_crs = "EPSG:4527"  # 从数据中获取的坐标系
    target_crs = "EPSG:4326"  # 目标坐标系（WGS84）
    
    # 设置表名
    vector_table = "oge_gdb_data"
    metadata_table = "oge_gdb_metadata"
    
    # 执行数据入库
    try:
        print(f"\n开始数据入库...")
        print(f"源坐标系: {source_crs}")
        print(f"目标坐标系: {target_crs}")
        print(f"矢量表: {vector_table}")
        print(f"元数据表: {metadata_table}")
        
        tool.process_vector_data(
            file_path=gdb_file_path,
            source_crs=source_crs,
            target_crs=target_crs,
            vector_table=vector_table,
            metadata_table=metadata_table,
            encoding='utf-8',
            batch_size=1000
        )
        
        print("✓ 数据入库成功！")
        return True
        
    except Exception as e:
        print(f"✗ 数据入库失败: {e}")
        return False


def test_data_verification():
    """验证入库后的数据"""
    print("\n" + "=" * 50)
    print("开始验证入库数据...")
    
    config = setup_test_config()
    vector_table = "oge_gdb_data"
    metadata_table = "oge_gdb_metadata"
    
    try:
        from sqlalchemy import create_engine, text
        
        # 连接数据库
        connection_string = (
            f"postgresql://{config['database']['username']}:{config['database']['password']}"
            f"@{config['database']['host']}:{config['database']['port']}/{config['database']['database']}"
        )
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            # 查询矢量数据
            vector_query = f"SELECT COUNT(*) as count FROM {vector_table}"
            result = conn.execute(text(vector_query))
            vector_count = result.fetchone()[0]
            print(f"✓ 矢量数据记录数: {vector_count}")
            
            # 查询元数据
            metadata_query = f"SELECT * FROM {metadata_table} ORDER BY id DESC LIMIT 1"
            result = conn.execute(text(metadata_query))
            metadata = result.fetchone()
            
            if metadata:
                print(f"✓ 元数据记录:")
                print(f"  文件名称: {metadata.file_name}")
                print(f"  记录数量: {metadata.feature_count}")
                print(f"  几何类型: {metadata.geometry_type}")
                print(f"  源坐标系: {metadata.source_crs}")
                print(f"  目标坐标系: {metadata.target_crs}")
                
                # 解析属性模式
                if metadata.properties_schema:
                    schema = json.loads(metadata.properties_schema)
                    print(f"  属性字段数: {len(schema)}")
                    print(f"  属性字段: {list(schema.keys())}")
            
            # 查询第一条记录的属性
            sample_query = f"SELECT properties FROM {vector_table} LIMIT 1"
            result = conn.execute(text(sample_query))
            sample = result.fetchone()
            
            if sample:
                properties = json.loads(sample.properties)
                print(f"✓ 样本数据属性字段数: {len(properties)}")
                print(f"  属性字段: {list(properties.keys())}")
                
                # 显示部分属性值
                print("  样本属性值:")
                for key, value in list(properties.items())[:5]:  # 只显示前5个
                    print(f"    {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据验证失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("GDB数据入库测试")
    print("=" * 60)
    
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
    
    # 执行入库测试
    success = test_gdb_import()
    
    if success:
        # 执行数据验证
        test_data_verification()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        print("数据已成功入库到PostGIS数据库")
        print("表名:")
        print("  - 矢量数据: oge_gdb_data")
        print("  - 元数据: oge_gdb_metadata")
        print("\n可以使用以下SQL查询数据:")
        print("  SELECT * FROM oge_gdb_data LIMIT 5;")
        print("  SELECT * FROM oge_gdb_metadata;")
    else:
        print("\n" + "=" * 60)
        print("测试失败！")
        print("=" * 60)
        return False
    
    return True


if __name__ == '__main__':
    main() 