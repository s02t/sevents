from models import Base
from database import engine
import os
import shutil

if __name__ == "__main__":
    # Confirm with the userr
    confirm = input("This will delete all data in the database. Are you sure? (y/n): ")
    
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        exit()
    
    # Drop all tables and recreate them
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating tables...")
    Base.metadata.create_all(bind=engine)
    
    # Clean up QR codes and image uploads
    if os.path.exists("qr_codes"):
        print("Cleaning up QR codes...")
        for file in os.listdir("qr_codes"):
            if file.endswith(".png"):
                os.remove(os.path.join("qr_codes", file))
    
    if os.path.exists("static/uploads"):
        print("Cleaning up uploaded images...")
        for file in os.listdir("static/uploads"):
            os.remove(os.path.join("static/uploads", file))
    
    print("Database reset complete!") 
