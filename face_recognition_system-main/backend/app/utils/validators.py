# Check dữ liệu đầu vào, validate file/image/email
import base64

def validate_base64_imgae(b64_string):
    try:
        base64.b64decode(b64_string)
        return True
    except Exception:
        return False
    

def validate_attendance_result(status):
    return status in ["check-in", "check-out"]