from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User
from dependencies import get_db, get_admin_user
from pydantic import BaseModel

# Templates setup
templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[User, Depends(get_admin_user)]

# Data models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    is_admin: bool = False

# Routes
@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_submit(
    request: Request,
    db: db_dependency,
    username: str = Form(...),
    password: str = Form(...)
):
    # Authentication is handled by the dependencies
    # If we reach here, login was successful
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@router.get("/users", dependencies=[Depends(get_admin_user)])
async def list_users(request: Request, db: db_dependency):
    users = db.query(User).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@router.post("/users", dependencies=[Depends(get_admin_user)])
async def create_user(
    user_data: UserCreate,
    db: db_dependency
):
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = User.get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_admin=user_data.is_admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email, "is_admin": new_user.is_admin}

@router.delete("/users/{user_id}", dependencies=[Depends(get_admin_user)])
async def delete_user(user_id: int, db: db_dependency):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"} 