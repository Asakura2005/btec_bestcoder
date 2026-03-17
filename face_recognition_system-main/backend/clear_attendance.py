from app import create_app
from app.db import db
app = create_app()
with app.app_context():
    from app.models.attendance import Attendance
    count = Attendance.query.count()
    Attendance.query.delete()
    db.session.commit()
    print(f"Deleted {count} attendance records.")
