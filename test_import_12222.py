#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：将12222.geojson文件入库到PostGIS数据库
"""

import json
import os
import sys
from vector_to_postgis import VectorToPostGIS


def load_config():
    """加载配置文件"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"配置文件加载失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    print("=" * 60)
    print("开始测试：12222.geojson文件入库")
    print("=" * 60)
    
    # 1. 加载配置
    print("1. 加载配置文件...")
    config = load_config()
    print(f"   数据库连接: {config['database']['host']}:{config['database']['port']}")
    print(f"   数据库名: {config['database']['database']}")
    print(f"   用户名: {config['database']['username']}")
    
    # 2. 设置文件路径和参数
    file_path = "12222.geojson"
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在")
        sys.exit(1)
    
    print(f"2. 检查文件: {file_path}")
    print(f"   文件大小: {os.path.getsize(file_path)} 字节")
    
    # 3. 设置坐标系参数
    # 根据GeoJSON文件内容，坐标看起来是WGS84经纬度
    source_crs = "EPSG:4326"  # WGS84经纬度坐标系
    target_crs = "EPSG:4326"  # 保持WGS84坐标系
    
    # 4. 设置表名
    vector_table = "test_12222_data"  # 新建的矢量数据表
    metadata_table = "test_12222_metadata"  # 新建的元数据表
    
    print(f"3. 设置参数:")
    print(f"   源坐标系: {source_crs}")
    print(f"   目标坐标系: {target_crs}")
    print(f"   矢量数据表: {vector_table}")
    print(f"   元数据表: {metadata_table}")
    
    # 5. 创建工具实例
    print("4. 初始化工具...")
    try:
        tool = VectorToPostGIS(config)
        print("   工具初始化成功")
    except Exception as e:
        print(f"   工具初始化失败: {e}")
        sys.exit(1)
    
    # 6. 处理数据入库
    print("5. 开始数据入库...")
    try:
        tool.process_vector_data(
            file_path=file_path,
            source_crs=source_crs,
            target_crs=target_crs,
            vector_table=vector_table,
            metadata_table=metadata_table,
            encoding='utf-8',
            batch_size=1000
        )
        print("   数据入库成功！")
        
    except Exception as e:
        print(f"   数据入库失败: {e}")
        sys.exit(1)
    
    # 7. 验证结果
    print("6. 验证入库结果...")
    try:
        with tool.engine.connect() as conn:
            # 检查矢量数据表
            result = conn.execute(tool.engine.text(f"SELECT COUNT(*) FROM {vector_table}"))
            vector_count = result.fetchone()[0]
            print(f"   矢量数据表记录数: {vector_count}")
            
            # 检查元数据表
            result = conn.execute(tool.engine.text(f"SELECT COUNT(*) FROM {metadata_table}"))
            metadata_count = result.fetchone()[0]
            print(f"   元数据表记录数: {metadata_count}")
            
            # 显示元数据信息
            result = conn.execute(tool.engine.text(f"SELECT file_name, feature_count, geometry_type FROM {metadata_table} ORDER BY import_time DESC LIMIT 1"))
            metadata = result.fetchone()
            if metadata:
                print(f"   最新导入文件: {metadata[0]}")
                print(f"   要素数量: {metadata[1]}")
                print(f"   几何类型: {metadata[2]}")
                
    except Exception as e:
        print(f"   验证失败: {e}")
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    main() 