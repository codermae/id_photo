"""
采集任务数据模型
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class Collection(Base):
    """采集任务表"""
    __tablename__ = 'collections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # 采集任务名称，如"学校A-2026年3月"
    organization = Column(String(100), nullable=False, index=True)  # 机构名称，如"学校A"
    description = Column(Text)  # 任务描述
    start_date = Column(Date)  # 采集开始日期
    end_date = Column(Date)  # 采集结束日期
    status = Column(String(20), default='active')  # 状态：active/completed/archived
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系（使用字符串延迟加载，避免循环导入）
    users = relationship('User', back_populates='collection', cascade='all, delete-orphan', lazy='select')
    records = relationship('CollectionRecord', back_populates='collection', cascade='all, delete-orphan', lazy='select')

    def __repr__(self):
        return f'<Collection {self.name}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'organization': self.organization,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
