/*
 矢量数据产品表设计
 基于 oge_data_resource_product 表结构调整，专门针对矢量数据特点优化
 
 主要调整：
 1. 移除栅格数据专用字段（波段、传感器、分辨率等）
 2. 增加矢量数据专用字段（几何类型、要素数量、属性结构等）
 3. 优化空间范围描述方式
 4. 增加矢量数据特有的管理字段
*/

-- ----------------------------
-- Table structure for oge_vector_data_product
-- ----------------------------
DROP TABLE IF EXISTS "public"."oge_vector_data_product";
CREATE TABLE "public"."oge_vector_data_product" (
  -- 基础信息字段
  "id" int4 NOT NULL DEFAULT nextval('oge_vector_data_product_seq'::regclass),
  "name" varchar(255) COLLATE "pg_catalog"."default" NOT NULL,
  "product_type" varchar(30) COLLATE "pg_catalog"."default" NOT NULL, -- 'vector'
  "data_category" varchar(50) COLLATE "pg_catalog"."default", -- 数据分类：行政区划、道路、水系、建筑物等
  "data_source" varchar(100) COLLATE "pg_catalog"."default", -- 数据来源：测绘、遥感解译、实地调查等
  
  -- 矢量数据专用字段
  "geometry_type" varchar(50) COLLATE "pg_catalog"."default", -- 几何类型：POINT, LINESTRING, POLYGON, MULTI*
  "feature_count" int4 DEFAULT 0, -- 要素数量
  "attribute_count" int4 DEFAULT 0, -- 属性字段数量
  "attribute_schema" jsonb, -- 属性字段结构定义
  "spatial_extent" geometry(POLYGON, 4326), -- 空间范围（多边形）
  "bbox_minx" float8, -- 边界框最小X坐标
  "bbox_miny" float8, -- 边界框最小Y坐标
  "bbox_maxx" float8, -- 边界框最大X坐标
  "bbox_maxy" float8, -- 边界框最大Y坐标
  
  -- 坐标系信息
  "source_crs" varchar(100) COLLATE "pg_catalog"."default", -- 源坐标系
  "target_crs" varchar(100) COLLATE "pg_catalog"."default" DEFAULT 'EPSG:4326', -- 目标坐标系
  "crs_authority" varchar(50) COLLATE "pg_catalog"."default", -- 坐标系权威机构
  
  -- 数据质量信息
  "data_quality_level" int2 DEFAULT 1, -- 数据质量等级：1-5
  "completeness" float4 DEFAULT 1.0, -- 完整性：0-1
  "accuracy" float4, -- 精度（米）
  "update_frequency" varchar(30) COLLATE "pg_catalog"."default", -- 更新频率：实时、日、周、月、年、不定期
  
  -- 文件信息
  "file_format" varchar(30) COLLATE "pg_catalog"."default", -- 文件格式：shp, geojson, gpkg, kml等
  "file_size" bigint, -- 文件大小（字节）
  "file_count" int4 DEFAULT 1, -- 文件数量（对于多文件格式如shp）
  "compression_type" varchar(30) COLLATE "pg_catalog"."default", -- 压缩类型
  
  -- 时间信息
  "data_collection_time" timestamp(6), -- 数据采集时间
  "data_processing_time" timestamp(6), -- 数据处理时间
  "start_time" text COLLATE "pg_catalog"."default", -- 数据时间范围开始
  "end_time" text COLLATE "pg_catalog"."default", -- 数据时间范围结束
  
  -- 管理信息
  "owner" varchar(32) COLLATE "pg_catalog"."default",
  "registertime" timestamp(6) DEFAULT CURRENT_TIMESTAMP,
  "update_by" varchar(32) COLLATE "pg_catalog"."default",
  "updatetime" timestamp(6) DEFAULT CURRENT_TIMESTAMP,
  "status" int2 DEFAULT 1, -- 状态：0-禁用，1-启用，2-维护中
  
  -- 描述信息
  "description" text COLLATE "pg_catalog"."default",
  "description_en" text COLLATE "pg_catalog"."default",
  "label" text COLLATE "pg_catalog"."default",
  "label_en" text COLLATE "pg_catalog"."default",
  "alias" text COLLATE "pg_catalog"."default",
  "alias_en" text COLLATE "pg_catalog"."default",
  "subject" text COLLATE "pg_catalog"."default",
  "themekeywords" text COLLATE "pg_catalog"."default",
  "themekeywords_en" text COLLATE "pg_catalog"."default",
  
  -- 分类信息
  "labelid" int4, -- 分类ID
  "tag_ids" varchar(255) COLLATE "pg_catalog"."default", -- 标签ID数组
  
  -- 发布信息
  "is_publish" bool NOT NULL DEFAULT false, -- 是否发布
  "publish_time" timestamp(6), -- 发布时间
  "access_level" int2 DEFAULT 0, -- 访问级别：0-公开，1-内部，2-受限
  
  -- 服务信息
  "service_url" varchar(255) COLLATE "pg_catalog"."default", -- 服务地址
  "service_type" varchar(30) COLLATE "pg_catalog"."default", -- 服务类型：WFS, WMS, WMTS等
  "api_version" varchar(20) COLLATE "pg_catalog"."default", -- API版本
  
  -- 存储信息
  "dbid" int4 NOT NULL DEFAULT 0, -- 数据库连接ID
  "storage_path" text COLLATE "pg_catalog"."default", -- 存储路径
  "table_name" varchar(255) COLLATE "pg_catalog"."default", -- 存储表名
  
  -- 统计信息
  "total_area" float8, -- 总面积（平方米）
  "total_length" float8, -- 总长度（米）
  "density" float8, -- 要素密度（要素/平方公里）
  
  -- 版本信息
  "version" varchar(20) COLLATE "pg_catalog"."default" DEFAULT '1.0', -- 版本号
  "version_notes" text COLLATE "pg_catalog"."default", -- 版本说明
  
  -- 扩展信息
  "additional_info" jsonb -- 其他扩展信息
);

