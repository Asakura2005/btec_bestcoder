import os
import math
import base64
from datetime import datetime
import cv2
import dlib
import numpy as np
import insightface

# === Local imports ===
from app.models.employee import Employee
from app.models.face_training_data import FaceTrainingData

# --------------------------------------------------
# Load models once at module import
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "shape_predictor_68_face_landmarks.dat"))
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Landmark model not found at %s" % MODEL_PATH)

_shape_predictor = dlib.shape_predictor(MODEL_PATH)
_face_detector = dlib.get_frontal_face_detector()
_face_analyzer = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
_face_analyzer.prepare(ctx_id=0)

def _extract_landmarks(image_bgr: np.ndarray):
    """Return landmarks (68,2) or None if not exactly one face."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    rects = _face_detector(gray, 1)
    if len(rects) != 1:
        return None
    shape = _shape_predictor(gray, rects[0])
    coords = np.zeros((68, 2), dtype="float")
    for i in range(68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords

# --------------------------------------------------
# Simplified LivenessChecker
# --------------------------------------------------
class LivenessChecker:
    def __init__(self):
        self.actions = ['blink', 'smile', 'head_movement']

    def detect_blink(self, landmarks):
        def ear(eye):
            A = np.linalg.norm(eye[1] - eye[5])
            B = np.linalg.norm(eye[2] - eye[4])
            C = np.linalg.norm(eye[0] - eye[3])
            return (A + B) / (2.0 * C)
        left, right = landmarks[36:42], landmarks[42:48]
        return (ear(left) + ear(right)) / 2 < 0.25

    def detect_smile(self, landmarks):
        mouth = landmarks[48:68]
        width = np.linalg.norm(mouth[0] - mouth[6])
        height = np.linalg.norm(mouth[3] - mouth[9])
        ratio = (width / height) if height else 0
        return ratio > 3.0

    def detect_head_movement(self, frames_data, min_distance=6.0):
        """Simple head movement detection - just check angle changes"""
        if len(frames_data) < 5:
            return False
        
        angles = []
        for frame_data in frames_data:
            landmarks = frame_data['landmarks']
            left_eye = landmarks[36:42].mean(axis=0)
            right_eye = landmarks[42:48].mean(axis=0)
            nose_tip = landmarks[30]
            face_center_x = (landmarks[0][0] + landmarks[16][0]) / 2
            
            # Simple angle calculation
            yaw = abs(nose_tip[0] - face_center_x)
            roll = abs(math.degrees(math.atan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0])))
            angles.append((yaw, roll))
        
        # Check for significant movement
        max_yaw_change = max(abs(angles[i][0] - angles[i-1][0]) for i in range(1, len(angles)))
        max_roll_change = max(abs(angles[i][1] - angles[i-1][1]) for i in range(1, len(angles)))
        
        return max_yaw_change > min_distance or max_roll_change > min_distance

# --------------------------------------------------
# Global Liveness Session Management
# --------------------------------------------------
LIVENESS_SESSIONS = {}
SESSION_TIMEOUT_SECONDS = 5
MAX_FRAMES_PER_SESSION = 30

# --------------------------------------------------
# Main Service Class
# --------------------------------------------------
class FacialRecognitionService:
    liveness_checker = LivenessChecker()

    @staticmethod
    def _bytes_to_image(image_bytes: bytes):
        arr = np.frombuffer(image_bytes, np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)

    @staticmethod
    def decode_base64_image(b64: str):
        try:
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            return FacialRecognitionService._bytes_to_image(base64.b64decode(b64))
        except Exception:
            return None

    @staticmethod
    def calculate_image_quality(img):
        """Simple quality score based on sharpness and contrast"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        sharp = cv2.Laplacian(gray, cv2.CV_64F).var()
        contrast = gray.std()
        return min(100, (sharp/100)*50 + (contrast/50)*50)

    @staticmethod
    def _get_pose_from_angles(pitch, yaw, roll):
        """Convert angles to pose type"""
        if yaw > 15: return "right"
        elif yaw < -15: return "left"
        elif pitch > 15: return "down"  
        elif pitch < -15: return "up"
        else: return "front"

    @staticmethod
    def detect_face_pose(img, faces):
        """Determine face pose from InsightFace"""
        if not faces or len(faces) != 1:
            return "unknown", 0.0
        face = faces[0]
        pitch, yaw, roll = face.pose[0], face.pose[1], face.pose[2]
        pose_type = FacialRecognitionService._get_pose_from_angles(pitch, yaw, roll)
        return pose_type, 0.0

    @staticmethod
    def generate_face_encoding_with_metadata(file_like, pose_type=None, employee_id=None):
        """Generate face encoding with metadata"""
        img = FacialRecognitionService._bytes_to_image(file_like.read())
        if img is None:
            return False, "Invalid image", None, None

        # Check lighting
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if gray.mean() < 50:
            return False, "Insufficient lighting", None, None

        # Detect face and generate embedding
        faces = _face_analyzer.get(img)
        if not faces or len(faces) != 1:
            return False, "Please ensure exactly one face is visible", None, None

        face = faces[0]
        embedding = face.embedding.astype(np.float32).tobytes()
        quality = FacialRecognitionService.calculate_image_quality(img)
        
        # Auto-detect pose
        if not pose_type:
            pose_type, _ = FacialRecognitionService.detect_face_pose(img, faces)

        metadata = {
            "pose_type": pose_type,
            "image_quality_score": quality
        }

        # Update training completion if needed
        if employee_id:
            try:
                employee = Employee.query.filter_by(employee_id=employee_id).first()
                if employee:
                    has_sufficient, _ = FaceTrainingData.has_sufficient_poses(employee_id, min_quality=25)
                    if has_sufficient and not employee.face_training_completed:
                        employee.complete_face_training()
            except Exception as e:
                print(f"Error updating training completion: {e}")

        return True, "Success", embedding, metadata

    @staticmethod
    def detect_liveness(img, session_id: str):
        """Enhanced liveness detection"""
        current_time = datetime.now()
        
        # Clean old sessions
        for sid in list(LIVENESS_SESSIONS.keys()):
            if (current_time - LIVENESS_SESSIONS[sid]['last_update']).total_seconds() > SESSION_TIMEOUT_SECONDS:
                del LIVENESS_SESSIONS[sid]

        # Initialize session
        if session_id not in LIVENESS_SESSIONS:
            LIVENESS_SESSIONS[session_id] = {
                'frames_data': [],
                'liveness_passed': False,
                'last_update': current_time,
                'blink_detected': False,
                'smile_detected': False,
                'head_movement_detected': False
            }

        session_data = LIVENESS_SESSIONS[session_id]
        session_data['last_update'] = current_time

        # Check lighting
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if np.std(gray) < 10:
            if session_id in LIVENESS_SESSIONS:
                del LIVENESS_SESSIONS[session_id]
            return False, "Lighting too dim"

        # Extract landmarks
        landmarks = _extract_landmarks(img)
        if landmarks is None:
            return False, "Unable to detect face"

        # Add frame data
        session_data['frames_data'].append({
            'timestamp': current_time,
            'landmarks': landmarks
        })

        # Clean old frames
        session_data['frames_data'] = [
            f for f in session_data['frames_data']
            if (current_time - f['timestamp']).total_seconds() <= SESSION_TIMEOUT_SECONDS
        ]
        
        if len(session_data['frames_data']) > MAX_FRAMES_PER_SESSION:
            session_data['frames_data'].pop(0)

        # Check liveness actions
        if not session_data['liveness_passed']:
            checker = FacialRecognitionService.liveness_checker

            # Check blink
            if not session_data['blink_detected']:
                for frame_data in session_data['frames_data']:
                    if checker.detect_blink(frame_data['landmarks']):
                        session_data['blink_detected'] = True
                        break

            # Check smile  
            if not session_data['smile_detected']:
                for frame_data in session_data['frames_data']:
                    if checker.detect_smile(frame_data['landmarks']):
                        session_data['smile_detected'] = True
                        break

            # Check head movement
            if not session_data['head_movement_detected']:
                if checker.detect_head_movement(session_data['frames_data']):
                    session_data['head_movement_detected'] = True

            # Pass if any action detected
            actions_detected = [
                session_data['blink_detected'],
                session_data['smile_detected'], 
                session_data['head_movement_detected']
            ]
            
            if any(actions_detected):
                session_data['liveness_passed'] = True
                detected = [a for a, d in zip(['blink', 'smile', 'head movement'], actions_detected) if d]
                return True, f"Liveness passed: {', '.join(detected)}"
            else:
                # Check timeout
                if session_data['frames_data'] and \
                   (current_time - session_data['frames_data'][0]['timestamp']).total_seconds() > SESSION_TIMEOUT_SECONDS:
                    del LIVENESS_SESSIONS[session_id]
                    return False, "Liveness timeout. Please blink, smile, or move your head."
                return False, "Please blink, smile, or gently move your head."
        
        return True, "Liveness check successful"

    @staticmethod
    def recognize_face_with_multiple_encodings(img):
        """Face recognition with multiple encodings"""
        faces = _face_analyzer.get(img)
        if not faces or len(faces) != 1:
            return False, "Image must contain exactly one face", None

        # Normalize query embedding
        query_embedding = faces[0].embedding.astype(np.float32)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Get active employees with completed training
        employees = Employee.query.filter_by(status=True, face_training_completed=True).all()
        if not employees:
            return False, "No employees have completed face training", None

        best_match = {"distance": float("inf"), "employee": None}

        for emp in employees:
            training_data_list = FaceTrainingData.get_employee_encodings(emp.employee_id)
            if not training_data_list:
                continue

            for d in training_data_list:
                try:
                    stored_embedding = np.frombuffer(d.face_encoding, dtype=np.float32)
                    if stored_embedding.shape[0] != 512:
                        continue
                    stored_embedding = stored_embedding / np.linalg.norm(stored_embedding)
                except Exception:
                    continue

                # Filter by quality
                if d.image_quality_score is not None and d.image_quality_score < 35:
                    continue

                # Calculate cosine distance
                cos_sim = np.dot(query_embedding, stored_embedding)
                distance = 1 - cos_sim

                if distance < best_match["distance"]:
                    best_match["distance"] = distance
                    best_match["employee"] = emp

        # Check threshold
        THRESHOLD = 0.35
        if best_match["employee"] and best_match["distance"] < THRESHOLD:
            print(f"Tìm thấy khớp: {best_match['employee'].employee_id} – Khoảng cách: {best_match['distance']:.4f}")
            return True, "Face recognized successfully", best_match["employee"]
        else:
            return False, "Face does not match any registered employee", None

    @staticmethod
    def recognize_face_with_liveness(img, session_id: str):
        """Recognition with liveness check"""
        live_ok, live_msg = FacialRecognitionService.detect_liveness(img, session_id)
        if not live_ok:
            return False, live_msg, None
        return FacialRecognitionService.recognize_face_with_multiple_encodings(img)

    @staticmethod  
    def get_required_poses():
        return ["front", "left", "right", "up", "down"]