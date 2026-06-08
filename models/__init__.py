"""
数据模型包
"""

from .user import User
from .photo import Photo
from .collection import Collection
from .record import CollectionRecord

__all__ = ['User', 'Photo', 'Collection', 'CollectionRecord']
