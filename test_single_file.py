#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单文件测试脚本：测试任意矢量文件导入PostGIS
使用方法：修改下面的 file_path 变量为你要测试的文件路径
"""

import json
import os
import sys
from sqlalchemy import text
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
    print("单文件矢量数据导入测试")
    print("=" * 60)
    
    # ========== 在这里修改你要测试的文件路径 ==========
    file_path = "s2_shandong.shp"  # 修改为你的文件路径
    # ================================================
    
    # 1. 加载配置
    print("1. 加载配置文件...")
    config = load_config()
    print(f"   数据库连接: {config['database']['host']}:{config['database']['port']}")
    print(f"   数据库名: {config['database']['database']}")
    print(f"   用户名: {config['database']['username']}")
    
    # 2. 检查文件
    if not os.path.exists(file_path):
        print(f"❌ 错误：文件 {file_path} 不存在")
        print("请检查文件路径是否正确，或修改脚本中的 file_path 变量")
        sys.exit(1)
    
    print(f"2. 检查文件: {file_path}")
    print(f"   文件大小: {os.path.getsize(file_path)} 字节")
    
    # 检查文件扩展名
    file_ext = os.path.splitext(file_path)[1].lower()
    print(f"   文件扩展名: {file_ext}")
    
    # 对于Shapefile，检查相关文件
    if file_ext == '.shp':
        base_name = os.path.splitext(file_path)[0]
        missing_files = []
        for ext in ['.shx', '.dbf']:
            if not os.path.exists(base_name + ext):
                missing_files.append(ext)
        
        if missing_files:
            print(f"⚠️  警告：缺少Shapefile必需文件: {', '.join(missing_files)}")
            print("   这可能导致导入失败")
        else:
            print("✅ Shapefile相关文件完整")
    
    # 3. 设置坐标系参数
    # 根据文件类型设置默认坐标系
    if file_ext in ['.shp', '.geojson', '.json', '.kml', '.gml']:
        source_crs = "EPSG:4326"  # 通常这些格式使用WGS84
    elif file_ext == '.csv':
        source_crs = "EPSG:4326"  # CSV通常包含经纬度
    else:
        source_crs = "EPSG:4326"  # 默认WGS84
    
    target_crs = "EPSG:4326"  # 保持WGS84坐标系
    
    print(f"3. 设置坐标系:")
    print(f"   源坐标系: {source_crs}")
    print(f"   目标坐标系: {target_crs}")
    
    # 4. 设置表名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    vector_table = f"test_{base_name}_data"
    metadata_table = f"test_{base_name}_metadata"
    
    print(f"4. 设置表名:")
    print(f"   矢量数据表: {vector_table}")
    print(f"   元数据表: {metadata_table}")
    
    # 5. 创建工具实例
    print("5. 初始化工具...")
    try:
        tool = VectorToPostGIS(config)
        print("✅ 工具初始化成功")
    except Exception as e:
        print(f"❌ 工具初始化失败: {e}")
        sys.exit(1)
    
    # 6. 处理数据入库
    print("6. 开始数据入库...")
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
        print("✅ 数据入库成功！")
        
    except Exception as e:
        print(f"❌ 数据入库失败: {e}")
        print("\n可能的解决方案：")
        print("1. 检查文件格式是否正确")
        print("2. 检查文件是否损坏")
        print("3. 对于Shapefile，确保有.shx和.dbf文件")
        print("4. 对于CSV，确保包含geometry列或longitude/latitude列")
        print("5. 检查坐标系设置是否正确")
        sys.exit(1)
    
    # 7. 验证结果
    print("7. 验证入库结果...")
    try:
        with tool.engine.connect() as conn:
            # 检查矢量数据表
            result = conn.execute(text(f"SELECT COUNT(*) FROM {vector_table}"))
            row = result.fetchone()
            vector_count = row[0] if row else 0
            print(f"   矢量数据表记录数: {vector_count}")
            
            # 检查元数据表
            result = conn.execute(text(f"SELECT COUNT(*) FROM {metadata_table}"))
            row = result.fetchone()
            metadata_count = row[0] if row else 0
            print(f"   元数据表记录数: {metadata_count}")
            
            # 显示元数据信息
            result = conn.execute(text(f"SELECT file_name, feature_count, geometry_type FROM {metadata_table} ORDER BY import_time DESC LIMIT 1"))
            metadata = result.fetchone()
            if metadata:
                print(f"   最新导入文件: {metadata[0]}")
                print(f"   要素数量: {metadata[1]}")
                print(f"   几何类型: {metadata[2]}")
                
    except Exception as e:
        print(f"⚠️  验证失败: {e}")
    
    print("=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

if __name__ == '__main__':
    main() 