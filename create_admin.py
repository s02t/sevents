from database import SessionLocal
from models import User, Base
from database import engine
import sys

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)
##
# Get database session
db = SessionLocal()

def create_admin(username, email, password):
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        print(f"User '{username}' already exists!")
        return

    # Create new admin user
    hashed_password = User.get_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_admin=True
    )
    
    db.add(new_user)
    db.commit()
    
    print(f"Admin user '{username}' created successfully!")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    create_admin(username, email, password) 
