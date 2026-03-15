from app import create_app
from app.db import db
from sqlalchemy import text, inspect

app = create_app()
with app.app_context():
    print("Checking for missing columns...")
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('admins')]
    print(f"Columns found in admins: {columns}")
    
    if 'failed_attempts' not in columns:
        print("Adding 'failed_attempts' to admins...")
        db.session.execute(text("ALTER TABLE admins ADD COLUMN failed_attempts INTEGER DEFAULT 0 NOT NULL"))
        
    if 'locked_until' not in columns:
        print("Adding 'locked_until' to admins...")
        db.session.execute(text("ALTER TABLE admins ADD COLUMN locked_until DATETIME"))

    if 'last_login' not in columns:
        print("Adding 'last_login' to admins...")
        db.session.execute(text("ALTER TABLE admins ADD COLUMN last_login DATETIME"))

    # Also check employees
    columns = [c['name'] for c in inspector.get_columns('employees')]
    print(f"Columns found in employees: {columns}")
    if 'failed_attempts' not in columns:
        db.session.execute(text("ALTER TABLE employees ADD COLUMN failed_attempts INTEGER DEFAULT 0 NOT NULL"))
    if 'locked_until' not in columns:
        db.session.execute(text("ALTER TABLE employees ADD COLUMN locked_until DATETIME"))
    if 'last_login' not in columns:
        db.session.execute(text("ALTER TABLE employees ADD COLUMN last_login DATETIME"))
    
    # Check if sessions table exists
    if 'sessions' not in inspector.get_table_names():
        print("Sessions table missing! Creating all tables...")
        from app.models.session import Session 
        db.create_all()
    else:
        print("Sessions table exists.")
        
    db.session.commit()
    print("Schema fix complete.")
