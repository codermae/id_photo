"""
身份证照片生成器

用于生成模拟的身份证照片，包含：
- 身份证背景
- 个人照片
- 文字信息
- 防伪元素
"""

import cv2
import numpy as np
from datetime import datetime, timedelta
import random
from PIL import Image, ImageDraw, ImageFont
import os


class IDCardPhotoGenerator:
    """身份证照片生成器"""
    
    # 身份证尺寸（mm）
    CARD_WIDTH = 85
    CARD_HEIGHT = 54
    
    # 转换为像素（300dpi）
    DPI = 300
    PIXEL_WIDTH = int(CARD_WIDTH * DPI / 25.4)
    PIXEL_HEIGHT = int(CARD_HEIGHT * DPI / 25.4)
    
    def __init__(self):
        """初始化生成器"""
        self.font_path = self._get_font_path()
    
    @staticmethod
    def _get_font_path():
        """获取中文字体路径"""
        # 尝试多个常见的中文字体位置
        font_paths = [
            'C:\\Windows\\Fonts\\simhei.ttf',  # Windows 黑体
            'C:\\Windows\\Fonts\\simsun.ttc',  # Windows 宋体
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Linux
            '/System/Library/Fonts/PingFang.ttc',  # macOS
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                return path
        
        # 如果找不到中文字体，返回None（使用默认字体）
        return None
    
    def generate_id_card_photo(self, user_data: dict, face_photo: np.ndarray = None) -> np.ndarray:
        """
        生成身份证照片
        
        Args:
            user_data: 用户信息字典，包含：
                - name: 姓名
                - id_number: 身份证号
                - gender: 性别
                - birth_date: 出生日期 (YYYY-MM-DD)
                - address: 地址
                - nation: 民族
                - issue_authority: 签发机关
                - valid_period: 有效期限
            face_photo: 人脸照片（可选，如果不提供则生成模拟照片）
        
        Returns:
            np.ndarray: 身份证照片
        """
        # 创建空白身份证背景
        card = self._create_card_background()
        
        # 添加人脸照片
        if face_photo is not None:
            card = self._add_face_photo(card, face_photo)
        else:
            card = self._add_placeholder_photo(card)
        
        # 添加文字信息
        card = self._add_text_info(card, user_data)
        
        # 添加防伪元素
        card = self._add_security_elements(card)
        
        return card
    
    def _create_card_background(self) -> Image.Image:
        """创建身份证背景"""
        # 创建红色背景（中国身份证标准颜色）
        background_color = (220, 20, 60)  # RGB 深红色
        
        # 使用PIL创建图像
        card = Image.new('RGB', (self.PIXEL_WIDTH, self.PIXEL_HEIGHT), background_color)
        
        return card
    
    def _add_face_photo(self, card: Image.Image, face_photo: np.ndarray) -> Image.Image:
        """添加人脸照片"""
        # 转换OpenCV图像为PIL图像
        if len(face_photo.shape) == 3:
            face_pil = Image.fromarray(cv2.cvtColor(face_photo, cv2.COLOR_BGR2RGB))
        else:
            face_pil = Image.fromarray(face_photo)
        
        # 调整照片大小（身份证照片区域）
        # 照片区域：左上角 (20, 20)，大小约 (35mm × 45mm)
        photo_width = int(35 * self.DPI / 25.4)
        photo_height = int(45 * self.DPI / 25.4)
        
        face_pil = face_pil.resize((photo_width, photo_height), Image.Resampling.LANCZOS)
        
        # 粘贴到身份证上
        card.paste(face_pil, (20, 20))
        
        return card
    
    def _add_placeholder_photo(self, card: Image.Image) -> Image.Image:
        """添加占位符照片"""
        # 创建灰色占位符
        photo_width = int(35 * self.DPI / 25.4)
        photo_height = int(45 * self.DPI / 25.4)
        
        placeholder = Image.new('RGB', (photo_width, photo_height), (200, 200, 200))
        
        # 添加"照片"文字
        draw = ImageDraw.Draw(placeholder)
        text = "照片"
        
        # 计算文字位置（居中）
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (photo_width - text_width) // 2
        y = (photo_height - text_height) // 2
        
        draw.text((x, y), text, fill=(100, 100, 100))
        
        # 粘贴到身份证上
        card.paste(placeholder, (20, 20))
        
        return card
    
    def _add_text_info(self, card: Image.Image, user_data: dict) -> Image.Image:
        """添加文字信息"""
        draw = ImageDraw.Draw(card)
        
        # 获取字体
        font_large = self._get_font(size=20)
        font_medium = self._get_font(size=16)
        font_small = self._get_font(size=12)
        
        # 文字颜色（白色）
        text_color = (255, 255, 255)
        
        # 计算文字位置
        # 照片右侧开始
        text_x = 70
        text_y = 30
        line_height = 25
        
        # 姓名
        name = user_data.get('name', '张三')
        draw.text((text_x, text_y), f"姓名: {name}", fill=text_color, font=font_medium)
        text_y += line_height
        
        # 性别
        gender = user_data.get('gender', '男')
        draw.text((text_x, text_y), f"性别: {gender}", fill=text_color, font=font_small)
        text_y += line_height
        
        # 民族
        nation = user_data.get('nation', '汉')
        draw.text((text_x, text_y), f"民族: {nation}", fill=text_color, font=font_small)
        text_y += line_height
        
        # 出生日期
        birth_date = user_data.get('birth_date', '1990-01-01')
        draw.text((text_x, text_y), f"出生: {birth_date}", fill=text_color, font=font_small)
        text_y += line_height
        
        # 身份证号（分两行显示）
        id_number = user_data.get('id_number', '110101199001010015')
        draw.text((text_x, text_y), f"证号: {id_number[:9]}", fill=text_color, font=font_small)
        text_y += line_height
        draw.text((text_x, text_y), f"      {id_number[9:]}", fill=text_color, font=font_small)
        
        return card
    
    def _add_security_elements(self, card: Image.Image) -> Image.Image:
        """添加防伪元素"""
        draw = ImageDraw.Draw(card)
        
        # 添加国徽（简化版）
        self._draw_national_emblem(draw, (self.PIXEL_WIDTH - 40, 10), size=30)
        
        # 添加"中华人民共和国"文字
        font = self._get_font(size=14)
        draw.text((10, self.PIXEL_HEIGHT - 25), "中华人民共和国", fill=(255, 255, 255), font=font)
        
        # 添加"居民身份证"文字
        draw.text((self.PIXEL_WIDTH - 100, self.PIXEL_HEIGHT - 25), "居民身份证", 
                 fill=(255, 255, 255), font=font)
        
        return card
    
    @staticmethod
    def _draw_national_emblem(draw: ImageDraw.ImageDraw, position: tuple, size: int):
        """绘制国徽（简化版）"""
        x, y = position
        
        # 绘制圆形
        draw.ellipse([x - size//2, y - size//2, x + size//2, y + size//2], 
                    outline=(255, 255, 255), width=2)
        
        # 绘制五角星
        star_x = x
        star_y = y - 2
        star_size = size // 3
        
        # 简化的五角星（用圆点表示）
        draw.ellipse([star_x - 2, star_y - 2, star_x + 2, star_y + 2], fill=(255, 255, 255))
    
    def _get_font(self, size: int = 16):
        """获取字体对象"""
        try:
            if self.font_path:
                return ImageFont.truetype(self.font_path, size)
        except:
            pass
        
        # 如果加载失败，使用默认字体
        return ImageFont.load_default()
    
    def generate_multiple_id_cards(self, users_data: list, face_photos: list = None) -> list:
        """
        批量生成身份证照片
        
        Args:
            users_data: 用户信息列表
            face_photos: 人脸照片列表（可选）
        
        Returns:
            list: 身份证照片列表
        """
        id_cards = []
        
        for i, user_data in enumerate(users_data):
            face_photo = None
            if face_photos and i < len(face_photos):
                face_photo = face_photos[i]
            
            id_card = self.generate_id_card_photo(user_data, face_photo)
            id_cards.append(id_card)
        
        return id_cards
    
    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """将PIL图像转换为OpenCV格式"""
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return cv_image
    
    @staticmethod
    def cv2_to_pil(cv_image: np.ndarray) -> Image.Image:
        """将OpenCV图像转换为PIL格式"""
        pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        return pil_image


class IDCardPhotoSimulator:
    """身份证照片模拟器 - 生成逼真的模拟身份证照片"""
    
    def __init__(self):
        """初始化模拟器"""
        self.generator = IDCardPhotoGenerator()
    
    def generate_realistic_id_card(self, user_data: dict) -> np.ndarray:
        """
        生成逼真的模拟身份证照片
        
        Args:
            user_data: 用户信息
        
        Returns:
            np.ndarray: 身份证照片（OpenCV格式）
        """
        # 生成模拟人脸照片
        face_photo = self._generate_face_photo(user_data)
        
        # 生成身份证
        id_card_pil = self.generator.generate_id_card_photo(user_data, face_photo)
        
        # 转换为OpenCV格式
        id_card_cv = self.generator.pil_to_cv2(id_card_pil)
        
        # 调整大小到合理的分辨率
        id_card_cv = cv2.resize(id_card_cv, (400, 250))
        
        return id_card_cv
    
    @staticmethod
    def _generate_face_photo(user_data: dict) -> np.ndarray:
        """
        生成模拟人脸照片
        
        Args:
            user_data: 用户信息
        
        Returns:
            np.ndarray: 人脸照片
        """
        # 创建一个简单的人脸照片（蓝色背景）
        height, width = 200, 160
        face_photo = np.ones((height, width, 3), dtype=np.uint8) * 100
        
        # 添加肤色区域（简化版）
        cv2.circle(face_photo, (width // 2, height // 3), 40, (180, 150, 120), -1)
        
        # 添加眼睛
        cv2.circle(face_photo, (width // 2 - 15, height // 3 - 10), 5, (0, 0, 0), -1)
        cv2.circle(face_photo, (width // 2 + 15, height // 3 - 10), 5, (0, 0, 0), -1)
        
        # 添加嘴巴
        cv2.ellipse(face_photo, (width // 2, height // 3 + 15), (15, 8), 0, 0, 180, (0, 0, 0), 2)
        
        return face_photo
    
    def generate_batch_id_cards(self, users_data: list) -> list:
        """
        批量生成模拟身份证照片
        
        Args:
            users_data: 用户信息列表
        
        Returns:
            list: 身份证照片列表
        """
        id_cards = []
        
        for user_data in users_data:
            id_card = self.generate_realistic_id_card(user_data)
            id_cards.append(id_card)
        
        return id_cards


# 使用示例
if __name__ == '__main__':
    # 测试数据
    test_users = [
        {
            'name': '张三',
            'id_number': '110101199001010015',
            'gender': '男',
            'birth_date': '1990-01-01',
            'nation': '汉',
            'address': '北京市东城区XX街道XX号',
            'issue_authority': '北京市公安局东城分局',
            'valid_period': '2010.01.01-2030.01.01'
        },
        {
            'name': '李四',
            'id_number': '110101199001010023',
            'gender': '女',
            'birth_date': '1990-01-01',
            'nation': '汉',
            'address': '北京市东城区XX街道XX号',
            'issue_authority': '北京市公安局东城分局',
            'valid_period': '2010.01.01-2030.01.01'
        }
    ]
    
    # 生成身份证照片
    simulator = IDCardPhotoSimulator()
    
    for user in test_users:
        id_card = simulator.generate_realistic_id_card(user)
        
        # 保存照片
        filename = f"id_card_{user['id_number']}.jpg"
        cv2.imwrite(filename, id_card)
        print(f"✓ 已生成: {filename}")
