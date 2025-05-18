from typing import Annotated, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Path, Query, HTTPException, Request, status, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from starlette import status
from models import FormModel, Submission, FormField, EventImage, User, QRCode
from sqlalchemy.orm import Session, joinedload
from database import SessionLocal
from dependencies import get_db, get_admin_user
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import qrcode
import uuid
import io
import os
from pyzbar.pyzbar import decode
from PIL import Image
from typing import Optional, List
from datetime import datetime
import pytz
import json
from fastapi.staticfiles import StaticFiles
from email_utils import EmailManager

templates = Jinja2Templates(directory="templates",
auto_reload=True,  # Critical for development
    cache_size=0)


router = APIRouter(
    prefix='/form',
    tags=['form']
)
db_dependency = Annotated[Session, Depends(get_db)]
admin_dependency = Annotated[User, Depends(get_admin_user)]

class FieldRequest(BaseModel):
    field_name: str
    field_type: str
    label: str
    placeholder: Optional[str] = None
    options: Optional[str] = None
    required: bool = False
    order: int

class EmailRequest(BaseModel):
    subject: str
    message: str
    send_to_all: bool = True
    selected_ids: List[int] = []

@router.get("/test-data")
async def test_data(db: db_dependency):
    return {
        "forms": [
            {**form.__dict__} 
            for form in db.query(FormModel).all()
        ]
    }
    
@router.get("", dependencies=[Depends(get_admin_user)])
async def read_root(request: Request, db: db_dependency):
    
    forms = db.query(FormModel).all()
    
    # Add public registration URL to each form
    for form in forms:
        form.public_url = f"/submission/create/{form.hash_id}"
    
    return templates.TemplateResponse("form.html", {
        "request": request,
        "forms": forms
    })

