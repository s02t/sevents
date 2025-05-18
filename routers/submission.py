from typing import Annotated, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Path, Query, HTTPException, Request, status, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from starlette import status
from models import QRCode, Submission, FormModel, FormField, EventImage, User
from sqlalchemy.orm import Session, joinedload
from dependencies import get_db, get_admin_user
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
import json
templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix='/submission',
    tags=['submission']
)

db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[User, Depends(get_admin_user)]

# @router.get("/")
# async def read_root(request: Request):
#     return templates.TemplateResponse("form.html", {
#         "request": request
        
#     })

# Make the submission-complete endpoint public (no admin dependency)
@router.get("/submission-complete/{submission_id}", response_class=HTMLResponse)
async def completed_submission(request: Request, submission_id: int, 
db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).options(joinedload(Submission.qr_code)).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Get form fields to display the submission data properly
    fields = db.query(FormField).filter(FormField.form_id == submission.form_id).order_by(FormField.order).all()
    
    return templates.TemplateResponse("submission-complete.html", {
        "request": request,
        "submission": submission,
        "fields": fields,
        "qr_image_path": f"/submission/qr/{submission.qr_code.uuid}",
        "is_public_page": True
    })  

# Public registration form - using hash_id instead of numeric ID
@router.get("/create/{form_hash_id}", response_class=HTMLResponse)
async def new_submission_form(request: Request, form_hash_id: str, 
db: Session = Depends(get_db)):
    # Look up form by hash_id instead of numeric ID
    form = db.query(FormModel).filter(FormModel.hash_id == form_hash_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Get the form fields to dynamically generate the submission form
    fields = db.query(FormField).filter(FormField.form_id == form.id).order_by(FormField.order).all()
    
    # Get event images
    event_images = db.query(EventImage).filter(EventImage.form_id == form.id).all()
    
    # Get submissions for capacity check
    submissions = db.query(Submission).filter(Submission.form_id == form.id).all()
    
    return templates.TemplateResponse("create-submission.html", {
        "request": request,
        "current_form": form,
        "fields": fields,
        "event_images": event_images,
        "submissions": submissions,
        "new_submission_form": True,
        "is_public_page": True
    })

# Public submission handler - no auth needed
@router.post("/submit")
async def create_submission(
    request: Request,
    db: Session = Depends(get_db)
):
    # Get form data
    form_data = await request.form()
    form_id = int(form_data.get("form_id"))
    
    # Get form and its fields
    form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Check if capacity is reached
    if form.has_capacity and form.capacity:
        submissions_count = db.query(Submission).filter(Submission.form_id == form_id).count()
        if submissions_count >= form.capacity:
            raise HTTPException(status_code=400, detail="Event has reached maximum capacity")
    
    fields = db.query(FormField).filter(FormField.form_id == form_id).all()
    
    # Collect field values into a JSON structure
    field_values = {}
    for field in fields:
        field_value = form_data.get(field.field_name)
        if field.required and not field_value:
            raise HTTPException(status_code=400, detail=f"Field {field.label} is required")
        field_values[field.field_name] = field_value
    
    # Create submission with dynamic fields
    new_submission = Submission(
        form_id=form_id,
        field_values=field_values,
        submitted_at=datetime.now(pytz.timezone('Asia/Bangkok'))
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)
    
    # Create QR code
    qr_id = str(uuid.uuid4())
    
    # Create directory if it doesn't exist
    os.makedirs("qr_codes", exist_ok=True)
    
    # Generate and save QR code image
    img = qrcode.make(qr_id)
    img.save(f"qr_codes/{qr_id}.png")

    new_qr = QRCode(
        uuid=qr_id,
        submission_id=new_submission.id,
        created_at=datetime.now(pytz.timezone('Asia/Bangkok'))
    )
    db.add(new_qr)
    db.commit()
    
    # Redirect to public submission-complete page
    return RedirectResponse(url=f"/submission/submission-complete/{new_submission.id}", status_code=303)

# Public QR code endpoint for public view
@router.get("/qr/{uuid}", response_class=HTMLResponse)
async def get_public_qr_code(uuid: str, db: Session = Depends(get_db)):
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

# Admin-only QR code endpoint for admin operations
@router.get("/admin/qr/{uuid}", response_class=HTMLResponse, dependencies=[Depends(get_admin_user)])
async def get_admin_qr_code(uuid: str, db: Session = Depends(get_db)):
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

# Public registration form for modal - no auth needed
@router.get("/modal-form/{form_hash_id}", response_class=HTMLResponse)
async def modal_registration_form(request: Request, form_hash_id: str, 
db: Session = Depends(get_db)):
    """Return a compact registration form for embedding in a modal"""
    # Look up form by hash_id instead of numeric ID
    form = db.query(FormModel).filter(FormModel.hash_id == form_hash_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Get the form fields
    fields = db.query(FormField).filter(FormField.form_id == form.id).order_by(FormField.order).all()
    
    # Get event images
    event_images = db.query(EventImage).filter(EventImage.form_id == form.id).all()
    
    # Get submissions for capacity check
    submissions = db.query(Submission).filter(Submission.form_id == form.id).all()
    
    # Check if capacity is reached
    if form.has_capacity and form.capacity and len(submissions) >= form.capacity:
        return templates.TemplateResponse("partials/capacity-reached.html", {
            "request": request,
            "current_form": form,
            "is_modal": True,
            "is_public_page": True
        })
    
    return templates.TemplateResponse("partials/registration-form.html", {
        "request": request,
        "current_form": form,
        "fields": fields,
        "event_images": event_images,
        "submissions": submissions,
        "is_modal": True,
        "is_public_page": True
    })

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