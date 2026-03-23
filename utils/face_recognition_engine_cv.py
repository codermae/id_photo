"""
人脸识别引擎 - 基于OpenCV和MediaPipe的实现
不依赖dlib，使用已有的依赖库
"""
import numpy as np
import cv2
from typing import Tuple, Optional, Dict, List
import pickle

class FaceRecognitionEngine:
    """人脸识别引擎 - OpenCV版本"""
    
    def __init__(self, similarity_threshold: float = 0.6):
        """
        初始化人脸识别引擎
        
        Args:
            similarity_threshold: 人脸相似度阈值（0-1），超过此值认为是同一个人
        """
        self.similarity_threshold = similarity_threshold
        self.available = True
        self._initialized = True
        print("[INFO] 人脸识别引擎已初始化（OpenCV版本）")
    
    def extract_face_encoding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        从图像中提取人脸特征向量
        使用图像的直方图和HOG特征作为人脸编码
        
        Args:
            image: 输入图像（BGR格式）
            
        Returns:
            人脸特征向量或None
        """
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 使用级联分类器检测人脸
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                print("[DEBUG] 未检测到人脸")
                return None
            
            if len(faces) > 1:
                print(f"[WARNING] 检测到{len(faces)}张人脸，使用最大的人脸")
            
            # 使用最大的人脸
            (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
            face_roi = gray[y:y+h, x:x+w]
            
            # 提取特征：使用直方图均衡化后的HOG特征
            # 1. 直方图均衡化
            face_roi = cv2.equalizeHist(face_roi)
            
            # 2. 计算HOG特征
            hog = cv2.HOGDescriptor()
            hog_features = hog.compute(face_roi)
            
            if hog_features is None or len(hog_features) == 0:
                # 备选方案：使用直方图特征
                hist = cv2.calcHist([face_roi], [0], None, [256], [0, 256])
                encoding = hist.flatten().astype(np.float32)
            else:
                encoding = hog_features.flatten().astype(np.float32)
            
            # 归一化
            encoding = encoding / (np.linalg.norm(encoding) + 1e-6)
            
            print(f"[INFO] 成功提取人脸特征（维度: {len(encoding)}）")
            
            return encoding
        
        except Exception as e:
            print(f"[ERROR] 人脸特征提取失败: {e}")
            return None
    
    def compare_faces(self, encoding1: np.ndarray, encoding2: np.ndarray) -> Tuple[bool, float]:
        """
        比较两个人脸特征向量
        
        Args:
            encoding1: 第一个人脸特征向量
            encoding2: 第二个人脸特征向量
            
        Returns:
            (是否为同一个人, 相似度分数)
        """
        if encoding1 is None or encoding2 is None:
            return False, 0.0
        
        try:
            # 确保维度相同
            if len(encoding1) != len(encoding2):
                # 使用较短的维度
                min_len = min(len(encoding1), len(encoding2))
                encoding1 = encoding1[:min_len]
                encoding2 = encoding2[:min_len]
            
            # 计算余弦相似度（更适合高维特征）
            dot_product = np.dot(encoding1, encoding2)
            norm1 = np.linalg.norm(encoding1)
            norm2 = np.linalg.norm(encoding2)
            
            if norm1 == 0 or norm2 == 0:
                similarity = 0.0
            else:
                similarity = dot_product / (norm1 * norm2)
            
            # 将相似度映射到0-1范围
            similarity = max(0, min(1, (similarity + 1) / 2))
            
            # 判断是否为同一个人
            is_same_person = similarity >= self.similarity_threshold
            
            print(f"[DEBUG] 人脸比对 - 相似度: {similarity:.4f}, 判定: {'同一个人' if is_same_person else '不同人'}")
            
            return is_same_person, similarity
        
        except Exception as e:
            print(f"[ERROR] 人脸比对失败: {e}")
            return False, 0.0
    
    def check_duplicate(self, image: np.ndarray, existing_encodings: List[np.ndarray]) -> Tuple[bool, float, int]:
        """
        检查是否与已有的人脸重复
        
        Args:
            image: 新拍摄的图像
            existing_encodings: 已有的人脸特征列表
            
        Returns:
            (是否重复, 最高相似度, 最相似的索引)
        """
        if not existing_encodings:
            return False, 0.0, -1
        
        # 提取新图像的人脸特征
        new_encoding = self.extract_face_encoding(image)
        if new_encoding is None:
            return False, 0.0, -1
        
        # 与所有已有特征比对
        max_similarity = 0.0
        max_index = -1
        
        for i, existing_encoding in enumerate(existing_encodings):
            if existing_encoding is None:
                continue
            
            is_same, similarity = self.compare_faces(new_encoding, existing_encoding)
            
            if similarity > max_similarity:
                max_similarity = similarity
                max_index = i
        
        is_duplicate = max_similarity >= self.similarity_threshold
        
        print(f"[INFO] 重复检查完成 - 最高相似度: {max_similarity:.4f}, 是否重复: {is_duplicate}")
        
        return is_duplicate, max_similarity, max_index
    
    def encode_to_bytes(self, encoding: np.ndarray) -> bytes:
        """
        将人脸特征向量编码为字节（用于数据库存储）
        
        Args:
            encoding: 人脸特征向量
            
        Returns:
            编码后的字节
        """
        if encoding is None:
            return None
        
        try:
            return pickle.dumps(encoding)
        except Exception as e:
            print(f"[ERROR] 人脸特征编码失败: {e}")
            return None
    
    def decode_from_bytes(self, data: bytes) -> Optional[np.ndarray]:
        """
        从字节解码人脸特征向量
        
        Args:
            data: 编码后的字节
            
        Returns:
            人脸特征向量或None
        """
        if data is None:
            return None
        
        try:
            return pickle.loads(data)
        except Exception as e:
            print(f"[ERROR] 人脸特征解码失败: {e}")
            return None
    
    def batch_extract_encodings(self, images: List[np.ndarray]) -> List[Optional[np.ndarray]]:
        """
        批量提取人脸特征
        
        Args:
            images: 图像列表
            
        Returns:
            人脸特征列表
        """
        encodings = []
        for i, image in enumerate(images):
            encoding = self.extract_face_encoding(image)
            encodings.append(encoding)
            print(f"[DEBUG] 已处理 {i+1}/{len(images)} 张图像")
        
        return encodings
    
    def get_similarity_matrix(self, encodings: List[np.ndarray]) -> np.ndarray:
        """
        计算人脸特征之间的相似度矩阵
        
        Args:
            encodings: 人脸特征列表
            
        Returns:
            相似度矩阵
        """
        n = len(encodings)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i, n):
                if encodings[i] is None or encodings[j] is None:
                    matrix[i][j] = 0.0
                    matrix[j][i] = 0.0
                else:
                    _, similarity = self.compare_faces(encodings[i], encodings[j])
                    matrix[i][j] = similarity
                    matrix[j][i] = similarity
        
        return matrix
    
    def find_duplicates(self, encodings: List[np.ndarray]) -> List[Tuple[int, int, float]]:
        """
        在特征列表中查找重复的人脸
        
        Args:
            encodings: 人脸特征列表
            
        Returns:
            重复对列表 [(索引1, 索引2, 相似度), ...]
        """
        duplicates = []
        n = len(encodings)
        
        for i in range(n):
            for j in range(i+1, n):
                if encodings[i] is None or encodings[j] is None:
                    continue
                
                is_same, similarity = self.compare_faces(encodings[i], encodings[j])
                
                if is_same:
                    duplicates.append((i, j, similarity))
        
        return duplicates
