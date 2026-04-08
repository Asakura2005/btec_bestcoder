from app import create_app
from app.db import db
from app.models.employee import Employee

app = create_app()
with app.app_context():
    emp = Employee.query.filter_by(email='hung@gmail.com').first()
    if emp:
        emp.set_password('123456')
        db.session.commit()
        print('Password for hung@gmail.com reset to 123456 successfully')
    else:
        print('Employee hung@gmail.com not found')
