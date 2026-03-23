"""
身份核验控制器 - 比对采集照片和身份证照片
"""
import cv2
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime
from utils.face_recognition_manager import get_face_recognition_manager
from utils.database_helper import DatabaseHelper
import logging

logger = logging.getLogger(__name__)


class IdentityVerifier:
    """身份核验器"""
    
    def __init__(self, similarity_threshold: float = 0.6):
        """初始化身份核验器"""
        self.face_manager = get_face_recognition_manager()
        self.db_helper = DatabaseHelper()
        self.similarity_threshold = similarity_threshold
    
    def verify_identity(self, id_card_photo: np.ndarray, captured_photo: np.ndarray,
                       user_id: Optional[int] = None) -> Dict:
        """
        核验身份 - 比对身份证照片和采集照片
        
        Args:
            id_card_photo: 身份证照片 (numpy array)
            captured_photo: 采集的照片 (numpy array)
            user_id: 用户ID (可选)
        
        Returns:
            核验结果字典
        """
        result = {
            'verified': False,
            'similarity': 0.0,
            'message': '',
            'id_card_face_detected': False,
            'captured_face_detected': False,
            'timestamp': datetime.now()
        }
        
        # 检查人脸识别是否可用
        if not self.face_manager.get_status()['is_ready']:
            result['message'] = '人脸识别功能不可用'
            logger.warning("人脸识别功能不可用，无法进行身份核验")
            return result
        
        try:
            # 提取身份证照片的人脸特征
            id_card_encoding = self.face_manager.encode_face(id_card_photo)
            if id_card_encoding is None:
                result['message'] = '身份证照片中未检测到人脸'
                result['id_card_face_detected'] = False
                logger.warning("身份证照片中未检测到人脸")
                return result
            
            result['id_card_face_detected'] = True
            
            # 提取采集照片的人脸特征
            captured_encoding = self.face_manager.encode_face(captured_photo)
            if captured_encoding is None:
                result['message'] = '采集照片中未检测到人脸'
                result['captured_face_detected'] = False
                logger.warning("采集照片中未检测到人脸")
                return result
            
            result['captured_face_detected'] = True
            
            # 比对特征
            is_same = self.face_manager.compare_faces(
                id_card_encoding, 
                captured_encoding,
                tolerance=1.0 - self.similarity_threshold
            )
            
            # 计算相似度
            distance = np.linalg.norm(id_card_encoding - captured_encoding)
            similarity = 1.0 - min(distance / 2.0, 1.0)
            
            result['similarity'] = similarity
            
            # 判断是否匹配
            if is_same:
                result['verified'] = True
                result['message'] = f'身份核验通过！相似度: {similarity:.2%}'
                logger.info(f"身份核验通过 (用户ID: {user_id}, 相似度: {similarity:.2%})")
            else:
                result['verified'] = False
                result['message'] = f'身份核验失败！相似度: {similarity:.2%}（低于阈值 {self.similarity_threshold:.0%}）'
                logger.warning(f"身份核验失败 (用户ID: {user_id}, 相似度: {similarity:.2%})")
            
            return result
        
        except Exception as e:
            result['message'] = f'核验失败: {str(e)}'
            logger.error(f"身份核验异常: {e}")
            return result
    
    def verify_with_id_number(self, id_number: str, captured_photo: np.ndarray) -> Dict:
        """
        根据身份证号进行身份核验
        
        Args:
            id_number: 身份证号
            captured_photo: 采集的照片
        
        Returns:
            核验结果字典
        """
        try:
            user = self.db_helper.get_user_by_id_number(id_number)
            if not user:
                return {
                    'verified': False,
                    'similarity': 0.0,
                    'message': '用户不存在',
                    'id_card_face_detected': False,
                    'captured_face_detected': False,
                    'timestamp': datetime.now()
                }
            
            # 获取身份证照片
            if not user.id_photo_data:
                return {
                    'verified': False,
                    'similarity': 0.0,
                    'message': '身份证照片不存在',
                    'id_card_face_detected': False,
                    'captured_face_detected': False,
                    'timestamp': datetime.now()
                }
            
            # 将二进制数据转换为图像
            nparr = np.frombuffer(user.id_photo_data, np.uint8)
            id_card_photo = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if id_card_photo is None:
                return {
                    'verified': False,
                    'similarity': 0.0,
                    'message': '身份证照片解析失败',
                    'id_card_face_detected': False,
                    'captured_face_detected': False,
                    'timestamp': datetime.now()
                }
            
            # 转换为 RGB
            id_card_photo = cv2.cvtColor(id_card_photo, cv2.COLOR_BGR2RGB)
            
            return self.verify_identity(id_card_photo, captured_photo, user.id)
        
        except Exception as e:
            logger.error(f"根据身份证号核验失败: {e}")
            return {
                'verified': False,
                'similarity': 0.0,
                'message': f'核验失败: {str(e)}',
                'id_card_face_detected': False,
                'captured_face_detected': False,
                'timestamp': datetime.now()
            }
    
    def get_verification_statistics(self) -> Dict:
        """
        获取身份核验的统计信息
        
        Returns:
            统计信息字典
        """
        try:
            users = self.db_helper.get_all_users()
            
            total_users = len(users)
            users_with_id_photo = sum(1 for u in users if u.id_photo_data is not None)
            
            return {
                'total_users': total_users,
                'users_with_id_photo': users_with_id_photo,
                'id_photo_coverage': f'{users_with_id_photo/total_users*100:.1f}%' if total_users > 0 else '0%',
                'face_recognition_available': self.face_manager.get_status()['is_ready']
            }
        
        except Exception as e:
            logger.error(f"获取核验统计失败: {e}")
            return {
                'total_users': 0,
                'users_with_id_photo': 0,
                'id_photo_coverage': '0%',
                'face_recognition_available': False
            }
    
    def close(self):
        """关闭数据库连接"""
        self.db_helper.close()
