import jwt
import os
from fastapi import Request, Form, Depends, Response
from fastapi.templating import Jinja2Templates
from sqlmodel import select, Session
from db import get_session, Users
from datetime import  datetime, timedelta, UTC
from fastapi import HTTPException

SECRET_KEY = os.environ.get("SEC_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

async def get_current_username(request: Request):
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("sub")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    else:
        raise HTTPException(status_code=401, detail="Could not find access_token cookie")

async def is_authenticated(request: Request):
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            _ = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            return True
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    else:
        return False


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


templates = Jinja2Templates(directory="templates")

async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

async def login_post(response: Response, request: Request, username: str = Form(...), password: str = Form(...), session: Session = Depends(get_session)):
    statement = select(Users).where(Users.email == username)
    user = session.exec(statement).first()

    if user is not None and user.verify_password(password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token_data = {"sub": username, "author_id": user.author_id}  # Add author_id to access token data
        access_token = create_access_token(data=access_token_data, expires_delta=access_token_expires)
        response = templates.TemplateResponse("refresh.html", {"request": request, "access_token": access_token})
        response.set_cookie(key="access_token", value=access_token, samesite='Lax', max_age=ACCESS_TOKEN_EXPIRE_MINUTES*60)
        return response
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

async def logout(request: Request):
    response = templates.TemplateResponse("logout.html", {"request": request})
    response.delete_cookie("access_token")
    return response