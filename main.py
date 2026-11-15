from fastapi import FastAPI, Depends, Request, Form                  
from fastapi.responses import HTMLResponse, RedirectResponse         # 回傳 HTML、轉址
from fastapi.templating import Jinja2Templates                       # HTML 樣板工具（填洞用）
from fastapi.staticfiles import StaticFiles                          # 提供靜態檔案（www 資料夾）
from starlette.middleware.sessions import SessionMiddleware          # Session 功能（登入的號碼牌）
from db import getDB, lifespan                                       # 從 db.py 拿：取得資料庫連線、開關機流程
from auth import chkLogin                                            # 從 auth.py 拿：守門員（檢查登入與角色）

app = FastAPI(lifespan=lifespan)                                     # 建立網站，開機時執行 lifespan 連資料庫
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")  # 開啟 session，secret_key 用來替號碼牌簽章防偽造
templates = Jinja2Templates(directory="templates")                   # 告訴 Jinja2：樣板檔都放在 templates 資料夾


# ==================== 首頁 ====================

@app.get("/")                                                        # 當有人打開網址 /（GET）
async def home(request: Request):                                    # 定義首頁函式，request 是這次請求的資訊
    user = request.session.get("user")                               # 從 session 拿登入者（沒登入會是 None）
    if user is None:                                                 # 如果沒登入
        return RedirectResponse(url="/w/login.html", status_code=302)  # 轉址到登入頁
    if user["role"] == "author":                                     # 如果角色是作者
        return RedirectResponse(url="/author/list", status_code=302)   # 轉址到作者的稿件清單
    else:                                                            # 否則（角色是編輯）
        return RedirectResponse(url="/editor/list", status_code=302)   # 轉址到編輯的待審查清單


# ==================== 登入 / 登出 ====================

@app.post("/login")                                                  # 登入表單送出時（POST /login）
async def login(request: Request,                                    # request：用來存 session
                username: str = Form(...),                           # 接收表單裡 name="username" 的值
                password: str = Form(...),                           # 接收表單裡 name="password" 的值
                db=Depends(getDB)):                                  # 請 FastAPI 給一條資料庫連線
    cur = await db.execute("SELECT * FROM users WHERE id=%s AND pwd=%s;", (username, password))  # 查帳號密碼都符合的使用者
    data = await cur.fetchone()                                      # 拿一筆結果，查不到會是 None
    if data:                                                         # 如果有查到（帳密正確）
        request.session["user"] = {"id": data["id"], "nickname": data["nickname"], "role": data["role"]}  # 發號碼牌：存帳號、暱稱、角色
        return RedirectResponse(url="/", status_code=302)            # 回首頁，首頁會依角色再轉址
    return HTMLResponse("帳號或密碼錯誤 <a href='/w/login.html'>重新登入</a>", status_code=401)  # 帳密錯誤，顯示錯誤訊息


@app.get("/logout")                                                  # 打開 /logout 時
async def logout(request: Request):                                  # 登出函式
    request.session.clear()                                          # 清空 session（號碼牌作廢）
    return RedirectResponse(url="/")                                 # 回首頁（沒登入會再被送到登入頁）

# 註冊新帳號
@app.post("/register")                                               # 註冊表單送出時（POST）
async def register(username: str = Form(...),                        # 接收表單的帳號
                   password: str = Form(...),                        # 接收表單的密碼
                   nickname: str = Form(...),                        # 接收表單的暱稱
                   role: str = Form(...),                            # 接收下拉選單的角色
                   db=Depends(getDB)):                               # 需要資料庫連線
    if role not in ("author", "editor"):                             # 角色只能是這兩種（防止有人亂送其他值）
        return HTMLResponse("角色錯誤 <a href='/w/register.html'>回註冊</a>", status_code=400)  # 不合法就擋掉
    cur = await db.execute("SELECT * FROM users WHERE id=%s;", (username,))  # 先查這個帳號有沒有人用過
    if await cur.fetchone():                                         # 如果查到了（帳號已存在）
        return HTMLResponse("帳號已被使用 <a href='/w/register.html'>回註冊</a>", status_code=400)  # 顯示錯誤
    await db.execute("INSERT INTO users (id, pwd, nickname, role) VALUES (%s, %s, %s, %s);",  # 新增一筆使用者
        (username, password, nickname, role))                        # 依序填入帳號、密碼、暱稱、角色
    return HTMLResponse("註冊成功！<a href='/w/login.html'>去登入</a>")  # 顯示成功訊息和登入連結

