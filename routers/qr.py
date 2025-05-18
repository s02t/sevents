from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Path, Query, HTTPException, Request, status, Form, UploadFile
from fastapi.responses import FileResponse
from starlette import status
from models import QRCode, Submission, FormModel
from sqlalchemy.orm import Session, joinedload
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
import pytz
templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix='/qr',
    tags=['qr']
)


#data: str = Form(...)
@router.post("/generate-qr/")
async def generate_qr(request: Request):
    db = SessionLocal()
    
    qr_id = str(uuid.uuid4())
    img = qrcode.make(qr_id)
    img.save(f"qr_codes/{qr_id}.png")
    
    db_qr = QRCode(
        uuid=qr_id,
        created_at=datetime.now(pytz.timezone('Asia/Bangkok'))
    )
    
    db.add(db_qr)
    db.commit()
    
    # Get the newly created QR code
    new_qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
    db.close()
    
    # Get all QR codes for the list
    db = SessionLocal()
    qr_codes = db.query(QRCode).order_by(QRCode.created_at.desc()).all()
    db.close()
    
    return templates.TemplateResponse("main.html", {
        "request": request,
        "qr_codes": qr_codes,
        "new_qr": new_qr,
        "message": "QR code generated successfully! Preview below 👇"
    })

@router.post("/scan-qr/")
async def scan_qr(request: Request, file: UploadFile):
    db = SessionLocal()
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        decoded = decode(image)
        
        if not decoded:
            raise HTTPException(status_code=400, detail="No QR code found")
        
        qr_data = decoded[0].data.decode("utf-8")
        qr_code = db.query(QRCode).filter(QRCode.data == qr_data).first()
        
        if not qr_code:
            raise HTTPException(status_code=404, detail="QR code not found")
        
        if qr_code.status:
            return templates.TemplateResponse("main.html", {
                "request": request,
                "qr_codes": db.query(QRCode).all(),
                "message": "QR code already used!"
            })
        
        qr_code.status = True
        db.commit()
        
        return templates.TemplateResponse("main.html", {
            "request": request,
            "qr_codes": db.query(QRCode).all(),
            "message": "QR code scanned successfully! Status updated to used."
        })
        
    except Exception as e:
        return templates.TemplateResponse("main.html", {
            "request": request,
            "qr_codes": db.query(QRCode).all(),
            "message": f"Error: {str(e)}"
        })
    finally:
        db.close()

@router.get("/qr-codes/{qr_id}.png")
async def get_qr_image(qr_id: str):
    filename = f"qr_codes/{qr_id}.png"
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="QR image not found")
    return FileResponse(filename)

@router.get("/scan-real")
async def scan_real(request: Request):
    return templates.TemplateResponse("scan.html", {"request": request})

class QRData(BaseModel):
    uuid: str
    
@router.post("/validate-qr")
async def validate_qr(qr_data: QRData, db: Session = Depends(get_db)):
    try:
        # Find the QR code
        qr_code = db.query(QRCode).filter(QRCode.uuid == qr_data.uuid).first()
        
        if not qr_code:
            return {"success": False, "message": "QR code not found in system"}
        
        # Check if QR code is already used
        if qr_code.status:
            return {"success": False, "message": "QR code already used!"}
        
        # Get the submission associated with this QR code
        submission = db.query(Submission).filter(Submission.id == qr_code.submission_id).options(
            joinedload(Submission.form)
        ).first()
        
        if not submission:
            return {"success": False, "message": "Submission not found"}
        
        # Update QR code status to used (checked in)
        qr_code.status = True
        db.commit()
        
        # Return success with submission data
        return {
            "success": True, 
            "message": "Check-in successful!", 
            "submission": {
                "id": submission.id,
                "form_id": submission.form_id,
                "field_values": submission.field_values,
                "submitted_at": submission.submitted_at.isoformat(),
                "form": {
                    "id": submission.form.id,
                    "title": submission.form.title,
                    "description": submission.form.description,
                    "location": submission.form.location,
                    "event_date": submission.form.event_date.isoformat() if submission.form.event_date else None,
                    "event_time": submission.form.event_time
                }
            }
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

# Add the verify-qr endpoint that the frontend is trying to use
class QRVerifyData(BaseModel):
    qr_data: str

@router.post("/verify-qr")
async def verify_qr(data: QRVerifyData, db: Session = Depends(get_db)):
    try:
        # Find the QR code using the provided UUID
        qr_code = db.query(QRCode).filter(QRCode.uuid == data.qr_data).first()
        
        if not qr_code:
            return {"success": False, "message": "Invalid QR code. This code was not found in our system."}
        
        # Check if QR code is already used
        if qr_code.status:
            return {"success": False, "message": "This QR code has already been used."}
        
        # Get the submission associated with this QR code
        submission = db.query(Submission).filter(Submission.id == qr_code.submission_id).options(
            joinedload(Submission.form)
        ).first()
        
        if not submission:
            return {"success": False, "message": "Registration information not found."}
        
        # Update QR code status to used (checked in) and record timestamp
        current_time = datetime.now(pytz.timezone('Asia/Bangkok'))
        qr_code.status = True
        qr_code.checked_in_at = current_time
        db.commit()
        
        # Return success with attendee data for display
        return {
            "success": True,
            "message": "Check-in successful!",
            "attendee_name": f"{submission.field_values.get('first_name', '')} {submission.field_values.get('last_name', '')}".strip(),
            "attendee_email": submission.field_values.get('email', 'No email provided'),
            "event_name": submission.form.title if submission.form else "Unknown Event",
            "submission_id": submission.id,
            "checked_in_at": current_time.isoformat()
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error processing QR code: {str(e)}"}