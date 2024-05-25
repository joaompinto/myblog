from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pydantic import BaseModel
from sqlmodel import select, Session
import json
from delta import quill_delta_to_html
from db import get_session, EditorContent, get_user_by_email
from auth import login_get, login_post, get_current_username, logout
from fastapi import Depends
from auth import get_current_username, is_authenticated

app = FastAPI()

templates = Jinja2Templates(directory="templates")
templates.env.filters['quill_delta_to_html'] = quill_delta_to_html

app.mount("/static", StaticFiles(directory="static"), name="static")

class LoginForm(BaseModel):
    username: str
    password: str

app.get("/login", response_class=HTMLResponse)(login_get)
app.post("/login", response_class=HTMLResponse)(login_post)
app.get("/logout", response_class=HTMLResponse)(logout)


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request, id: Optional[int] = None, session: Session = Depends(get_session), is_authenticated: str = Depends(is_authenticated)):

    statement = select(EditorContent).order_by(EditorContent.content_id.desc())
    editor_contents = session.exec(statement).all()
    return templates.TemplateResponse("index.html", {"request": request, "editor_contents": editor_contents, "is_authenticated": is_authenticated})

@app.get("/edit/{author_id}/{content_id}", response_class=HTMLResponse)
@app.get("/edit/{author_id}/", response_class=HTMLResponse)
@app.get("/edit", response_class=HTMLResponse)
async def get_editor(
    request: Request,
    author_id: Optional[int] = None,
    content_id: Optional[int] = None,
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username)
):
    editor_content = None
    name, user_id = get_user_by_email(username)
    if author_id is not None:
        statement = select(EditorContent).where(EditorContent.author_id == author_id,
                                                EditorContent.content_id == content_id)
        editor_content = session.exec(statement).first()
        if editor_content:
            editor_content = editor_content.content
        else:
            raise HTTPException(status_code=404, detail="Content not found")
    return templates.TemplateResponse(
        "edit.html", {"request": request,
        "editor_content": editor_content,
        "contend_id": content_id,
        "author_id": author_id,
        "name": name})

@app.post("/save/{id}", response_class=JSONResponse)
@app.post("/save", response_class=JSONResponse)
async def save_editor_content(request: Request, id: Optional[int] = None, session: Session = Depends(get_session), username: str = Depends(get_current_username)):
    try:
        name, user_id = get_user_by_email(username)
        content = await request.json()
        editor_content = content.get("content")

        if editor_content is None:
            raise HTTPException(status_code=422, detail="Missing 'content' field in request body")

        editor_content = json.dumps(editor_content)
        if id is not None:
            statement = select(EditorContent).where(EditorContent.content_id == id)
            existing_content = session.exec(statement).first()
            if existing_content is None:
                raise HTTPException(status_code=404, detail="Content not found")
            existing_content.content = editor_content
        else:
            editor_content_obj = EditorContent(content=editor_content, author_id=user_id)
            session.add(editor_content_obj)

        session.commit()

        content_id = id if id is not None else editor_content_obj.content_id

        return {"message": "Content saved successfully", "id": content_id, "content": quill_delta_to_html(editor_content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/create", response_class=HTMLResponse)
async def create_entry(request: Request):
    return templates.TemplateResponse("edit.html", {"request": request})

@app.get("/load/{author_id}/{content_id}", response_class=JSONResponse)
async def load_editor_content(
    author_id: int,
    content_id: int,
    session: Session = Depends(get_session)
):
    statement = select(EditorContent).where(EditorContent.author_id == author_id, 
                                            EditorContent.content_id == content_id)
    editor_content = session.exec(statement).first()
    if editor_content:
        return {"id": content_id, "content": json.loads(editor_content.content)}
    else:
        raise HTTPException(status_code=404, detail="Content not found")

@app.get("/test", response_class=HTMLResponse)
async def test(request: Request):
    return templates.TemplateResponse("test.html", {"request": request})
