# 投稿審查系統

113213081 何彥緻｜軟體工程 期中作業

使用 **FastAPI + PostgreSQL** 製作的投稿審查系統，有「作者」和「編輯」兩種角色。

## 功能

### 作者
- 查看自己的投稿清單（類別、標題、審查狀態）
- 新增 / 編輯投稿（類別、標題、文章內容），狀態為「編輯中」
- 刪除編輯中的稿件
- 送出投稿：編輯中 → 審查中

### 編輯
- 查看待審查清單（作者、類別、標題）
- 查看稿件內容
- 通過：審查中 → 已通過
- 退回：審查中 → 編輯中

### 其他
- 登入 / 登出（Session）
- 註冊新帳號
- 權限控制：作者和編輯只能進入自己角色的頁面

## 稿件狀態流程

```
編輯中 ──送出──► 審查中 ──通過──► 已通過
   ▲                │
   └────退回─────────┘
```

## 檔案結構

```
├── main.py          主程式：所有網址與功能
├── db.py            資料庫連線（連線池）
├── auth.py          權限檢查 chkLogin
├── review.sql       建立資料表與測試資料
├── www/             靜態頁面（登入、註冊）
└── templates/       Jinja2 樣板（清單、表單、稿件內容）
```

## 資料表

| 資料表 | 欄位 |
|---|---|
| users | id（帳號）、pwd（密碼）、nickname（暱稱）、role（author / editor） |
| articles | aid（編號）、author（作者帳號）、category、title、content、status |

## 執行方式

1. 啟動 PostgreSQL，用 Adminer 在 `mydb` 資料庫執行 `review.sql`
2. 修改 `db.py` 的連線密碼
3. 安裝套件
   ```
   pip install "fastapi[standard]" "psycopg[binary]" psycopg_pool
   ```
4. 啟動
   ```
   python -m fastapi dev main.py
   ```
5. 開啟 http://127.0.0.1:8000

## 測試帳號

| 帳號 | 密碼 | 角色 |
|---|---|---|
| john | 123 | 作者 |
| mary | 123 | 作者 |
| editor | 123 | 編輯 |
