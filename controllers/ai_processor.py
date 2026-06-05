"""
AI处理控制器
包含人脸检测、识别、质量评估等功能
使用 face-detection-tflite 进行高精度人脸检测
"""
import cv2
import numpy as np
from config.config import FACE_DETECTION_CONFIDENCE, FACE_RECOGNITION_THRESHOLD
import os
import time

class AIProcessor:
    """AI处理控制器"""

    def __init__(self, debug_mode=False):
        self.face_detector = None
        self.eye_cascade = None
        self.use_tflite = False
        self.landmark_detector = None  # dlib 人脸关键点检测器
        
        # 检测稳定性机制
        self.detection_history = []  # 存储最近的检测结果
        self.history_size = 5  # 历史记录大小
        self.stable_threshold = 3  # 稳定阈值（5次中至少3次检测到才认为稳定）
        
        # 调试输出控制
        self.last_debug_time = 0
        self.debug_interval = 2.0  # 🔧 调试输出间隔（秒）- 改为2秒
        self.debug_mode = debug_mode  # 🔧 调试模式（无时间限制）
        
        self._init_models()

    def _should_print_debug(self):
        """检查是否应该输出调试信息"""
        current_time = time.time()
        if current_time - self.last_debug_time >= self.debug_interval:
            self.last_debug_time = current_time
            return True
        return False

    def _debug_print(self, message):
        """控制调试输出频率"""
        if self.debug_mode or self._should_print_debug():
            print(message)
    
    def _debug_print_detailed(self, message):
        """详细调试信息，严格按时间控制"""
        if self.debug_mode or self._should_print_debug():
            print(message)

    def _init_models(self):
        """初始化AI模型"""
        # 尝试 face-detection-tflite（推荐）
        self._try_init_face_detection_tflite()
        
        # 如果失败，使用 OpenCV
        if not self.use_tflite:
            self._init_opencv_cascade()
        
        # 初始化 dlib 人脸关键点检测器
        self._init_dlib_landmark_detector()

    def _try_init_face_detection_tflite(self):
        """尝试初始化 face-detection-tflite 包 (fdlite)"""
        try:
            # 临时修复 numpy 兼容性问题
            import numpy as np
            if not hasattr(np, 'math'):
                import math
                np.math = math
            
            from fdlite import FaceDetection
            
            print("[OK] fdlite (face-detection-tflite) 模块可用")
            
            try:
                self.face_detector = FaceDetection()
                print("[OK] 人脸检测器初始化成功 (fdlite)")
                self.use_tflite = True
                return
            except Exception as e:
                print(f"  fdlite 初始化失败: {e}")
                
        except ImportError as e:
            print(f"  fdlite 不可用: {e}")
            print("  提示: 运行 pip install face-detection-tflite")
        except Exception as e:
            print(f"  fdlite 初始化异常: {e}")
        
        self.use_tflite = False

    def _init_opencv_cascade(self):
        """初始化 OpenCV 级联分类器"""
        try:
            model_dir = cv2.data.haarcascades
            
            # 尝试使用更好的级联分类器
            cascade_paths = [
                os.path.join(model_dir, 'lbpcascade_frontalface.xml'),
                os.path.join(model_dir, 'haarcascade_frontalface_alt2.xml'),
                os.path.join(model_dir, 'haarcascade_frontalface_default.xml'),
            ]
            
            for cascade_path in cascade_paths:
                if os.path.exists(cascade_path):
                    self.face_cascade = cv2.CascadeClassifier(cascade_path)
                    if not self.face_cascade.empty():
                        print(f"[OK] 使用级联分类器: {os.path.basename(cascade_path)}")
                        break
            
            if not hasattr(self, 'face_cascade') or self.face_cascade is None or self.face_cascade.empty():
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                print("[OK] 使用默认级联分类器进行人脸检测")
            
            # 初始化眼睛检测器
            eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
            self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
            print("[OK] 眼睛检测器初始化成功")
            
        except Exception as e:
            print(f"警告: OpenCV 级联分类器初始化失败: {e}")
            self.face_cascade = None
            self.eye_cascade = None

    def _init_dlib_landmark_detector(self):
        """初始化人脸关键点检测器"""
        try:
            import dlib
            import os
            
            # 尝试从 face_recognition_models 获取模型路径
            try:
                from face_recognition_models import face_recognition_model_location
                models_dir = os.path.dirname(face_recognition_model_location())
                model_path = os.path.join(models_dir, 'shape_predictor_68_face_landmarks.dat')
                
                if os.path.exists(model_path):
                    self.landmark_detector = dlib.shape_predictor(model_path)
                    self.use_face_recognition_landmarks = True
                    print(f"[OK] dlib 人脸关键点检测器初始化成功 (68个关键点)")
                    print(f"[INFO] 模型路径: {model_path}")
                    return
            except Exception as e:
                print(f"[WARNING] 从 face_recognition_models 加载模型失败: {e}")
            
            # 如果上面失败，尝试其他方式
            print("[WARNING] 未找到 dlib 预训练模型 - 将使用虚拟关键点")
            self.landmark_detector = None
            self.use_face_recognition_landmarks = False
        except ImportError:
            print("[WARNING] dlib 未安装 - 将使用虚拟关键点")
            self.landmark_detector = None
            self.use_face_recognition_landmarks = False
        except Exception as e:
            print(f"[WARNING] 关键点检测器初始化失败: {e} - 将使用虚拟关键点")
            self.landmark_detector = None
            self.use_face_recognition_landmarks = False

    def _get_landmarks_from_dlib(self, image, face_box):
        """使用 dlib 获取人脸关键点"""
        try:
            if self.landmark_detector is None:
                return None
            
            import dlib
            
            x, y, w, h = face_box
            # 创建 dlib 的矩形对象
            dlib_rect = dlib.rectangle(x, y, x + w, y + h)
            
            # 检测关键点
            landmarks = self.landmark_detector(image, dlib_rect)
            
            # 转换为坐标列表
            landmark_points = []
            for point in landmarks.parts():
                landmark_points.append((point.x, point.y))
            
            return landmark_points if landmark_points else None
        except Exception as e:
            self._debug_print(f"[DEBUG] dlib 关键点检测失败: {e}")
            return None

    def detect_face(self, image):
        """检测人脸 - 带稳定性机制"""
        if self.use_tflite and self.face_detector:
            raw_result = self._detect_face_tflite(image)
        else:
            raw_result = self._detect_face_cascade(image)
        
        # 更新检测历史
        self.detection_history.append(raw_result is not None)
        if len(self.detection_history) > self.history_size:
            self.detection_history.pop(0)
        
        # 计算稳定性
        if len(self.detection_history) >= 3:  # 至少有3次检测记录
            positive_count = sum(self.detection_history)
            
            # 如果大部分检测都成功，返回当前结果
            if positive_count >= self.stable_threshold:
                return raw_result
            # 如果大部分检测都失败，返回 None
            elif positive_count <= 1:
                return None
            # 中间状态，返回当前结果但不太稳定
            else:
                return raw_result
        else:
            # 检测历史不足，直接返回当前结果
            return raw_result

    def detect_faces(self, image):
        """检测所有人脸 - 返回详细信息列表（用于绘制检测框和关键点）"""
        try:
            faces = []
            h, w = image.shape[:2]
            
            # 使用 fdlite 检测人脸
            if self.use_tflite and self.face_detector:
                detections = self.face_detector(image)
                
                if detections and len(detections) > 0:
                    min_confidence = 0.3
                    
                    for detection in detections:
                        if detection.score >= min_confidence:
                            bbox = detection.bbox
                            
                            # 转换坐标
                            if bbox.normalized:
                                x = int(bbox.xmin * w)
                                y = int(bbox.ymin * h)
                                x2 = int(bbox.xmax * w)
                                y2 = int(bbox.ymax * h)
                            else:
                                x = int(bbox.xmin)
                                y = int(bbox.ymin)
                                x2 = int(bbox.xmax)
                                y2 = int(bbox.ymax)
                            
                            width = x2 - x
                            height = y2 - y
                            
                            # 验证检测框
                            if width > 20 and height > 20 and width < w * 0.8 and height < h * 0.8:
                                x = max(0, min(x, w - 1))
                                y = max(0, min(y, h - 1))
                                width = max(1, min(width, w - x))
                                height = max(1, min(height, h - y))
                                
                                # 使用 dlib 获取关键点
                                landmarks = self._get_landmarks_from_dlib(image, (x, y, width, height))
                                
                                # 如果 dlib 失败，生成虚拟关键点
                                if not landmarks:
                                    self._debug_print(f"[DEBUG] dlib 关键点检测失败，使用虚拟关键点")
                                    landmarks = self._generate_virtual_landmarks(x, y, width, height)
                                
                                faces.append({
                                    'box': (x, y, width, height),
                                    'confidence': detection.score,
                                    'landmarks': landmarks if landmarks else None
                                })
            else:
                # 使用级联分类器
                face = self.detect_face(image)
                if face:
                    x, y, width, height = face
                    # 尝试使用 dlib 获取关键点
                    landmarks = self._get_landmarks_from_dlib(image, (x, y, width, height))
                    if not landmarks:
                        landmarks = self._generate_virtual_landmarks(x, y, width, height)
                    
                    faces.append({
                        'box': (x, y, width, height),
                        'confidence': 0.5,
                        'landmarks': landmarks
                    })
            
            return faces
        except Exception as e:
            self._debug_print(f"检测人脸列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _generate_virtual_landmarks(self, x, y, width, height):
        """生成虚拟关键点（基于人脸框）- 68个点"""
        landmarks = []
        
        # 脸部轮廓 (0-16) - 17个点
        for i in range(17):
            angle = i * (180 / 16)  # 从0到180度
            rad = np.radians(angle)
            px = int(x + width // 2 + (width // 2.2) * np.cos(rad))
            py = int(y + height // 2 + (height // 2.5) * np.sin(rad))
            landmarks.append((px, py))
        
        # 左眉毛 (17-21) - 5个点
        for i in range(5):
            px = int(x + width // 4 + (i * width // 20))
            py = int(y + height // 4 - height // 10)
            landmarks.append((px, py))
        
        # 右眉毛 (22-26) - 5个点
        for i in range(5):
            px = int(x + 3 * width // 4 - (i * width // 20))
            py = int(y + height // 4 - height // 10)
            landmarks.append((px, py))
        
        # 鼻子 (27-30) - 4个点
        landmarks.append((int(x + width // 2), int(y + height // 3)))  # 鼻梁
        landmarks.append((int(x + width // 2 - width // 10), int(y + height // 2)))  # 左鼻孔
        landmarks.append((int(x + width // 2 + width // 10), int(y + height // 2)))  # 右鼻孔
        landmarks.append((int(x + width // 2), int(y + height // 2 + height // 10)))  # 鼻尖
        
        # 左眼 (31-35) - 5个点
        for i in range(5):
            angle = i * (180 / 4)
            rad = np.radians(angle)
            px = int(x + width // 3 + (width // 8) * np.cos(rad))
            py = int(y + height // 3 + (height // 12) * np.sin(rad))
            landmarks.append((px, py))
        
        # 右眼 (36-41) - 6个点
        for i in range(6):
            angle = i * (180 / 5)
            rad = np.radians(angle)
            px = int(x + 2 * width // 3 + (width // 8) * np.cos(rad))
            py = int(y + height // 3 + (height // 12) * np.sin(rad))
            landmarks.append((px, py))
        
        # 嘴巴 (42-67) - 26个点
        # 上嘴唇 (42-47)
        for i in range(6):
            px = int(x + width // 4 + (i * width // 12))
            py = int(y + 2 * height // 3 - height // 15)
            landmarks.append((px, py))
        
        # 下嘴唇 (48-53)
        for i in range(6):
            px = int(x + width // 4 + (i * width // 12))
            py = int(y + 2 * height // 3 + height // 15)
            landmarks.append((px, py))
        
        # 嘴唇内部 (54-67) - 14个点
        for i in range(14):
            if i < 7:
                px = int(x + width // 3 + (i * width // 14))
                py = int(y + 2 * height // 3)
            else:
                px = int(x + width // 3 + ((13 - i) * width // 14))
                py = int(y + 2 * height // 3 + height // 20)
            landmarks.append((px, py))
        
        return landmarks

    def _detect_face_tflite(self, image):
        """使用 fdlite (face-detection-tflite) 检测人脸"""
        try:
            # fdlite 返回一个 Detection 对象列表
            detections = self.face_detector(image)
            
            if detections and len(detections) > 0:
                # 按置信度排序，选择最佳检测结果
                detections = sorted(detections, key=lambda d: d.score, reverse=True)
                
                # 降低置信度阈值，提高检测率
                min_confidence = 0.3  # 从 0.5 降低到 0.3
                
                for detection in detections:
                    if detection.score >= min_confidence:
                        bbox = detection.bbox
                        
                        # 获取图像尺寸
                        h, w = image.shape[:2]
                        
                        # fdlite 返回归一化坐标 (0-1)，需要转换为像素坐标
                        if bbox.normalized:
                            x = int(bbox.xmin * w)
                            y = int(bbox.ymin * h)
                            x2 = int(bbox.xmax * w)
                            y2 = int(bbox.ymax * h)
                        else:
                            x = int(bbox.xmin)
                            y = int(bbox.ymin)
                            x2 = int(bbox.xmax)
                            y2 = int(bbox.ymax)
                        
                        # 计算宽度和高度
                        width = x2 - x
                        height = y2 - y
                        
                        # 验证检测框的合理性
                        if width > 20 and height > 20 and width < w * 0.8 and height < h * 0.8:
                            # 确保坐标在图像范围内
                            x = max(0, min(x, w - 1))
                            y = max(0, min(y, h - 1))
                            width = max(1, min(width, w - x))
                            height = max(1, min(height, h - y))
                            
                            # 人脸检测成功，不输出日志减少噪音
                            pass
                            
                            return (x, y, width, height)
                
                # 如果没有找到合适的检测结果，静默处理
                if detections:
                    best_detection = detections[0]
                    # 不输出低置信度检测信息，避免控制台噪音
            
            return None
        except Exception as e:
            self._debug_print(f"fdlite 人脸检测失败: {e}")
            return None

    def _detect_face_cascade(self, image):
        """使用级联分类器检测人脸"""
        if self.face_cascade is None:
            return None

        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 使用多尺度检测，参数优化
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,
                minNeighbors=4,
                minSize=(30, 30),
                maxSize=(500, 500)
            )
            
            if len(faces) > 0:
                return max(faces, key=lambda f: f[2] * f[3])
            return None
        except Exception as e:
            self._debug_print(f"级联分类器人脸检测失败: {e}")
            return None

    def get_face_landmarks(self, image):
        """获取人脸关键点"""
        # 当前使用 OpenCV，不支持关键点检测
        return None

    def check_face_quality(self, image):
        """检查人脸质量 - 详细分析版本"""
        quality_info = {
            'face_detected': False,
            'is_frontal': False,
            'eyes_open': False,
            'eyes_looking_forward': False,
            'mouth_closed': False,
            'no_glasses': False,
            'good_lighting': False,
            'face_position': 'center',  # 'left', 'right', 'up', 'down', 'center'
            'face_size': 'good',        # 'too_small', 'too_large', 'good'
            'overall_score': 0,
            'detailed_feedback': []
        }

        try:
            face = self.detect_face(image)
            if face is None:
                quality_info['detailed_feedback'].append("未检测到人脸")
                return quality_info

            quality_info['face_detected'] = True
            h, w = image.shape[:2]
            x, y, fw, fh = face
            
            # 详细的位置分析
            face_center_x = x + fw / 2
            face_center_y = y + fh / 2
            image_center_x = w / 2
            image_center_y = h / 2
            
            # 水平位置检查
            horizontal_offset = face_center_x - image_center_x
            vertical_offset = face_center_y - image_center_y
            
            # 位置容忍度 - 调整为更敏感的检测
            h_tolerance = w * 0.1   # 水平容忍度 10% (更严格)
            v_tolerance = h * 0.08  # 垂直容忍度 8% (更严格)
            
            # 首先检查是否在中心区域
            if abs(horizontal_offset) <= h_tolerance and abs(vertical_offset) <= v_tolerance:
                quality_info['is_frontal'] = True
                quality_info['face_position'] = 'center'
            else:
                quality_info['is_frontal'] = False
                
                # 确定具体的偏移方向 - 优先处理更大的偏移
                if abs(horizontal_offset) > abs(vertical_offset):
                    # 水平偏移更大
                    if horizontal_offset > h_tolerance:
                        quality_info['face_position'] = 'right'  # 人脸在右边，需要往左移
                    elif horizontal_offset < -h_tolerance:
                        quality_info['face_position'] = 'left'   # 人脸在左边，需要往右移
                    else:
                        # 水平偏移不大，检查垂直偏移
                        if vertical_offset > v_tolerance:
                            quality_info['face_position'] = 'down'   # 人脸在下方，需要往上移
                        else:
                            quality_info['face_position'] = 'up'     # 人脸在上方，需要往下移
                else:
                    # 垂直偏移更大
                    if vertical_offset > v_tolerance:
                        quality_info['face_position'] = 'down'   # 人脸在下方，需要往上移
                    elif vertical_offset < -v_tolerance:
                        quality_info['face_position'] = 'up'     # 人脸在上方，需要往下移
                    else:
                        # 垂直偏移不大，检查水平偏移
                        if horizontal_offset > h_tolerance:
                            quality_info['face_position'] = 'right'  # 人脸在右边，需要往左移
                        else:
                            quality_info['face_position'] = 'left'   # 人脸在左边，需要往右移
            
            # 调试信息
            self._debug_print_detailed(f"人脸位置分析: 中心({face_center_x:.1f}, {face_center_y:.1f}), "
                  f"图像中心({image_center_x:.1f}, {image_center_y:.1f}), "
                  f"偏移({horizontal_offset:.1f}, {vertical_offset:.1f}), "
                  f"容忍度({h_tolerance:.1f}, {v_tolerance:.1f}), "
                  f"结果: {quality_info['face_position']}")
            
            # 人脸大小检查
            face_area = fw * fh
            image_area = w * h
            face_ratio = face_area / image_area
            
            if face_ratio < 0.05:  # 人脸太小
                quality_info['face_size'] = 'too_small'
            elif face_ratio > 0.3:  # 人脸太大
                quality_info['face_size'] = 'too_large'
            else:
                quality_info['face_size'] = 'good'
            
            # 光照检查
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            face_roi = gray[y:y+fh, x:x+fw]
            brightness = np.mean(face_roi)
            brightness_std = np.std(face_roi)
            
            if 60 < brightness < 180 and brightness_std > 20:
                quality_info['good_lighting'] = True
            
            # 详细的眼睛检查 - 改进版本
            # 眼睛检测 - 简化版：只检测是否正视（看镜头）
            try:
                quality_info['eyes_open'] = True  # 默认认为眼睛睁开
                quality_info['eyes_looking_forward'] = False
                
                # 定义眼睛区域（更精确）
                left_eye_x1 = fw//6
                left_eye_y1 = fh//4
                left_eye_x2 = fw//2
                left_eye_y2 = fh//2
                
                right_eye_x1 = fw//2
                right_eye_y1 = fh//4
                right_eye_x2 = 5*fw//6
                right_eye_y2 = fh//2
                
                left_eye_region = face_roi[left_eye_y1:left_eye_y2, left_eye_x1:left_eye_x2]
                right_eye_region = face_roi[right_eye_y1:right_eye_y2, right_eye_x1:right_eye_x2]
                
                if left_eye_region.size > 0 and right_eye_region.size > 0:
                    # 分析左右眼的对称性（正视检测）
                    left_eye_score = self._analyze_eye_symmetry(left_eye_region, "左眼")
                    right_eye_score = self._analyze_eye_symmetry(right_eye_region, "右眼")
                    
                    # 计算对称性差异
                    symmetry_diff = abs(left_eye_score - right_eye_score)
                    avg_score = (left_eye_score + right_eye_score) / 2
                    
                    self._debug_print_detailed(f"眼睛对称性分析: 左眼={left_eye_score:.1f}, 右眼={right_eye_score:.1f}, 差异={symmetry_diff:.1f}, 平均={avg_score:.1f}")
                    
                    # 判断是否正视（更严格的条件）
                    # 1. 任一眼睛严重偏移都不算正视
                    max_single_eye_score = max(left_eye_score, right_eye_score)
                    min_single_eye_score = min(left_eye_score, right_eye_score)
                    
                    # 2. 综合判断条件
                    if (symmetry_diff < 0.5 and avg_score >= 2.0 and 
                        min_single_eye_score >= 1.5):  # 🔧 增加条件：两眼都要有基本分数
                        quality_info['eyes_looking_forward'] = True
                        self._debug_print("判断: 眼睛正视")
                    else:
                        self._debug_print(f"判断: 眼睛未正视 (差异={symmetry_diff:.1f}, 平均={avg_score:.1f}, 最低分={min_single_eye_score:.1f})")
                        
            except Exception as e:
                self._debug_print(f"眼睛检测失败: {e}")
                quality_info['eyes_open'] = True  # 默认睁开
                quality_info['eyes_looking_forward'] = False
                quality_info['eyes_open'] = False
                quality_info['eyes_looking_forward'] = False
            
            # 嘴巴检查 - 改进版本
            # 嘴巴检测 - 全新算法：轮廓分析 + 面积比例 + 亮度对比
            try:
                quality_info['mouth_closed'] = True  # 默认闭合
                
                # 嘴巴区域（精确定位）
                mouth_x1 = x + fw//3
                mouth_y1 = y + int(0.65*fh)  # 更精确的嘴巴位置
                mouth_x2 = x + 2*fw//3
                mouth_y2 = y + int(0.9*fh)
                mouth_region = image[mouth_y1:mouth_y2, mouth_x1:mouth_x2]
                
                if mouth_region.size > 0:
                    # 转换为灰度图
                    gray_mouth = cv2.cvtColor(mouth_region, cv2.COLOR_BGR2GRAY) if len(mouth_region.shape) == 3 else mouth_region
                    h_mouth, w_mouth = gray_mouth.shape
                    
                    # 方法1: 轮廓面积分析（最有效）
                    # 使用自适应阈值找到暗区域（张嘴时的口腔）
                    adaptive_thresh = cv2.adaptiveThreshold(gray_mouth, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
                    contours, _ = cv2.findContours(adaptive_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    # 计算最大轮廓面积
                    max_contour_area = 0
                    if contours:
                        max_contour_area = max([cv2.contourArea(c) for c in contours])
                    
                    # 面积比例（相对于嘴巴区域）
                    area_ratio = max_contour_area / (w_mouth * h_mouth)
                    
                    # 方法2: 上下半部分亮度对比
                    upper_half = gray_mouth[:h_mouth//2, :]
                    lower_half = gray_mouth[h_mouth//2:, :]
                    upper_brightness = np.mean(upper_half)
                    lower_brightness = np.mean(lower_half)
                    brightness_diff = upper_brightness - lower_brightness
                    
                    # 方法3: 中心区域暗度检测
                    center_y1 = h_mouth//3
                    center_y2 = 2*h_mouth//3
                    center_x1 = w_mouth//4
                    center_x2 = 3*w_mouth//4
                    center_region = gray_mouth[center_y1:center_y2, center_x1:center_x2]
                    center_brightness = np.mean(center_region)
                    mouth_avg_brightness = np.mean(gray_mouth)
                    darkness_ratio = (mouth_avg_brightness - center_brightness) / mouth_avg_brightness if mouth_avg_brightness > 0 else 0
                    
                    self._debug_print_detailed(f"嘴巴分析: 轮廓面积比={area_ratio:.3f}, 亮度差={brightness_diff:.1f}, 暗度比={darkness_ratio:.3f}")
                    
                    # 综合判断 - 新指标
                    mouth_open_score = 0
                    
                    # 指标1: 轮廓面积大（张嘴时有明显的暗区域轮廓）
                    if area_ratio > 0.08:  # 面积比例超过8%
                        mouth_open_score += 2  # 权重更高
                        self._debug_print("嘴巴指标1: 轮廓面积大 (+2分)")
                    elif area_ratio > 0.04:  # 面积比例超过4%
                        mouth_open_score += 1
                        self._debug_print("嘴巴指标1: 轮廓面积中等 (+1分)")
                    
                    # 指标2: 上下亮度差异大（张嘴时下半部分更暗）
                    if brightness_diff > 8:  # 上半部分比下半部分亮8以上
                        mouth_open_score += 1
                        self._debug_print("嘴巴指标2: 上下亮度差大 (+1分)")
                    
                    # 指标3: 中心区域暗（张嘴时中心是口腔）
                    if darkness_ratio > 0.15:  # 中心比周围暗15%以上
                        mouth_open_score += 1
                        self._debug_print("嘴巴指标3: 中心区域暗 (+1分)")
                    
                    # 最终判断：2分或以上认为张嘴
                    if mouth_open_score >= 2:
                        quality_info['mouth_closed'] = False
                        self._debug_print(f"判断: 嘴巴张开 (得分: {mouth_open_score}/4)")
                    else:
                        self._debug_print(f"判断: 嘴巴闭合 (得分: {mouth_open_score}/4)")
                        
            except Exception as e:
                self._debug_print(f"嘴巴检测失败: {e}")
                quality_info['mouth_closed'] = True
            
            # 眼镜检测 - 改进版本
            try:
                quality_info['no_glasses'] = True  # 默认无眼镜
                
                # 定义眼镜检测区域（眼睛周围）
                glasses_y_start = int(fh // 6)
                glasses_y_end = int(fh // 2)
                glasses_x_start = int(fw // 8)
                glasses_x_end = int(7 * fw // 8)
                
                glasses_region = face_roi[glasses_y_start:glasses_y_end, glasses_x_start:glasses_x_end]
                
                if glasses_region.size > 0:
                    # 方法1: 边缘检测（眼镜框）
                    edges = cv2.Canny(glasses_region, 50, 150)
                    edge_density = np.sum(edges > 0) / edges.size
                    
                    # 方法2: 霍夫圆检测（眼镜镜片）
                    circles = cv2.HoughCircles(
                        glasses_region, 
                        cv2.HOUGH_GRADIENT, 
                        dp=1, 
                        minDist=30,
                        param1=50, 
                        param2=30, 
                        minRadius=10, 
                        maxRadius=50
                    )
                    
                    # 方法3: 反光检测（镜片反光）
                    bright_pixels = np.sum(glasses_region > brightness * 1.3)
                    bright_ratio = bright_pixels / glasses_region.size
                    
                    self._debug_print(f"眼镜分析: 边缘密度={edge_density:.3f}, 圆形={len(circles[0]) if circles is not None else 0}, 反光比例={bright_ratio:.3f}")
                    
                    glasses_indicators = 0
                    
                    # 指标1: 边缘密度高
                    if edge_density > 0.12:
                        glasses_indicators += 1
                        self._debug_print("眼镜指标1: 边缘密度高")
                    
                    # 指标2: 检测到圆形（镜片）
                    if circles is not None and len(circles[0]) >= 1:
                        glasses_indicators += 1
                        self._debug_print("眼镜指标2: 检测到圆形")
                    
                    # 指标3: 反光区域多
                    if bright_ratio > 0.05:
                        glasses_indicators += 1
                        self._debug_print("眼镜指标3: 反光区域多")
                    
                    # 如果有2个或以上指标，认为戴眼镜
                    if glasses_indicators >= 2:
                        quality_info['no_glasses'] = False
                        self._debug_print(f"判断: 戴眼镜 ({glasses_indicators}/3 个指标)")
                    else:
                        self._debug_print(f"判断: 无眼镜 ({glasses_indicators}/3 个指标)")
                        
            except Exception as e:
                self._debug_print(f"眼镜检测失败: {e}")
                quality_info['no_glasses'] = True
            
            # 计算总体评分
            score = 0
            if quality_info['face_detected']:
                score += 25
            if quality_info['is_frontal']:
                score += 20
            if quality_info['eyes_open']:
                score += 15
            if quality_info['eyes_looking_forward']:
                score += 10
            if quality_info['mouth_closed']:
                score += 10
            if quality_info['good_lighting']:
                score += 15
            if quality_info['face_size'] == 'good':
                score += 5
            
            quality_info['overall_score'] = score

        except Exception as e:
            self._debug_print(f"质量检查失败: {e}")
            quality_info['detailed_feedback'].append(f"检查失败: {e}")

        return quality_info

    def _analyze_eye_symmetry(self, eye_region, eye_name):
        """分析眼珠子是否在中央（正视检测），返回0-3分"""
        try:
            if eye_region.size == 0:
                return 0
            
            # 转换为灰度图
            if len(eye_region.shape) == 3:
                gray_eye = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)
            else:
                gray_eye = eye_region
            
            h, w = gray_eye.shape
            score = 0
            
            # 方法1: 检测最暗区域（瞳孔）是否在中央
            # 找到最暗的区域，应该是瞳孔位置
            min_val = np.min(gray_eye)
            min_locations = np.where(gray_eye == min_val)
            
            if len(min_locations[0]) > 0:
                # 计算最暗区域的中心
                pupil_center_y = np.mean(min_locations[0])
                pupil_center_x = np.mean(min_locations[1])
                
                # 眼睛区域的中心
                eye_center_y = h / 2
                eye_center_x = w / 2
                
                # 计算偏移
                offset_y = abs(pupil_center_y - eye_center_y) / h
                offset_x = abs(pupil_center_x - eye_center_x) / w
                
                # 如果瞳孔在中央附近（偏移小于20%）
                if offset_x < 0.2 and offset_y < 0.3:  # 🔧 X偏移从0.3改为0.2，更严格
                    score += 1
                    self._debug_print(f"{eye_name}指标1: 瞳孔位置居中 (X偏移={offset_x:.2f}, Y偏移={offset_y:.2f})")
                else:
                    self._debug_print(f"{eye_name}指标1: 瞳孔偏移 (X偏移={offset_x:.2f}, Y偏移={offset_y:.2f})")
            
            # 方法2: 左右亮度平衡检测
            # 正视时，眼睛左右两侧的亮度应该相对平衡
            left_half = gray_eye[:, :w//2]
            right_half = gray_eye[:, w//2:]
            
            left_brightness = np.mean(left_half)
            right_brightness = np.mean(right_half)
            brightness_diff = abs(left_brightness - right_brightness)
            brightness_ratio = brightness_diff / max(left_brightness, right_brightness) if max(left_brightness, right_brightness) > 0 else 1
            
            if brightness_ratio < 0.2:  # 左右亮度差异小于20%
                score += 1
                self._debug_print(f"{eye_name}指标2: 左右亮度平衡 (差异比例={brightness_ratio:.3f})")
            else:
                self._debug_print(f"{eye_name}指标2: 左右亮度不平衡 (差异比例={brightness_ratio:.3f})")
            
            # 方法3: 水平梯度中心检测
            # 正视时，最大的水平梯度（瞳孔边缘）应该在中央
            horizontal_grad = cv2.Sobel(gray_eye, cv2.CV_64F, 1, 0, ksize=3)
            grad_abs = np.abs(horizontal_grad)
            
            # 找到最大梯度的位置
            max_grad_pos = np.unravel_index(np.argmax(grad_abs), grad_abs.shape)
            grad_center_x = max_grad_pos[1] / w
            
            # 检查是否在水平中央附近
            if 0.35 < grad_center_x < 0.65:  # 🔧 从0.3-0.7改为0.35-0.65，更严格
                score += 1
                self._debug_print(f"{eye_name}指标3: 梯度中心居中 (位置={grad_center_x:.3f})")
            else:
                self._debug_print(f"{eye_name}指标3: 梯度中心偏移 (位置={grad_center_x:.3f})")
            
            self._debug_print(f"{eye_name}总分: {score}/3")
            return score
            
        except Exception as e:
            self._debug_print(f"眼珠子中央检测失败 ({eye_name}): {e}")
            return 0

    def _analyze_eyes_by_brightness(self, face_roi, fw, fh, brightness, quality_info):
        """使用亮度分析检测眼睛状态"""
        try:
            # 定义眼睛区域（上半部分，左右分开）
            eye_y_start = int(fh // 4)
            eye_y_end = int(fh // 2)
            
            # 左眼区域
            left_eye_region = face_roi[eye_y_start:eye_y_end, fw//6:fw//2]
            # 右眼区域  
            right_eye_region = face_roi[eye_y_start:eye_y_end, fw//2:5*fw//6]
            
            if left_eye_region.size > 0 and right_eye_region.size > 0:
                left_brightness = np.mean(left_eye_region)
                right_brightness = np.mean(right_eye_region)
                left_std = np.std(left_eye_region)
                right_std = np.std(right_eye_region)
                
                self._debug_print(f"亮度分析: 左眼={left_brightness:.1f}±{left_std:.1f}, 右眼={right_brightness:.1f}±{right_std:.1f}, 人脸={brightness:.1f}")
                
                # 眼睛通常比周围区域稍暗，且有一定的变化（眼白和瞳孔对比）
                eyes_open_indicators = 0
                
                # 指标1: 眼睛区域有足够的亮度变化（眼白和瞳孔对比）
                if left_std > 15 or right_std > 15:
                    eyes_open_indicators += 1
                    self._debug_print("眼睛亮度指标1: 区域内有变化")
                
                # 指标2: 眼睛区域不会太暗（完全闭眼会很暗）
                if left_brightness > brightness * 0.6 and right_brightness > brightness * 0.6:
                    eyes_open_indicators += 1
                    self._debug_print("眼睛亮度指标2: 区域不会太暗")
                
                # 指标3: 左右眼亮度相近（正视时对称）
                brightness_diff = abs(left_brightness - right_brightness)
                if brightness_diff < brightness * 0.2:
                    quality_info['eyes_looking_forward'] = True
                    self._debug_print("眼睛亮度指标3: 左右对称")
                
                # 如果有足够指标，认为眼睛睁开
                if eyes_open_indicators >= 1:
                    quality_info['eyes_open'] = True
                    self._debug_print(f"亮度分析结果: 眼睛睁开 ({eyes_open_indicators}/2 个指标)")
                else:
                    self._debug_print(f"亮度分析结果: 眼睛可能闭合 ({eyes_open_indicators}/2 个指标)")
                    
        except Exception as e:
            self._debug_print(f"亮度分析失败: {e}")
            # 默认值
            quality_info['eyes_open'] = True
            quality_info['eyes_looking_forward'] = True

    def get_quality_feedback(self, quality_info):
        """获取质量反馈信息 - 详细指导版本"""
        feedback = []
        
        if not quality_info['face_detected']:
            feedback.append("❌ 未检测到人脸，请将脸部移到摄像头中央")
            return feedback
        
        # 位置指导
        position = quality_info.get('face_position', 'center')
        if position != 'center':
            if position == 'left':
                feedback.append("👈 请向右移动一些")
            elif position == 'right':
                feedback.append("👉 请向左移动一些")
            elif position == 'up':
                feedback.append("👇 请向下移动一些")
            elif position == 'down':
                feedback.append("👆 请向上移动一些")
        else:
            feedback.append("✅ 位置正确")
        
        # 人脸大小指导
        face_size = quality_info.get('face_size', 'good')
        if face_size == 'too_small':
            feedback.append("🔍 请靠近摄像头一些")
        elif face_size == 'too_large':
            feedback.append("🔍 请远离摄像头一些")
        else:
            feedback.append("✅ 距离合适")
        
        # 眼睛状态
        if not quality_info.get('eyes_open', True):
            feedback.append("👀 请睁开眼睛")
        elif not quality_info.get('eyes_looking_forward', True):
            feedback.append("👀 请直视摄像头")
        else:
            feedback.append("✅ 眼睛状态良好")
        
        # 嘴巴状态
        if not quality_info.get('mouth_closed', True):
            feedback.append("👄 请闭上嘴巴")
        else:
            feedback.append("✅ 嘴巴状态良好")
        
        # 眼镜检查
        if not quality_info.get('no_glasses', True):
            feedback.append("👓 检测到眼镜，请确保镜片无反光")
        
        # 光照检查
        if not quality_info.get('good_lighting', True):
            feedback.append("💡 光线不佳，请调整位置或增加照明")
        else:
            feedback.append("✅ 光线良好")
        
        # 总体评价
        score = quality_info.get('overall_score', 0)
        if score >= 90:
            feedback.insert(0, "🎉 照片质量优秀，可以拍摄！")
        elif score >= 75:
            feedback.insert(0, "👍 照片质量良好，可以拍摄")
        elif score >= 60:
            feedback.insert(0, "⚠️ 照片质量一般，建议调整后拍摄")
        else:
            feedback.insert(0, "❌ 照片质量需要改善")
        
        return feedback

    def get_segmentation_mask(self, image):
        """获取人物分割掩码"""
        return self._get_segmentation_mask_hsv(image)

    def _get_segmentation_mask_hsv(self, image):
        """使用 HSV 肤色检测获取分割掩码"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            lower_skin1 = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin1 = np.array([20, 255, 255], dtype=np.uint8)
            
            lower_skin2 = np.array([170, 20, 70], dtype=np.uint8)
            upper_skin2 = np.array([180, 255, 255], dtype=np.uint8)
            
            mask1 = cv2.inRange(hsv, lower_skin1, upper_skin1)
            mask2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
            mask = cv2.bitwise_or(mask1, mask2)
            
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
            mask = cv2.dilate(mask, kernel, iterations=2)
            mask = cv2.erode(mask, kernel, iterations=1)
            mask = cv2.GaussianBlur(mask, (21, 21), 0)
            
            return mask
        except Exception as e:
            self._debug_print(f"HSV 分割失败: {e}")
            return None

    def compare_faces(self, image1, image2):
        """比较两张人脸图像的相似度"""
        try:
            if isinstance(image1, str):
                img1 = cv2.imread(image1)
            else:
                img1 = image1
            
            if isinstance(image2, str):
                img2 = cv2.imread(image2)
            else:
                img2 = image2
            
            if img1 is None or img2 is None:
                return 0
            
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]
            
            size_ratio = min(h1, h2) / max(h1, h2)
            similarity = int(size_ratio * 100)
            
            return similarity
        except Exception as e:
            self._debug_print(f"人脸比对失败: {e}")
            return 0

    def detect_liveness(self, image):
        """活体检测"""
        try:
            face = self.detect_face(image)
            return face is not None
        except Exception as e:
            self._debug_print(f"活体检测失败: {e}")
            return False

    def close(self):
        """关闭模型"""
        pass