@router.post("/forms/", dependencies=[Depends(get_admin_user)])
async def create_form(
    request: Request,
    db: db_dependency,
    title: str = Form(...),
    description: str = Form(...),
    location: Optional[str] = Form(None),
    event_date: Optional[str] = Form(None),
    event_time: Optional[str] = Form(None),
    has_capacity: str = Form(False),
    capacity: Optional[int] = Form(None),
    images: List[UploadFile] = File(...)
):
    # Validate at least one image is provided
    if not images or len(images) == 0:
        raise HTTPException(status_code=400, detail="At least one image is required")
    
    # Process capacity settings
    has_capacity_bool = has_capacity.lower() == 'true'
    capacity_value = int(capacity) if has_capacity_bool and capacity else None
    
    # Create new form with enhanced event information
    new_form = FormModel(
        title=title,
        description=description,
        location=location,
        event_date=datetime.fromisoformat(event_date) if event_date else None,
        event_time=event_time,
        hash_id=uuid.uuid4().hex,  # Generate a random hash_id
        has_capacity=has_capacity_bool,
        capacity=capacity_value,
        created_at=datetime.now(pytz.timezone('Asia/Bangkok'))
    )
    
    db.add(new_form)
    db.commit()
    db.refresh(new_form)
    
    # Create static/uploads directory if it doesn't exist
    os.makedirs("static/uploads", exist_ok=True)
    
    # Process all images
    for i, image in enumerate(images):
        if image and image.filename:
            # Generate unique filename
            file_extension = os.path.splitext(image.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = f"static/uploads/{unique_filename}"
            
            # Save image
            with open(file_path, "wb") as f:
                contents = await image.read()
                f.write(contents)
            
            # Create image record
            event_image = EventImage(
                form_id=new_form.id,
                image_url=f"/static/uploads/{unique_filename}",
                is_primary=(i == 0)  # First image is primary
            )
            db.add(event_image)
    
    # For backward compatibility
    first_image = db.query(EventImage).filter(EventImage.form_id == new_form.id, EventImage.is_primary == True).first()
    if first_image:
        new_form.image_url = first_image.image_url
    
    # Add default fields (email is typically required)
    default_fields = [
        FormField(
            form_id=new_form.id,
            field_name="email",
            field_type="email",
            label="Email Address",
            placeholder="Enter your email",
            required=True,
            order=1
        ),
        FormField(
            form_id=new_form.id,
            field_name="first_name",
            field_type="text",
            label="First Name",
            placeholder="Enter your first name",
            required=True,
            order=2
        ),
        FormField(
            form_id=new_form.id,
            field_name="last_name",
            field_type="text",
            label="Last Name",
            placeholder="Enter your last name",
            required=True,
            order=3
        )
    ]
    
    db.bulk_save_objects(default_fields)
    db.commit()
    
    return RedirectResponse(url=f"/form/forms/{new_form.id}/edit", status_code=303)

@router.post("/forms/{form_id}/update", dependencies=[Depends(get_admin_user)])
async def update_form(
    request: Request,
    form_id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(...),
    location: Optional[str] = Form(None),
    event_date: Optional[str] = Form(None),
    event_time: Optional[str] = Form(None),
    has_capacity: str = Form(False),
    capacity: Optional[int] = Form(None),
    images: List[UploadFile] = File(None)
):
    form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Process capacity settings
    has_capacity_bool = has_capacity.lower() == 'true'
    capacity_value = int(capacity) if has_capacity_bool and capacity else None
    
    # Update basic details
    form.title = title
    form.description = description
    form.location = location
    form.event_date = datetime.fromisoformat(event_date) if event_date and event_date.strip() else None
    form.event_time = event_time
    form.has_capacity = has_capacity_bool
    form.capacity = capacity_value
    
    # Handle image uploads
    if images and len(images) > 0:
        # Create directory if it doesn't exist
        os.makedirs("static/uploads", exist_ok=True)
        
        # Get existing images
        existing_images = db.query(EventImage).filter(EventImage.form_id == form_id).all()
        
        # If form has no existing images, at least one is required
        if len(existing_images) == 0 and (not images or len(images) == 0 or not images[0].filename):
            raise HTTPException(status_code=400, detail="At least one image is required")
        
        # Process all new images
        primary_set = False
        for i, image in enumerate(images):
            if image and image.filename:
                # Generate unique filename
                file_extension = os.path.splitext(image.filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = f"static/uploads/{unique_filename}"
                
                # Save image
                with open(file_path, "wb") as f:
                    contents = await image.read()
                    f.write(contents)
                
                # Create new image record
                is_primary = not primary_set and (i == 0 or len(existing_images) == 0)
                if is_primary:
                    primary_set = True
                
                event_image = EventImage(
                    form_id=form_id,
                    image_url=f"/static/uploads/{unique_filename}",
                    is_primary=is_primary
                )
                db.add(event_image)
        
        # Update primary image for backwards compatibility
        primary_image = db.query(EventImage).filter(EventImage.form_id == form_id, EventImage.is_primary == True).first()
        if primary_image:
            form.image_url = primary_image.image_url
    
    db.commit()
    
    return RedirectResponse(url=f"/form/forms/{form_id}/edit", status_code=303)

@router.get("/forms/{form_id}/edit", response_class=HTMLResponse, dependencies=[Depends(get_admin_user)])
async def edit_form(
    request: Request,
    form_id: int,
    db: Session = Depends(get_db)
):
    form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    fields = db.query(FormField).filter(FormField.form_id == form_id).order_by(FormField.order).all()
    
    # Add public URL to the form
    form.public_url = f"/submission/create/{form.hash_id}"
    
    return templates.TemplateResponse("edit-form.html", {
        "request": request,
        "current_form": form,
        "fields": fields,
        "forms": db.query(FormModel).all()
    })

@router.post("/forms/{form_id}/fields", dependencies=[Depends(get_admin_user)])
async def add_field(
    form_id: int,
    field_data: FieldRequest,
    db: Session = Depends(get_db)
):
    form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    new_field = FormField(
        form_id=form_id,
        field_name=field_data.field_name,
        field_type=field_data.field_type,
        label=field_data.label,
        placeholder=field_data.placeholder,
        options=field_data.options,
        required=field_data.required,
        order=field_data.order
    )
    
    db.add(new_field)
    db.commit()
    
    return {"message": "Field added successfully", "field_id": new_field.id}

@router.delete("/forms/{form_id}/fields/{field_id}", dependencies=[Depends(get_admin_user)])
async def delete_field(
    form_id: int,
    field_id: int,
    db: Session = Depends(get_db)
):
    field = db.query(FormField).filter(FormField.id == field_id, FormField.form_id == form_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    
    db.delete(field)
    db.commit()
    
    return {"message": "Field deleted successfully"}

@router.get("/forms/{form_id}", response_class=HTMLResponse, dependencies=[Depends(get_admin_user)])
async def view_form_submissions(
    request: Request,
    form_id: int,
    db: Session = Depends(get_db)
):
    form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    submissions = db.query(Submission).filter(Submission.form_id == form_id).options(joinedload(Submission.qr_code)).all()
    fields = db.query(FormField).filter(FormField.form_id == form_id).order_by(FormField.order).all()
    event_images = db.query(EventImage).filter(EventImage.form_id == form_id).all()
    
    # Add public URL to the form
    form.public_url = f"/submission/create/{form.hash_id}"
    
    return templates.TemplateResponse("event-form-page.html", {
        "request": request,
        "current_form": form,
        "submissions": submissions,
        "fields": fields,
        "forms": db.query(FormModel).all(),
        "event_images": event_images
    })

@router.get("/forms/{form_id}/images", dependencies=[Depends(get_admin_user)])
async def get_form_images(
    form_id: int,
    db: Session = Depends(get_db)
):
    # Get all images for the form
    images = db.query(EventImage).filter(EventImage.form_id == form_id).all()
    
    return {
        "images": [
            {
                "id": image.id,
                "url": image.image_url,
                "is_primary": image.is_primary
            }
            for image in images
        ]
    }

@router.post("/forms/{form_id}/images/{image_id}/set-primary", dependencies=[Depends(get_admin_user)])
async def set_primary_image(
    form_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    # Check if image exists
    image = db.query(EventImage).filter(EventImage.id == image_id, EventImage.form_id == form_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Reset all primary flags
    db.query(EventImage).filter(EventImage.form_id == form_id).update({"is_primary": False})
    
    # Set this image as primary
    image.is_primary = True
    
    # Update form.image_url for backward compatibility
    form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if form:
        form.image_url = image.image_url
    
    db.commit()
    
    return {"success": True}

@router.delete("/forms/{form_id}/images/{image_id}", dependencies=[Depends(get_admin_user)])
async def delete_image(
    form_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    # Check if image exists
    image = db.query(EventImage).filter(EventImage.id == image_id, EventImage.form_id == form_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Count existing images
    image_count = db.query(EventImage).filter(EventImage.form_id == form_id).count()
    
    # Don't allow deletion if this is the only image
    if image_count <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the only image. At least one image is required.")
    
    # If this is the primary image, set another one as primary
    if image.is_primary:
        # Find another image to set as primary
        other_image = db.query(EventImage).filter(
            EventImage.form_id == form_id, 
            EventImage.id != image_id
        ).first()
        
        if other_image:
            other_image.is_primary = True
            
            # Update form.image_url for backward compatibility
            form = db.query(FormModel).filter(FormModel.id == form_id).first()
            if form:
                form.image_url = other_image.image_url
    
    # Delete the physical file if possible
    if image.image_url and image.image_url.startswith("/static/uploads/"):
        file_path = "." + image.image_url
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                # Log error but continue
                print(f"Error removing file {file_path}: {str(e)}")
    
    # Delete the image record
    db.delete(image)
    db.commit()
    
    return {"success": True}

@router.post("/submissions/{submission_id}/toggle-status", dependencies=[Depends(get_admin_user)])
async def toggle_submission_status(
    submission_id: int,
    db: Session = Depends(get_db)
):
    # Find the submission
    submission = db.query(Submission).filter(Submission.id == submission_id).options(
        joinedload(Submission.qr_code)
    ).first()
    
    if not submission or not submission.qr_code:
        raise HTTPException(status_code=404, detail="Submission or QR code not found")
    
    # Toggle the status
    submission.qr_code.status = not submission.qr_code.status
    
    # Update the check-in timestamp if being checked in
    if submission.qr_code.status:
        submission.qr_code.checked_in_at = datetime.now(pytz.timezone('Asia/Bangkok'))
    else:
        # If marking as pending, clear the check-in timestamp
        submission.qr_code.checked_in_at = None
    
    db.commit()
    
    return {
        "success": True,
        "status": submission.qr_code.status,
        "checked_in_at": submission.qr_code.checked_in_at.isoformat() if submission.qr_code.checked_in_at else None
    }

@router.get("/stats/submissions", dependencies=[Depends(get_admin_user)])
async def get_submission_stats(db: db_dependency):
    """Get statistics about submissions"""
    count = db.query(Submission).count()
    return {"count": count}

@router.get("/stats/scanned", dependencies=[Depends(get_admin_user)])
async def get_scanned_stats(db: db_dependency):
    """Get statistics about scanned QR codes"""
    count = db.query(QRCode).filter(QRCode.status == True).count()
    return {"count": count}

@router.get("/public-link/{form_id}")
async def get_public_link(form_id: int, db: db_dependency):
    """Get the public registration link for a form by ID"""
    form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    return {"url": f"/submission/create/{form.hash_id}"}

@router.get("/submissions/{submission_id}", response_class=HTMLResponse, dependencies=[Depends(get_admin_user)])
async def view_attendee_details(
    request: Request,
    submission_id: int,
    db: Session = Depends(get_db)
):
    """View detailed information for a specific attendee/submission"""
    
    # Get the submission with related data
    submission = db.query(Submission).filter(Submission.id == submission_id).options(
        joinedload(Submission.form),
        joinedload(Submission.qr_code)
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Get the form fields to display submission data properly
    fields = db.query(FormField).filter(FormField.form_id == submission.form_id).order_by(FormField.order).all()
    
    return templates.TemplateResponse("attendee-details.html", {
        "request": request,
        "submission": submission,
        "fields": fields,
        "forms": db.query(FormModel).all()  # For navbar
    })

@router.get("/forms/{form_id}/fields", dependencies=[Depends(get_admin_user)])
async def get_form_fields(
    form_id: int,
    db: Session = Depends(get_db)
):
    """Get all fields for a form, used for full data exports"""
    fields = db.query(FormField).filter(FormField.form_id == form_id).order_by(FormField.order).all()
    
    return {
        "fields": [
            {
                "id": field.id,
                "field_name": field.field_name,
                "field_type": field.field_type,
                "label": field.label,
                "required": field.required,
                "order": field.order
            }
            for field in fields
        ]
    }

@router.post("/forms/{form_id}/send-email", dependencies=[Depends(get_admin_user)])
async def send_batch_email(
    form_id: int,
    email_request: EmailRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    """Send batch emails to event attendees"""
    form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Get submissions to email
    query = db.query(Submission).filter(Submission.form_id == form_id)
    
    # If not sending to all, filter by selected IDs
    if not email_request.send_to_all and email_request.selected_ids:
        query = query.filter(Submission.id.in_(email_request.selected_ids))
    
    submissions = query.all()
    
    # Check if there are any submissions
    if not submissions:
        return {"success": False, "message": "No recipients found"}
    
    # Collect email addresses
    email_list = []
    for submission in submissions:
        if "email" in submission.field_values and submission.field_values["email"]:
            email_list.append(submission.field_values["email"])
    
    if not email_list:
        return {"success": False, "message": "No valid email addresses found"}
    
    # Prepare email data
    email_data = {
        "event_title": form.title,
        "event_location": form.location,
        "event_date": form.event_date.strftime('%A, %B %d, %Y') if form.event_date else "",
        "event_time": form.event_time,
        "message_content": email_request.message,
        "organizer_name": "sevents",
        "current_year": datetime.now().year,
        "action_url": str(request.base_url).rstrip("/") + f"/submission/create/{form.hash_id}",
        "action_text": "View Event Details"
    }
    
    # Add email sending to background tasks
    background_tasks.add_task(
        EmailManager.send_event_update,
        email_list,
        email_request.subject,
        email_data
    )
    
    return {
        "success": True, 
        "message": f"Email scheduled to be sent to {len(email_list)} recipients"
    }