from database import SessionLocal, engine
from models import Base, Submission
import uuid
from sqlalchemy import text

def add_hash_id_to_submissions():
    # Get database session
    db = SessionLocal()
    
    try:
        # Add the column if it doesn't exist
        try:
            db.execute(text('ALTER TABLE submissions ADD COLUMN hash_id VARCHAR'))
            print("Added hash_id column to submissions table")
        except Exception as e:
            if 'duplicate column name' not in str(e).lower():
                print(f"Warning when adding column: {e}")
        
        # Create index on hash_id if it doesn't exist
        try:
            db.execute(text('CREATE UNIQUE INDEX ix_submissions_hash_id ON submissions (hash_id)'))
            print("Created index on hash_id")
        except Exception as e:
            if 'already exists' not in str(e).lower():
                print(f"Warning when creating index: {e}")
        
        db.commit()
        
        # Get all submissions
        submissions = db.query(Submission).all()
        
        # Add hash_id to each submission that doesn't have one
        updated_count = 0
        for submission in submissions:
            if not submission.hash_id:
                submission.hash_id = uuid.uuid4().hex[:12]
                updated_count += 1
        
        # Commit changes
        db.commit()
        print(f"Added hash_id to {updated_count} submissions")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_hash_id_to_submissions() 