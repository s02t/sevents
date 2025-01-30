from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Path, Query, HTTPException, Request, status, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from starlette import status
from models import QRCode, Submission, FormModel
from sqlalchemy.orm import Session, joinedload
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
import pytz
templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix='/submission',
    tags=['submission']
)

db_dependency = Annotated[Session, Depends(get_db)]

# @router.get("/")
# async def read_root(request: Request):
#     return templates.TemplateResponse("form.html", {
#         "request": request
        
#     })

@router.get("/submission-complete/{submission_id}", response_class=HTMLResponse)
async def completed_submission(request: Request, submission_id: int, 
db: Session = Depends(get_db)):
    submissions = db.query(Submission).filter(Submission.id == submission_id).options(joinedload(Submission.qr_code)).first()
    if not submissions:
        raise HTTPException(status_code=404, detail="not found")
    
    return templates.TemplateResponse("submission-complete.html", {
        "request": request,
        "submissions": submissions
        
        
    })

@router.get("/create/{form_id}", response_class=HTMLResponse)
async def new_submission_form(request: Request, form_id: int, 
db: Session = Depends(get_db)):
    form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    return templates.TemplateResponse("create-submission.html", {
        "request": request,
        "current_form": form,
        "new_submission_form": True,
        
    })

@router.post("/submit")
async def create_submission(
    request: Request,
    form_id: int = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    db: Session = Depends(get_db)
):
    # Create submission
    new_submission = Submission(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        form_id=form_id,
        submitted_at=datetime.now(pytz.timezone('Asia/Bangkok'))
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)
    
    # Create QR code
    # qr = qrcode.QRCode(
    #     version=1,
    #     error_correction=qrcode.constants.ERROR_CORRECT_L,
    #     box_size=10,
    #     border=4,
    # )
    #qr.add_data(str(new_submission.id))
    # qr.make(fit=True)
    # img = qr.make_image(fill_color="black", back_color="white")
    
    # # Save QR code
    # buffer = io.BytesIO()
    # img.save(buffer)
    # buffer.seek(0)
    
    qr_id = str(uuid.uuid4())
    img = qrcode.make(qr_id)
    img.save(f"qr_codes/{qr_id}.png")

    new_qr = QRCode(
        uuid=qr_id,
        submission_id=new_submission.id,
        created_at=datetime.now(pytz.timezone('Asia/Bangkok'))
    )
    db.add(new_qr)
    db.commit()
    
    return RedirectResponse(url=f"/submission/submission-complete/{new_submission.id}", status_code=303)

@router.get("/qr/{uuid}", response_class=HTMLResponse)
async def get_qr_code(uuid: str, db: Session = Depends(get_db)):
    qr_record = db.query(QRCode).filter(QRCode.uuid == uuid).first()
    if not qr_record:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_record.uuid)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return Response(content=buffer.getvalue(), media_type="image/png")

# new_form = Form(title="Conference Registration", description="2024 Tech Summit")
# db.add(new_form)
# db.commit()

# # User submits the form
# submission = Submission(
#     first_name="John",
#     last_name="Doe",
#     email="john@example.com",
#     form_id=new_form.id
# )
# db.add(submission)
# db.commit()

# # Generate QR code (would typically be automatic)
# qrcode = QRCode(submission_id=submission.id)
# db.add(qrcode)
# db.commit()