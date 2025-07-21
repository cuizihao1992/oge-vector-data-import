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

 Date: 18/07/2025 09:05:20
*/


-- ----------------------------
-- Table structure for shp_chengzhenkaifa
-- ----------------------------
DROP TABLE IF EXISTS "public"."shp_chengzhenkaifa";
CREATE TABLE "public"."shp_chengzhenkaifa" (
  "id" int4 NOT NULL DEFAULT nextval('shp_chengzhenkaifa_id_seq'::regclass),
  "geom" geometry(MULTIPOLYGON, 4490),
  "objectid_1" numeric,
  "bsm" varchar(18) COLLATE "pg_catalog"."default",
  "ysdm" varchar(10) COLLATE "pg_catalog"."default",
  "xzqdm" varchar(12) COLLATE "pg_catalog"."default",
  "xzqmc" varchar(100) COLLATE "pg_catalog"."default",
  "ghfqdm" varchar(3) COLLATE "pg_catalog"."default",
  "ghfqmc" varchar(50) COLLATE "pg_catalog"."default",
  "bz" varchar(254) COLLATE "pg_catalog"."default",
  "mj_ys" numeric,
  "mj_ys_doub" numeric,
  "mj_tq" numeric,
  "mj" numeric,
  "shape_leng" numeric,
  "objectid" numeric,
  "objectid_2" int8,
  "objectid_3" int8,
  "shape_le_1" numeric,
  "shape_le_2" numeric,
  "shape_le_3" numeric,
  "shape_area" numeric
)
;
ALTER TABLE "public"."shp_chengzhenkaifa" OWNER TO "oge";

-- ----------------------------
-- Primary Key structure for table shp_chengzhenkaifa
-- ----------------------------
ALTER TABLE "public"."shp_chengzhenkaifa" ADD CONSTRAINT "shp_chengzhenkaifa_pkey" PRIMARY KEY ("id");
