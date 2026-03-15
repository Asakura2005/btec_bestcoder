from app import create_app
from app.db import db
from app.models.admin import Admin

app = create_app()

with app.app_context():
    username = "admin1"
    password = "123456"
    email = "van49785@gmail.com"
    role = "admin"  # hoặc 'superadmin' nếu bạn có phân quyền

    # Kiểm tra admin đã tồn tại chưa
    existing_admin = Admin.query.filter(
        (Admin.username == username) | (Admin.email == email)
    ).first()

    if existing_admin:
        print("Admin already exists.")
    else:
        admin = Admin(
            username=username,
            email=email,
            role=role,
            is_active=True  # kích hoạt tài khoản
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print("Admin created successfully.")
