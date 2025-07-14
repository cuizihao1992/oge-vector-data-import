#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用测试脚本：测试vector_to_postgis.py支持的所有矢量数据格式
支持格式：Shapefile, GeoJSON, KML, GML, CSV, GPKG, FileGDB
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

def get_file_info(file_path):
    """获取文件信息"""
    if not os.path.exists(file_path):
        return None
    
    file_size = os.path.getsize(file_path)
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # 对于Shapefile，检查相关文件
    if file_ext == '.shp':
        base_name = os.path.splitext(file_path)[0]
        related_files = []
        for ext in ['.shx', '.dbf', '.prj', '.cpg']:
            if os.path.exists(base_name + ext):
                related_files.append(ext)
        return {
            'exists': True,
            'size': file_size,
            'ext': file_ext,
            'related_files': related_files
        }
    
    return {
        'exists': True,
        'size': file_size,
        'ext': file_ext,
        'related_files': []
    }

def test_format_import(config, file_path, format_name, source_crs="EPSG:4326", target_crs="EPSG:4326"):
    """测试特定格式的文件导入"""
    print(f"\n{'='*60}")
    print(f"测试格式：{format_name}")
    print(f"文件路径：{file_path}")
    print(f"{'='*60}")
    
    # 检查文件
    file_info = get_file_info(file_path)
    if not file_info or not file_info['exists']:
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    print(f"✅ 文件存在")
    print(f"   文件大小：{file_info['size']} 字节")
    print(f"   文件扩展名：{file_info['ext']}")
    
    if file_info['related_files']:
        print(f"   相关文件：{', '.join(file_info['related_files'])}")
    
    # 设置表名
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    vector_table = f"test_{base_name}_data"
    metadata_table = f"test_{base_name}_metadata"
    
    print(f"   矢量数据表：{vector_table}")
    print(f"   元数据表：{metadata_table}")
    
    # 创建工具实例
    try:
        tool = VectorToPostGIS(config)
        print("✅ 工具初始化成功")
    except Exception as e:
        print(f"❌ 工具初始化失败：{e}")
        return False
    
    # 处理数据入库
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
        
        # 验证结果
        try:
            with tool.engine.connect() as conn:
                # 检查矢量数据表
                result = conn.execute(text(f"SELECT COUNT(*) FROM {vector_table}"))
                row = result.fetchone()
                vector_count = row[0] if row else 0
                print(f"   矢量数据表记录数：{vector_count}")
                
                # 检查元数据表
                result = conn.execute(text(f"SELECT COUNT(*) FROM {metadata_table}"))
                row = result.fetchone()
                metadata_count = row[0] if row else 0
                print(f"   元数据表记录数：{metadata_count}")
                
                # 显示元数据信息
                result = conn.execute(text(f"SELECT file_name, feature_count, geometry_type FROM {metadata_table} ORDER BY import_time DESC LIMIT 1"))
                metadata = result.fetchone()
                if metadata:
                    print(f"   最新导入文件：{metadata[0]}")
                    print(f"   要素数量：{metadata[1]}")
                    print(f"   几何类型：{metadata[2]}")
                    
        except Exception as e:
            print(f"⚠️  验证失败：{e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据入库失败：{e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("通用矢量数据格式测试脚本")
    print("支持格式：Shapefile, GeoJSON, KML, GML, CSV, GPKG, FileGDB")
    print("=" * 80)
    
    # 加载配置
    print("1. 加载配置文件...")
    config = load_config()
    print(f"   数据库连接：{config['database']['host']}:{config['database']['port']}")
    print(f"   数据库名：{config['database']['database']}")
    print(f"   用户名：{config['database']['username']}")
    
    # 定义要测试的文件格式
    test_files = [
        # Shapefile格式
        {
            'file_path': 's2_shandong.shp',
            'format_name': 'ESRI Shapefile',
            'description': '山东省边界数据'
        },
        {
            'file_path': 'cities.shp',
            'format_name': 'ESRI Shapefile',
            'description': '城市点数据'
        },
        
        # GeoJSON格式
        {
            'file_path': '12222.geojson',
            'format_name': 'GeoJSON',
            'description': '测试GeoJSON数据'
        },
        {
            'file_path': 'rivers.geojson',
            'format_name': 'GeoJSON',
            'description': '河流线数据'
        },
        
        # KML格式
        {
            'file_path': 'points.kml',
            'format_name': 'KML',
            'description': '兴趣点数据'
        },
        {
            'file_path': 'areas.kml',
            'format_name': 'KML',
            'description': '区域面数据'
        },
        
        # GML格式
        {
            'file_path': 'buildings.gml',
            'format_name': 'GML',
            'description': '建筑物数据'
        },
        
        # CSV格式（需要包含经纬度列）
        {
            'file_path': 'points.csv',
            'format_name': 'CSV',
            'description': '点数据（包含longitude/latitude列）'
        },
        {
            'file_path': 'locations.csv',
            'format_name': 'CSV',
            'description': '位置数据（包含geometry列）'
        },
        
        # GeoPackage格式
        {
            'file_path': 'data.gpkg',
            'format_name': 'GeoPackage',
            'description': 'GeoPackage数据'
        },
        
        # File Geodatabase格式
        {
            'file_path': 'data.gdb',
            'format_name': 'File Geodatabase',
            'description': '文件地理数据库'
        }
    ]
    
    # 统计结果
    total_tests = 0
    successful_tests = 0
    failed_tests = []
    
    print(f"\n2. 开始测试各种格式...")
    print(f"   共 {len(test_files)} 种格式待测试")
    
    # 逐个测试每种格式
    for i, test_file in enumerate(test_files, 1):
        print(f"\n--- 测试 {i}/{len(test_files)} ---")
        print(f"格式：{test_file['format_name']}")
        print(f"描述：{test_file['description']}")
        
        total_tests += 1
        
        # 检查文件是否存在
        if not os.path.exists(test_file['file_path']):
            print(f"⚠️  文件不存在，跳过测试：{test_file['file_path']}")
            failed_tests.append({
                'file': test_file['file_path'],
                'format': test_file['format_name'],
                'reason': '文件不存在'
            })
            continue
        
        # 执行测试
        success = test_format_import(
            config=config,
            file_path=test_file['file_path'],
            format_name=test_file['format_name']
        )
        
        if success:
            successful_tests += 1
        else:
            failed_tests.append({
                'file': test_file['file_path'],
                'format': test_file['format_name'],
                'reason': '导入失败'
            })
    
    # 输出测试结果
    print(f"\n{'='*80}")
    print("测试结果汇总")
    print(f"{'='*80}")
    print(f"总测试数：{total_tests}")
    print(f"成功数：{successful_tests}")
    print(f"失败数：{len(failed_tests)}")
    print(f"成功率：{successful_tests/total_tests*100:.1f}%" if total_tests > 0 else "成功率：0%")
    
    if failed_tests:
        print(f"\n失败详情：")
        for i, failed in enumerate(failed_tests, 1):
            print(f"  {i}. {failed['format']} - {failed['file']}")
            print(f"     原因：{failed['reason']}")
    
    print(f"\n{'='*80}")
    print("测试完成！")
    print(f"{'='*80}")

if __name__ == '__main__':
    main() 