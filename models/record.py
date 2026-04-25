"""
采集记录数据模型
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class CollectionRecord(Base):
    """采集记录表"""
    __tablename__ = 'collection_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(Integer, ForeignKey('collections.id'), nullable=False, index=True)  # 采集任务ID
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    collection_date = Column(Date, default=datetime.now, index=True)
    operator = Column(String(50))  # 操作员
    status = Column(String(20), default='pending')  # completed/processing/pending
    notes = Column(Text)  # 备注
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    collection = relationship('Collection', back_populates='records')
    user = relationship('User', back_populates='records')

    def __repr__(self):
        return f'<CollectionRecord {self.user_id} {self.status}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'collection_id': self.collection_id,
            'user_id': self.user_id,
            'collection_date': self.collection_date.isoformat(),
            'operator': self.operator,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
        }