# ==================== 練習用（第 2、3 關） ====================

@app.get("/test")                                                    # 打開 /test 時
async def test(db=Depends(getDB)):                                   # 需要資料庫連線
    cur = await db.execute("SELECT * FROM articles;")                # 查出所有稿件
    return await cur.fetchall()                                      # 回傳全部資料，FastAPI 自動轉成 JSON


@app.get("/list")                                                    # 打開 /list 時
async def articleList(request: Request, db=Depends(getDB)):          # 需要 request（給樣板）和資料庫
    cur = await db.execute("SELECT * FROM articles order by aid;")   # 查出所有稿件，依編號排序
    data = await cur.fetchall()                                      # 拿出全部結果（list）
    return templates.TemplateResponse(name="list.html", request=request, context={"articles": data})  # 用 list.html 樣板顯示，資料取名 articles


# ==================== 作者功能 ====================

# --- 1. 查看自己的稿件清單 ---
@app.get("/author/list")                                             # 打開 /author/list 時
async def myList(request: Request, db=Depends(getDB), user=Depends(chkLogin("author"))):  # 守門員：只有作者能進，user 是登入者
    cur = await db.execute("SELECT * FROM articles WHERE author=%s ORDER BY aid;", (user["id"],))  # 只查作者是自己的稿件
    data = await cur.fetchall()                                      # 拿出全部結果
    return templates.TemplateResponse(name="authorList.html", request=request,  # 用 authorList.html 樣板
        context={"articles": data, "user": user})                    # 把稿件和登入者都交給樣板


# --- 2-1. 新增投稿：顯示空白表單 ---
@app.get("/author/new")                                              # 打開 /author/new 時
async def newForm(request: Request, user=Depends(chkLogin("author"))):  # 只有作者能進
    return templates.TemplateResponse(name="articleNew.html", request=request, context={})  # 顯示空白的新增表單


# --- 2-2. 新增投稿：存進資料庫 ---
@app.post("/author/add")                                             # 新增表單送出時（POST）
async def add(category: str = Form(...), title: str = Form(...), content: str = Form(...),  # 接收表單的類別、標題、內容
              db=Depends(getDB), user=Depends(chkLogin("author"))):  # 需要資料庫，且只有作者能用
    await db.execute(                                                # 執行 SQL：
        "INSERT INTO articles (author, category, title, content, status) VALUES (%s, %s, %s, %s, '編輯中');",  # 新增一筆，狀態固定是「編輯中」
        (user["id"], category, title, content))                      # 作者從 session 拿（使用者改不了），其他從表單拿
    return RedirectResponse(url="/author/list", status_code=303)     # 303：改用 GET 回清單，避免 F5 重複送出


# --- 2-3. 編輯投稿：顯示表單（帶入原本內容） ---
@app.get("/author/edit/{aid}")                                       # 打開 /author/edit/編號 時，{aid} 是網址參數
async def editForm(aid: int, request: Request, db=Depends(getDB), user=Depends(chkLogin("author"))):  # aid 自動轉成整數
    cur = await db.execute("SELECT * FROM articles WHERE aid=%s AND author=%s AND status='編輯中';",  # 只查：這一篇＋是自己的＋編輯中
        (aid, user["id"]))                                           # 依序填入稿件編號、登入者帳號
    data = await cur.fetchone()                                      # 拿一筆，不符合條件會是 None
    if data is None:                                                 # 不是自己的，或不是編輯中
        return RedirectResponse(url="/author/list", status_code=302)   # 不給改，送回清單
    return templates.TemplateResponse(name="articleEdit.html", request=request, context={"a": data})  # 顯示編輯表單，資料取名 a


# --- 2-4. 編輯投稿：更新資料庫 ---
@app.post("/author/update")                                          # 編輯表單送出時（POST）
async def update(aid: int = Form(...), category: str = Form(...), title: str = Form(...),  # 接收隱藏欄位 aid 和三個欄位
                 content: str = Form(...), db=Depends(getDB), user=Depends(chkLogin("author"))):  # 需要資料庫，只有作者能用
    await db.execute(                                                # 執行 SQL：
        "UPDATE articles SET category=%s, title=%s, content=%s WHERE aid=%s AND author=%s AND status='編輯中';",  # 只更新自己的、編輯中的那篇
        (category, title, content, aid, user["id"]))                 # %s 依照順序一一對應
    return RedirectResponse(url="/author/list", status_code=303)     # 回清單


