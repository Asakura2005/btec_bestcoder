from app import create_app
from app.db import db
from app.models.admin import Admin
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.attendance_recovery import AttendanceRecovery
from app.models.audit_log import AuditLog
from app.models.session import Session
from app.models.face_training_data import FaceTrainingData
from app.models.settings import Settings

app = create_app()
with app.app_context():
    print("Forcing table creation...")
    db.create_all()
    print("Tables created successfully!")
    
    # Check if admin1 exists, if not seed it (just in case)
    admin = Admin.query.filter_by(username="admin1").first()
    if not admin:
        print("Creating admin1...")
        admin = Admin(username="admin1", email="van49785@gmail.com", role="admin")
        admin.set_password("123456")
        db.session.add(admin)
        db.session.commit()
    print("Check complete.")
