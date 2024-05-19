import json
from fastapi import HTTPException
from sqlmodel import Session
from sqlmodel import Field, SQLModel, Session, create_engine, select
from fastapi import FastAPI, HTTPException, Request



async def save_editor_content(request: Request):
    try:
        content = await request.json()
        editor_content = content.get("content")

        if editor_content is None:
            raise HTTPException(status_code=422, detail="Missing 'content' field in request body")

        editor_content = json.dumps(editor_content)
        # Open a database session
        with Session(engine) as session:
            # Create a new EditorContent instance
            editor_content_obj = EditorContent(content=editor_content)
            # Add the instance to the session
            session.add(editor_content_obj)
            # Commit the session to save the data to the database
            session.commit()

            # Get the id of the new added content
            content_id = editor_content_obj.id

        return {"message": "Content saved successfully", "id": content_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))