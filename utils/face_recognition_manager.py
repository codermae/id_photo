"""
人脸识别管理器 - 智能处理face_recognition库的可用性
支持优雅降级：如果face_recognition不可用，使用备选方案
"""
import numpy as np
from typing import Optional, Tuple, List
import logging
import os

logger = logging.getLogger(__name__)

# 尝试导入face_recognition
FACE_RECOGNITION_AVAILABLE = False
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
    logger.info("[✓] face_recognition 库已加载")
except ImportError:
    logger.warning("[⚠] face_recognition 库未安装，人脸识别功能将使用备选方案")

# 尝试导入OpenCV作为备选
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.error("[✗] OpenCV 未安装")


class FaceRecognitionManager:
    """人脸识别管理器"""
    
    def __init__(self):
        """初始化"""
        self.face_recognition_available = FACE_RECOGNITION_AVAILABLE
        self.opencv_available = OPENCV_AVAILABLE
        self.mode = self._determine_mode()
        
        if self.mode == 'face_recognition':
            logger.info("[✓] 使用 face_recognition 模式（dlib CNN）")
        elif self.mode == 'opencv':
            logger.info("[⚠] 使用 OpenCV 模式（备选方案）")
        else:
            logger.error("[✗] 没有可用的人脸识别方案")
    
    def _determine_mode(self) -> str:
        """确定使用的模式"""
        if self.face_recognition_available:
            return 'face_recognition'
        elif self.opencv_available:
            return 'opencv'
        else:
            return 'none'
    
    def get_status(self) -> dict:
        """获取系统状态"""
        return {
            'mode': self.mode,
            'face_recognition_available': self.face_recognition_available,
            'opencv_available': self.opencv_available,
            'is_ready': self.mode != 'none',
            'description': self._get_mode_description()
        }
    
    def _get_mode_description(self) -> str:
        """获取模式描述"""
        if self.mode == 'face_recognition':
            return "使用 face_recognition (dlib CNN) - 高精度深度学习模型"
        elif self.mode == 'opencv':
            return "使用 OpenCV Haar Cascade - 备选方案（精度较低）"
        else:
            return "未配置人脸识别"
    
    def encode_face(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        提取人脸特征向量
        
        Args:
            image: RGB 图像 (numpy array)
        
        Returns:
            128维特征向量，如果未检测到人脸则返回 None
        """
        if self.mode == 'face_recognition':
            return self._encode_face_dlib(image)
        elif self.mode == 'opencv':
            return self._encode_face_opencv(image)
        else:
            logger.error("人脸识别不可用")
            return None
    
    def _encode_face_dlib(self, image: np.ndarray) -> Optional[np.ndarray]:
        """使用 dlib 提取人脸特征"""
        try:
            # 检测人脸 - 使用更快的 HOG 模型而不是 CNN
            face_locations = face_recognition.face_locations(image, model='hog')
            
            if not face_locations:
                logger.debug("未检测到人脸")
                return None
            
            # 提取特征（使用第一个检测到的人脸）
            encodings = face_recognition.face_encodings(image, face_locations)
            
            if encodings:
                return encodings[0]  # 返回第一个人脸的特征
            else:
                logger.debug("无法提取人脸特征")
                return None
        
        except Exception as e:
            logger.error(f"dlib 人脸编码失败: {e}")
            return None
    
    def _encode_face_opencv(self, image: np.ndarray) -> Optional[np.ndarray]:
        """使用 OpenCV 提取人脸特征（简化版）"""
        try:
            # 加载 Haar Cascade 分类器
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
            
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # 检测人脸
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                logger.debug("未检测到人脸")
                return None
            
            # 生成简单的特征向量（基于人脸区域的统计特征）
            # 这是一个简化的实现，用于演示
            x, y, w, h = faces[0]
            face_region = image[y:y+h, x:x+w]
            
            # 计算特征（128维向量）
            features = self._compute_simple_features(face_region)
            return features
        
        except Exception as e:
            logger.error(f"OpenCV 人脸编码失败: {e}")
            return None
    
    def _compute_simple_features(self, face_region: np.ndarray) -> np.ndarray:
        """计算简单的人脸特征向量"""
        # 调整大小为 128x128
        resized = cv2.resize(face_region, (128, 128))
        
        # 计算直方图特征
        hist_r = cv2.calcHist([resized], [0], None, [32], [0, 256])
        hist_g = cv2.calcHist([resized], [1], None, [32], [0, 256])
        hist_b = cv2.calcHist([resized], [2], None, [32], [0, 256])
        
        # 合并特征
        features = np.concatenate([hist_r.flatten(), hist_g.flatten(), hist_b.flatten()])
        
        # 归一化到 128 维
        if len(features) > 128:
            features = features[:128]
        elif len(features) < 128:
            features = np.pad(features, (0, 128 - len(features)), mode='constant')
        
        return features.astype(np.float32)
    
    def compare_faces(self, encoding1: np.ndarray, encoding2: np.ndarray, 
                     tolerance: float = 0.6) -> bool:
        """
        比较两个人脸特征向量
        
        Args:
            encoding1: 第一个人脸特征向量
            encoding2: 第二个人脸特征向量
            tolerance: 相似度阈值（0-1，越小越严格）
        
        Returns:
            True 如果是同一个人，False 否则
        """
        if encoding1 is None or encoding2 is None:
            return False
        
        if self.mode == 'face_recognition':
            # 使用 face_recognition 的比较方法
            distance = np.linalg.norm(encoding1 - encoding2)
            return distance < tolerance
        else:
            # 使用欧几里得距离
            distance = np.linalg.norm(encoding1 - encoding2)
            return distance < tolerance
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        检测图像中的人脸
        
        Returns:
            人脸位置列表 [(top, right, bottom, left), ...]
        """
        if self.mode == 'face_recognition':
            try:
                return face_recognition.face_locations(image, model='hog')  # 使用更快的 HOG 模型
            except Exception as e:
                logger.error(f"人脸检测失败: {e}")
                return []
        elif self.mode == 'opencv':
            try:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                face_cascade = cv2.CascadeClassifier(cascade_path)
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                # 转换格式为 (top, right, bottom, left)
                result = []
                for (x, y, w, h) in faces:
                    result.append((y, x + w, y + h, x))
                return result
            except Exception as e:
                logger.error(f"人脸检测失败: {e}")
                return []
        else:
            return []


# 全局实例
_manager = None

def get_face_recognition_manager() -> FaceRecognitionManager:
    """获取全局人脸识别管理器实例"""
    global _manager
    if _manager is None:
        _manager = FaceRecognitionManager()
    return _manager

def print_status():
    """打印系统状态"""
    manager = get_face_recognition_manager()
    status = manager.get_status()
    
    print("\n" + "="*60)
    print("人脸识别系统状态")
    print("="*60)
    print(f"模式: {status['mode']}")
    print(f"描述: {status['description']}")
    print(f"就绪: {'✓ 是' if status['is_ready'] else '✗ 否'}")
    print("="*60 + "\n")
    
    if not status['is_ready']:
        print("[INFO] 要启用人脸识别功能，请运行:")
        print("  python INSTALL_FACE_RECOGNITION_GUIDE.md")
        print()

if __name__ == '__main__':
    print_status()
