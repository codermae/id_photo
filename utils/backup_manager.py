"""
数据备份和恢复管理器
"""
import os
import shutil
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from config.config import DATABASE_DIR, DATA_DIR

class BackupManager:
    """数据备份和恢复管理器"""
    
    def __init__(self):
        self.backup_dir = DATA_DIR / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = DATABASE_DIR / 'id_photo.db'
        self.backup_index_file = self.backup_dir / 'backup_index.json'
    
    def create_backup(self, backup_name=None, include_photos=True):
        """
        创建备份
        
        Args:
            backup_name: 备份名称（如果为None，自动生成）
            include_photos: 是否包含照片文件
        
        Returns:
            dict: 备份信息
        """
        try:
            # 生成备份名称
            if backup_name is None:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 创建备份目录
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 备份数据库
            db_backup_path = backup_path / 'id_photo.db'
            shutil.copy2(self.db_path, db_backup_path)
            
            # 备份照片（可选）
            if include_photos:
                photos_src = DATA_DIR / 'photos'
                photos_backup = backup_path / 'photos'
                if photos_src.exists():
                    shutil.copytree(photos_src, photos_backup, dirs_exist_ok=True)
            
            # 创建备份信息文件
            backup_info = {
                'name': backup_name,
                'timestamp': datetime.now().isoformat(),
                'include_photos': include_photos,
                'db_size': os.path.getsize(db_backup_path),
                'photos_size': self._get_dir_size(backup_path / 'photos') if include_photos else 0,
                'status': 'completed'
            }
            
            # 保存备份信息
            self._save_backup_info(backup_name, backup_info)
            
            print(f"[INFO] 备份已创建: {backup_name}")
            return backup_info
        
        except Exception as e:
            print(f"[ERROR] 备份创建失败: {e}")
            raise
    
    def restore_backup(self, backup_name, restore_photos=True):
        """
        恢复备份
        
        Args:
            backup_name: 备份名称
            restore_photos: 是否恢复照片文件
        
        Returns:
            bool: 是否恢复成功
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                raise ValueError(f"备份不存在: {backup_name}")
            
            # 恢复数据库
            db_backup_path = backup_path / 'id_photo.db'
            if db_backup_path.exists():
                # 备份当前数据库
                current_db_backup = self.db_path.parent / f'id_photo_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
                if self.db_path.exists():
                    shutil.copy2(self.db_path, current_db_backup)
                
                # 恢复备份的数据库
                shutil.copy2(db_backup_path, self.db_path)
            
            # 恢复照片（可选）
            if restore_photos:
                photos_backup = backup_path / 'photos'
                photos_dst = DATA_DIR / 'photos'
                
                if photos_backup.exists():
                    # 备份当前照片
                    if photos_dst.exists():
                        current_photos_backup = DATA_DIR / f'photos_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                        shutil.copytree(photos_dst, current_photos_backup, dirs_exist_ok=True)
                    
                    # 恢复备份的照片
                    shutil.copytree(photos_backup, photos_dst, dirs_exist_ok=True)
            
            print(f"[INFO] 备份已恢复: {backup_name}")
            return True
        
        except Exception as e:
            print(f"[ERROR] 备份恢复失败: {e}")
            raise
    
    def list_backups(self):
        """
        列出所有备份
        
        Returns:
            list: 备份列表
        """
        try:
            backups = []
            
            if self.backup_index_file.exists():
                with open(self.backup_index_file, 'r', encoding='utf-8') as f:
                    backup_index = json.load(f)
                    backups = list(backup_index.values())
            
            # 按时间排序（最新的在前）
            backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return backups
        
        except Exception as e:
            print(f"[ERROR] 列出备份失败: {e}")
            return []
    
    def delete_backup(self, backup_name):
        """
        删除备份
        
        Args:
            backup_name: 备份名称
        
        Returns:
            bool: 是否删除成功
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            # 从索引中删除
            if self.backup_index_file.exists():
                with open(self.backup_index_file, 'r', encoding='utf-8') as f:
                    backup_index = json.load(f)
                
                if backup_name in backup_index:
                    del backup_index[backup_name]
                
                with open(self.backup_index_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_index, f, ensure_ascii=False, indent=2)
            
            print(f"[INFO] 备份已删除: {backup_name}")
            return True
        
        except Exception as e:
            print(f"[ERROR] 备份删除失败: {e}")
            raise
    
    def get_backup_info(self, backup_name):
        """
        获取备份信息
        
        Args:
            backup_name: 备份名称
        
        Returns:
            dict: 备份信息
        """
        try:
            if self.backup_index_file.exists():
                with open(self.backup_index_file, 'r', encoding='utf-8') as f:
                    backup_index = json.load(f)
                    return backup_index.get(backup_name)
            
            return None
        
        except Exception as e:
            print(f"[ERROR] 获取备份信息失败: {e}")
            return None
    
    def _save_backup_info(self, backup_name, backup_info):
        """保存备份信息到索引文件"""
        try:
            backup_index = {}
            
            if self.backup_index_file.exists():
                with open(self.backup_index_file, 'r', encoding='utf-8') as f:
                    backup_index = json.load(f)
            
            backup_index[backup_name] = backup_info
            
            with open(self.backup_index_file, 'w', encoding='utf-8') as f:
                json.dump(backup_index, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"[ERROR] 保存备份信息失败: {e}")
    
    def _get_dir_size(self, path):
        """获取目录大小（字节）"""
        try:
            total_size = 0
            if os.path.exists(path):
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
            return total_size
        except Exception as e:
            print(f"[WARNING] 获取目录大小失败: {e}")
            return 0
    
    def verify_backup(self, backup_name):
        """
        验证备份完整性
        
        Args:
            backup_name: 备份名称
        
        Returns:
            dict: 验证结果
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                return {'valid': False, 'message': '备份不存在'}
            
            # 检查数据库文件
            db_backup_path = backup_path / 'id_photo.db'
            if not db_backup_path.exists():
                return {'valid': False, 'message': '数据库文件缺失'}
            
            # 验证数据库完整性
            try:
                conn = sqlite3.connect(db_backup_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                if not tables:
                    return {'valid': False, 'message': '数据库表缺失'}
            except Exception as e:
                return {'valid': False, 'message': f'数据库验证失败: {e}'}
            
            return {'valid': True, 'message': '备份完整有效'}
        
        except Exception as e:
            return {'valid': False, 'message': f'验证失败: {e}'}
    
    def export_backup(self, backup_name, export_path):
        """
        导出备份到指定位置
        
        Args:
            backup_name: 备份名称
            export_path: 导出路径
        
        Returns:
            bool: 是否导出成功
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                raise ValueError(f"备份不存在: {backup_name}")
            
            # 创建导出目录
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制备份文件
            export_backup_path = export_dir / backup_name
            shutil.copytree(backup_path, export_backup_path, dirs_exist_ok=True)
            
            print(f"[INFO] 备份已导出: {export_backup_path}")
            return True
        
        except Exception as e:
            print(f"[ERROR] 备份导出失败: {e}")
            raise
    
    def import_backup(self, import_path, backup_name=None):
        """
        从指定位置导入备份
        
        Args:
            import_path: 导入路径
            backup_name: 备份名称（如果为None，使用导入目录名）
        
        Returns:
            dict: 导入的备份信息
        """
        try:
            import_dir = Path(import_path)
            
            if not import_dir.exists():
                raise ValueError(f"导入路径不存在: {import_path}")
            
            # 生成备份名称
            if backup_name is None:
                backup_name = f"imported_{import_dir.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 复制导入的备份
            backup_path = self.backup_dir / backup_name
            shutil.copytree(import_dir, backup_path, dirs_exist_ok=True)
            
            # 验证导入的备份
            verify_result = self.verify_backup(backup_name)
            
            if not verify_result['valid']:
                shutil.rmtree(backup_path)
                raise ValueError(f"导入的备份无效: {verify_result['message']}")
            
            # 保存备份信息
            backup_info = {
                'name': backup_name,
                'timestamp': datetime.now().isoformat(),
                'imported': True,
                'original_path': str(import_path),
                'status': 'completed'
            }
            self._save_backup_info(backup_name, backup_info)
            
            print(f"[INFO] 备份已导入: {backup_name}")
            return backup_info
        
        except Exception as e:
            print(f"[ERROR] 备份导入失败: {e}")
            raise
