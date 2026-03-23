"""
重复采集检查器 - 集成人脸识别进行防重复采集
"""
import cv2
import numpy as np
from typing import Tuple, Optional, Dict
from datetime import datetime
from utils.face_recognition_manager import get_face_recognition_manager
from utils.database_helper import DatabaseHelper
import logging

logger = logging.getLogger(__name__)

class DuplicateChecker:
    """重复采集检查器"""
    
    def __init__(self, similarity_threshold: float = 0.6):
        """初始化重复检查器"""
        self.face_manager = get_face_recognition_manager()
        self.db_helper = DatabaseHelper()
        self.similarity_threshold = similarity_threshold
        
        if not self.face_manager.get_status()['is_ready']:
            logger.warning("[⚠] 人脸识别不可用，重复检查功能将被禁用")
    
    def check_duplicate_for_user(self, user_id: int, image: np.ndarray) -> Dict:
        """
        检查用户是否已采集过照片
        
        Args:
            user_id: 用户ID
            image: 新拍摄的图像
            
        Returns:
            检查结果字典
        """
        result = {
            'is_duplicate': False,
            'similarity': 0.0,
            'message': '',
            'previous_photo_id': None,
            'previous_photo_path': None
        }
        
        # 检查人脸识别是否可用
        if not self.face_manager.get_status()['is_ready']:
            result['message'] = '人脸识别功能不可用'
            logger.warning("人脸识别功能不可用，跳过重复检查")
            return result
        
        try:
            # 获取用户信息
            user = self.db_helper.get_user_by_id(user_id)
            if not user:
                result['message'] = '用户不存在'
                return result
            
            # 如果用户还没有保存过人脸特征，则首次采集
            if not user.face_encoding:
                result['message'] = '该用户首次采集'
                return result
            
            # 提取新图像的人脸特征
            new_encoding = self.face_manager.encode_face(image)
            if new_encoding is None:
                result['message'] = '无法提取新图像的人脸特征'
                logger.warning(f"无法提取用户 {user_id} 的人脸特征")
                return result
            
            # 从数据库获取已存储的人脸特征
            existing_encoding = np.frombuffer(user.face_encoding, dtype=np.float32)
            
            # 比对特征
            is_same = self.face_manager.compare_faces(new_encoding, existing_encoding, 
                                                      tolerance=1.0 - self.similarity_threshold)
            
            # 计算相似度（使用欧几里得距离）
            distance = np.linalg.norm(new_encoding - existing_encoding)
            similarity = 1.0 - min(distance / 2.0, 1.0)  # 归一化到 0-1
            
            result['similarity'] = similarity
            
            # 判断是否重复
            if is_same:
                result['is_duplicate'] = True
                result['message'] = f'检测到重复采集！相似度: {similarity:.2%}'
            else:
                result['message'] = f'未检测到重复（相似度: {similarity:.2%}）'
            
            return result
        
        except Exception as e:
            result['message'] = f'检查失败: {str(e)}'
            logger.error(f"重复检查失败: {e}")
            return result
    
    def check_duplicate_for_id_number(self, id_number: str, image: np.ndarray) -> Dict:
        """
        根据身份证号检查是否重复
        
        Args:
            id_number: 身份证号
            image: 新拍摄的图像
            
        Returns:
            检查结果字典
        """
        try:
            user = self.db_helper.get_user_by_id_number(id_number)
            if not user:
                return {
                    'is_duplicate': False,
                    'similarity': 0.0,
                    'message': '该身份证号首次采集',
                    'previous_photo_id': None,
                    'previous_photo_path': None
                }
            
            return self.check_duplicate_for_user(user.id, image)
        
        except Exception as e:
            logger.error(f"根据身份证号检查重复失败: {e}")
            return {
                'is_duplicate': False,
                'similarity': 0.0,
                'message': f'检查失败: {str(e)}',
                'previous_photo_id': None,
                'previous_photo_path': None
            }
    
    def save_face_encoding(self, user_id: int, image: np.ndarray) -> bool:
        """
        保存用户的人脸特征到数据库
        
        Args:
            user_id: 用户ID
            image: 图像
            
        Returns:
            是否保存成功
        """
        # 检查人脸识别是否可用
        if not self.face_manager.get_status()['is_ready']:
            logger.warning("人脸识别功能不可用，跳过人脸特征保存")
            return False
        
        try:
            # 提取人脸特征
            encoding = self.face_manager.encode_face(image)
            if encoding is None:
                logger.warning(f"无法提取用户 {user_id} 的人脸特征，跳过保存")
                return False
            
            # 编码为字节
            encoding_bytes = encoding.astype(np.float32).tobytes()
            
            # 保存到数据库
            self.db_helper.update_user(
                user_id,
                face_encoding=encoding_bytes,
                face_encoding_timestamp=datetime.now()
            )
            
            logger.info(f"用户 {user_id} 的人脸特征已保存")
            return True
        
        except Exception as e:
            logger.error(f"保存人脸特征失败: {e}")
            return False
    
    def get_duplicate_statistics(self) -> Dict:
        """
        获取重复采集的统计信息
        
        Returns:
            统计信息字典
        """
        try:
            users = self.db_helper.get_all_users()
            
            total_users = len(users)
            users_with_encoding = sum(1 for u in users if u.face_encoding is not None)
            
            return {
                'total_users': total_users,
                'users_with_encoding': users_with_encoding,
                'encoding_coverage': f'{users_with_encoding/total_users*100:.1f}%' if total_users > 0 else '0%',
                'face_recognition_available': self.face_manager.get_status()['is_ready']
            }
        
        except Exception as e:
            logger.error(f"获取重复统计失败: {e}")
            return {
                'total_users': 0,
                'users_with_encoding': 0,
                'encoding_coverage': '0%',
                'face_recognition_available': False
            }
    
    def close(self):
        """关闭数据库连接"""
        self.db_helper.close()
