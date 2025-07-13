#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
矢量数据入库PostGIS工具使用示例
"""

import json
from vector_to_postgis import VectorToPostGIS


def example_import_shapefile():
    """示例：导入Shapefile"""
    print("=" * 50)
    print("示例1：导入Shapefile")
    print("=" * 50)
    
    # 配置信息
    config = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'gis_db',
            'username': 'postgres',
            'password': 'your_password'
        },
        'log_level': 'INFO',
        'log_dir': 'logs'
    }
    
    # 创建工具实例
    tool = VectorToPostGIS(config)
    
    # 处理数据
    tool.process_vector_data(
        file_path='/path/to/cities.shp',
        source_crs='EPSG:4326',
        target_crs='EPSG:3857',
        vector_table='cities',
        metadata_table='cities_metadata',
        encoding='utf-8',
        batch_size=1000
    )


def example_import_geojson():
    """示例：导入GeoJSON"""
    print("=" * 50)
    print("示例2：导入GeoJSON")
    print("=" * 50)
    
    config = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'gis_db',
            'username': 'postgres',
            'password': 'your_password'
        },
        'log_level': 'INFO',
        'log_dir': 'logs'
    }
    
    tool = VectorToPostGIS(config)
    
    tool.process_vector_data(
        file_path='/path/to/rivers.geojson',
        source_crs='EPSG:4326',
        target_crs='EPSG:4326',
        vector_table='rivers',
        metadata_table='rivers_metadata',
        encoding='utf-8',
        batch_size=500
    )


def example_import_csv():
    """示例：导入CSV文件"""
    print("=" * 50)
    print("示例3：导入CSV文件")
    print("=" * 50)
    
    config = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'gis_db',
            'username': 'postgres',
            'password': 'your_password'
        },
        'log_level': 'INFO',
        'log_dir': 'logs'
    }
    
    tool = VectorToPostGIS(config)
    
    tool.process_vector_data(
        file_path='/path/to/points.csv',
        source_crs='EPSG:4326',
        target_crs='EPSG:3857',
        vector_table='points',
        metadata_table='points_metadata',
        encoding='gbk',
        batch_size=1000
    )


def example_batch_import():
    """示例：批量导入多个文件"""
    print("=" * 50)
    print("示例4：批量导入多个文件")
    print("=" * 50)
    
    config = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'gis_db',
            'username': 'postgres',
            'password': 'your_password'
        },
        'log_level': 'INFO',
        'log_dir': 'logs'
    }
    
    tool = VectorToPostGIS(config)
    
    # 定义要导入的文件列表
    files_to_import = [
        {
            'file_path': '/path/to/cities.shp',
            'source_crs': 'EPSG:4326',
            'target_crs': 'EPSG:3857',
            'vector_table': 'cities',
            'metadata_table': 'cities_metadata',
            'encoding': 'utf-8'
        },
        {
            'file_path': '/path/to/rivers.geojson',
            'source_crs': 'EPSG:4326',
            'target_crs': 'EPSG:4326',
            'vector_table': 'rivers',
            'metadata_table': 'rivers_metadata',
            'encoding': 'utf-8'
        },
        {
            'file_path': '/path/to/points.csv',
            'source_crs': 'EPSG:4326',
            'target_crs': 'EPSG:3857',
            'vector_table': 'points',
            'metadata_table': 'points_metadata',
            'encoding': 'gbk'
        }
    ]
    
    # 批量处理
    for file_config in files_to_import:
        try:
            print(f"正在处理文件: {file_config['file_path']}")
            tool.process_vector_data(
                file_path=file_config['file_path'],
                source_crs=file_config['source_crs'],
                target_crs=file_config['target_crs'],
                vector_table=file_config['vector_table'],
                metadata_table=file_config['metadata_table'],
                encoding=file_config['encoding'],
                batch_size=1000
            )
            print(f"文件处理完成: {file_config['file_path']}")
        except Exception as e:
            print(f"文件处理失败: {file_config['file_path']}, 错误: {e}")
            continue


def example_with_config_file():
    """示例：使用配置文件"""
    print("=" * 50)
    print("示例5：使用配置文件")
    print("=" * 50)
    
    # 读取配置文件
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 创建工具实例
    tool = VectorToPostGIS(config)
    
    # 处理数据
    tool.process_vector_data(
        file_path='/path/to/data.shp',
        source_crs='EPSG:4326',
        target_crs='EPSG:3857',
        vector_table=config['tables']['vector_table'],
        metadata_table=config['tables']['metadata_table'],
        encoding=config['processing']['encoding'],
        batch_size=config['processing']['batch_size']
    )


if __name__ == '__main__':
    # 运行示例
    print("矢量数据入库PostGIS工具使用示例")
    print("请根据实际情况修改文件路径和数据库连接信息")
    print()
    
    # 取消注释下面的行来运行相应的示例
    # example_import_shapefile()
    # example_import_geojson()
    # example_import_csv()
    # example_batch_import()
    # example_with_config_file()
    
    print("示例代码已准备就绪，请根据实际情况修改参数后运行。") 