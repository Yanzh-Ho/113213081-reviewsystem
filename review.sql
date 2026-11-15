-- 投稿審查系統 資料表
-- 用法：Adminer 登入 → 選資料庫 → 「SQL 命令」→ 貼上全部 → 執行

DROP TABLE IF EXISTS "public"."articles";
DROP TABLE IF EXISTS "public"."users";

-- 使用者（沿用課堂 users 表：id / pwd / nickname，多加 role 角色欄位）
CREATE TABLE "public"."users" (
    "id"       character varying(15) PRIMARY KEY,
    "pwd"      character varying(30) NOT NULL,
    "nickname" character varying(30) NOT NULL,
    "role"     character varying(10) NOT NULL   -- 'author' 作者 / 'editor' 編輯
);

-- 稿件
CREATE TABLE "public"."articles" (
    "aid"      serial PRIMARY KEY,                       -- 稿件編號，自動遞增
    "author"   character varying(15) NOT NULL REFERENCES users(id),  -- 作者帳號
    "category" character varying(20) NOT NULL,           -- 類別
    "title"    character varying(100) NOT NULL,          -- 標題
    "content"  text NOT NULL,                            -- 文章內容
    "status"   character varying(10) NOT NULL DEFAULT '編輯中'  -- 編輯中 / 審查中 / 已通過
);

INSERT INTO "public"."users" ("id", "pwd", "nickname", "role") VALUES
('john',   '123', '約翰', 'author'),
('mary',   '123', '馬麗', 'author'),
('editor', '123', '總編輯', 'editor');

INSERT INTO "public"."articles" ("author", "category", "title", "content", "status") VALUES
('john', '科技', 'AI 在農業的應用', '介紹 AI 如何協助農民判斷作物病害。', '編輯中'),
('john', '生活', '埔里的秋天', '介紹埔里秋天值得去的地方。', '審查中'),
('mary', '教育', '大學生的時間管理', '分享時間管理的小技巧。', '審查中');
