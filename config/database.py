"""
数据库配置和初始化
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.config import DATABASE_URL, init_directories

# 初始化目录
init_directories()

# 创建数据库引擎
engine = create_engine(DATABASE_URL, echo=False)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 导入所有模型（确保它们被注册到 Base）
from models.collection import Collection
from models.user import User
from models.photo import Photo
from models.record import CollectionRecord

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
