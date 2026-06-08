"""
证件照智能采集及处理系统 - 软著鉴别材料第5部分
数据库助手、工具类和辅助功能

================================================================================
第5部分: 工具类和数据库助手
================================================================================

本部分包含数据库操作助手、图像处理工具、文件管理工具等
辅助功能模块，为业务逻辑层提供基础支持。

"""

# ============================================================================
# 文件名: utils/database_helper.py
# 功能: 数据库操作助手，提供通用的CRUD操作
# 行数: 98 行
# ============================================================================

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from config.database import SessionLocal
from models.user import User
from models.photo import Photo
from models.record import CollectionRecord
from models.collection import Collection
from datetime import datetime, timedelta
import json

class DatabaseHelper:
    """
    数据库操作助手 - 单例模式
    
    功能:
    1. 用户数据CRUD操作
    2. 照片数据管理
    3. 采集任务管理
    4. 统计查询
    5. 数据备份和恢复
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式 - 保证全局唯一实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化数据库助手"""
        self.db = SessionLocal()
    
    # ========== 用户相关操作 ==========
    
    def create_user(self, user_data):
        """
        创建用户
        
        参数: user_data = {
            'name': str,
            'id_number': str,
            'sex': str,
            'birth_date': date,
            'nationality': str,
            'province': str,
            'city': str,
            'address': str,
            'phone': str,
            'email': str
        }
        """
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户"""
        return self.db.query(User).filter(
            User.id == user_id, User.is_deleted == False
        ).first()
    
    def get_user_by_id_number(self, id_number):
        """根据身份证号获取用户"""
        return self.db.query(User).filter(
            User.id_number == id_number, User.is_deleted == False
        ).first()
    
    def update_user(self, user_id, update_data):
        """更新用户信息"""
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in update_data.items():
                setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            self.db.commit()
            return user
        return None
    
    def delete_user(self, user_id):
        """软删除用户"""
        user = self.get_user_by_id(user_id)
        if user:
            user.is_deleted = True
            self.db.commit()
            return True
        return False
    
    def search_users(self, **filters):
        """
        搜索用户
        
        支持的过滤条件:
        - name: 姓名（模糊匹配）
        - id_number: 身份证号
        - sex: 性别
        - status: 采集状态
        - province: 省份
        - nationality: 民族
        """
        query = self.db.query(User).filter(User.is_deleted == False)
        
        if 'name' in filters and filters['name']:
            query = query.filter(User.name.like(f"%{filters['name']}%"))
        
        if 'id_number' in filters and filters['id_number']:
            query = query.filter(User.id_number == filters['id_number'])
        
        if 'sex' in filters and filters['sex']:
            query = query.filter(User.sex == filters['sex'])
        
        if 'status' in filters and filters['status']:
            query = query.filter(User.status == filters['status'])
        
        if 'province' in filters and filters['province']:
            query = query.filter(User.province == filters['province'])
        
        if 'nationality' in filters and filters['nationality']:
            query = query.filter(User.nationality == filters['nationality'])
        
        return query.order_by(desc(User.created_at)).all()
    
    # ========== 照片相关操作 ==========
    
    def create_photo(self, photo_data):
        """创建照片记录"""
        photo = Photo(**photo_data)
        self.db.add(photo)
        self.db.commit()
        self.db.refresh(photo)
        return photo
    
    def get_user_photos(self, user_id, photo_type=None):
        """获取用户的所有照片"""
        query = self.db.query(Photo).filter(
            Photo.user_id == user_id, Photo.is_deleted == False
        )
        if photo_type:
            query = query.filter(Photo.photo_type == photo_type)
        return query.order_by(desc(Photo.created_at)).all()
    
    def get_photos_by_spec(self, spec, start_date=None, end_date=None):
        """获取特定规格的照片"""
        query = self.db.query(Photo).filter(
            Photo.spec == spec, Photo.is_deleted == False
        )
        
        if start_date:
            query = query.filter(Photo.created_at >= start_date)
        if end_date:
            query = query.filter(Photo.created_at <= end_date)
        
        return query.order_by(desc(Photo.created_at)).all()
    
    def update_photo(self, photo_id, update_data):
        """更新照片信息"""
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            for key, value in update_data.items():
                setattr(photo, key, value)
            photo.updated_at = datetime.utcnow()
            self.db.commit()
            return photo
        return None
    
    # ========== 采集任务相关操作 ==========
    
    def create_collection(self, name, description=''):
        """创建采集任务"""
        collection = Collection(
            name=name,
            description=description,
            status='created'
        )
        self.db.add(collection)
        self.db.commit()
        self.db.refresh(collection)
        return collection
    
    def get_collection(self, collection_id):
        """获取采集任务"""
        return self.db.query(Collection).filter(
            Collection.id == collection_id, Collection.is_deleted == False
        ).first()
    
    def update_collection_status(self, collection_id, status):
        """更新采集任务状态"""
        collection = self.get_collection(collection_id)
        if collection:
            collection.status = status
            if status == 'running' and not collection.started_at:
                collection.started_at = datetime.utcnow()
            elif status == 'completed':
                collection.completed_at = datetime.utcnow()
            self.db.commit()
            return collection
        return None
    
    # ========== 统计查询 ==========
    
    def get_statistics(self, start_date=None, end_date=None):
        """
        获取统计数据
        
        返回:
        {
            'total_users': 总用户数,
            'completed_users': 已采集数,
            'pending_users': 待采集数,
            'failed_users': 采集失败数,
            'total_photos': 总照片数,
            'avg_quality_score': 平均质量分,
            'most_used_spec': 最常用规格,
            'most_used_bg': 最常用背景色
        }
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # 用户统计
        total_users = self.db.query(User).filter(
            User.created_at >= start_date,
            User.created_at <= end_date,
            User.is_deleted == False
        ).count()
        
        completed_users = self.db.query(User).filter(
            User.created_at >= start_date,
            User.created_at <= end_date,
            User.status == 'completed',
            User.is_deleted == False
        ).count()
        
        # 照片统计
        total_photos = self.db.query(Photo).filter(
            Photo.created_at >= start_date,
            Photo.created_at <= end_date,
            Photo.is_deleted == False
        ).count()
        
        # 平均质量分
        avg_quality = self.db.query(
            func.avg(Photo.quality_score)
        ).filter(
            Photo.created_at >= start_date,
            Photo.created_at <= end_date,
            Photo.is_deleted == False
        ).scalar()
        
        return {
            'total_users': total_users,
            'completed_users': completed_users,
            'pending_users': total_users - completed_users,
            'total_photos': total_photos,
            'avg_quality_score': float(avg_quality) if avg_quality else 0.0
        }
    
    def get_daily_statistics(self, days=30):
        """获取日均统计数据"""
        results = []
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            start = date.replace(hour=0, minute=0, second=0)
            end = date.replace(hour=23, minute=59, second=59)
            
            count = self.db.query(User).filter(
                User.created_at >= start,
                User.created_at <= end,
                User.status == 'completed'
            ).count()
            
            results.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        return results


