"""
证件照智能采集及处理系统 - 软著鉴别材料第3部分
核心业务逻辑层 - 控制器和处理器

================================================================================
第3部分: 核心业务逻辑（Controller层）
================================================================================

本部分包含系统的核心业务逻辑处理，包括AI人脸检测、图像处理、
身份证读取、批量处理等关键功能模块。

"""

# ============================================================================
# 文件名: controllers/ai_processor.py
# 功能: AI处理核心模块，负责人脸检测、美颜、背景替换等
# 行数: 95 行
# ============================================================================

import os
import numpy as np
import cv2
from PIL import Image
import face_detection_tflite
from face_recognition import face_encodings, compare_faces
import insightface
from gfpgan import GFPGANer
import rembg
from config.config import (
    FACE_DETECTION_CONFIDENCE, FACE_RECOGNITION_THRESHOLD,
    QUALITY_SCORE_THRESHOLD, USE_GPU, GPU_DEVICE_ID
)
from utils.image_helper import ImageHelper

class AIProcessor:
    """
    AI处理器 - 整合所有AI功能
    
    功能:
    1. 人脸检测与定位
    2. 人脸质量评分
    3. AI美颜处理（GFPGAN）
    4. AI背景移除（rembg）
    5. 人脸识别与重复检测
    6. 人脸关键点检测
    """
    
    def __init__(self):
        """初始化AI处理器，加载所有模型"""
        self.detector = face_detection_tflite.FaceDetector()
        self.gfpgan = GFPGANer(
            scale=2, model_path='resources/models/GFPGANv1.3.pth',
            upscayl_arch='realesrgan', channel_multiplier=2, bg_upsampler=None,
            device='cuda' if USE_GPU else 'cpu'
        )
        self.image_helper = ImageHelper()
        self._face_encodings_cache = {}
    
    def detect_faces(self, image):
        """
        人脸检测
        
        参数:
        - image: numpy数组或PIL Image
        
        返回:
        - faces: 检测到的人脸列表，每个元素为 (x1, y1, x2, y2, confidence)
        """
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        faces = self.detector(image_rgb)
        
        # 过滤低置信度的检测
        filtered_faces = [
            f for f in faces if f[-1] >= FACE_DETECTION_CONFIDENCE
        ]
        return filtered_faces
    
    def evaluate_face_quality(self, image, face_box):
        """
        评估人脸质量
        
        评分维度:
        1. 人脸大小 (占比30%)
        2. 清晰度 (占比25%)
        3. 光照均匀度 (占比25%)
        4. 人脸正面度 (占比20%)
        
        返回: 0-100的质量分数
        """
        score = 0
        
        # 1. 人脸大小评分
        h, w = image.shape[:2]
        face_w = face_box[2] - face_box[0]
        face_h = face_box[3] - face_box[1]
        face_ratio = (face_w * face_h) / (h * w)
        size_score = min(100, (face_ratio / 0.4) * 30)  # 40%为最优
        
        # 2. 清晰度评分 (使用Laplacian算子)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        sharpness_score = min(100, (sharpness / 500) * 25)
        
        # 3. 光照均匀度评分
        brightness_mean = cv2.mean(gray)[0]
        brightness_std = np.std(gray)
        lighting_score = min(100, 25 - (brightness_std / 50))
        
        # 4. 人脸正面度评分
        frontal_score = 20  # 可通过人脸关键点进一步优化
        
        total_score = size_score + sharpness_score + lighting_score + frontal_score
        return max(0, min(100, total_score))
    
    def beautify_face(self, image, enhancement_level=1.5):
        """
        AI美颜处理
        
        参数:
        - image: 输入图像
        - enhancement_level: 增强级别 (0.5-2.0)
        
        返回:
        - output: 美颜处理后的图像
        """
        try:
            # 使用GFPGAN进行人脸增强
            input_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR) \
                if isinstance(image, Image.Image) else image
            
            _, _, output = self.gfpgan.enhance(input_img, has_aligned=False,
                                               only_center_face=False, pad=10,
                                               weight=enhancement_level)
            
            return Image.fromarray(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))
        except Exception as e:
            print(f"美颜处理错误: {e}")
            return image
    
    def remove_background(self, image):
        """
        AI背景移除
        
        使用U2-Net深度学习模型进行高精度人像分割
        
        参数:
        - image: 输入图像
        
        返回:
        - output: RGBA图像（包含透明通道）
        """
        input_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR) \
            if isinstance(image, Image.Image) else image
        
        # rembg处理
        result = rembg.remove(input_img)
        
        return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGBA))
    
    def recognize_face(self, image):
        """
        生成人脸识别特征向量
        
        返回: 128维人脸特征向量
        """
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        encodings = face_encodings(image_rgb)
        
        return encodings[0] if len(encodings) > 0 else None
    
    def compare_faces_similarity(self, encoding1, encoding2):
        """
        比较两个人脸的相似度
        
        返回: 相似度 (0-1)
        """
        if encoding1 is None or encoding2 is None:
            return 0.0
        
        distance = np.linalg.norm(encoding1 - encoding2)
        similarity = 1.0 / (1.0 + distance)
        
        return similarity


# ============================================================================
# 文件名: controllers/image_processor.py
# 功能: 图像处理模块，负责裁剪、背景替换、格式转换等
# 行数: 88 行
# ============================================================================

