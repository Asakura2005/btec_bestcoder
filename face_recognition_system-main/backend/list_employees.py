from app import create_app
from app.db import db
from app.models.employee import Employee
import json

app = create_app()
with app.app_context():
    emps = Employee.query.all()
    results = []
    for e in emps:
        results.append({
            "employee_id": e.employee_id,
            "email": e.email,
            "status": e.status,
            "has_password": e.password_hash is not None
        })
    print("---EMPLOYEE_DATA_START---")
    print(json.dumps(results, indent=2))
    print("---EMPLOYEE_DATA_END---")
