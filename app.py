from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pydantic import BaseModel
from sqlmodel import select, Session
import json
from delta import quill_delta_to_html, delta_title
from db import get_session, EditorContent, get_user_by_email
from auth import login_get, login_post, get_current_username, logout
from auth import get_current_user_data

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
async def get_index(request: Request, id: Optional[int] = None, session: Session = Depends(get_session), get_current_user_data: dict = Depends(get_current_user_data)):
    is_authenticated = get_current_user_data is not None
    author_id = get_current_user_data.get("author_id") if is_authenticated else None
    statement = select(EditorContent).order_by(EditorContent.content_id.desc())
    editor_contents = session.exec(statement).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "editor_contents": editor_contents,
            "is_authenticated": is_authenticated,
            "author_id": author_id
        }
)

@app.get("/edit/{author_id}/{content_id}", response_class=HTMLResponse)
@app.get("/edit/{author_id}", response_class=HTMLResponse)
@app.get("/edit", response_class=HTMLResponse)
async def get_editor(
    request: Request,
    author_id: Optional[int] = None,
    content_id: Optional[int] = None,
    session: Session = Depends(get_session),
    get_current_user_data: dict = Depends(get_current_user_data)
):
    is_authenticated = get_current_user_data is not None
    if is_authenticated:
        username = get_current_user_data['sub']
        editor_content = None
        name, user_id = get_user_by_email(username)
    else:
        name =" John Doe"
    if content_id is not None:
        statement = select(EditorContent).where(EditorContent.author_id == author_id,
                                                EditorContent.content_id == content_id)
        editor_content = session.exec(statement).first()
        if editor_content:
            editor_content = editor_content.content
        else:
            raise HTTPException(status_code=404, detail="Content not found")
    return templates.TemplateResponse(
        "edit.html", {
            "request": request,
            "editor_content": editor_content,
            "contend_id": content_id,
            "author_id": author_id,
            "name": name,
            "is_authenticated": is_authenticated
            }
        )

@app.post("/save/{author_id}/{content_id}", response_class=JSONResponse)
@app.post("/save/{author_id}", response_class=JSONResponse)
async def save_editor_content(
    request: Request,
    author_id: Optional[int] = None,
    content_id: Optional[int] = None,
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username)
):
    try:
        name, user_id = get_user_by_email(username)
        content = await request.json()
        editor_content = content.get("content")

        if editor_content is None:
            raise HTTPException(status_code=422, detail="Missing 'content' field in request body")

        editor_content = json.dumps(editor_content)
        if content_id is not None:
            statement = select(EditorContent).where(
                EditorContent.author_id == user_id,
                EditorContent.content_id == content_id)
            existing_content = session.exec(statement).first()
            print("existing_content", existing_content)
            if existing_content is None:
                raise HTTPException(status_code=404, detail="Content not found")
            existing_content.content = editor_content
        else:
            editor_content_obj = EditorContent(content=editor_content, author_id=user_id)
            session.add(editor_content_obj)
        # commit either the new record or the updated record
        session.commit()

        content_id = content_id if content_id is not None else editor_content_obj.content_id
        content = quill_delta_to_html(editor_content)
        title = delta_title(editor_content)

        return {
            "message": "Content saved successfully",
            "content_id": content_id,
            "author_id": user_id,
            "content": quill_delta_to_html(editor_content),
            "title": title
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/create", response_class=HTMLResponse)
async def create_entry(request: Request):
    return templates.TemplateResponse("edit.html", {"request": request})

@app.get("/view/{author_id}/{content_id}", response_class=HTMLResponse)
async def view_content(
    request: Request,
    author_id: int,
    content_id: int,
    session: Session = Depends(get_session),
    get_current_user_data: bool = Depends(get_current_user_data)
):
    is_authenticated = get_current_user_data is not None
    statement = select(EditorContent).where(EditorContent.author_id == author_id, 
                                            EditorContent.content_id == content_id)
    editor_content = session.exec(statement).first()
    title = delta_title(editor_content.content)
    if editor_content:
        return templates.TemplateResponse(
            "view.html", {
                "request": request,
                "title": title,
                "editor_content": editor_content,
                "is_authenticated": is_authenticated
            }
        )
    else:
        raise HTTPException(status_code=404, detail="Content not found")


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
