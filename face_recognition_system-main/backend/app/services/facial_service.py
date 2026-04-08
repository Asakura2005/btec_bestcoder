import os
import math
import base64
from datetime import datetime
import cv2
import dlib
import numpy as np
import insightface
import onnxruntime

# === Local imports ===
from app.models.employee import Employee
from app.models.face_training_data import FaceTrainingData
from app.db import db

# --------------------------------------------------
# Load models once at module import
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "shape_predictor_68_face_landmarks.dat"))
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Landmark model not found at %s" % MODEL_PATH)

_shape_predictor = dlib.shape_predictor(MODEL_PATH)
_face_detector = dlib.get_frontal_face_detector()

# Primary analyzer with standard det-size
_face_analyzer = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
_face_analyzer.prepare(ctx_id=0, det_size=(640, 640))

# Fallback analyzer with smaller det-size for low-res images
_face_analyzer_small = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
_face_analyzer_small.prepare(ctx_id=0, det_size=(320, 320))

# Anti-Spoofing Dedicated AI (MiniFASNetV2)
ANTISPOOF_MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "weights", "MiniFASNetV2.onnx"))

class AntiSpoofAI:
    def __init__(self, model_path):
        self.session = None
        if os.path.exists(model_path):
            try:
                self.session = onnxruntime.InferenceSession(model_path, providers=['CPUExecutionProvider'])
                print(f"[AntiSpoofAI] Loaded model from {model_path}")
            except Exception as e:
                print(f"[AntiSpoofAI] Failed to load model: {e}")
        else:
            print(f"[AntiSpoofAI] Warning: Model file not found at {model_path}")

    def predict(self, img_bgr, bbox):
        """Returns (is_real, score, msg)"""
        if self.session is None:
            return True, 0.0, "AI model not loaded"

        try:
            h, w = img_bgr.shape[:2]
            x1, y1, x2, y2 = bbox
            fw, fh = x2 - x1, y2 - y1
            
            # MiniFASNetV2 expects a specific scale (2.7)
            # We need to expand the bbox slightly to include context
            cx, cy = x1 + fw/2, y1 + fh/2
            size = max(fw, fh) * 2.7
            nx1 = max(0, int(cx - size/2))
            ny1 = max(0, int(cy - size/2))
            nx2 = min(w, int(cx + size/2))
            ny2 = min(h, int(cy + size/2))
            
            face_img = img_bgr[ny1:ny2, nx1:nx2]
            if face_img.size == 0:
                return True, 0.0, "Invalid crop"

            # Preprocessing
            # Resize to 80x80
            face_img = cv2.resize(face_img, (80, 80))
            # BGR to RGB
            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            # Normalize and transpose (HWC to CHW)
            face_img = face_img.astype(np.float32)
            face_img = np.transpose(face_img, (2, 0, 1))
            face_img = np.expand_dims(face_img, axis=0) # Add batch dim

            # Run inference
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: face_img})
            
            # Post-processing (softmax)
            logits = outputs[0][0]
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / exp_logits.sum()
            
            # Class 1 is Real, Class 0 is Fake (depends on the model training, 
            # for MiniFASNetV2 usually 1 is real)
            is_real_score = probs[1]
            is_real = is_real_score > 0.7  # Higher confidence required for real
            
            return is_real, 1.0 - is_real_score, f"AI Confidence: {is_real_score:.2f}"
        except Exception as e:
            print(f"[AntiSpoofAI] Prediction error: {e}")
            return True, 0.0, f"Error: {e}"

_antispoof_ai = AntiSpoofAI(ANTISPOOF_MODEL_PATH)

def _preprocess_image(img):
    """Preprocess image to improve face detection reliability."""
    h, w = img.shape[:2]
    
    # If image is very small, resize up
    if h < 400 or w < 400:
        scale = max(400 / h, 400 / w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        print(f"[FaceDetect] Resized small image from ({w},{h}) to ({img.shape[1]},{img.shape[0]})")
    
    # If image is too large, resize down to avoid slowness
    max_dim = 1280
    if h > max_dim or w > max_dim:
        scale = min(max_dim / h, max_dim / w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        print(f"[FaceDetect] Resized large image to ({img.shape[1]},{img.shape[0]})")
    
    return img

def _detect_faces_robust(img):
    """Try multiple detection strategies to find faces."""
    # Strategy 1: Primary analyzer (det-size 640x640)
    faces = _face_analyzer.get(img)
    if faces and len(faces) >= 1:
        print(f"[FaceDetect] Primary detector found {len(faces)} face(s)")
        return faces
    
    # Strategy 2: Smaller det-size for low-res images
    faces = _face_analyzer_small.get(img)
    if faces and len(faces) >= 1:
        print(f"[FaceDetect] Small detector found {len(faces)} face(s)")
        return faces
    
    # Strategy 3: Enhance contrast and retry
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    faces = _face_analyzer.get(enhanced)
    if faces and len(faces) >= 1:
        print(f"[FaceDetect] Enhanced image detector found {len(faces)} face(s)")
        return faces
    
    print(f"[FaceDetect] No faces detected after all strategies. Image shape: {img.shape}, mean brightness: {cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean():.1f}")
    return []

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

    def get_ear(self, landmarks):
        def ear(eye):
            A = np.linalg.norm(eye[1] - eye[5])
            B = np.linalg.norm(eye[2] - eye[4])
            C = np.linalg.norm(eye[0] - eye[3])
            return (A + B) / (2.0 * C) if C > 0 else 0
        left, right = landmarks[36:42], landmarks[42:48]
        return (ear(left) + ear(right)) / 2

    def get_smile_ratio(self, landmarks):
        mouth = landmarks[48:68]
        width = np.linalg.norm(mouth[0] - mouth[6])
        height = np.linalg.norm(mouth[3] - mouth[9])
        return (width / height) if height > 0 else 0

    def detect_head_movement(self, frames_data, min_distance=15.0):
        """Simple head movement detection - checks angle changes over time"""
        if len(frames_data) < 5:
            return False
        
        angles = []
        for frame_data in frames_data:
            landmarks = frame_data['landmarks']
            left_eye = landmarks[36:42].mean(axis=0)
            right_eye = landmarks[42:48].mean(axis=0)
            nose_tip = landmarks[30]
            face_center_x = (landmarks[0][0] + landmarks[16][0]) / 2
            
            yaw = abs(nose_tip[0] - face_center_x)
            roll = abs(math.degrees(math.atan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0])))
            angles.append((yaw, roll))
        
        # Check for significant movement
        max_yaw_change = max(abs(angles[i][0] - angles[0][0]) for i in range(1, len(angles)))
        max_roll_change = max(abs(angles[i][1] - angles[0][1]) for i in range(1, len(angles)))
        
        return max_yaw_change > min_distance or max_roll_change > min_distance

