from typing import Annotated, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Path, Query, HTTPException, Request, status, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from starlette import status
from models import FormModel, Submission
from sqlalchemy.orm import Session
from database import SessionLocal
from dependencies import get_db
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import qrcode
import uuid
import io
import os
from pyzbar.pyzbar import decode
from PIL import Image
from typing import Optional
from datetime import datetime
templates = Jinja2Templates(directory="templates",
auto_reload=True,  # Critical for development
    cache_size=0)


router = APIRouter(
    prefix='/form',
    tags=['form']
)
db_dependency = Annotated[Session, Depends(get_db)]
@router.get("/test-data")
async def test_data(db: db_dependency):
    return {
        "forms": [
            {**form.__dict__} 
            for form in db.query(FormModel).all()
        ]
    }
    
@router.get("")
async def read_root(request: Request, db: db_dependency):
    
    forms = db.query(FormModel).all()
    
    return templates.TemplateResponse("form.html", {
        "request": request,
        "forms": forms
    })

# class SubmissionBase(BaseModel):
#     id: int
#     form_id: int
#     data: Optional[str] 

# class FormRequest(BaseModel):
#     id: int
#     title: str
#     description: Optional[str]
#     created_at: datetime
#     submissions: Optional[List[SubmissionBase]] = []

@router.post("/forms/")
async def create_form(
    request: Request,
    db:  db_dependency,
    title: str = Form(...),
    description: str = Form(...)
    
):
    # form_model = Todos(**form_req.model_dump())
    new_form = FormModel(
        title=title,
        description=description,
        created_at=datetime.utcnow()
    )
    db.add(new_form)
    db.commit()
    
    return RedirectResponse(url="/form", status_code=303)

@router.get("/forms/{form_id}", response_class=HTMLResponse)
async def view_form_submissions(
    request: Request,
    form_id: int,
    db: Session = Depends(get_db)
):
    form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    submissions = db.query(Submission).filter(Submission.form_id == form_id).all()
    return templates.TemplateResponse("event-form-page.html", {
        "request": request,
        "current_form": form,
        "submissions": submissions,
        "forms": db.query(FormModel).all()
    })