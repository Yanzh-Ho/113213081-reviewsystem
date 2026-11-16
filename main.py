from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from db import getDB, lifespan
from auth import chkLogin

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    if user is None:
        return RedirectResponse(url="/w/login.html", status_code=302)
    if user["role"] == "author":
        return RedirectResponse(url="/author/list", status_code=302)
    else:
        return RedirectResponse(url="/editor/list", status_code=302)


@app.post("/login")
async def login(request: Request,
                username: str = Form(...),
                password: str = Form(...),
                db=Depends(getDB)):
    cur = await db.execute("SELECT * FROM users WHERE id=%s AND pwd=%s;", (username, password))
    data = await cur.fetchone()
    if data:
        request.session["user"] = {"id": data["id"], "nickname": data["nickname"], "role": data["role"]}
        return RedirectResponse(url="/", status_code=302)
    return HTMLResponse("帳號或密碼錯誤 <a href='/w/login.html'>重新登入</a>", status_code=401)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")


@app.post("/register")
async def register(username: str = Form(...),
                   password: str = Form(...),
                   nickname: str = Form(...),
                   role: str = Form(...),
                   db=Depends(getDB)):
    if role not in ("author", "editor"):
        return HTMLResponse("角色錯誤 <a href='/w/register.html'>回註冊</a>", status_code=400)
    cur = await db.execute("SELECT * FROM users WHERE id=%s;", (username,))
    if await cur.fetchone():
        return HTMLResponse("帳號已被使用 <a href='/w/register.html'>回註冊</a>", status_code=400)
    await db.execute("INSERT INTO users (id, pwd, nickname, role) VALUES (%s, %s, %s, %s);",
        (username, password, nickname, role))
    return HTMLResponse("註冊成功！<a href='/w/login.html'>去登入</a>")


@app.get("/author/list")
async def myList(request: Request, db=Depends(getDB), user=Depends(chkLogin("author"))):
    cur = await db.execute("SELECT * FROM articles WHERE author=%s ORDER BY aid;", (user["id"],))
    data = await cur.fetchall()
    return templates.TemplateResponse(name="authorList.html", request=request,
        context={"articles": data, "user": user})


@app.get("/author/new")
async def newForm(request: Request, user=Depends(chkLogin("author"))):
    return templates.TemplateResponse(name="articleNew.html", request=request, context={})


@app.post("/author/add")
async def add(category: str = Form(...), title: str = Form(...), content: str = Form(...),
              db=Depends(getDB), user=Depends(chkLogin("author"))):
    await db.execute(
        "INSERT INTO articles (author, category, title, content, status) VALUES (%s, %s, %s, %s, '編輯中');",
        (user["id"], category, title, content))
    return RedirectResponse(url="/author/list", status_code=303)


@app.get("/author/edit/{aid}")
async def editForm(aid: int, request: Request, db=Depends(getDB), user=Depends(chkLogin("author"))):
    cur = await db.execute("SELECT * FROM articles WHERE aid=%s AND author=%s AND status='編輯中';",
        (aid, user["id"]))
    data = await cur.fetchone()
    if data is None:
        return RedirectResponse(url="/author/list", status_code=302)
    return templates.TemplateResponse(name="articleEdit.html", request=request, context={"a": data})


@app.post("/author/update")
async def update(aid: int = Form(...), category: str = Form(...), title: str = Form(...),
                 content: str = Form(...), db=Depends(getDB), user=Depends(chkLogin("author"))):
    await db.execute(
        "UPDATE articles SET category=%s, title=%s, content=%s WHERE aid=%s AND author=%s AND status='編輯中';",
        (category, title, content, aid, user["id"]))
    return RedirectResponse(url="/author/list", status_code=303)


@app.post("/author/delete/{aid}")
async def delete(aid: int, db=Depends(getDB), user=Depends(chkLogin("author"))):
    await db.execute("DELETE FROM articles WHERE aid=%s AND author=%s AND status='編輯中';",
        (aid, user["id"]))
    return RedirectResponse(url="/author/list", status_code=303)


@app.post("/author/submit/{aid}")
async def submit(aid: int, db=Depends(getDB), user=Depends(chkLogin("author"))):
    await db.execute("UPDATE articles SET status='審查中' WHERE aid=%s AND author=%s AND status='編輯中';",
        (aid, user["id"]))
    return RedirectResponse(url="/author/list", status_code=303)


@app.get("/editor/list")
async def reviewList(request: Request, db=Depends(getDB), user=Depends(chkLogin("editor"))):
    cur = await db.execute("""
        SELECT a.aid, u.nickname, a.category, a.title
        FROM articles a JOIN users u ON a.author = u.id
        WHERE a.status = '審查中' ORDER BY a.aid;""")
    data = await cur.fetchall()
    return templates.TemplateResponse(name="editorList.html", request=request,
        context={"articles": data, "user": user})


@app.get("/editor/view/{aid}")
async def view(aid: int, request: Request, db=Depends(getDB), user=Depends(chkLogin("editor"))):
    cur = await db.execute("""
        SELECT a.*, u.nickname
        FROM articles a JOIN users u ON a.author = u.id
        WHERE a.aid = %s AND a.status = '審查中';""", (aid,))
    data = await cur.fetchone()
    if data is None:
        return RedirectResponse(url="/editor/list", status_code=302)
    return templates.TemplateResponse(name="articleView.html", request=request, context={"a": data})


@app.post("/editor/pass/{aid}")
async def approve(aid: int, db=Depends(getDB), user=Depends(chkLogin("editor"))):
    await db.execute("UPDATE articles SET status='已通過' WHERE aid=%s AND status='審查中';", (aid,))
    return RedirectResponse(url="/editor/list", status_code=303)


@app.post("/editor/reject/{aid}")
async def reject(aid: int, db=Depends(getDB), user=Depends(chkLogin("editor"))):
    await db.execute("UPDATE articles SET status='編輯中' WHERE aid=%s AND status='審查中';", (aid,))
    return RedirectResponse(url="/editor/list", status_code=303)


app.mount("/w", StaticFiles(directory="www"))