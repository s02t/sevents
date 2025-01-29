from typing import Annotated
from fastapi import FastAPI, Depends, Request, Form, UploadFile, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from pydantic import BaseModel
from routers import qr, submission, form
from models import Base, QRCode, FormModel
from database import engine
from dependencies import get_db
from sqlalchemy.orm import Session

# FastAPI setup
app = FastAPI()
Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


db_dependency = Annotated[Session, Depends(get_db)]
# Routes
@app.get("/")
async def read_root(request: Request, db: db_dependency):
    
    qr_codes = db.query(QRCode).order_by(QRCode.created_at.desc()).all()
    
    return templates.TemplateResponse("submissions.html", {
        "request": request,
        "qr_codes": qr_codes,
        
    })



app.include_router(qr.router)
app.include_router(submission.router)
app.include_router(form.router)