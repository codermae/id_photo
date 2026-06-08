"""
证件照智能采集及处理系统 - 软著鉴别材料第2部分
数据模型和ORM层实现

================================================================================
第2部分: 数据库模型（ORM层）
================================================================================

本部分包含系统的数据模型定义，使用SQLAlchemy作为ORM框架，
定义了用户、照片、采集任务和采集记录等核心数据结构。

"""

# ============================================================================
# 文件名: models/user.py
# 功能: 用户数据模型，存储用户基本信息
# 行数: 68 行
# ============================================================================

from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class User(Base):
    """
    用户模型
    
    属性说明:
    - id: 唯一标识符
    - name: 姓名
    - id_number: 身份证号
    - sex: 性别 (M/F)
    - birth_date: 出生日期
    - nationality: 民族
    - province: 省份
    - city: 城市
    - address: 地址
    - phone: 电话号码
    - email: 电子邮箱
    - status: 采集状态 (pending/completed/failed)
    - created_at: 创建时间
    - updated_at: 修改时间
    - is_deleted: 是否删除（软删除）
    
    关联关系:
    - photos: 该用户的所有照片记录
    - records: 该用户的所有采集记录
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    id_number = Column(String(18), unique=True, index=True)
    sex = Column(String(1))  # M/F
    birth_date = Column(Date)
    nationality = Column(String(20))
    province = Column(String(50))
    city = Column(String(50))
    address = Column(String(200))
    phone = Column(String(20))
    email = Column(String(100))
    status = Column(String(20), default='pending')  # pending/completed/failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, index=True)
    
    # 关联关系
    photos = relationship('Photo', back_populates='user', cascade='all, delete-orphan')
    records = relationship('CollectionRecord', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, id_number={self.id_number})>"


# ============================================================================
# 文件名: models/photo.py
# 功能: 照片数据模型，存储照片信息和路径
# 行数: 72 行
# ============================================================================

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class Photo(Base):
    """
    照片模型
    
    属性说明:
    - id: 唯一标识符
    - user_id: 用户外键
    - photo_type: 照片类型 (raw/processed)
    - file_path: 文件路径
    - file_size: 文件大小 (字节)
    - width: 图像宽度 (像素)
    - height: 图像高度 (像素)
    - spec: 证件照规格
    - background: 背景颜色
    - quality_score: 质量评分 (0-100)
    - has_face: 是否包含人脸
    - face_confidence: 人脸检测置信度
    - created_at: 创建时间
    - updated_at: 修改时间
    - is_deleted: 是否删除（软删除）
    
    关联关系:
    - user: 所属用户
    """
    __tablename__ = 'photos'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    photo_type = Column(String(20), index=True)  # raw/processed
    file_path = Column(String(500), unique=True)
    file_size = Column(Integer)  # 字节
    width = Column(Integer)  # 像素
    height = Column(Integer)  # 像素
    spec = Column(String(50), index=True)  # 证件照规格
    background = Column(String(50))  # 背景颜色
    quality_score = Column(Float, default=0.0)  # 0-100
    has_face = Column(Boolean, default=False)
    face_confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, index=True)
    
    # 关联关系
    user = relationship('User', back_populates='photos')
    
    def __repr__(self):
        return f"<Photo(id={self.id}, user_id={self.user_id}, type={self.photo_type})>"


# ============================================================================
# 文件名: models/collection.py
# 功能: 采集任务模型，管理批量采集任务
# 行数: 65 行
# ============================================================================

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class Collection(Base):
    """
    采集任务模型
    
    属性说明:
    - id: 任务唯一标识符
    - name: 任务名称
    - description: 任务描述
    - status: 任务状态 (created/running/completed/failed)
    - total_users: 总用户数
    - completed_count: 已完成数
    - failed_count: 失败数
    - created_at: 创建时间
    - started_at: 开始时间
    - completed_at: 完成时间
    - is_active: 是否活跃
    - is_deleted: 是否删除（软删除）
    
    关联关系:
    - records: 该任务的所有采集记录
    """
    __tablename__ = 'collections'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(String(500))
    status = Column(String(20), default='created', index=True)  # created/running/completed/failed
    total_users = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, index=True)
    
    # 关联关系
    records = relationship('CollectionRecord', back_populates='collection', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Collection(id={self.id}, name={self.name}, status={self.status})>"


# ============================================================================
# 文件名: models/record.py
# 功能: 采集记录模型，记录每次采集的详细信息
# 行数: 68 行
# ============================================================================

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class CollectionRecord(Base):
    """
    采集记录模型
    
    属性说明:
    - id: 记录唯一标识符
    - collection_id: 所属任务ID
    - user_id: 用户ID
    - status: 采集状态 (pending/in_progress/completed/failed)
    - raw_photo_id: 原始照片ID
    - processed_photo_id: 处理后照片ID
    - processing_time: 处理耗时 (秒)
    - ai_score: AI处理评分
    - error_message: 错误信息
    - created_at: 创建时间
    - completed_at: 完成时间
    - is_deleted: 是否删除（软删除）
    
    关联关系:
    - collection: 所属采集任务
    - user: 所属用户
    """
    __tablename__ = 'collection_records'
    
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey('collections.id'), index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    status = Column(String(20), default='pending', index=True)  # pending/in_progress/completed/failed
    raw_photo_id = Column(Integer, ForeignKey('photos.id'), nullable=True)
    processed_photo_id = Column(Integer, ForeignKey('photos.id'), nullable=True)
    processing_time = Column(Float, default=0.0)  # 秒
    ai_score = Column(Float, default=0.0)  # 0-100
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)
    
    # 关联关系
    collection = relationship('Collection', back_populates='records')
    user = relationship('User', back_populates='records')
    
    def __repr__(self):
        return f"<CollectionRecord(id={self.id}, user_id={self.user_id}, status={self.status})>"
