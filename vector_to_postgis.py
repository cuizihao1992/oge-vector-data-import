#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
矢量数据入库PostGIS工具
支持多种矢量格式：Shapefile, GeoJSON, KML, GML, CSV等
具备坐标系转换功能
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2.extras import RealDictCursor
import fiona
from shapely.geometry import shape
from shapely.ops import transform
import pyproj
from pyproj import CRS, Transformer


class VectorToPostGIS:
    """矢量数据入库PostGIS工具类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化工具类
        
        Args:
            config: 配置字典，包含数据库连接等信息
        """
        self.config = config
        self.setup_logging()
        self.setup_database_connection()
        
    def setup_logging(self):
        """设置日志"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        
        # 创建日志目录
        log_dir = self.config.get('log_dir', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 日志文件名包含时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'vector_import_{timestamp}.log')
        
        # 配置日志格式
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("矢量数据入库工具初始化完成")
        
    def setup_database_connection(self):
        """设置数据库连接"""
        try:
            # 构建数据库连接字符串
            db_config = self.config['database']
            connection_string = (
                f"postgresql://{db_config['username']}:{db_config['password']}"
                f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            )
            
            self.engine = create_engine(connection_string)
            self.logger.info("数据库连接建立成功")
            
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise
            
    def get_supported_formats(self) -> List[str]:
        """获取支持的矢量数据格式"""
        return fiona.supported_drivers.keys()
        
    def validate_file_format(self, file_path: str) -> bool:
        """验证文件格式是否支持"""
        supported_formats = self.get_supported_formats()
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # 常见格式映射
        format_mapping = {
            '.shp': 'ESRI Shapefile',
            '.geojson': 'GeoJSON',
            '.json': 'GeoJSON',
            '.kml': 'KML',
            '.gml': 'GML',
            '.csv': 'CSV',
            '.gpkg': 'GPKG',
            '.gdb': 'OpenFileGDB'
        }
        
        if file_ext in format_mapping:
            return format_mapping[file_ext] in supported_formats
        return False
        
    def read_vector_data(self, file_path: str, encoding: str = 'utf-8') -> gpd.GeoDataFrame:
        """
        读取矢量数据
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            
        Returns:
            GeoDataFrame对象
        """
        try:
            self.logger.info(f"开始读取文件: {file_path}")
            
            # 根据文件类型选择读取方式
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                # CSV文件需要特殊处理
                df = pd.read_csv(file_path, encoding=encoding)
                # 假设有geometry列或经纬度列
                if 'geometry' in df.columns:
                    gdf = gpd.GeoDataFrame(df, geometry='geometry')
                elif 'longitude' in df.columns and 'latitude' in df.columns:
                    gdf = gpd.GeoDataFrame(
                        df, 
                        geometry=gpd.points_from_xy(df.longitude, df.latitude)
                    )
                else:
                    raise ValueError("CSV文件必须包含geometry列或longitude/latitude列")
            else:
                # 其他格式使用geopandas读取
                gdf = gpd.read_file(file_path, encoding=encoding)
                
            self.logger.info(f"文件读取成功，共{len(gdf)}条记录")
            return gdf
            
        except Exception as e:
            self.logger.error(f"文件读取失败: {e}")
            raise
            
    def transform_coordinate_system(self, gdf: gpd.GeoDataFrame, 
                                  source_crs: str, target_crs: str) -> gpd.GeoDataFrame:
        """
        坐标系转换
        
        Args:
            gdf: GeoDataFrame对象
            source_crs: 源坐标系
            target_crs: 目标坐标系
            
        Returns:
            转换后的GeoDataFrame
        """
        try:
            self.logger.info(f"开始坐标系转换: {source_crs} -> {target_crs}")
            
            # 设置源坐标系
            if gdf.crs is None:
                gdf.set_crs(source_crs, inplace=True)
            elif str(gdf.crs) != source_crs:
                self.logger.warning(f"文件坐标系({gdf.crs})与指定源坐标系({source_crs})不一致")
                
            # 执行坐标系转换
            gdf_transformed = gdf.to_crs(target_crs)
            
            self.logger.info("坐标系转换完成")
            return gdf_transformed
            
        except Exception as e:
            self.logger.error(f"坐标系转换失败: {e}")
            raise
            
    def create_tables(self, vector_table: str, metadata_table: str):
        """
        创建数据表和元数据表
        
        Args:
            vector_table: 矢量数据表名
            metadata_table: 元数据表名
        """
        try:
            with self.engine.connect() as conn:
                # 创建矢量数据表（如果不存在）
                vector_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {vector_table} (
                    id SERIAL PRIMARY KEY,
                    geometry GEOMETRY(GEOMETRY, 4326),
                    properties JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- 创建空间索引
                CREATE INDEX IF NOT EXISTS idx_{vector_table}_geometry 
                ON {vector_table} USING GIST (geometry);
                
                -- 创建JSONB索引
                CREATE INDEX IF NOT EXISTS idx_{vector_table}_properties 
                ON {vector_table} USING GIN (properties);
                """
                
                # 创建元数据表（如果不存在）
                metadata_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {metadata_table} (
                    id SERIAL PRIMARY KEY,
                    file_name VARCHAR(255),
                    file_path TEXT,
                    file_size BIGINT,
                    file_format VARCHAR(50),
                    source_crs VARCHAR(100),
                    target_crs VARCHAR(100),
                    feature_count INTEGER,
                    geometry_type VARCHAR(50),
                    bbox_minx DOUBLE PRECISION,
                    bbox_miny DOUBLE PRECISION,
                    bbox_maxx DOUBLE PRECISION,
                    bbox_maxy DOUBLE PRECISION,
                    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    properties_schema JSONB,
                    additional_info JSONB
                );
                """
                
                conn.execute(text(vector_table_sql))
                conn.execute(text(metadata_table_sql))
                conn.commit()
                
            self.logger.info(f"数据表创建成功: {vector_table}, {metadata_table}")
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据表创建失败: {e}")
            raise
            
    def extract_metadata(self, gdf: gpd.GeoDataFrame, file_path: str, 
                        source_crs: str, target_crs: str) -> Dict[str, Any]:
        """
        提取数据元信息
        
        Args:
            gdf: GeoDataFrame对象
            file_path: 文件路径
            source_crs: 源坐标系
            target_crs: 目标坐标系
            
        Returns:
            元数据字典
        """
        try:
            # 获取文件信息
            file_stat = os.stat(file_path)
            
            # 获取几何信息
            bbox = gdf.total_bounds  # [minx, miny, maxx, maxy]
            geometry_types = gdf.geometry.geom_type.unique()
            
            # 获取属性字段信息
            properties_schema = {}
            for col in gdf.columns:
                if col != 'geometry':
                    properties_schema[col] = str(gdf[col].dtype)
                    
            metadata = {
                'file_name': os.path.basename(file_path),
                'file_path': file_path,
                'file_size': int(file_stat.st_size),
                'file_format': os.path.splitext(file_path)[1].lower(),
                'source_crs': source_crs,
                'target_crs': target_crs,
                'feature_count': int(len(gdf)),
                'geometry_type': ','.join(geometry_types),
                'bbox_minx': float(bbox[0]),
                'bbox_miny': float(bbox[1]),
                'bbox_maxx': float(bbox[2]),
                'bbox_maxy': float(bbox[3]),
                'properties_schema': json.dumps(properties_schema, ensure_ascii=False),
                'additional_info': json.dumps({
                    'crs_info': str(gdf.crs),
                    'memory_usage': int(gdf.memory_usage(deep=True).sum()),
                    'null_counts': gdf.isnull().sum().to_dict()
                }, ensure_ascii=False)
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"元数据提取失败: {e}")
            raise
            
    def insert_data(self, gdf: gpd.GeoDataFrame, vector_table: str, 
                   metadata: Dict[str, Any], metadata_table: str,
                   batch_size: int = 1000):
        """
        插入数据到数据库
        
        Args:
            gdf: GeoDataFrame对象
            vector_table: 矢量数据表名
            metadata: 元数据字典
            metadata_table: 元数据表名
            batch_size: 批量插入大小
        """
        try:
            self.logger.info("开始数据入库...")
            
            with self.engine.connect() as conn:
                # 插入元数据
                metadata_sql = f"""
                INSERT INTO {metadata_table} (
                    file_name, file_path, file_size, file_format, source_crs, target_crs,
                    feature_count, geometry_type, bbox_minx, bbox_miny, bbox_maxx, bbox_maxy,
                    properties_schema, additional_info
                ) VALUES (
                    :file_name, :file_path, :file_size, :file_format, :source_crs, :target_crs,
                    :feature_count, :geometry_type, :bbox_minx, :bbox_miny, :bbox_maxx, :bbox_maxy,
                    :properties_schema, :additional_info
                ) RETURNING id;
                """
                
                result = conn.execute(text(metadata_sql), metadata)
                metadata_id = result.fetchone()[0]
                conn.commit()
                
                self.logger.info(f"元数据插入成功，ID: {metadata_id}")
                
                # 批量插入矢量数据
                total_features = len(gdf)
                inserted_count = 0
                
                for i in range(0, total_features, batch_size):
                    batch_gdf = gdf.iloc[i:i+batch_size]
                    
                    # 准备批量插入数据
                    batch_data = []
                    for idx, row in batch_gdf.iterrows():
                        # 提取几何和属性
                        geometry = row.geometry
                        properties = row.drop('geometry').to_dict()
                        
                        # 处理NaN值
                        properties = {k: v for k, v in properties.items() 
                                    if pd.notna(v)}
                        
                        batch_data.append({
                            'geometry': geometry.wkt,
                            'properties': json.dumps(properties, ensure_ascii=False)
                        })
                    
                    # 批量插入
                    if batch_data:
                        insert_sql = f"""
                        INSERT INTO {vector_table} (geometry, properties)
                        VALUES (:geometry, :properties);
                        """
                        
                        conn.execute(text(insert_sql), batch_data)
                        conn.commit()
                        
                        inserted_count += len(batch_data)
                        self.logger.info(f"已插入 {inserted_count}/{total_features} 条记录")
                        
                self.logger.info(f"数据入库完成，共插入 {inserted_count} 条记录")
                
        except SQLAlchemyError as e:
            self.logger.error(f"数据插入失败: {e}")
            raise
            
    def process_vector_data(self, file_path: str, source_crs: str, target_crs: str,
                          vector_table: str, metadata_table: str, 
                          encoding: str = 'utf-8', batch_size: int = 1000):
        """
        处理矢量数据入库的主流程
        
        Args:
            file_path: 文件路径
            source_crs: 源坐标系
            target_crs: 目标坐标系
            vector_table: 矢量数据表名
            metadata_table: 元数据表名
            encoding: 文件编码
            batch_size: 批量插入大小
        """
        try:
            self.logger.info("=" * 50)
            self.logger.info(f"开始处理文件: {file_path}")
            self.logger.info("=" * 50)
            
            # 1. 验证文件格式
            if not self.validate_file_format(file_path):
                raise ValueError(f"不支持的文件格式: {file_path}")
                
            # 2. 读取数据
            gdf = self.read_vector_data(file_path, encoding)
            
            # 3. 坐标系转换
            gdf_transformed = self.transform_coordinate_system(gdf, source_crs, target_crs)
            
            # 4. 创建数据表
            self.create_tables(vector_table, metadata_table)
            
            # 5. 提取元数据
            metadata = self.extract_metadata(gdf_transformed, file_path, source_crs, target_crs)
            
            # 6. 插入数据
            self.insert_data(gdf_transformed, vector_table, metadata, metadata_table, batch_size)
            
            self.logger.info("=" * 50)
            self.logger.info("数据处理完成")
            self.logger.info("=" * 50)
            
        except Exception as e:
            self.logger.error(f"数据处理失败: {e}")
            raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='矢量数据入库PostGIS工具')
    
    # 必需参数
    parser.add_argument('--file_path', required=True, help='矢量文件路径')
    parser.add_argument('--source_crs', required=True, help='源坐标系 (如: EPSG:4326)')
    parser.add_argument('--target_crs', required=True, help='目标坐标系 (如: EPSG:4326)')
    
    # 数据库参数
    parser.add_argument('--db_host', default='localhost', help='数据库主机')
    parser.add_argument('--db_port', default=5432, type=int, help='数据库端口')
    parser.add_argument('--db_name', required=True, help='数据库名')
    parser.add_argument('--db_user', required=True, help='数据库用户名')
    parser.add_argument('--db_password', required=True, help='数据库密码')
    
    # 表名参数
    parser.add_argument('--vector_table', default='vector_data', help='矢量数据表名')
    parser.add_argument('--metadata_table', default='vector_metadata', help='元数据表名')
    
    # 其他参数
    parser.add_argument('--encoding', default='utf-8', help='文件编码')
    parser.add_argument('--batch_size', default=1000, type=int, help='批量插入大小')
    parser.add_argument('--log_level', default='INFO', help='日志级别')
    parser.add_argument('--log_dir', default='logs', help='日志目录')
    
    args = parser.parse_args()
    
    # 构建配置字典
    config = {
        'database': {
            'host': args.db_host,
            'port': args.db_port,
            'database': args.db_name,
            'username': args.db_user,
            'password': args.db_password
        },
        'log_level': args.log_level,
        'log_dir': args.log_dir
    }
    
    try:
        # 创建工具实例
        tool = VectorToPostGIS(config)
        
        # 处理数据
        tool.process_vector_data(
            file_path=args.file_path,
            source_crs=args.source_crs,
            target_crs=args.target_crs,
            vector_table=args.vector_table,
            metadata_table=args.metadata_table,
            encoding=args.encoding,
            batch_size=args.batch_size
        )
        
        print("数据入库成功！")
        
    except Exception as e:
        print(f"数据入库失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 