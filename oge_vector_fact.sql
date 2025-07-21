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

 Date: 18/07/2025 08:55:57
*/


-- ----------------------------
-- Table structure for oge_vector_fact
-- ----------------------------
DROP TABLE IF EXISTS "public"."oge_vector_fact";
CREATE TABLE "public"."oge_vector_fact" (
  "id" int4 NOT NULL,
  "product_key" int4,
  "fact_data_ids" text COLLATE "pg_catalog"."default",
  "create_by" varchar(32) COLLATE "pg_catalog"."default" DEFAULT NULL::character varying,
  "create_time" timestamp(6),
  "update_by" varchar(32) COLLATE "pg_catalog"."default" DEFAULT NULL::character varying,
  "update_time" timestamp(6),
  "table_name" varchar(255) COLLATE "pg_catalog"."default" NOT NULL,
  "where_store" int4
)
;
ALTER TABLE "public"."oge_vector_fact" OWNER TO "oge";

-- ----------------------------
-- Uniques structure for table oge_vector_fact
-- ----------------------------
ALTER TABLE "public"."oge_vector_fact" ADD CONSTRAINT "oge_vector_tile_fact_id_key" UNIQUE ("id");

-- ----------------------------
-- Primary Key structure for table oge_vector_fact
-- ----------------------------
ALTER TABLE "public"."oge_vector_fact" ADD CONSTRAINT "gc_vector_tile_fact_copy1_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Foreign Keys structure for table oge_vector_fact
-- ----------------------------
ALTER TABLE "public"."oge_vector_fact" ADD CONSTRAINT "oge_vector_tile_fact_product_key_fkey" FOREIGN KEY ("product_key") REFERENCES "public"."oge_data_resource_product" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
