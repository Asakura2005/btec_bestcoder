from app import create_app
from app.db import db
from app.models.attendance import Attendance
from datetime import datetime
import pytz

app = create_app()
with app.app_context():
    # Get current date in VN timezone
    now = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
    
    print(f"Deleting attendance records since {today_start}...")
    
    # Delete records
    deleted_count = Attendance.query.filter(Attendance.timestamp >= today_start).delete()
    db.session.commit()
    
    print(f"Successfully deleted {deleted_count} records.")
    print("You can now test check-in and check-out again.")
