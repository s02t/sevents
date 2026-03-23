from database import SessionLocal, engine
from models import Base, FormModel
import uuid
##
def add_hash_id_to_forms():
    """
    Migration script to add a hash_id to existing forms that don't have one.
    """
    print("Starting migration to add hash_id to forms...")
    db = SessionLocal()
    try:
        # Ensure all tables are created
        Base.metadata.create_all(bind=engine)
        
        # Get all forms
        forms = db.query(FormModel).all()
        updated_count = 0
        
        for form in forms:
            # If hash_id is None or empty, generate a new UUID
            if not form.hash_id:
                form.hash_id = uuid.uuid4().hex
                updated_count += 1
        
        # Commit changes if any forms were updated
        if updated_count > 0:
            db.commit()
            print(f"Successfully added hash_id to {updated_count} forms.")
        else:
            print("No forms needed updating.")
            
    except Exception as e:
        db.rollback()
        print(f"Error updating forms: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    add_hash_id_to_forms() 
