from app import create_app
from app.db import db

app = create_app()

# Ensure all tables exist (including new payroll & AI fields)
with app.app_context():
    db.create_all()
    print("[Startup] Database tables verified/created")

if __name__ == "__main__":
    app.run(
        host='0.0.0.0',    
        port=5000,
        debug=True        
    )