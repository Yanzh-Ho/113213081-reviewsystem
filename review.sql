
DROP TABLE IF EXISTS "public"."users";

CREATE TABLE "public"."users" (
    "id"       character varying(15) PRIMARY KEY,
    "pwd"      character varying(30) NOT NULL,
    "nickname" character varying(30) NOT NULL,
    "role"     character varying(10) NOT NULL   
);

-- 稿件
CREATE TABLE "public"."articles" (
    "aid"      serial PRIMARY KEY,                       
    "author"   character varying(15) NOT NULL REFERENCES users(id),  
    "category" character varying(20) NOT NULL,           
    "title"    character varying(100) NOT NULL,          
    "content"  text NOT NULL,                            
    "status"   character varying(10) NOT NULL DEFAULT '編輯中'  
);

INSERT INTO "public"."users" ("id", "pwd", "nickname", "role") VALUES
('john',   '123', '約翰', 'author'),
('mary',   '123', '馬麗', 'author'),
('editor', '123', '總編輯', 'editor');

INSERT INTO "public"."articles" ("author", "category", "title", "content", "status") VALUES
('john', '科技', 'AI 在農業的應用', '介紹 AI 如何協助農民判斷作物病害。', '編輯中'),
('john', '生活', '埔里的秋天', '介紹埔里秋天值得去的地方。', '審查中'),
('mary', '教育', '大學生的時間管理', '分享時間管理的小技巧。', '審查中');
