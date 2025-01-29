from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import qrcode
import uuid
import io
import os
from pyzbar.pyzbar import decode
from PIL import Image

# FastAPI setup
app = FastAPI()

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./qrcodes.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create database directory if not exists
os.makedirs("qr_codes", exist_ok=True)

# Database model
class QRCode(Base):
    __tablename__ = "qrcodes"
    id = Column(String, primary_key=True, index=True)
    data = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Boolean, default=False)  # False=unused, True=used

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class QRCodeCreate(BaseModel):
    data: str

class QRCodeResponse(BaseModel):
    id: str
    data: str
    created_at: datetime
    status: bool

# Generate QR code endpoint
@app.post("/generate-qr/", response_model=QRCodeResponse)
async def generate_qr(qr_data: QRCodeCreate):
    db = SessionLocal()
    
    # Generate unique ID
    qr_id = str(uuid.uuid4())
    
    # Create QR code
    img = qrcode.make(qr_data.data)
    filename = f"qr_codes/{qr_id}.png"
    img.save(filename)
    
    # Store in database
    db_qr = QRCode(
        id=qr_id,
        data=qr_data.data,
        created_at=datetime.utcnow()
    )
    
    db.add(db_qr)
    db.commit()
    db.refresh(db_qr)
    db.close()
    
    return db_qr

# Scan QR code endpoint
@app.post("/scan-qr/")
async def scan_qr(file: UploadFile):
    db = SessionLocal()
    
    # Read image
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # Decode QR code
    decoded = decode(image)
    if not decoded:
        raise HTTPException(status_code=400, detail="No QR code found")
    
    qr_data = decoded[0].data.decode("utf-8")
    
    # Find QR code in database
    qr_code = db.query(QRCode).filter(QRCode.data == qr_data).first()
    if not qr_code:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    if qr_code.status:
        raise HTTPException(status_code=400, detail="QR code already used")
    
    # Update status
    qr_code.status = True
    db.commit()
    db.refresh(qr_code)
    db.close()
    
    return {"message": "QR code marked as used", "qr_code": qr_code}

# Get QR code status endpoint
@app.get("/qr-status/{qr_id}", response_model=QRCodeResponse)
async def get_qr_status(qr_id: str):
    db = SessionLocal()
    qr_code = db.query(QRCode).filter(QRCode.id == qr_id).first()
    db.close()
    
    if not qr_code:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    return qr_code

# Serve QR code images
@app.get("/qr-codes/{qr_id}.png")
async def get_qr_image(qr_id: str):
    filename = f"qr_codes/{qr_id}.png"
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="QR image not found")
    return FileResponse(filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)