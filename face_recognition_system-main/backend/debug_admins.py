from app import create_app
from app.models.admin import Admin

app = create_app()

with app.app_context():
    admins = Admin.query.all()
    print(f"Admins: {[{'id': a.id, 'username': a.username} for a in admins]}")
