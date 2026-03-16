from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        # Check if column exists
        try:
            db.session.execute(text("SELECT resume_ai_feedback FROM student_profile LIMIT 1"))
            print("Column 'resume_ai_feedback' already exists.")
        except Exception:
            print("Adding column 'resume_ai_feedback' to 'student_profile'...")
            try:
                db.session.execute(text("ALTER TABLE student_profile ADD COLUMN resume_ai_feedback TEXT DEFAULT ''"))
                db.session.commit()
                print("Column added successfully.")
            except Exception as e:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    migrate()
