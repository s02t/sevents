from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from datetime import datetime
import pytz

# Database model
class QRCode(Base):
    __tablename__ = "qrcodes"
    id = Column(Integer, primary_key=True, index=True)
    uuid= Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Boolean, default=False)

    # Submission relationship
    submission_id = Column(Integer, ForeignKey("submissions.id"), unique=True)
    submission = relationship("Submission", back_populates="qr_code")

class FormModel(Base):
    __tablename__ = "forms"
    id = Column(Integer, primary_key=True, index=True)
    # Form metadata (not user data)
    title = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Bangkok')))
    
    # Relationship to submissions
    submissions = relationship("Submission", back_populates="form")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    # User data fields
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String, unique=True)
    
    # Form relationship
    form_id = Column(Integer, ForeignKey("forms.id"))
    form = relationship("FormModel", back_populates="submissions")
    
    # QR Code relationship
    qr_code = relationship("QRCode", back_populates="submission", uselist=False)
    submitted_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Bangkok')))


# class QRCode(Base):
#     __tablename__ = "qr_codes"
#     id = Column(Integer, primary_key=True)
#     uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
#     status = Column(Enum(QRCodeStatus), default=QRCodeStatus.UNUSED)
    
#     # Submission relationship
#     submission_id = Column(Integer, ForeignKey("submissions.id"), unique=True)
#     submission = relationship("Submission", back_populates="qr_code")