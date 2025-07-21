/*
 Navicat Premium Dump SQL

 Source Server         : 公网山东测绘院
 Source Server Type    : PostgreSQL
 Source Server Version : 140005 (140005)
 Source Host           : 111.37.195.111:7011
 Source Catalog        : oge
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 140005 (140005)
 File Encoding         : 65001

 Date: 18/07/2025 08:58:57
*/


-- ----------------------------
-- Table structure for oge_data_resource_product
-- ----------------------------
DROP TABLE IF EXISTS "public"."oge_data_resource_product";
CREATE TABLE "public"."oge_data_resource_product" (
  "id" int4 NOT NULL DEFAULT nextval('oge_data_resource_product_seq'::regclass),
  "name" varchar(255) COLLATE "pg_catalog"."default",
  "product_type" varchar(30) COLLATE "pg_catalog"."default",
  "dtype" varchar(30) COLLATE "pg_catalog"."default",
  "sensor_key" int4 DEFAULT 0,
  "owner" varchar(32) COLLATE "pg_catalog"."default",
  "registertime" timestamp(6),
  "update_by" varchar(32) COLLATE "pg_catalog"."default",
  "updatetime" timestamp(6),
  "label" text COLLATE "pg_catalog"."default",
  "labelid" int4,
  "description" text COLLATE "pg_catalog"."default",
  "dbid" int4 NOT NULL DEFAULT 0,
  "subject" text COLLATE "pg_catalog"."default",
  "alias" text COLLATE "pg_catalog"."default",
  "land_cover_adapt" int4,
  "data_size" varchar(30) COLLATE "pg_catalog"."default",
  "image_amount" varchar(30) COLLATE "pg_catalog"."default",
  "start_time" text COLLATE "pg_catalog"."default",
  "end_time" text COLLATE "pg_catalog"."default",
  "cover_area" varchar(255) COLLATE "pg_catalog"."default",
  "resolution" varchar(30) COLLATE "pg_catalog"."default",
  "status" int2,
  "sample_code" text COLLATE "pg_catalog"."default",
  "is_publish" bool NOT NULL DEFAULT false,
  "description_en" text COLLATE "pg_catalog"."default",
  "alias_en" text COLLATE "pg_catalog"."default",
  "label_en" text COLLATE "pg_catalog"."default",
  "image_amount_en" varchar(30) COLLATE "pg_catalog"."default",
  "cover_area_en" text COLLATE "pg_catalog"."default",
  "source_type" int2,
  "param" text COLLATE "pg_catalog"."default",
  "themekeywords" text COLLATE "pg_catalog"."default",
  "themekeywords_en" text COLLATE "pg_catalog"."default",
  "tag_ids" varchar(255) COLLATE "pg_catalog"."default",
  "sensor_sort" int2,
  "detail_meta" varchar(255) COLLATE "pg_catalog"."default",
  "map_url" varchar(255) COLLATE "pg_catalog"."default",
  "lower_right_lat" float8,
  "lower_right_long" float8,
  "upper_left_lat" float8,
  "upper_left_long" float8
)
;
ALTER TABLE "public"."oge_data_resource_product" OWNER TO "oge";
COMMENT ON COLUMN "public"."oge_data_resource_product"."id" IS 'product_key';
COMMENT ON COLUMN "public"."oge_data_resource_product"."name" IS 'product_name';
COMMENT ON COLUMN "public"."oge_data_resource_product"."dtype" IS '数据类型，如int8,uint8';
COMMENT ON COLUMN "public"."oge_data_resource_product"."sensor_key" IS 'EPSG:4326';
COMMENT ON COLUMN "public"."oge_data_resource_product"."owner" IS 'create_by';
COMMENT ON COLUMN "public"."oge_data_resource_product"."registertime" IS 'create_time';
COMMENT ON COLUMN "public"."oge_data_resource_product"."updatetime" IS 'update_time';
COMMENT ON COLUMN "public"."oge_data_resource_product"."land_cover_adapt" IS '地表覆盖应用适应等级';
COMMENT ON COLUMN "public"."oge_data_resource_product"."is_publish" IS '该数据是否向外通过OGC API发表';
COMMENT ON COLUMN "public"."oge_data_resource_product"."source_type" IS '数据类型（（类型 0-参数 1-波段 2- 无））';
COMMENT ON COLUMN "public"."oge_data_resource_product"."param" IS '参数/波段信息';
COMMENT ON COLUMN "public"."oge_data_resource_product"."themekeywords" IS '主题关键词
';
COMMENT ON COLUMN "public"."oge_data_resource_product"."themekeywords_en" IS '主题关键词（英文）';
COMMENT ON COLUMN "public"."oge_data_resource_product"."tag_ids" IS 'tag_id 数组';
COMMENT ON COLUMN "public"."oge_data_resource_product"."sensor_sort" IS '同卫星传感器显示排序';
COMMENT ON COLUMN "public"."oge_data_resource_product"."detail_meta" IS '底图服务中心点';
COMMENT ON COLUMN "public"."oge_data_resource_product"."map_url" IS '底图服务地址';

-- ----------------------------
-- Uniques structure for table oge_data_resource_product
-- ----------------------------
ALTER TABLE "public"."oge_data_resource_product" ADD CONSTRAINT "oge_product_product_key_key" UNIQUE ("id");

-- ----------------------------
-- Primary Key structure for table oge_data_resource_product
-- ----------------------------
ALTER TABLE "public"."oge_data_resource_product" ADD CONSTRAINT "lge_product_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Foreign Keys structure for table oge_data_resource_product
-- ----------------------------
ALTER TABLE "public"."oge_data_resource_product" ADD CONSTRAINT "oge_data_resource_product_dbid_fkey" FOREIGN KEY ("dbid") REFERENCES "public"."oge_db_connection" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "public"."oge_data_resource_product" ADD CONSTRAINT "oge_data_resource_product_labelid_fkey" FOREIGN KEY ("labelid") REFERENCES "public"."oge_catalog_scheme" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "public"."oge_data_resource_product" ADD CONSTRAINT "oge_data_resource_product_sensor_key_fkey" FOREIGN KEY ("sensor_key") REFERENCES "public"."oge_sensor" ("sensor_key") ON DELETE NO ACTION ON UPDATE NO ACTION;
