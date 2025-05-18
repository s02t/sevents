from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from datetime import datetime
import pytz
from passlib.context import CryptContext
import uuid

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User model for authentication
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self.hashed_password)
    
    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(password)

# Database model
class QRCode(Base):
    __tablename__ = "qrcodes"
    id = Column(Integer, primary_key=True, index=True)
    uuid= Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Boolean, default=False)
    checked_in_at = Column(DateTime, nullable=True)  # New column to record check-in time

    # Submission relationship
    submission_id = Column(Integer, ForeignKey("submissions.id"), unique=True)
    submission = relationship("Submission", back_populates="qr_code")

class EventImage(Base):
    __tablename__ = "event_images"
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"))
    image_url = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False)  # Flag for primary image
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Bangkok')))
    
    # Relationship
    form = relationship("FormModel", back_populates="images")

class FormModel(Base):
    __tablename__ = "forms"
    id = Column(Integer, primary_key=True, index=True)
    # Add a random hash/UUID for public URLs
    hash_id = Column(String, unique=True, index=True, default=lambda: uuid.uuid4().hex)
    # Form metadata
    title = Column(String)
    description = Column(String)
    location = Column(String, nullable=True)
    event_date = Column(DateTime, nullable=True)
    event_time = Column(String, nullable=True)
    image_url = Column(String, nullable=True)  # Legacy field - maintain for backward compatibility
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Bangkok')))
    
    # Relationships
    fields = relationship("FormField", back_populates="form", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="form")
    images = relationship("EventImage", back_populates="form", cascade="all, delete-orphan")

class FormField(Base):
    __tablename__ = "form_fields"
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"))
    field_name = Column(String, nullable=False)
    field_type = Column(String, nullable=False)  # text, email, number, select, etc.
    label = Column(String, nullable=False)
    placeholder = Column(String, nullable=True)
    options = Column(String, nullable=True)  # For select fields, comma-separated options
    required = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    
    # Relationship
    form = relationship("FormModel", back_populates="fields")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    
    # Store dynamic form field values as JSON
    field_values = Column(JSON, nullable=False, default=dict)
    
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