# --- 3. 刪除編輯中的稿件 ---
@app.post("/author/delete/{aid}")                                    # 按刪除按鈕時（POST /author/delete/編號）
async def delete(aid: int, db=Depends(getDB), user=Depends(chkLogin("author"))):  # 只有作者能用
    await db.execute("DELETE FROM articles WHERE aid=%s AND author=%s AND status='編輯中';",  # 只能刪自己的、編輯中的
        (aid, user["id"]))                                           # 填入稿件編號、登入者帳號
    return RedirectResponse(url="/author/list", status_code=303)     # 回清單


# --- 4. 送出投稿：編輯中 → 審查中 ---
@app.post("/author/submit/{aid}")                                    # 按送出投稿時（POST /author/submit/編號）
async def submit(aid: int, db=Depends(getDB), user=Depends(chkLogin("author"))):  # 只有作者能用
    await db.execute("UPDATE articles SET status='審查中' WHERE aid=%s AND author=%s AND status='編輯中';",  # 狀態改成審查中（只限自己的編輯中稿件）
        (aid, user["id"]))                                           # 填入稿件編號、登入者帳號
    return RedirectResponse(url="/author/list", status_code=303)     # 回清單


# ==================== 編輯功能 ====================

# --- 1. 待審查清單（作者、類別、標題） ---
@app.get("/editor/list")                                             # 打開 /editor/list 時
async def reviewList(request: Request, db=Depends(getDB), user=Depends(chkLogin("editor"))):  # 守門員：只有編輯能進
    cur = await db.execute("""
        SELECT a.aid, u.nickname, a.category, a.title
        FROM articles a JOIN users u ON a.author = u.id
        WHERE a.status = '審查中' ORDER BY a.aid;""")                # JOIN users 拿作者名字；只列出審查中的稿件
    data = await cur.fetchall()                                      # 拿出全部結果
    return templates.TemplateResponse(name="editorList.html", request=request,  # 用 editorList.html 樣板
        context={"articles": data, "user": user})                    # 把稿件和登入者交給樣板


# --- 2. 查看稿件內容 ---
@app.get("/editor/view/{aid}")                                       # 打開 /editor/view/編號 時
async def view(aid: int, request: Request, db=Depends(getDB), user=Depends(chkLogin("editor"))):  # 只有編輯能進
    cur = await db.execute("""
        SELECT a.*, u.nickname
        FROM articles a JOIN users u ON a.author = u.id
        WHERE a.aid = %s AND a.status = '審查中';""", (aid,))         # 查這一篇的全部欄位＋作者名字，且要是審查中
    data = await cur.fetchone()                                      # 拿一筆，不符合會是 None
    if data is None:                                                 # 找不到，或不是審查中
        return RedirectResponse(url="/editor/list", status_code=302)   # 送回待審查清單
    return templates.TemplateResponse(name="articleView.html", request=request, context={"a": data})  # 顯示稿件內容頁


# --- 3. 通過：審查中 → 已通過 ---
@app.post("/editor/pass/{aid}")                                      # 按通過按鈕時（POST）
async def approve(aid: int, db=Depends(getDB), user=Depends(chkLogin("editor"))):  # 只有編輯能用
    await db.execute("UPDATE articles SET status='已通過' WHERE aid=%s AND status='審查中';", (aid,))  # 只有審查中的才能改成已通過
    return RedirectResponse(url="/editor/list", status_code=303)     # 回待審查清單


# --- 4. 退回：審查中 → 編輯中 ---
@app.post("/editor/reject/{aid}")                                    # 按退回按鈕時（POST）
async def reject(aid: int, db=Depends(getDB), user=Depends(chkLogin("editor"))):  # 只有編輯能用
    await db.execute("UPDATE articles SET status='編輯中' WHERE aid=%s AND status='審查中';", (aid,))  # 只有審查中的才能退回成編輯中
    return RedirectResponse(url="/editor/list", status_code=303)     # 回待審查清單


# ==================== 靜態檔案 ====================

app.mount("/w", StaticFiles(directory="www"))                        # 網址 /w/ 開頭 → 去 www 資料夾找檔案（例如 /w/login.html）