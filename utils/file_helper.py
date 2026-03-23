"""
文件操作助手
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from config.config import RAW_PHOTOS_DIR, PROCESSED_PHOTOS_DIR, ID_PHOTOS_DIR

class FileHelper:
    """文件操作助手类"""

    @staticmethod
    def save_raw_photo(id_number, image_data):
        """保存原始照片"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{id_number}_{timestamp}.jpg'
        filepath = RAW_PHOTOS_DIR / filename
        
        # 使用 cv2.imencode() + Python文件写入来支持中文路径
        try:
            import cv2
            import numpy as np
            
            success, encoded_image = cv2.imencode('.jpg', image_data)
            if success:
                with open(str(filepath), 'wb') as f:
                    f.write(encoded_image.tobytes())
            else:
                raise Exception("图像编码失败")
        except Exception as e:
            print(f"[ERROR] 保存原始照片失败: {e}")
            # 尝试使用PIL保存
            try:
                from PIL import Image
                if isinstance(image_data, np.ndarray):
                    # 转换BGR到RGB
                    image_rgb = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(image_rgb)
                    pil_image.save(str(filepath))
                else:
                    image_data.save(str(filepath))
            except Exception as e2:
                print(f"[ERROR] PIL保存也失败: {e2}")
                raise
        
        return str(filepath)

    @staticmethod
    def save_processed_photo(id_number, image_data, spec='一寸', bg_color='白色'):
        """保存处理后的照片"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{id_number}_{spec}_{bg_color}_{timestamp}.jpg'
        filepath = PROCESSED_PHOTOS_DIR / filename
        
        try:
            import cv2
            import numpy as np
            
            # 使用 cv2.imencode() + Python文件写入来支持中文路径
            success, encoded_image = cv2.imencode('.jpg', image_data)
            if success:
                with open(str(filepath), 'wb') as f:
                    f.write(encoded_image.tobytes())
            else:
                raise Exception("图像编码失败")
        except Exception as e:
            print(f"[ERROR] 保存处理后照片失败: {e}")
            # 尝试使用PIL保存
            try:
                from PIL import Image
                if isinstance(image_data, np.ndarray):
                    # 转换BGR到RGB
                    image_rgb = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(image_rgb)
                    pil_image.save(str(filepath))
                else:
                    image_data.save(str(filepath))
            except Exception as e2:
                print(f"[ERROR] PIL保存也失败: {e2}")
                raise
        
        return str(filepath)

    @staticmethod
    def save_id_photo(id_number, image_data):
        """保存身份证照片"""
        filename = f'{id_number}_id_photo.jpg'
        filepath = ID_PHOTOS_DIR / filename
        
        try:
            import cv2
            import numpy as np
            
            # 如果是 bytes 类型，直接写入
            if isinstance(image_data, bytes):
                with open(str(filepath), 'wb') as f:
                    f.write(image_data)
            else:
                # 如果是 numpy 数组，使用 cv2 编码
                success, encoded_image = cv2.imencode('.jpg', image_data)
                if success:
                    with open(str(filepath), 'wb') as f:
                        f.write(encoded_image.tobytes())
                else:
                    raise Exception("图像编码失败")
        except Exception as e:
            print(f"[ERROR] 保存身份证照片失败: {e}")
            # 尝试使用PIL保存
            try:
                from PIL import Image
                if isinstance(image_data, np.ndarray):
                    # 转换BGR到RGB
                    image_rgb = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(image_rgb)
                    pil_image.save(str(filepath))
                elif isinstance(image_data, bytes):
                    # 从 bytes 创建 PIL Image
                    from io import BytesIO
                    pil_image = Image.open(BytesIO(image_data))
                    pil_image.save(str(filepath))
                else:
                    image_data.save(str(filepath))
            except Exception as e2:
                print(f"[ERROR] PIL保存也失败: {e2}")
                raise
        
        return str(filepath)

    @staticmethod
    def get_file_size(filepath):
        """获取文件大小（字节）"""
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0

    @staticmethod
    def delete_file(filepath):
        """删除文件"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False

    @staticmethod
    def copy_file(src, dst):
        """复制文件"""
        try:
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"复制文件失败: {e}")
            return False

    @staticmethod
    def get_photos_by_user(id_number):
        """获取用户的所有照片"""
        photos = {
            'raw': [],
            'processed': []
        }
        
        # 获取原始照片
        for file in RAW_PHOTOS_DIR.glob(f'{id_number}_*.jpg'):
            photos['raw'].append(str(file))
        
        # 获取处理后的照片
        for file in PROCESSED_PHOTOS_DIR.glob(f'{id_number}_*.jpg'):
            photos['processed'].append(str(file))
        
        return photos

    @staticmethod
    def cleanup_old_photos(id_number, keep_count=5):
        """清理旧照片，只保留最新的N张"""
        raw_photos = sorted(RAW_PHOTOS_DIR.glob(f'{id_number}_*.jpg'), 
                           key=lambda x: x.stat().st_mtime, reverse=True)
        
        for photo in raw_photos[keep_count:]:
            FileHelper.delete_file(str(photo))
