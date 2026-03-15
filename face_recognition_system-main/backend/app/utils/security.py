# Hàm JWT, mã hóa mật khẩu, xác thực token
import os
import bcrypt
from datetime import datetime, timedelta
import jwt
import uuid 
import hashlib 
import pytz 
from app.config import Config 

# ---------------  Password helpers  ------------------

def hash_password(plain: str) -> str:
    """Hash mật khẩu sử dụng bcrypt."""
    # `gensalt()` tạo ra một salt ngẫu nhiên.
    # `rounds` là số vòng lặp băm, càng cao càng an toàn nhưng chậm hơn. Mặc định 12.
    salt = bcrypt.gensalt() 
    return bcrypt.hashpw(plain.encode('utf-8'), salt).decode('utf-8')

def check_password_hash(hashed: str, plain: str) -> bool:
    """Kiểm tra mật khẩu khớp với hash đã lưu."""
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

# ---------------  JWT helpers  ------------------

# THÊM HÀM BĂM RIÊNG CHO JTI (SỬ DỤNG SHA256)
def hash_jti(jti: str) -> str:
    """Hash JWT ID (jti) bằng SHA256 để lưu vào database."""
    return hashlib.sha256(jti.encode('utf-8')).hexdigest()

def generate_jwt_token(payload_data: dict) -> str:
    now_utc = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))  
    # Lấy thời gian hết hạn từ Config
    expires_utc = now_utc + timedelta(minutes=Config.JWT_EXPIRATION_MINUTES)
    
    # Tạo JWT ID duy nhất cho mỗi token
    jti = str(uuid.uuid4()) 

    payload = {
        **payload_data, 
        "jti": jti, 
        "iat": now_utc,
        "exp": expires_utc 
    }
    
    # Sử dụng các cấu hình từ Config
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)
    return token

# CẬP NHẬT: Hàm giải mã JWT token
def decode_jwt_token(token: str) -> dict | None:
    """
    Giải mã JWT token.
    Trả về payload nếu hợp lệ, None nếu hết hạn hoặc không hợp lệ.
    """
    try:
        # Sử dụng các cấu hình từ Config
        return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        return None