# ============================================================================
# 文件名: utils/image_helper.py
# 功能: 图像处理工具类
# 行数: 84 行
# ============================================================================

import cv2
import numpy as np
from PIL import Image
import os

class ImageHelper:
    """
    图像处理工具类
    
    功能:
    1. 图像读写
    2. 格式转换
    3. 尺寸调整
    4. 质量评估
    5. 缓存管理
    """
    
    def __init__(self, cache_size=50):
        """初始化图像工具"""
        self.cache = {}
        self.cache_size = cache_size
    
    def read_image(self, file_path):
        """
        读取图像
        
        支持格式: JPG, PNG, BMP, GIF等
        
        返回: PIL Image 对象
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"图像文件不存在: {file_path}")
        
        # 检查缓存
        if file_path in self.cache:
            return self.cache[file_path].copy()
        
        try:
            image = Image.open(file_path)
            
            # 缓存管理
            if len(self.cache) >= self.cache_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            self.cache[file_path] = image.copy()
            return image
        
        except Exception as e:
            raise Exception(f"读取图像失败: {e}")
    
    def save_image(self, image, file_path, format='JPEG', quality=95):
        """保存图像"""
        try:
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            image.save(file_path, format, quality=quality, dpi=(300, 300))
        except Exception as e:
            raise Exception(f"保存图像失败: {e}")
    
    def resize_image(self, image, width=None, height=None, keep_ratio=True):
        """
        调整图像尺寸
        
        参数:
        - width/height: 目标尺寸，None表示保持原尺寸
        - keep_ratio: 是否保持宽高比
        
        返回: 调整后的图像
        """
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        orig_w, orig_h = image.size
        
        if keep_ratio:
            if width and not height:
                height = int(width * orig_h / orig_w)
            elif height and not width:
                width = int(height * orig_w / orig_h)
        
        if width and height:
            return image.resize((width, height), Image.Resampling.LANCZOS)
        
        return image
    
    def crop_image(self, image, left, top, right, bottom):
        """裁剪图像"""
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        return image.crop((left, top, right, bottom))
    
    def rotate_image(self, image, angle, expand=True):
        """旋转图像"""
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        return image.rotate(angle, expand=expand)
    
    def convert_color_space(self, image, target_mode='RGB'):
        """转换颜色空间"""
        if isinstance(image, np.ndarray):
            if target_mode == 'RGB':
                return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            elif target_mode == 'GRAY':
                return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            return image.convert(target_mode)
    
    def get_image_info(self, image):
        """获取图像信息"""
        if isinstance(image, np.ndarray):
            h, w = image.shape[:2]
            return {'width': w, 'height': h, 'channels': image.shape[2] if len(image.shape) > 2 else 1}
        else:
            w, h = image.size
            return {'width': w, 'height': h, 'mode': image.mode}
    
    def estimate_file_size(self, image, quality=95):
        """估计压缩后的文件大小"""
        w, h = image.size
        # 粗略估算 (实际大小取决于内容)
        estimated_bytes = (w * h * 3) * (quality / 100.0) / 8
        return estimated_bytes
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


# ============================================================================
# 文件名: utils/file_helper.py
# 功能: 文件操作工具类
# 行数: 76 行
# ============================================================================

import os
import shutil
from pathlib import Path
from datetime import datetime
import json

class FileHelper:
    """
    文件操作工具类
    
    功能:
    1. 文件/目录创建和删除
    2. 文件移动和复制
    3. 目录遍历
    4. 文件备份
    5. 路径处理
    """
    
    @staticmethod
    def create_directory(path):
        """创建目录"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"创建目录失败: {e}")
            return False
    
    @staticmethod
    def delete_directory(path):
        """删除目录及其内容"""
        try:
            shutil.rmtree(path)
            return True
        except Exception as e:
            print(f"删除目录失败: {e}")
            return False
    
    @staticmethod
    def delete_file(file_path):
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False
    
    @staticmethod
    def copy_file(src, dest):
        """复制文件"""
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            return True
        except Exception as e:
            print(f"复制文件失败: {e}")
            return False
    
    @staticmethod
    def move_file(src, dest):
        """移动文件"""
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(src, dest)
            return True
        except Exception as e:
            print(f"移动文件失败: {e}")
            return False
    
    @staticmethod
    def list_files(directory, extension=None, recursive=False):
        """
        列出目录中的文件
        
        参数:
        - directory: 目录路径
        - extension: 文件扩展名过滤（如 '.jpg'）
        - recursive: 是否递归列出
        
        返回: 文件路径列表
        """
        files = []
        
        if recursive:
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if extension is None or filename.endswith(extension):
                        files.append(os.path.join(root, filename))
        else:
            if os.path.isdir(directory):
                for filename in os.listdir(directory):
                    filepath = os.path.join(directory, filename)
                    if os.path.isfile(filepath):
                        if extension is None or filename.endswith(extension):
                            files.append(filepath)
        
        return files
    
    @staticmethod
    def backup_directory(source_dir, backup_dir=None):
        """
        备份目录
        
        参数:
        - source_dir: 源目录
        - backup_dir: 备份目录（默认在源目录同级创建backup_yyyymmdd_hhmmss）
        
        返回: 备份路径
        """
        if backup_dir is None:
            parent = os.path.dirname(source_dir)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(parent, f'backup_{timestamp}')
        
        try:
            shutil.copytree(source_dir, backup_dir)
            print(f"备份成功: {backup_dir}")
            return backup_dir
        except Exception as e:
            print(f"备份失败: {e}")
            return None
    
    @staticmethod
    def get_file_size(file_path):
        """获取文件大小（字节）"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    @staticmethod
    def get_directory_size(directory):
        """获取目录总大小（字节）"""
        total = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total += os.path.getsize(filepath)
                except:
                    pass
        return total
