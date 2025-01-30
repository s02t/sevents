from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Path, Query, HTTPException, Request, status, Form, UploadFile
from fastapi.responses import FileResponse
from starlette import status
from models import QRCode
from database import SessionLocal
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
async def validate_qr(request: Request, qr_data: QRData):
    db = SessionLocal()
    try:
        qr_code = db.query(QRCode).filter(QRCode.uuid == qr_data.uuid).first()
        
        if not qr_code:
            raise HTTPException(status_code=404, detail="QR code not found")
        
        if qr_code.status:
            return {"message": "QR code already used!"}
        
        qr_code.status = True
        db.commit()
        
        return {"message": "QR code scanned successfully! Status updated to used."}
        
    finally:
        db.close()