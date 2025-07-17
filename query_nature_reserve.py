#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然保护地数据查询脚本
用于验证入库后的数据
"""

import json
from sqlalchemy import create_engine, text


def query_nature_reserve_data():
    """查询自然保护地数据"""
    
    # 数据库配置
    config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'oge_vector_db',
        'username': 'postgres',
        'password': 'postgres'
    }
    
    try:
        # 连接数据库
        connection_string = (
            f"postgresql://{config['username']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['database']}"
        )
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            print("=" * 60)
            print("自然保护地数据查询结果")
            print("=" * 60)
            
            # 1. 查询记录数
            count_query = "SELECT COUNT(*) FROM nature_reserve_data"
            result = conn.execute(text(count_query))
            count = result.fetchone()[0]
            print(f"✓ 总记录数: {count}")
            
            # 2. 查询所有数据
            data_query = """
            SELECT 
                id,
                properties->>'OBJECTID' as objectid,
                properties->>'mj' as area,
                properties->>'Shape_Length' as length,
                properties->>'Shape_Area' as shape_area,
                ST_AsText(geometry) as geom_text
            FROM nature_reserve_data 
            ORDER BY CAST(properties->>'mj' AS FLOAT) DESC
            """
            result = conn.execute(text(data_query))
            records = result.fetchall()
            
            print(f"\n✓ 数据详情:")
            for record in records:
                print(f"  ID: {record.id}")
                print(f"    OBJECTID: {record.objectid}")
                print(f"    面积(mj): {record.area}")
                print(f"    长度: {record.length}")
                print(f"    形状面积: {record.shape_area}")
                print(f"    几何: {record.geom_text[:100]}...")
                print()
            
            # 3. 面积统计
            stats_query = """
            SELECT 
                COUNT(*) as count,
                SUM(CAST(properties->>'mj' AS FLOAT)) as total_area,
                AVG(CAST(properties->>'mj' AS FLOAT)) as avg_area,
                MAX(CAST(properties->>'mj' AS FLOAT)) as max_area,
                MIN(CAST(properties->>'mj' AS FLOAT)) as min_area
            FROM nature_reserve_data
            """
            result = conn.execute(text(stats_query))
            stats = result.fetchone()
            
            print(f"✓ 面积统计:")
            print(f"  记录数: {stats.count}")
            print(f"  总面积: {stats.total_area:.6f}")
            print(f"  平均面积: {stats.avg_area:.6f}")
            print(f"  最大面积: {stats.max_area:.6f}")
            print(f"  最小面积: {stats.min_area:.6f}")
            
            # 4. 查询元数据
            metadata_query = "SELECT * FROM nature_reserve_metadata ORDER BY id DESC LIMIT 1"
            result = conn.execute(text(metadata_query))
            metadata = result.fetchone()
            
            if metadata:
                print(f"\n✓ 元数据:")
                print(f"  文件名称: {metadata.file_name}")
                print(f"  记录数量: {metadata.feature_count}")
                print(f"  几何类型: {metadata.geometry_type}")
                print(f"  源坐标系: {metadata.source_crs}")
                print(f"  目标坐标系: {metadata.target_crs}")
                print(f"  导入时间: {metadata.import_time}")
            
            print("\n" + "=" * 60)
            print("查询完成！")
            print("=" * 60)
            
    except Exception as e:
        print(f"✗ 查询失败: {e}")
        print("请检查数据库连接和表是否存在")


if __name__ == '__main__':
    query_nature_reserve_data() 