-- 设置表所有者
ALTER TABLE "public"."oge_vector_data_product" OWNER TO "oge";

-- 添加字段注释
COMMENT ON COLUMN "public"."oge_vector_data_product"."id" IS '产品主键ID';
COMMENT ON COLUMN "public"."oge_vector_data_product"."name" IS '产品名称';
COMMENT ON COLUMN "public"."oge_vector_data_product"."product_type" IS '产品类型，固定为vector';
COMMENT ON COLUMN "public"."oge_vector_data_product"."data_category" IS '数据分类：行政区划、道路、水系、建筑物、土地利用等';
COMMENT ON COLUMN "public"."oge_vector_data_product"."data_source" IS '数据来源：测绘、遥感解译、实地调查、第三方等';
COMMENT ON COLUMN "public"."oge_vector_data_product"."geometry_type" IS '几何类型：POINT, LINESTRING, POLYGON, MULTIPOINT, MULTILINESTRING, MULTIPOLYGON等';
COMMENT ON COLUMN "public"."oge_vector_data_product"."feature_count" IS '要素数量';
COMMENT ON COLUMN "public"."oge_vector_data_product"."attribute_count" IS '属性字段数量';
COMMENT ON COLUMN "public"."oge_vector_data_product"."attribute_schema" IS '属性字段结构定义，JSON格式';
COMMENT ON COLUMN "public"."oge_vector_data_product"."spatial_extent" IS '空间范围多边形';
COMMENT ON COLUMN "public"."oge_vector_data_product"."source_crs" IS '源坐标系';
COMMENT ON COLUMN "public"."oge_vector_data_product"."target_crs" IS '目标坐标系';
COMMENT ON COLUMN "public"."oge_vector_data_product"."data_quality_level" IS '数据质量等级：1-低，2-中低，3-中，4-中高，5-高';
COMMENT ON COLUMN "public"."oge_vector_data_product"."completeness" IS '数据完整性：0-1之间的数值';
COMMENT ON COLUMN "public"."oge_vector_data_product"."accuracy" IS '数据精度（米）';
COMMENT ON COLUMN "public"."oge_vector_data_product"."update_frequency" IS '更新频率';
COMMENT ON COLUMN "public"."oge_vector_data_product"."file_format" IS '文件格式';
COMMENT ON COLUMN "public"."oge_vector_data_product"."file_size" IS '文件大小（字节）';
COMMENT ON COLUMN "public"."oge_vector_data_product"."data_collection_time" IS '数据采集时间';
COMMENT ON COLUMN "public"."oge_vector_data_product"."data_processing_time" IS '数据处理时间';
COMMENT ON COLUMN "public"."oge_vector_data_product"."status" IS '状态：0-禁用，1-启用，2-维护中';
COMMENT ON COLUMN "public"."oge_vector_data_product"."is_publish" IS '是否通过OGC API发布';
COMMENT ON COLUMN "public"."oge_vector_data_product"."access_level" IS '访问级别：0-公开，1-内部，2-受限';
COMMENT ON COLUMN "public"."oge_vector_data_product"."service_url" IS '服务地址';
COMMENT ON COLUMN "public"."oge_vector_data_product"."service_type" IS '服务类型：WFS, WMS, WMTS等';
COMMENT ON COLUMN "public"."oge_vector_data_product"."storage_path" IS '存储路径';
COMMENT ON COLUMN "public"."oge_vector_data_product"."table_name" IS '存储表名';
COMMENT ON COLUMN "public"."oge_vector_data_product"."total_area" IS '总面积（平方米）';
COMMENT ON COLUMN "public"."oge_vector_data_product"."total_length" IS '总长度（米）';
COMMENT ON COLUMN "public"."oge_vector_data_product"."density" IS '要素密度（要素/平方公里）';
COMMENT ON COLUMN "public"."oge_vector_data_product"."version" IS '版本号';
COMMENT ON COLUMN "public"."oge_vector_data_product"."additional_info" IS '其他扩展信息，JSON格式';

