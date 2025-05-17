from typing import Annotated
from fastapi import FastAPI, Depends, Request, Form, UploadFile, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from pydantic import BaseModel
from routers import qr, submission, form
from models import Base, QRCode, FormModel, FormField, Submission
from database import engine
#from dependencies import get_db
from sqlalchemy.orm import Session
import os

# FastAPI setup
app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/qr_codes", StaticFiles(directory="qr_codes"), name="qr_codes")

# Create directories if they don't exist
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("qr_codes", exist_ok=True)

templates = Jinja2Templates(directory="templates")

#clear template cache on startup (not neccessary however important if
#templates not changing or Dynamic Template Changes: If you dynamically 
#modify templates or the content inside them at runtime, clearing 
#the cache ensures that those changes are reflected in the next request.
#⬇️⬇️⬇️⬇️⬇️⬇️
# @app.on_event("startup")
# async def clear_template_cache():
#     templates.env.cache.clear()  


#db_dependency = Annotated[Session, Depends(get_db)]
# Routes


@app.get("/")
async def root(request: Request):
    return RedirectResponse(url="/form", status_code=status.HTTP_302_FOUND)
# @app.get("/")
# async def read_root(request: Request, db: db_dependency):
    
#     qr_codes = db.query(QRCode).order_by(QRCode.created_at.desc()).all()
    
#     return templates.TemplateResponse("submissions.html", {
#         "request": request,
#         "qr_codes": qr_codes,
        
#     })



app.include_router(qr.router)
app.include_router(submission.router)
app.include_router(form.router)