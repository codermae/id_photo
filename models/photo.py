"""
照片数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class Photo(Base):
    """证件照表"""
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    photo_type = Column(String(20), nullable=False)  # raw/processed
    file_path = Column(String(255), nullable=False)
    file_size = Column(Integer)  # 字节
    photo_spec = Column(String(20))  # 一寸/二寸等
    background_color = Column(String(20))  # 背景色
    quality_score = Column(Integer)  # 质量评分 0-100
    face_similarity = Column(Integer)  # 与身份证照片的相似度 0-100
    created_at = Column(DateTime, default=datetime.now, index=True)

    # 关系
    user = relationship('User', back_populates='photos')

    def __repr__(self):
        return f'<Photo {self.id} {self.photo_type}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'photo_type': self.photo_type,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'photo_spec': self.photo_spec,
            'background_color': self.background_color,
            'quality_score': self.quality_score,
            'face_similarity': self.face_similarity,
            'created_at': self.created_at.isoformat(),
        }