-- ----------------------------
-- 索引结构
-- ----------------------------
-- 主键
ALTER TABLE "public"."oge_vector_data_product" ADD CONSTRAINT "oge_vector_data_product_pkey" PRIMARY KEY ("id");

-- 唯一约束
ALTER TABLE "public"."oge_vector_data_product" ADD CONSTRAINT "oge_vector_data_product_name_key" UNIQUE ("name");

-- 空间索引
CREATE INDEX "idx_oge_vector_data_product_spatial_extent" ON "public"."oge_vector_data_product" USING GIST ("spatial_extent");

-- 其他索引
CREATE INDEX "idx_oge_vector_data_product_category" ON "public"."oge_vector_data_product" ("data_category");
CREATE INDEX "idx_oge_vector_data_product_type" ON "public"."oge_vector_data_product" ("geometry_type");
CREATE INDEX "idx_oge_vector_data_product_status" ON "public"."oge_vector_data_product" ("status");
CREATE INDEX "idx_oge_vector_data_product_publish" ON "public"."oge_vector_data_product" ("is_publish");
CREATE INDEX "idx_oge_vector_data_product_owner" ON "public"."oge_vector_data_product" ("owner");
CREATE INDEX "idx_oge_vector_data_product_registertime" ON "public"."oge_vector_data_product" ("registertime");

-- ----------------------------
-- 外键约束
-- ----------------------------
ALTER TABLE "public"."oge_vector_data_product" ADD CONSTRAINT "oge_vector_data_product_dbid_fkey" 
    FOREIGN KEY ("dbid") REFERENCES "public"."oge_db_connection" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

ALTER TABLE "public"."oge_vector_data_product" ADD CONSTRAINT "oge_vector_data_product_labelid_fkey" 
    FOREIGN KEY ("labelid") REFERENCES "public"."oge_catalog_scheme" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- 触发器：自动更新时间戳
-- ----------------------------
CREATE OR REPLACE FUNCTION update_vector_product_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updatetime = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_update_vector_product_timestamp 
    BEFORE UPDATE ON "public"."oge_vector_data_product"
    FOR EACH ROW EXECUTE FUNCTION update_vector_product_timestamp();

-- ----------------------------
-- 示例数据
-- ----------------------------
INSERT INTO "public"."oge_vector_data_product" (
    "name", "product_type", "data_category", "data_source", 
    "geometry_type", "feature_count", "attribute_count",
    "source_crs", "target_crs", "file_format", "status",
    "description", "is_publish", "owner"
) VALUES (
    '山东省城镇开发边界', 'vector', '规划边界', '测绘数据',
    'MULTIPOLYGON', 1, 20,
    'EPSG:4490', 'EPSG:4326', 'shp', 1,
    '山东省城镇开发边界矢量数据，包含行政区划、面积等属性信息', false, 'oge'
); 