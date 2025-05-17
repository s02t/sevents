#!/usr/bin/env python3
"""
Seed script to generate fake submissions for an event
Usage: python seed.py <event_id> [number_of_submissions]
Example: python seed.py 1 50
"""

import sys
import random
import uuid
from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
import pytz
from faker import Faker
from database import SessionLocal
from models import FormModel, FormField, Submission, QRCode
import os

# Initialize Faker
fake = Faker()

def create_submissions(event_id, num_submissions=10):
    """Create fake submissions for the specified event"""
    db = SessionLocal()
    
    try:
        # Get the event
        event = db.query(FormModel).filter(FormModel.id == event_id).first()
        if not event:
            print(f"Error: Event with ID {event_id} not found")
            return
            
        # Get the form fields
        form_fields = db.query(FormField).filter(FormField.form_id == event_id).all()
        if not form_fields:
            print(f"Error: No form fields found for event ID {event_id}")
            return
        
        # Create directory for QR codes if it doesn't exist
        os.makedirs("qr_codes", exist_ok=True)
            
        print(f"Generating {num_submissions} fake submissions for event: {event.title}")
        
        # Create submissions
        for i in range(num_submissions):
            # Generate submission data based on form fields
            field_values = generate_field_values(form_fields)
            
            # Create random submission date within the last month
            submission_date = datetime.now(pytz.timezone('Asia/Bangkok')) - timedelta(days=random.randint(0, 30))
            
            # Create submission
            new_submission = Submission(
                form_id=event_id,
                field_values=field_values,
                submitted_at=submission_date
            )
            db.add(new_submission)
            db.flush()  # This gives us the ID without committing the transaction
            
            # Create QR code
            qr_id = str(uuid.uuid4())
            new_qr = QRCode(
                uuid=qr_id,
                submission_id=new_submission.id,
                created_at=submission_date,
                status=random.choice([True, False, False])  # 1/3 chance of being checked in
            )
            db.add(new_qr)
            
            # Generate QR code image
            import qrcode
            img = qrcode.make(qr_id)
            img.save(f"qr_codes/{qr_id}.png")
            
            # Print progress
            if (i + 1) % 10 == 0 or (i + 1) == num_submissions:
                print(f"Created {i + 1} submissions...")
        
        # Commit all changes
        db.commit()
        print(f"Successfully created {num_submissions} submissions!")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {str(e)}")
    finally:
        db.close()

def generate_field_values(form_fields):
    """Generate fake values for form fields"""
    field_values = {}
    
    for field in form_fields:
        field_name = field.field_name
        field_type = field.field_type
        
        # Generate appropriate value based on field type and name
        if field_name == 'email':
            field_values[field_name] = fake.email()
        elif field_name == 'first_name' or field_name.startswith('first'):
            field_values[field_name] = fake.first_name()
        elif field_name == 'last_name' or field_name.startswith('last'):
            field_values[field_name] = fake.last_name()
        elif field_name == 'phone' or field_type == 'tel':
            field_values[field_name] = fake.phone_number()
        elif field_name == 'address' or field_name.endswith('address'):
            field_values[field_name] = fake.address()
        elif field_type == 'number':
            field_values[field_name] = random.randint(18, 65)
        elif field_type == 'checkbox':
            field_values[field_name] = random.choice(['yes', None])
        elif field_type == 'date':
            field_values[field_name] = fake.date_between(start_date='-5y', end_date='today').isoformat()
        elif field_type == 'select' and field.options:
            options = field.options.split(',')
            field_values[field_name] = random.choice(options).strip()
        elif field_type == 'textarea':
            field_values[field_name] = fake.paragraph()
        else:
            # Default text field
            field_values[field_name] = fake.text(max_nb_chars=30)
    
    return field_values

def main():
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python seed.py <event_id> [number_of_submissions]")
        return
    
    try:
        event_id = int(sys.argv[1])
        num_submissions = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        
        create_submissions(event_id, num_submissions)
    except ValueError:
        print("Error: Event ID and number of submissions must be integers")
    
if __name__ == "__main__":
    main() 