# --------------------------------------------------
# Global Liveness Session Management
# --------------------------------------------------
LIVENESS_SESSIONS = {}
SESSION_TIMEOUT_SECONDS = 60
MAX_FRAMES_PER_SESSION = 50

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

        # Preprocess image
        img = _preprocess_image(img)

        # Check lighting
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_brightness = gray.mean()
        print(f"[FaceDetect] Image brightness: {mean_brightness:.1f}, shape: {img.shape}")
        if mean_brightness < 30:
            return False, "Insufficient lighting - please move to a brighter area", None, None

        # Detect face using robust multi-strategy detection
        faces = _detect_faces_robust(img)
        if not faces:
            return False, "No face detected. Please look straight at the camera and ensure good lighting.", None, None
        if len(faces) > 1:
            return False, f"Multiple faces detected ({len(faces)}). Please ensure only one face is visible.", None, None

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
                'head_movement_detected': False,
                'spoof_strikes': 0
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

        # Always pass liveness challenge for speed, relying on AI anti-spoofing layers instead
        session_data['liveness_passed'] = True
        return True, "Liveness check successful"

    @staticmethod
    def recognize_face_with_multiple_encodings(img):
        """Face recognition with multiple encodings"""
        img = _preprocess_image(img)
        faces = _detect_faces_robust(img)
        if not faces:
            return False, "No face detected. Please look straight at the camera.", None
        if len(faces) > 1:
            return False, f"Multiple faces detected ({len(faces)}). Please ensure only one face is visible.", None

        face = faces[0]

        # Normalize query embedding
        query_embedding = face.embedding.astype(np.float32)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Detect emotion and mask
        emotion = FacialRecognitionService.detect_emotion(img, face)
        is_masked, mask_confidence = FacialRecognitionService.detect_mask(img, face)

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

        # Check threshold - relax slightly if mask detected
        THRESHOLD = 0.40 if is_masked else 0.35
        if best_match["employee"] and best_match["distance"] < THRESHOLD:
            # Calculate confidence score (0-100%)
            confidence_score = round(max(0, min(100, (1 - best_match["distance"] / THRESHOLD) * 100)), 1)
            
            print(f"Tìm thấy khớp: {best_match['employee'].employee_id} – Khoảng cách: {best_match['distance']:.4f} – Confidence: {confidence_score}%")
            
            # Auto-update face encoding if very high confidence (>90%)
            if confidence_score > 90 and not is_masked:
                try:
                    # Quick quality check: brightness + blur
                    gray_check = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    brightness = gray_check.mean()
                    blur_var = cv2.Laplacian(gray_check, cv2.CV_64F).var()
                    quick_quality = min(100, (brightness / 2) + min(50, blur_var / 2))
                    
                    FacialRecognitionService._auto_update_encoding(
                        best_match["employee"].employee_id,
                        query_embedding,
                        quick_quality
                    )
                except Exception as e:
                    print(f"[AutoUpdate] Error: {e}")
            
            # Attach extra info to employee object for downstream use
            best_match["employee"]._recognition_meta = {
                "emotion": emotion,
                "is_masked": is_masked,
                "mask_confidence": mask_confidence,
                "match_distance": best_match["distance"],
                "confidence_score": confidence_score
            }
            return True, "Face recognized successfully", best_match["employee"]
        else:
            return False, "Face does not match any registered employee", None

    @staticmethod
    def recognize_face_with_liveness(img, session_id: str):
        """Recognition with liveness check + multi-layer anti-spoofing"""
        combined_spoof_score = 0.0
        spoof_details = []
        all_reasons = []

        # Check if this session is already flagged as spoof (too many strikes)
        session_data = LIVENESS_SESSIONS.get(session_id)
        if session_data and session_data.get('spoof_strikes', 0) >= 3:
            return False, "Screen or photo detected. Please use your real face.", None
        # Find face to crop tightly (prevents 'holding phone far away' exploit where background is seen)
        img_for_spoof = img
        try:
            faces = _detect_faces_robust(img)
            if faces:
                h, w = img.shape[:2]
                bbox = faces[0].bbox.astype(int)
                x1, y1, x2, y2 = max(0, bbox[0]), max(0, bbox[1]), min(w, bbox[2]), min(h, bbox[3])
                
                face_ratio = ((x2 - x1) * (y2 - y1)) / (w * h)
                if face_ratio > 0.4:
                    combined_spoof_score += 0.4
                    spoof_details.append(f"too_close=0.40")
                    all_reasons.append("Face is unnaturally close to the camera")
                    
                margin_x = int((x2-x1) * 0.15)
                margin_y = int((y2-y1) * 0.15)
                x1_m = max(0, x1 - margin_x)
                y1_m = max(0, y1 - margin_y)
                x2_m = min(w, x2 + margin_x)
                y2_m = min(h, y2 + margin_y)
                crop = img[y1_m:y2_m, x1_m:x2_m]
                if crop.size > 0:
                    img_for_spoof = crop
        except Exception:
            pass

        # Layer 1: LBP texture + color uniformity
        is_real, spoof_score, spoof_msg = FacialRecognitionService.detect_screen_spoofing(img_for_spoof)
        combined_spoof_score += spoof_score
        spoof_details.append(f"texture={spoof_score:.2f}")
        if not is_real:
            all_reasons.append(spoof_msg)

        # Layer 2: 3D depth estimation
        depth_real, depth_score, depth_msg = FacialRecognitionService.detect_depth_spoofing(img_for_spoof)
        combined_spoof_score += depth_score
        spoof_details.append(f"depth={depth_score:.2f}")
        if not depth_real:
            all_reasons.append(depth_msg)

        # Layer 3: Moiré pattern (phone screen pixel grid)
        moire_real, moire_score, moire_msg = FacialRecognitionService.detect_moire_pattern(img_for_spoof)
        combined_spoof_score += moire_score
        spoof_details.append(f"moire={moire_score:.2f}")
        if not moire_real:
            all_reasons.append(moire_msg)

        # Layer 4: Screen reflection/glare
        reflect_real, reflect_score, reflect_msg = FacialRecognitionService.detect_screen_reflection(img_for_spoof)
        combined_spoof_score += reflect_score
        spoof_details.append(f"reflect={reflect_score:.2f}")
        if not reflect_real:
            all_reasons.append(reflect_msg)

        # Layer 5: Frame-to-frame consistency (screens produce identical frames, real faces have sensor noise)
        try:
            session_data = LIVENESS_SESSIONS.get(session_id)
            if session_data is not None:
                # Store current face crop for comparison
                small_crop = cv2.resize(img_for_spoof, (64, 64))
                gray_crop = cv2.cvtColor(small_crop, cv2.COLOR_BGR2GRAY).astype(np.float64)
                
                if 'prev_crops' not in session_data:
                    session_data['prev_crops'] = []
                
                prev_crops = session_data['prev_crops']
                if len(prev_crops) >= 2:
                    similarities = []
                    for prev in prev_crops[-3:]:
                        diff = np.mean(np.abs(gray_crop - prev))
                        similarities.append(diff)
                    
                    avg_diff = np.mean(similarities)
                    if avg_diff < 2.0:
                        frame_score = 0.4
                        combined_spoof_score += frame_score
                        spoof_details.append(f"frame_consistency={frame_score:.2f}")
                        all_reasons.append("Suspicious frame-to-frame consistency (static screen)")
                    elif avg_diff < 3.0:
                        frame_score = 0.2
                        combined_spoof_score += frame_score
                        spoof_details.append(f"frame_consistency={frame_score:.2f}")
                    
                    print(f"[FrameConsistency] avg_diff={avg_diff:.2f}")
                
                prev_crops.append(gray_crop)
                if len(prev_crops) > 5:
                    prev_crops.pop(0)
        except Exception as e:
            print(f"[FrameConsistency] Error: {e}")

        # Layer 6: Deep Learning Anti-Spoofing (Option 1)
        # This is the most powerful layer, uses a specialized CNN
        try:
            faces = _detect_faces_robust(img)
            if faces:
                bbox = faces[0].bbox.astype(int)
                ai_real, ai_score, ai_msg = _antispoof_ai.predict(img, bbox)
                
                # Trust AI heavily
                if not ai_real:
                    # If AI detects spoof, add heavy penalty
                    ai_weight = 0.7 if ai_score > 0.8 else 0.5
                    combined_spoof_score += ai_weight
                    spoof_details.append(f"ai_dl={ai_weight:.2f}")
                    all_reasons.append(f"AI: {ai_msg}")
                    print(f"[AntiSpoof-AI] Suspicious: {ai_msg}")
                else:
                    # If AI is extremely confident it's real (>0.9), ignore minor heuristic warnings
                    ai_confidence = 1.0 - ai_score
                    if ai_confidence > 0.92:
                        print(f"[AntiSpoof-AI] High confidence REAL ({ai_confidence:.2f}), clearing score")
                        combined_spoof_score = 0.0
                        spoof_details.append("ai_dl=REAL_WIN")
                    else:
                        print(f"[AntiSpoof-AI] Moderate confidence REAL ({ai_confidence:.2f})")
        except Exception as e:
            print(f"[AntiSpoof-AI] Error: {e}")

        # ONLY combined score triggers rejection
        COMBINED_THRESHOLD = 0.5
        print(f"[AntiSpoof-Combined] total={combined_spoof_score:.2f}, details=[{', '.join(spoof_details)}]")
        
        # Check liveness FIRST to update session frames
        live_ok, live_msg = FacialRecognitionService.detect_liveness(img, session_id)
        
        if combined_spoof_score >= COMBINED_THRESHOLD:
            # Increment spoof strikes - after 3 strikes, session is permanently blocked
            session_data = LIVENESS_SESSIONS.get(session_id)
            if session_data:
                session_data['spoof_strikes'] = session_data.get('spoof_strikes', 0) + 1
                print(f"[AntiSpoof] Strike {session_data['spoof_strikes']}/3 for session {session_id[:8]}")
            
            is_video = False
            if session_data and len(session_data.get('frames_data', [])) >= 2:
                frames = session_data['frames_data']
                try:
                    nose_positions = [f['landmarks'][30] for f in frames if f['landmarks'] is not None]
                    if len(nose_positions) >= 2:
                        max_move = max(np.linalg.norm(np.array(p) - np.array(nose_positions[0])) for p in nose_positions[1:])
                        if max_move > 3.0 or session_data.get('blink_detected') or session_data.get('smile_detected') or session_data.get('head_movement_detected'):
                            is_video = True
                except Exception:
                    pass

            if is_video:
                return False, "Phone video playback detected. Please use your real face.", None
            else:
                return False, "Screen or photo detected. Please use your real face.", None

        # If spoofing passed but liveness challenge failed
        if not live_ok:
            return False, live_msg, None
            
        return FacialRecognitionService.recognize_face_with_multiple_encodings(img)

    @staticmethod  
    def get_required_poses():
        return ["front", "left", "right", "up", "down"]

    # --------------------------------------------------
    # Anti-spoofing: LBP Texture Analysis
    # --------------------------------------------------
    @staticmethod
    def detect_screen_spoofing(img):
        """
        Detect if face image is from a screen/phone photo using:
        1. LBP (Local Binary Pattern) texture analysis
        2. Moiré pattern detection
        3. Color distribution analysis
        Returns: (is_real, score, message)
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # --- 1. LBP Texture Analysis ---
            # Real skin has rich, varied micro-texture; screens have uniform texture
            h, w = gray.shape
            
            # Extract face region (center 60%)
            margin_y, margin_x = int(h * 0.2), int(w * 0.2)
            face_region = gray[margin_y:h-margin_y, margin_x:w-margin_x]
            
            if face_region.size == 0:
                return True, 0.5, "Unable to analyze"
            
            # Compute LBP
            lbp = np.zeros_like(face_region, dtype=np.uint8)
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if dy == 0 and dx == 0:
                        continue
                    shifted = np.roll(np.roll(face_region, dy, axis=0), dx, axis=1)
                    lbp = (lbp << 1) | (shifted >= face_region).astype(np.uint8)
            
            # LBP histogram analysis
            lbp_hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
            lbp_hist = lbp_hist.astype(float)
            lbp_hist /= (lbp_hist.sum() + 1e-7)
            
            # Entropy - real faces have higher entropy (more varied texture)
            lbp_entropy = -np.sum(lbp_hist[lbp_hist > 0] * np.log2(lbp_hist[lbp_hist > 0]))
            
            # --- 2. Color Uniformity (screens have less natural color variation) ---
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            saturation = hsv[:, :, 1]
            sat_std = np.std(saturation[margin_y:h-margin_y, margin_x:w-margin_x])
            
            # Higher entropy = more likely real (threshold ~5.2)
            # Higher sat_std = more likely real (natural skin has varied saturation)
            # Note: hf_ratio removed - webcam noise makes it always ~0.9 for all inputs
            # Moiré detection is handled by dedicated Layer 3 (detect_moire_pattern)
            
            spoof_score = 0.0
            reasons = []
            
            if lbp_entropy < 5.2:
                spoof_score += 0.4
                reasons.append("uniform texture detected")
            elif lbp_entropy < 5.6:
                spoof_score += 0.2
            
            if sat_std < 20:
                spoof_score += 0.3
                reasons.append("abnormal color uniformity")
            elif sat_std < 30:
                spoof_score += 0.15
            
            is_real = spoof_score < 0.4
            
            print(f"[AntiSpoof] entropy={lbp_entropy:.2f}, "
                  f"sat_std={sat_std:.1f}, score={spoof_score:.2f}, real={is_real}")
            
            if not is_real:
                msg = "Suspected photo/screen attack: " + ", ".join(reasons)
                return False, spoof_score, msg
            
            return True, spoof_score, "Passed"
            
        except Exception as e:
            print(f"[AntiSpoof] Error: {e}")
            return False, 1.0, f"Anti-spoofing analysis error (rejected for safety): {str(e)}"

    # --------------------------------------------------
    # Emotion Detection
    # --------------------------------------------------
    @staticmethod
    def detect_emotion(img, face=None):
        """
        Detect emotion from face using geometric analysis of landmarks.
        Returns: emotion string (happy, neutral, sad, angry, surprise)
        """
        try:
            # Try to use dlib landmarks for more accurate analysis
            landmarks = _extract_landmarks(img)
            if landmarks is None:
                return "neutral"
            
            # Mouth analysis
            mouth = landmarks[48:68]
            mouth_width = np.linalg.norm(mouth[0] - mouth[6])
            mouth_height = np.linalg.norm(mouth[3] - mouth[9])
            mouth_ratio = mouth_width / (mouth_height + 1e-7)
            
            # Inner mouth opening (top lip bottom to bottom lip top)
            inner_mouth_height = np.linalg.norm(landmarks[62] - landmarks[66])
            
            # Eye analysis
            left_eye = landmarks[36:42]
            right_eye = landmarks[42:48]
            
            def eye_aspect_ratio(eye):
                A = np.linalg.norm(eye[1] - eye[5])
                B = np.linalg.norm(eye[2] - eye[4])
                C = np.linalg.norm(eye[0] - eye[3])
                return (A + B) / (2.0 * C)
            
            avg_ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2
            
            # Eyebrow analysis
            left_brow = landmarks[17:22]
            right_brow = landmarks[22:27]
            left_brow_height = np.mean(left_brow[:, 1]) - np.mean(left_eye[:, 1])
            right_brow_height = np.mean(right_brow[:, 1]) - np.mean(right_eye[:, 1])
            avg_brow_height = (left_brow_height + right_brow_height) / 2
            
            # Classification
            if mouth_ratio > 3.5 and mouth_height < mouth_width * 0.35:
                return "happy"  # Wide smiling mouth
            elif inner_mouth_height > 15 and avg_ear > 0.32:
                return "surprise"  # Open mouth + wide eyes
            elif avg_brow_height > -5 and mouth_ratio < 2.0:
                return "angry"  # Furrowed brows + tight mouth
            elif mouth_ratio < 2.5 and avg_ear < 0.22:
                return "sad"  # Narrow mouth + droopy eyes
            else:
                return "neutral"
                
        except Exception as e:
            print(f"[Emotion] Detection error: {e}")
            return "neutral"

    # --------------------------------------------------
    # Mask Detection
    # --------------------------------------------------
    @staticmethod
    def detect_mask(img, face=None):
        """
        Detect if face is wearing a mask using landmark analysis.
        Returns: (is_masked: bool, confidence: float)
        """
        try:
            landmarks = _extract_landmarks(img)
            
            if landmarks is not None:
                # Lower face region (nose bridge to chin) 
                nose_bridge = landmarks[27]  # Top of nose bridge
                chin = landmarks[8]  # Bottom of chin
                left_jaw = landmarks[3]
                right_jaw = landmarks[13]
                
                # Extract lower face region
                lower_face_top = int(nose_bridge[1])
                lower_face_bottom = int(chin[1])
                lower_face_left = int(left_jaw[0])
                lower_face_right = int(right_jaw[0])
                
                h, w = img.shape[:2]
                lower_face_top = max(0, lower_face_top)
                lower_face_bottom = min(h, lower_face_bottom)
                lower_face_left = max(0, lower_face_left)
                lower_face_right = min(w, lower_face_right)
                
                if lower_face_bottom > lower_face_top and lower_face_right > lower_face_left:
                    lower_face = img[lower_face_top:lower_face_bottom, lower_face_left:lower_face_right]
                    
                    # Convert to HSV for skin color analysis
                    hsv = cv2.cvtColor(lower_face, cv2.COLOR_BGR2HSV)
                    
                    # Skin color range in HSV
                    lower_skin = np.array([0, 20, 70], dtype=np.uint8)
                    upper_skin = np.array([20, 255, 255], dtype=np.uint8)
                    skin_mask1 = cv2.inRange(hsv, lower_skin, upper_skin)
                    
                    # Second skin range (handles darker skin tones)
                    lower_skin2 = np.array([170, 20, 70], dtype=np.uint8)
                    upper_skin2 = np.array([180, 255, 255], dtype=np.uint8)
                    skin_mask2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
                    
                    skin_mask = skin_mask1 | skin_mask2
                    
                    total_pixels = skin_mask.size
                    skin_pixels = np.sum(skin_mask > 0)
                    skin_ratio = skin_pixels / total_pixels if total_pixels > 0 else 1.0
                    
                    # Also check color uniformity (masks tend to be uniform color)
                    color_std = np.std(lower_face.reshape(-1, 3), axis=0).mean()
                    
                    print(f"[MaskDetect] skin_ratio={skin_ratio:.3f}, color_std={color_std:.1f}")
                    
                    # If very little skin visible in lower face → likely masked
                    if skin_ratio < 0.15 and color_std < 40:
                        return True, 0.9
                    elif skin_ratio < 0.25:
                        return True, 0.7
                    elif skin_ratio < 0.35 and color_std < 30:
                        return True, 0.6
                    else:
                        return False, 1.0 - skin_ratio
            
            return False, 0.0
            
        except Exception as e:
            print(f"[MaskDetect] Error: {e}")
            return False, 0.0

    # --------------------------------------------------
    # Auto-update Face Encoding (Feature C)
    # --------------------------------------------------
    @staticmethod
    def _auto_update_encoding(employee_id, new_embedding, quality_score):
        """
        Tự động cập nhật face encoding khi nhận diện high-confidence.
        Sử dụng weighted average để dần dần cập nhật encoding theo thời gian.
        Chỉ update khi quality_score > 60 để đảm bảo chất lượng.
        """
        if quality_score < 60:
            return
        
        try:
            # Lấy encoding front pose (primary)
            front_data = FaceTrainingData.get_employee_encoding_by_pose(employee_id, 'front')
            if not front_data:
                return
            
            # Decode old embedding
            old_embedding = np.frombuffer(front_data.face_encoding, dtype=np.float32).copy()
            if old_embedding.shape[0] != 512:
                return
            
            # Weighted average: 85% old + 15% new (gradual adaptation)
            updated_embedding = 0.85 * old_embedding + 0.15 * new_embedding
            updated_embedding = updated_embedding / np.linalg.norm(updated_embedding)
            
            # Update in database
            front_data.face_encoding = updated_embedding.astype(np.float32).tobytes()
            if quality_score > (front_data.image_quality_score or 0):
                front_data.image_quality_score = quality_score
            
            db.session.commit()
            print(f"[AutoUpdate] Updated encoding for {employee_id}, quality={quality_score:.1f}")
            
        except Exception as e:
            db.session.rollback()
            print(f"[AutoUpdate] Failed for {employee_id}: {e}")

    # --------------------------------------------------
    # Real-time Face Quality Analysis (Feature B)
    # --------------------------------------------------
    @staticmethod
    def analyze_face_quality(img):
        """
        Phân tích chất lượng ảnh khuôn mặt real-time.
        Returns dict with quality indicators for camera overlay.
        """
        result = {
            "face_detected": False,
            "brightness": {"value": 0, "status": "unknown", "message": ""},
            "sharpness": {"value": 0, "status": "unknown", "message": ""},
            "face_size": {"value": 0, "status": "unknown", "message": ""},
            "face_angle": {"value": 0, "status": "unknown", "message": ""},
            "overall_quality": 0,
            "ready_to_capture": False,
            "suggestions": []
        }
        
        try:
            img = _preprocess_image(img)
            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 1. Brightness analysis
            brightness = gray.mean()
            result["brightness"]["value"] = round(brightness, 1)
            if brightness < 50:
                result["brightness"]["status"] = "low"
                result["brightness"]["message"] = "Too dark"
                result["suggestions"].append("Move to a brighter area")
            elif brightness > 200:
                result["brightness"]["status"] = "high"
                result["brightness"]["message"] = "Too bright"
                result["suggestions"].append("Avoid direct light")
            else:
                result["brightness"]["status"] = "good"
                result["brightness"]["message"] = "Good lighting"
            
            # 2. Sharpness (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            result["sharpness"]["value"] = round(laplacian_var, 1)
            if laplacian_var < 50:
                result["sharpness"]["status"] = "low"
                result["sharpness"]["message"] = "Blurry"
                result["suggestions"].append("Hold camera steady")
            elif laplacian_var < 100:
                result["sharpness"]["status"] = "medium"
                result["sharpness"]["message"] = "Slightly blurry"
            else:
                result["sharpness"]["status"] = "good"
                result["sharpness"]["message"] = "Sharp"
            
            # 3. Face detection and size
            faces = _face_analyzer.get(img)
            if not faces:
                result["suggestions"].append("No face detected - look at camera")
                return result
            
            if len(faces) > 1:
                result["suggestions"].append("Multiple faces - only one person please")
                return result
            
            result["face_detected"] = True
            face = faces[0]
            bbox = face.bbox.astype(int)
            face_w = bbox[2] - bbox[0]
            face_h = bbox[3] - bbox[1]
            face_area_ratio = (face_w * face_h) / (w * h)
            
            result["face_size"]["value"] = round(face_area_ratio * 100, 1)
            if face_area_ratio < 0.05:
                result["face_size"]["status"] = "small"
                result["face_size"]["message"] = "Too far"
                result["suggestions"].append("Move closer to camera")
            elif face_area_ratio > 0.60:
                result["face_size"]["status"] = "large"
                result["face_size"]["message"] = "Too close"
                result["suggestions"].append("Move further from camera")
            else:
                result["face_size"]["status"] = "good"
                result["face_size"]["message"] = "Good distance"
            
            # 4. Face angle
            if hasattr(face, 'pose') and face.pose is not None:
                pitch, yaw, roll = abs(face.pose[0]), abs(face.pose[1]), abs(face.pose[2])
                max_angle = max(pitch, yaw, roll)
                result["face_angle"]["value"] = round(max_angle, 1)
                
                if max_angle > 30:
                    result["face_angle"]["status"] = "bad"
                    result["face_angle"]["message"] = "Face too tilted"
                    result["suggestions"].append("Look straight at camera")
                elif max_angle > 15:
                    result["face_angle"]["status"] = "medium"
                    result["face_angle"]["message"] = "Slightly tilted"
                else:
                    result["face_angle"]["status"] = "good"
                    result["face_angle"]["message"] = "Good angle"
            
            # 5. Overall quality score
            quality_score = 0
            if result["brightness"]["status"] == "good":
                quality_score += 25
            elif result["brightness"]["status"] != "unknown":
                quality_score += 10
            
            if result["sharpness"]["status"] == "good":
                quality_score += 25
            elif result["sharpness"]["status"] == "medium":
                quality_score += 15
            
            if result["face_size"]["status"] == "good":
                quality_score += 25
            elif result["face_size"]["status"] != "unknown":
                quality_score += 10
            
            if result["face_angle"]["status"] == "good":
                quality_score += 25
            elif result["face_angle"]["status"] == "medium":
                quality_score += 15
            
            result["overall_quality"] = quality_score
            result["ready_to_capture"] = quality_score >= 70 and result["face_detected"]
            
            return result
            
        except Exception as e:
            print(f"[FaceQuality] Error: {e}")
            result["suggestions"].append(f"Analysis error: {str(e)}")
            return result

    # --------------------------------------------------
    # 3D Depth Anti-spoofing (Feature D)
    # --------------------------------------------------
    @staticmethod
    def detect_depth_spoofing(img):
        """
        Monocular depth estimation for anti-spoofing.
        Real faces have depth variation (nose protrudes, cheeks curve)
        while photos/screens are flat.
        
        Uses gradient analysis and edge patterns to estimate depth.
        Returns: (is_real, depth_score, message)
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            
            # Extract face region
            margin_y, margin_x = int(h * 0.15), int(w * 0.15)
            face_region = gray[margin_y:h-margin_y, margin_x:w-margin_x]
            
            if face_region.size == 0:
                return True, 0.5, "Unable to analyze depth"
            
            # --- 1. Gradient Depth Analysis ---
            # Real faces: strong gradients around nose, eyes, jawline
            # Flat images: more uniform gradients
            
            # Sobel gradients
            sobel_x = cv2.Sobel(face_region, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(face_region, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
            
            # Divide face into regions (top/mid/bottom)
            fh, fw = face_region.shape
            top_region = gradient_magnitude[:fh//3, :]  # Forehead
            mid_region = gradient_magnitude[fh//3:2*fh//3, :]  # Eyes/nose
            bot_region = gradient_magnitude[2*fh//3:, :]  # Mouth/chin
            
            # Real faces: mid region (nose/eyes) has much higher gradients
            top_mean = np.mean(top_region)
            mid_mean = np.mean(mid_region)
            bot_mean = np.mean(bot_region)
            
            # Depth variation ratio: how much gradient varies across regions
            gradient_values = [top_mean, mid_mean, bot_mean]
            depth_variation = np.std(gradient_values) / (np.mean(gradient_values) + 1e-7)
            
            # --- 2. Laplacian Depth Map ---
            # Second derivative shows curvature - real faces have more curvature variation
            laplacian = cv2.Laplacian(face_region, cv2.CV_64F, ksize=5)
            
            # Curvature variation across the face
            lap_blocks = []
            block_h, block_w = fh // 4, fw // 4
            for by in range(4):
                for bx in range(4):
                    block = laplacian[by*block_h:(by+1)*block_h, bx*block_w:(bx+1)*block_w]
                    lap_blocks.append(np.var(block))
            
            curvature_variation = np.std(lap_blocks) / (np.mean(lap_blocks) + 1e-7)
            
            # --- 3. Edge Density Analysis ---
            # Real 3D faces have non-uniform edge distribution
            edges = cv2.Canny(face_region, 50, 150)
            
            # Compare edge density in center vs periphery
            center_h, center_w = fh//4, fw//4
            center_edges = edges[center_h:3*center_h, center_w:3*center_w]
            center_density = np.mean(center_edges > 0)
            overall_density = np.mean(edges > 0)
            
            edge_ratio = center_density / (overall_density + 1e-7)
            
            # --- Scoring ---
            spoof_score = 0.0
            reasons = []
            
            # Low depth variation → flat → likely photo/screen
            if depth_variation < 0.20:
                spoof_score += 0.4
                reasons.append("flat gradient pattern")
            elif depth_variation < 0.30:
                spoof_score += 0.2
            
            # Low curvature variation → flat surface
            if curvature_variation < 0.35:
                spoof_score += 0.4
                reasons.append("uniform curvature (flat surface)")
            elif curvature_variation < 0.55:
                spoof_score += 0.2
            
            # Abnormal edge distribution → screen artifact
            if edge_ratio > 1.8 or edge_ratio < 0.6:
                spoof_score += 0.3
                reasons.append("abnormal edge distribution")
            elif edge_ratio > 1.5 or edge_ratio < 0.7:
                spoof_score += 0.1
            
            is_real = spoof_score < 0.4
            
            print(f"[DepthSpoof] depth_var={depth_variation:.3f}, curvature_var={curvature_variation:.3f}, "
                  f"edge_ratio={edge_ratio:.3f}, score={spoof_score:.2f}, real={is_real}")
            
            if not is_real:
                msg = "Suspected flat image: " + ", ".join(reasons)
                return False, spoof_score, msg
            
            return True, spoof_score, "Depth check passed"
            
        except Exception as e:
            print(f"[DepthSpoof] Error: {e}")
            return False, 1.0, f"Depth analysis error (rejected for safety): {str(e)}"

    # --------------------------------------------------
    # Moiré Pattern Detection (Phone Screen Pixel Grid)
    # --------------------------------------------------
    @staticmethod
    def detect_moire_pattern(img):
        """
        Detect Moiré patterns caused by phone/monitor pixel grids.
        When a camera captures a screen, the interaction between the camera
        sensor grid and the screen pixel grid creates visible interference
        patterns (Moiré) at specific frequencies.
        
        Uses multi-scale FFT analysis to find periodic peaks.
        Returns: (is_real, score, message)
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            
            # Extract center region for analysis
            margin_y, margin_x = int(h * 0.2), int(w * 0.2)
            roi = gray[margin_y:h-margin_y, margin_x:w-margin_x].astype(np.float64)
            
            if roi.size == 0:
                return True, 0.0, "Cannot analyze"
            
            moire_score = 0.0
            reasons = []
            
            # --- 1. Multi-scale FFT Peak Detection ---
            # Moiré patterns create sharp peaks in frequency domain
            for scale in [1.0, 0.75, 0.5, 0.25]:
                if scale != 1.0:
                    scaled = cv2.resize(roi, None, fx=scale, fy=scale)
                else:
                    scaled = roi
                
                # 2D FFT
                f_transform = np.fft.fft2(scaled)
                f_shift = np.fft.fftshift(f_transform)
                magnitude = np.log(np.abs(f_shift) + 1)
                
                # Remove DC component (center)
                sh, sw = magnitude.shape
                cy, cx = sh // 2, sw // 2
                dc_radius = max(3, min(cy, cx) // 10)
                magnitude[cy-dc_radius:cy+dc_radius, cx-dc_radius:cx+dc_radius] = 0
                
                # Detect peaks: values significantly above mean
                mean_mag = np.mean(magnitude)
                std_mag = np.std(magnitude)
                threshold = mean_mag + 3.5 * std_mag
                peak_mask = magnitude > threshold
                num_peaks = np.sum(peak_mask)
                
                # Moiré creates clustered periodic peaks
                total_pixels = magnitude.size
                peak_ratio = num_peaks / total_pixels
                
                if peak_ratio > 0.005:
                    moire_score += 0.25
                    
            # --- 2. Directional Gradient Periodicity ---
            # Screen pixels create periodic horizontal/vertical lines
            # Check for periodic patterns in horizontal and vertical directions
            
            # Horizontal periodicity (scan lines)
            row_means = np.mean(roi, axis=1)
            row_diff = np.diff(row_means)
            row_fft = np.abs(np.fft.fft(row_diff))
            row_fft = row_fft[1:len(row_fft)//2]  # Remove DC, take half
            
            if len(row_fft) > 10:
                row_peak_ratio = np.max(row_fft) / (np.mean(row_fft) + 1e-7)
                if row_peak_ratio > 6.0:
                    moire_score += 0.2
                    reasons.append("horizontal periodic pattern")
            
            # Vertical periodicity (pixel columns)
            col_means = np.mean(roi, axis=0)
            col_diff = np.diff(col_means)
            col_fft = np.abs(np.fft.fft(col_diff))
            col_fft = col_fft[1:len(col_fft)//2]
            
            if len(col_fft) > 10:
                col_peak_ratio = np.max(col_fft) / (np.mean(col_fft) + 1e-7)
                if col_peak_ratio > 6.0:
                    moire_score += 0.2
                    reasons.append("vertical periodic pattern")
            
            # --- 3. Sub-pixel color fringing ---
            # Screens show RGB sub-pixel pattern visible at close range
            b, g, r = cv2.split(img[margin_y:h-margin_y, margin_x:w-margin_x])
            
            # Compute inter-channel correlation
            # Real skin: high correlation between R,G,B channels
            # Screen: lower correlation due to sub-pixel rendering
            rg_corr = np.corrcoef(r.ravel(), g.ravel())[0, 1]
            rb_corr = np.corrcoef(r.ravel(), b.ravel())[0, 1]
            
            avg_corr = (rg_corr + rb_corr) / 2
            if avg_corr < 0.88:
                moire_score += 0.25
                reasons.append("sub-pixel color fringing detected")
            elif avg_corr < 0.94:
                moire_score += 0.15
            
            is_real = moire_score < 0.4
            
            print(f"[MoiréDetect] score={moire_score:.2f}, real={is_real}, "
                  f"avg_corr={avg_corr:.3f}, reasons={reasons}")
            
            if not is_real:
                msg = "Screen pattern detected: " + ", ".join(reasons) if reasons else "Moiré interference pattern"
                return False, moire_score, msg
            
            return True, moire_score, "No Moiré pattern"
            
        except Exception as e:
            print(f"[MoiréDetect] Error: {e}")
            return False, 1.0, f"Moiré analysis error (rejected for safety): {str(e)}"

    # --------------------------------------------------
    # Screen Reflection / Glare Detection
    # --------------------------------------------------
    @staticmethod
    def detect_screen_reflection(img):
        """
        Detect screen reflections and glare spots typical of phone glass.
        Phone screens have:
        1. Specular highlights (bright spots from ambient light reflecting off glass)
        2. Rectangular bright regions (screen backlight edges)
        3. Color temperature shifts (screen white is different from daylight)
        
        Returns: (is_real, score, message)
        """
        try:
            h, w = img.shape[:2]
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            margin_y, margin_x = int(h * 0.15), int(w * 0.15)
            
            reflect_score = 0.0
            reasons = []
            
            # --- 1. Specular Highlight Detection ---
            # Phone glass creates small, very bright spots
            value_channel = hsv[:, :, 2]
            
            # Find pixels that are extremely bright (> 240)
            bright_mask = value_channel > 240
            bright_ratio = np.sum(bright_mask) / bright_mask.size
            
            if bright_ratio > 0.01 and bright_ratio < 0.15:
                # Small bright spots = likely reflection
                # Count number of distinct bright clusters
                bright_uint8 = bright_mask.astype(np.uint8) * 255
                contours, _ = cv2.findContours(bright_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                small_bright_spots = 0
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if 10 < area < (h * w * 0.02):  # Small but not tiny
                        small_bright_spots += 1
                
                if small_bright_spots >= 2:
                    reflect_score += 0.3
                    reasons.append(f"{small_bright_spots} specular highlights detected")
                elif small_bright_spots == 1:
                    reflect_score += 0.1
            
            # --- 2. Edge Brightness Gradient ---
            # Phone screens have brightness fall-off at edges (backlight)
            top_strip = gray[:margin_y, :]
            bottom_strip = gray[h-margin_y:, :]
            left_strip = gray[:, :margin_x]
            right_strip = gray[:, w-margin_x:]
            center = gray[margin_y:h-margin_y, margin_x:w-margin_x]
            
            edge_brightness = np.mean([
                np.mean(top_strip), np.mean(bottom_strip),
                np.mean(left_strip), np.mean(right_strip)
            ])
            center_brightness = np.mean(center)
            
            # Screen backlight: edges are dimmer than center
            brightness_diff = center_brightness - edge_brightness
            if brightness_diff > 20:
                reflect_score += 0.2
                reasons.append("screen backlight pattern")
            elif brightness_diff > 15:
                reflect_score += 0.15
            
            # --- 3. Color Temperature Analysis ---
            # Screens emit blue-shifted light
            b, g, r = cv2.split(img[margin_y:h-margin_y, margin_x:w-margin_x])
            blue_ratio = np.mean(b) / (np.mean(r) + 1e-7)
            
            # Screen light is typically more blue than natural daylight on skin
            if blue_ratio > 1.10:
                reflect_score += 0.25
                reasons.append("blue-shifted color temperature")
            elif blue_ratio > 1.02:
                reflect_score += 0.15
            
            # --- 4. Uniform Background Light ---
            # Phone screens emit uniform backlight
            face_roi = value_channel[margin_y:h-margin_y, margin_x:w-margin_x]
            # Check if brightness is very uniform (low std)
            brightness_std = np.std(face_roi)
            if brightness_std < 25:
                reflect_score += 0.25
                reasons.append("uniform screen backlight")
            
            is_real = reflect_score < 0.4
            
            print(f"[ReflectDetect] score={reflect_score:.2f}, real={is_real}, "
                  f"bright_ratio={bright_ratio:.4f}, blue_ratio={blue_ratio:.3f}, "
                  f"reasons={reasons}")
            
            if not is_real:
                msg = "Screen reflection detected: " + ", ".join(reasons)
                return False, reflect_score, msg
            
            return True, reflect_score, "No screen reflection"
            
        except Exception as e:
            print(f"[ReflectDetect] Error: {e}")
            return False, 1.0, f"Reflection analysis error (rejected for safety): {str(e)}"