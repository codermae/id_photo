"""
用户数据模型
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(Integer, ForeignKey('collections.id'), nullable=False, index=True)  # 采集任务ID
    name = Column(String(50), nullable=False)
    id_number = Column(String(18), nullable=False, index=True)  # 身份证号（在同一采集任务内唯一）
    gender = Column(String(10))
    nation = Column(String(20))
    birthday = Column(Date)
    address = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    collection = relationship('Collection', back_populates='users')
    photos = relationship('Photo', back_populates='user', cascade='all, delete-orphan')
    records = relationship('CollectionRecord', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.name} {self.id_number}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'collection_id': self.collection_id,
            'name': self.name,
            'id_number': self.id_number,
            'gender': self.gender,
            'nation': self.nation,
            'birthday': self.birthday.isoformat() if self.birthday else None,
            'address': self.address,
            'id_photo_path': self.id_photo_path,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
