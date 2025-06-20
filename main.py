from typing import Annotated
from fastapi import FastAPI, Depends, Request, Form, UploadFile, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from pydantic import BaseModel
from routers import qr, submission, form, auth
from models import Base, QRCode, FormModel, FormField, Submission, User
from database import engine
from dependencies import get_db, get_admin_user
from sqlalchemy.orm import Session
import os
import uuid
from starlette.middleware.sessions import SessionMiddleware
import secrets

# FastAPI setup
app = FastAPI()

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", secrets.token_urlsafe(32)),
    session_cookie="session",
    max_age=86400  # 24 hours
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/qr-codes", StaticFiles(directory="qr_codes"), name="qr_codes")

# Create directories if they don't exist
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/sounds", exist_ok=True)
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

# Admin dependency for protected routes
admin_dependency = Annotated[User, Depends(get_admin_user)]
db_dependency = Annotated[Session, Depends(get_db)]

# Add migration to run on startup - ensure all forms have hash_id
@app.on_event("startup")
async def ensure_form_hash_ids():
    print("Running migration check: Ensuring all forms have hash_id...")
    from database import SessionLocal
    db = SessionLocal()
    try:
        # Get all forms without hash_id
        forms_without_hash = db.query(FormModel).filter(
            (FormModel.hash_id == None) | (FormModel.hash_id == "")
        ).all()
        
        if forms_without_hash:
            print(f"Found {len(forms_without_hash)} forms without hash_id. Adding hash_id...")
            for form in forms_without_hash:
                form.hash_id = uuid.uuid4().hex
            db.commit()
            print("Migration complete: All forms now have hash_id.")
        else:
            print("No migration needed: All forms already have hash_id.")
    except Exception as e:
        print(f"Error during migration: {str(e)}")
    finally:
        db.close()

# Routes
@app.get("/")
async def root(request: Request):
    # Redirect to login if not authenticated
    if not request.session.get("user_id"):
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/form", status_code=status.HTTP_303_SEE_OTHER)

# Admin login shortcut
@app.get("/admin")
async def admin_login(request: Request):
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

# Include routers
app.include_router(auth.router)

# Protected admin router for QR scanning
app.include_router(
    qr.router,
    dependencies=[Depends(get_admin_user)]
)

# Submission router - the submission.py file handles authorization internally
# so we include it without global protection since registration is public
app.include_router(submission.router)

# Form router - selectively protect routes within the router
app.include_router(form.router)