# backend/app/__init__.py

from flask import Flask, send_from_directory
from flask_cors import CORS 
from .config import Config
from dotenv import load_dotenv
from .db import db, migrate  
from .routes.attendance_routes import attendance_bp
from .routes.employee_route import employee_bp
from .routes.auth_routes import auth_bp
from .routes.report_routes import report_bp
from .routes.settings_routes import settings_bp
from .routes.attendance_recovery_routes import attendance_recovery_bp
from flask_jwt_extended import JWTManager
import os

load_dotenv()

def create_app(config_class=Config):
    # Lấy đường dẫn gốc của thư mục 'app'
    app_root_path = os.path.dirname(os.path.abspath(__file__))
    
    # Định nghĩa đường dẫn tuyệt đối đến thư mục 'static' mặc định
    default_static_folder = os.path.join(app_root_path, '..', 'static')

    app = Flask(__name__, 
                static_folder=default_static_folder, 
                static_url_path='/static',
            )
    app.config.from_object(config_class)

    jwt = JWTManager(app)

    db.init_app(app)
    migrate.init_app(app, db) 

    # Cấu hình CORS chi tiết hơn
    CORS(app, resources={
        r"/api/*": {"origins": "*", "methods": ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"]},
        r"/uploads/*": {"origins": "*", "methods": ["GET", "HEAD", "OPTIONS"]},
        r"/exports/*": {"origins": "*", "methods": ["GET", "HEAD", "OPTIONS"]}
    })

    # Đăng ký blueprints
    app.register_blueprint(attendance_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(report_bp)  
    app.register_blueprint(settings_bp)
    app.register_blueprint(attendance_recovery_bp)

    @app.route('/exports/<path:filename>')
    def serve_export_file(filename):
        # Sử dụng đường dẫn tuyệt đối thay vì tương đối
        from .utils.helpers import get_export_path
        export_path = get_export_path()
        return send_from_directory(export_path, filename)

    from . import models  

    return app