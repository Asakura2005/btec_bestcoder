# Import các thư viện cần thiết
from app import db  # SQLAlchemy database instance - FIX: đồng nhất với Employee model
from datetime import datetime  # Xử lý thời gian
import uuid  # Tạo ID duy nhất cho training data
import pytz  # Xử lý múi giờ
import numpy as np  # Để validate face encoding

# Model lưu trữ dữ liệu training khuôn mặt cho từng nhân viên
class FaceTrainingData(db.Model):
    __tablename__ = 'face_training_data'  
    
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'pose_type', name='unique_employee_pose'),
        db.Index('idx_employee_quality', 'employee_id', 'image_quality_score'),  # Composite index cho performance
    )
    
    # Các cột trong bảng
    id = db.Column(db.Integer, primary_key=True)  # ID chính, tự động tăng
    training_id = db.Column(db.String(36), unique=True, nullable=False, index=True)  # ID duy nhất cho mỗi bản ghi training
    employee_id = db.Column(db.String(8), db.ForeignKey('employees.employee_id'),
                            nullable=False, index=True)  # Khóa ngoại liên kết với bảng employees
    pose_type = db.Column(db.String(20), nullable=False)  # Loại pose (front, left, right, up, down)
    face_encoding = db.Column(db.LargeBinary, nullable=False)  # Mã hóa khuôn mặt dạng binary
    image_quality_score = db.Column(db.Float)  # Điểm chất lượng ảnh (tùy chọn)
    created_at = db.Column(db.DateTime,
                           default=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None),
                           nullable=False)  
    
    # Khởi tạo bản ghi mới
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Tự động tạo training_id nếu chưa có
        if not self.training_id:
            self.training_id = str(uuid.uuid4())
    
    # IMPROVED: Kiểm tra tính hợp lệ của pose_type
    @staticmethod
    def validate_pose_type(pose_type):
        """Kiểm tra pose_type có thuộc danh sách hợp lệ không"""
        valid_poses = ['front', 'left', 'right', 'up', 'down']  # Đồng bộ với FacialRecognitionService.get_required_poses()
        if pose_type not in valid_poses:
            raise ValueError(f"Invalid pose type: {pose_type}. Must be one of {valid_poses}")
        return True
    
    # NEW: Validate face encoding
    @staticmethod
    def validate_face_encoding(face_encoding_bytes):
        """Kiểm tra face encoding có đúng định dạng và kích thước không (512D cho ArcFace)"""
        try:
            if not isinstance(face_encoding_bytes, bytes):
                raise ValueError("Face encoding must be bytes")
            
            # Kiểm tra kích thước (512 float32 = 512 * 4 = 2048 bytes)
            expected_size = 512 * 4  # 512 float32 values
            if len(face_encoding_bytes) != expected_size:
                raise ValueError(f"Face encoding must be {expected_size} bytes (512 float32 values), got {len(face_encoding_bytes)}")
            
            # Thử decode để đảm bảo dữ liệu hợp lệ
            np.frombuffer(face_encoding_bytes, dtype=np.float32)
            return True
        except Exception as e:
            raise ValueError(f"Invalid face encoding: {e}")
    
    # IMPROVED: Factory method với validation đầy đủ
    @classmethod
    def create_training_data(cls, employee_id, pose_type, face_encoding, image_quality_score=None):
        """Tạo bản ghi training mới với validation đầy đủ"""
        cls.validate_pose_type(pose_type)
        cls.validate_face_encoding(face_encoding)
        
        # Validate image quality score
        if image_quality_score is not None and (image_quality_score < 0 or image_quality_score > 100):
            raise ValueError("Image quality score must be between 0 and 100")
        
        return cls(
            employee_id=employee_id,
            pose_type=pose_type,
            face_encoding=face_encoding,
            image_quality_score=image_quality_score
        )
    
    # IMPROVED: Lấy encodings với sắp xếp theo chất lượng
    @classmethod
    def get_employee_encodings(cls, employee_id, min_quality=None):
        """Trả về danh sách encodings của nhân viên, sắp xếp theo chất lượng giảm dần"""
        query = cls.query.filter_by(employee_id=employee_id)
        
        if min_quality is not None:
            query = query.filter(cls.image_quality_score >= min_quality)
        
        return query.order_by(cls.image_quality_score.desc().nullslast()).all()
    
    # NEW: Lấy encoding theo pose cụ thể
    @classmethod
    def get_employee_encoding_by_pose(cls, employee_id, pose_type):
        """Lấy encoding của nhân viên theo pose cụ thể"""
        return cls.query.filter_by(employee_id=employee_id, pose_type=pose_type).first()
    
    # IMPROVED: Đếm pose với điều kiện chất lượng
    @classmethod
    def get_employee_pose_count(cls, employee_id, min_quality=None):
        """Trả về số lượng pose đã được lưu cho một nhân viên"""
        query = cls.query.filter_by(employee_id=employee_id)
        
        if min_quality is not None:
            query = query.filter(cls.image_quality_score >= min_quality)
            
        return query.count()
    
    # NEW: Lấy danh sách pose đã train
    @classmethod
    def get_employee_trained_poses(cls, employee_id):
        """Trả về danh sách các pose đã được train cho nhân viên"""
        results = cls.query.filter_by(employee_id=employee_id).with_entities(cls.pose_type).all()
        return [r.pose_type for r in results]
    
    # NEW: Xóa dữ liệu training cũ khi retrain
    @classmethod
    def clear_employee_training_data(cls, employee_id):
        """Xóa tất cả dữ liệu training của nhân viên (dùng khi retrain)"""
        deleted_count = cls.query.filter_by(employee_id=employee_id).delete()
        db.session.commit()
        return deleted_count
    
    # NEW: Replace encoding cho pose cụ thể
    @classmethod
    def replace_employee_pose_encoding(cls, employee_id, pose_type, face_encoding, image_quality_score=None):
        """Thay thế encoding cho pose cụ thể của nhân viên"""
        cls.validate_pose_type(pose_type)
        cls.validate_face_encoding(face_encoding)
        
        # Xóa encoding cũ nếu có
        cls.query.filter_by(employee_id=employee_id, pose_type=pose_type).delete()
        
        # Tạo encoding mới
        new_training_data = cls.create_training_data(
            employee_id=employee_id,
            pose_type=pose_type,
            face_encoding=face_encoding,
            image_quality_score=image_quality_score
        )
        
        db.session.add(new_training_data)
        db.session.commit()
        return new_training_data
    
    # NEW: Kiểm tra đủ pose training
    @classmethod
    def has_sufficient_poses(cls, employee_id, required_poses=None, min_quality=35):
        """Kiểm tra nhân viên đã train đủ pose chưa"""
        if required_poses is None:
            required_poses = ['front', 'left', 'right', 'up', 'down']
        
        trained_poses = set(cls.get_employee_trained_poses(employee_id))
        
        # Nếu có min_quality, chỉ đếm pose có quality >= min_quality
        if min_quality is not None:
            quality_poses = cls.query.filter(
                cls.employee_id == employee_id,
                cls.image_quality_score >= min_quality
            ).with_entities(cls.pose_type).all()
            trained_poses = set([r.pose_type for r in quality_poses])
        
        missing_poses = set(required_poses) - trained_poses
        return len(missing_poses) == 0, list(missing_poses)
    
    def __repr__(self):
        """Trả về chuỗi mô tả training data"""
        return f'<FaceTrainingData {self.employee_id}:{self.pose_type} Q:{self.image_quality_score}>'