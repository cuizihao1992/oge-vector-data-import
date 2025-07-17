#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据完整性测试脚本
验证矢量数据入库后是否保留了所有属性信息
"""

import os
import sys
import json
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
import psycopg2
from psycopg2.extras import RealDictCursor


def test_data_integrity(config, vector_table, metadata_table, original_file_path):
    """
    测试数据完整性
    
    Args:
        config: 数据库配置
        vector_table: 矢量数据表名
        metadata_table: 元数据表名
        original_file_path: 原始文件路径
    """
    
    # 连接数据库
    connection_string = (
        f"postgresql://{config['database']['username']}:{config['database']['password']}"
        f"@{config['database']['host']}:{config['database']['port']}/{config['database']['database']}"
    )
    engine = create_engine(connection_string)
    
    # 读取原始数据
    print("=" * 50)
    print("读取原始数据...")
    original_gdf = gpd.read_file(original_file_path)
    print(f"原始数据记录数: {len(original_gdf)}")
    print(f"原始数据字段: {list(original_gdf.columns)}")
    
    # 统计原始数据的空值
    original_null_counts = {}
    for col in original_gdf.columns:
        if col != 'geometry':
            original_null_counts[col] = original_gdf[col].isnull().sum()
    
    print("原始数据空值统计:")
    for col, count in original_null_counts.items():
        print(f"  {col}: {count}")
    
    # 从数据库读取数据
    print("\n" + "=" * 50)
    print("从数据库读取数据...")
    
    with engine.connect() as conn:
        # 查询矢量数据
        query = f"SELECT * FROM {vector_table} ORDER BY id LIMIT 10"
        result = conn.execute(text(query))
        db_records = result.fetchall()
        
        print(f"数据库记录数: {len(db_records)}")
        
        if db_records:
            # 分析第一条记录的属性
            first_record = db_records[0]
            properties = json.loads(first_record.properties)
            
            print(f"数据库字段数: {len(properties)}")
            print(f"数据库字段: {list(properties.keys())}")
            
            # 统计数据库中的空值
            db_null_counts = {}
            for col in properties.keys():
                null_count = 0
                for record in db_records:
                    record_props = json.loads(record.properties)
                    if col in record_props and record_props[col] is None:
                        null_count += 1
                db_null_counts[col] = null_count
            
            print("数据库空值统计:")
            for col, count in db_null_counts.items():
                print(f"  {col}: {count}")
            
            # 比较字段数量
            print("\n" + "=" * 50)
            print("数据完整性检查结果:")
            
            original_fields = set(original_gdf.columns) - {'geometry'}
            db_fields = set(properties.keys())
            
            if original_fields == db_fields:
                print("✓ 字段数量一致")
            else:
                print("✗ 字段数量不一致")
                print(f"  原始字段: {original_fields}")
                print(f"  数据库字段: {db_fields}")
                print(f"  缺失字段: {original_fields - db_fields}")
                print(f"  多余字段: {db_fields - original_fields}")
            
            # 比较空值统计
            print("\n空值统计比较:")
            for col in original_fields:
                if col in db_null_counts:
                    if original_null_counts[col] == db_null_counts[col]:
                        print(f"✓ {col}: 空值数量一致 ({original_null_counts[col]})")
                    else:
                        print(f"✗ {col}: 空值数量不一致 (原始: {original_null_counts[col]}, 数据库: {db_null_counts[col]})")
                else:
                    print(f"✗ {col}: 字段在数据库中不存在")
        
        # 查询元数据
        metadata_query = f"SELECT * FROM {metadata_table} ORDER BY id DESC LIMIT 1"
        metadata_result = conn.execute(text(metadata_query))
        metadata_record = metadata_result.fetchone()
        
        if metadata_record:
            print("\n" + "=" * 50)
            print("元数据信息:")
            print(f"文件名称: {metadata_record.file_name}")
            print(f"记录数量: {metadata_record.feature_count}")
            print(f"几何类型: {metadata_record.geometry_type}")
            
            # 解析属性模式
            if metadata_record.properties_schema:
                schema = json.loads(metadata_record.properties_schema)
                print(f"属性模式: {schema}")
            
            # 解析附加信息
            if metadata_record.additional_info:
                additional = json.loads(metadata_record.additional_info)
                if 'null_counts' in additional:
                    print("元数据中的空值统计:")
                    for col, count in additional['null_counts'].items():
                        print(f"  {col}: {count}")


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python test_data_integrity.py <原始文件路径>")
        sys.exit(1)
    
    original_file_path = sys.argv[1]
    
    if not os.path.exists(original_file_path):
        print(f"文件不存在: {original_file_path}")
        sys.exit(1)
    
    # 数据库配置（需要根据实际情况修改）
    config = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'your_database',
            'username': 'your_username',
            'password': 'your_password'
        }
    }
    
    vector_table = 'vector_data'
    metadata_table = 'vector_metadata'
    
    try:
        test_data_integrity(config, vector_table, metadata_table, original_file_path)
    except Exception as e:
        print(f"测试失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 