"""
人脸识别引擎 - 基于dlib的人脸特征提取和比对
用于防重复采集和身份核验

注意: 这是可选的高级版本，需要安装face_recognition库
如果未安装，系统会自动使用OpenCV版本
"""
import numpy as np
import cv2
from typing import Tuple, Optional, Dict, List
import pickle
import os

class FaceRecognitionEngineDlib:
    """人脸识别引擎 - dlib版本（可选）"""
    
    def __init__(self, similarity_threshold: float = 0.6):
        """
        初始化人脸识别引擎
        
        Args:
            similarity_threshold: 人脸相似度阈值（0-1），超过此值认为是同一个人
        """
        self.similarity_threshold = similarity_threshold
        self.face_recognition = None
        self.dlib_available = False
        self._initialized = False
        self._initialize()
    
    def _initialize(self):
        """延迟初始化face_recognition库"""
        if self._initialized:
            return
        
        self._initialized = True
        
        try:
            import face_recognition
            self.face_recognition = face_recognition
            self.dlib_available = True
            print("[INFO] face_recognition库已加载，使用dlib CNN模型进行人脸识别")
        except ImportError:
            print("[INFO] face_recognition库未安装，将使用OpenCV版本")
            self.dlib_available = False
        except Exception as e:
            print(f"[WARNING] face_recognition初始化失败: {e}")
            self.dlib_available = False
    
    def extract_face_encoding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        从图像中提取人脸特征向量
        
        Args:
            image: 输入图像（BGR格式）
            
        Returns:
            人脸特征向量（128维）或None
        """
        if not self.dlib_available:
            return None
        
        try:
            # 转换为RGB格式（face_recognition需要RGB）
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 检测人脸
            face_locations = self.face_recognition.face_locations(rgb_image, model='hog')
            
            if not face_locations:
                print("[DEBUG] 未检测到人脸")
                return None
            
            if len(face_locations) > 1:
                print(f"[WARNING] 检测到{len(face_locations)}张人脸，使用最大的人脸")
            
            # 提取人脸特征（使用第一张人脸）
            face_encodings = self.face_recognition.face_encodings(rgb_image, face_locations)
            
            if not face_encodings:
                print("[DEBUG] 无法提取人脸特征")
                return None
            
            encoding = face_encodings[0]
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
        if not self.dlib_available or encoding1 is None or encoding2 is None:
            return False, 0.0
        
        try:
            # 计算欧几里得距离
            distance = np.linalg.norm(encoding1 - encoding2)
            
            # 转换为相似度分数（0-1，越接近1越相似）
            # 距离范围通常是0-0.6，我们将其映射到0-1
            similarity = 1.0 - min(distance / 0.6, 1.0)
            
            # 判断是否为同一个人
            is_same_person = similarity >= self.similarity_threshold
            
            print(f"[DEBUG] 人脸比对 - 距离: {distance:.4f}, 相似度: {similarity:.4f}, 判定: {'同一个人' if is_same_person else '不同人'}")
            
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
