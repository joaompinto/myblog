from fastapi import FastAPI, HTTPException, Request
from sqlmodel import Field, SQLModel, Session, create_engine, select
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import json
from delta import quill_delta_to_html
from typing import Optional

# Define a custom Jinja filter
def type_filter(value):
    return str(type(value))

templates = Jinja2Templates(directory="templates")
templates.env.filters['quill_delta_to_html'] = quill_delta_to_html

# Define a SQLModel model for the editor content
class EditorContent(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    content: str

app = FastAPI()

# Create a SQLite database engine
sqlite_url = "sqlite:///editor_content.db"
engine = create_engine(sqlite_url)

# Create the table for EditorContent if it doesn't exist
SQLModel.metadata.create_all(engine)

# Mount the "static" directory to serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request, id: Optional[int] = None):
    # Open a database session
    with Session(engine) as session:
        # Retrieve all editor content from the database, revrsed sorted by id
        statement = select(EditorContent).order_by(EditorContent.id.desc())
        editor_contents = session.exec(statement).all()
    return templates.TemplateResponse("index.html", {"request": request, "editor_contents": editor_contents})

@app.get("/edit/{id}", response_class=HTMLResponse)
@app.get("/edit", response_class=HTMLResponse)
async def get_editor(request: Request, id: Optional[int] = None):
    editor_content = None
    if id is not None:
        with Session(engine) as session:
            statement = select(EditorContent).where(EditorContent.id == id)
            editor_content = session.exec(statement).first()
            if editor_content:
                editor_content = editor_content.content
            else:
                raise HTTPException(status_code=404, detail="Content not found")
    return templates.TemplateResponse("edit.html", {"request": request, "editor_content": editor_content, "contend_id": id})

@app.post("/save/{id}", response_class=JSONResponse)
@app.post("/save", response_class=JSONResponse)
async def save_editor_content(request: Request, id: Optional[int] = None):
    try:
        content = await request.json()
        editor_content = content.get("content")

        if editor_content is None:
            raise HTTPException(status_code=422, detail="Missing 'content' field in request body")

        editor_content = json.dumps(editor_content)
        # Open a database session
        with Session(engine) as session:
            if id is not None:
                # Update existing content
                statement = select(EditorContent).where(EditorContent.id == id)
                existing_content = session.exec(statement).first()
                if existing_content is None:
                    raise HTTPException(status_code=404, detail="Content not found")
                existing_content.content = editor_content
            else:
                # Create a new EditorContent instance
                editor_content_obj = EditorContent(content=editor_content)
                # Add the instance to the session
                session.add(editor_content_obj)

            # Commit the session to save the data to the database
            session.commit()

            # Get the id of the content
            content_id = id if id is not None else editor_content_obj.id

        return {"message": "Content saved successfully", "id": content_id, "content": quill_delta_to_html(editor_content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/create", response_class=HTMLResponse)
async def create_entry(request: Request):
    return templates.TemplateResponse("edit.html", {"request": request})

@app.get("/load/{id}", response_class=JSONResponse)
async def load_editor_content(id: int):
    with Session(engine) as session:
        statement = select(EditorContent).where(EditorContent.id == id)
        editor_content = session.exec(statement).first()
        if editor_content:
            return {"id": id, "content": json.loads(editor_content.content)}
        else:
            raise HTTPException(status_code=404, detail="Content not found")


@app.get("/test", response_class=HTMLResponse)
async def test(request: Request):
    # Render test.html
    return templates.TemplateResponse("test.html", {"request": request})