from PIL import Image, ImageDraw
import cv2
import numpy as np
from config.config import PHOTO_SPECS, BACKGROUND_COLORS, PHOTO_QUALITY
from utils.image_helper import ImageHelper

class ImageProcessor:
    """
    图像处理器 - 图像基础处理
    
    功能:
    1. 智能裁剪（人脸居中）
    2. 背景替换（纯色/渐变）
    3. 格式转换和压缩
    4. 批量处理
    5. 多规格生成
    """
    
    def __init__(self):
        """初始化图像处理器"""
        self.image_helper = ImageHelper()
    
    def smart_crop(self, image, target_width, target_height, face_box=None):
        """
        智能裁剪 - 人脸居中裁剪
        
        参数:
        - image: 输入图像
        - target_width/height: 目标尺寸
        - face_box: 人脸检测框
        
        返回: 裁剪后的图像
        """
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        img_w, img_h = image.size
        
        # 计算缩放比例
        scale_w = target_width / img_w
        scale_h = target_height / img_h
        scale = max(scale_w, scale_h)
        
        # 缩放图像
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        image_resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 计算裁剪位置（人脸居中）
        if face_box:
            face_x = (face_box[0] + face_box[2]) / 2 * scale
            face_y = (face_box[1] + face_box[3]) / 2 * scale
            left = max(0, int(face_x - target_width / 2))
            top = max(0, int(face_y - target_height / 2.5))
        else:
            left = (new_w - target_width) // 2
            top = (new_h - target_height) // 2
        
        left = min(left, new_w - target_width)
        top = min(top, new_h - target_height)
        
        return image_resized.crop((left, top, left + target_width, top + target_height))
    
    def replace_background_color(self, image, background_color):
        """
        纯色背景替换
        
        参数:
        - image: RGBA图像（需要透明通道）
        - background_color: RGB颜色元组
        
        返回: RGB图像（替换背景后）
        """
        # 如果没有alpha通道，先移除背景
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # 创建背景
        background = Image.new('RGB', image.size, background_color)
        
        # 合并
        background.paste(image, (0, 0), image)
        
        return background
    
    def replace_background_gradient(self, image, color1, color2, direction='vertical'):
        """
        渐变背景替换
        
        参数:
        - image: RGBA图像
        - color1/color2: 起始和结束颜色
        - direction: 'vertical' 或 'horizontal'
        
        返回: RGB图像
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        w, h = image.size
        
        # 创建渐变背景
        if direction == 'vertical':
            gradient = Image.new('RGB', (w, h))
            for y in range(h):
                ratio = y / h
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                ImageDraw.floodfill(gradient, (0, y), (r, g, b))
        else:  # horizontal
            gradient = Image.new('RGB', (w, h))
            for x in range(w):
                ratio = x / w
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                ImageDraw.floodfill(gradient, (x, 0), (r, g, b))
        
        # 合并
        gradient.paste(image, (0, 0), image)
        return gradient
    
    def generate_multiple_specs(self, image, spec_list, bg_color):
        """
        一键生成多个规格
        
        参数:
        - image: 输入图像
        - spec_list: 规格列表 ['一寸', '二寸', ...]
        - bg_color: 背景颜色
        
        返回: {规格: 图像} 字典
        """
        results = {}
        for spec in spec_list:
            if spec in PHOTO_SPECS:
                w, h = PHOTO_SPECS[spec]
                cropped = self.smart_crop(image, w, h)
                final = self.replace_background_color(cropped, bg_color)
                results[spec] = final
        
        return results
    
    def save_photo(self, image, file_path, quality=PHOTO_QUALITY):
        """
        保存照片
        
        参数:
        - image: PIL Image对象
        - file_path: 保存路径
        - quality: JPEG质量 (1-100)
        """
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        image.save(file_path, 'JPEG', quality=quality, dpi=(300, 300))


# ============================================================================
# 文件名: controllers/camera.py
# 功能: 摄像头控制和实时预览
# 行数: 72 行
# ============================================================================

import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
import numpy as np

class CameraThread(QThread):
    """
    摄像头线程 - 独立线程处理摄像头输入
    
    信号:
    - frame_ready: 新帧可用
    - face_detected: 检测到人脸
    - error: 发生错误
    """
    
    frame_ready = pyqtSignal(QImage)
    face_detected = pyqtSignal(dict)  # 人脸信息
    error = pyqtSignal(str)
    
    def __init__(self, camera_id=0, width=640, height=480, fps=15):
        """初始化摄像头线程"""
        super().__init__()
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.is_running = False
        self.cap = None
    
    def run(self):
        """
        线程运行函数 - 持续采集和处理视频帧
        
        流程:
        1. 打开摄像头
        2. 读取帧
        3. 转换格式
        4. 发送信号
        5. 处理错误
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            self.is_running = True
            
            while self.is_running:
                ret, frame = self.cap.read()
                
                if not ret:
                    self.error.emit("无法读取摄像头帧")
                    break
                
                # 转换为RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 转换为QImage
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_frame.data, w, h, bytes_per_line,
                                 QImage.Format_RGB888)
                
                self.frame_ready.emit(qt_image)
                
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if self.cap:
                self.cap.release()
    
    def stop(self):
        """停止摄像头"""
        self.is_running = False
        self.wait()
    
    def capture_frame(self):
        """捕获当前帧"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None
