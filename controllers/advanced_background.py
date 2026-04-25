"""
高级背景替换 - 支持渐变、纹理、虚化背景
"""
import cv2
import numpy as np
from typing import Tuple, Dict, Optional
import os

class AdvancedBackgroundReplacer:
    """高级背景替换器 - 支持渐变、纹理、虚化背景"""
    
    def __init__(self):
        """初始化高级背景替换器"""
        self.background_colors = {
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'blue': (67, 142, 219),
            'light_blue': (173, 216, 230),
            'gray': (192, 192, 192),
            'light_gray': (220, 220, 220),
        }
    
    def replace_with_gradient(self, image: np.ndarray, mask: np.ndarray,
                             color1: Tuple[int, int, int],
                             color2: Tuple[int, int, int],
                             direction: str = 'vertical') -> Tuple[np.ndarray, Dict]:
        """
        使用渐变背景替换
        
        Args:
            image: 输入图像
            mask: 人物mask（255为人物，0为背景）
            color1: 渐变起始颜色 (B, G, R)
            color2: 渐变结束颜色 (B, G, R)
            direction: 渐变方向 ('vertical', 'horizontal', 'diagonal')
        
        Returns:
            tuple: (处理后的图像, 处理信息)
        """
        try:
            h, w = image.shape[:2]
            
            # 创建渐变背景
            gradient_bg = np.zeros((h, w, 3), dtype=np.uint8)
            
            if direction == 'vertical':
                # 垂直渐变
                for y in range(h):
                    ratio = y / h
                    color = tuple(int(c1 * (1 - ratio) + c2 * ratio) 
                                for c1, c2 in zip(color1, color2))
                    gradient_bg[y, :] = color
            
            elif direction == 'horizontal':
                # 水平渐变
                for x in range(w):
                    ratio = x / w
                    color = tuple(int(c1 * (1 - ratio) + c2 * ratio) 
                                for c1, c2 in zip(color1, color2))
                    gradient_bg[:, x] = color
            
            elif direction == 'diagonal':
                # 对角线渐变
                for y in range(h):
                    for x in range(w):
                        ratio = (x + y) / (w + h)
                        color = tuple(int(c1 * (1 - ratio) + c2 * ratio) 
                                    for c1, c2 in zip(color1, color2))
                        gradient_bg[y, x] = color
            
            # 平滑mask边缘
            mask_smooth = self._smooth_mask_edges(mask)
            
            # 合成图像
            mask_3ch = cv2.cvtColor(mask_smooth, cv2.COLOR_GRAY2BGR) / 255.0
            result = (image * mask_3ch + gradient_bg * (1 - mask_3ch)).astype(np.uint8)
            
            return result, {
                'method': 'gradient',
                'direction': direction,
                'color1': color1,
                'color2': color2
            }
        
        except Exception as e:
            print(f"[ERROR] 渐变背景替换失败: {e}")
            raise
    
    def replace_with_texture(self, image: np.ndarray, mask: np.ndarray,
                            texture) -> Tuple[np.ndarray, Dict]:
        """
        使用纹理背景替换
        
        Args:
            image: 输入图像
            mask: 人物mask
            texture: 纹理图像数组或纹理文件路径
        
        Returns:
            tuple: (处理后的图像, 处理信息)
        """
        try:
            h, w = image.shape[:2]
            
            # 如果texture是字符串，则作为文件路径加载
            if isinstance(texture, str):
                if not os.path.exists(texture):
                    raise ValueError(f"纹理文件不存在: {texture}")
                
                texture_img = cv2.imread(texture)
                if texture_img is None:
                    raise ValueError(f"无法加载纹理: {texture}")
            else:
                # 否则假设是numpy数组
                texture_img = texture
            
            # 调整纹理大小以匹配图像
            texture_img = cv2.resize(texture_img, (w, h))
            
            # 平滑mask边缘
            mask_smooth = self._smooth_mask_edges(mask)
            
            # 合成图像
            mask_3ch = cv2.cvtColor(mask_smooth, cv2.COLOR_GRAY2BGR) / 255.0
            result = (image * mask_3ch + texture_img * (1 - mask_3ch)).astype(np.uint8)
            
            return result, {
                'method': 'texture',
                'texture_type': 'file' if isinstance(texture, str) else 'array'
            }
        
        except Exception as e:
            print(f"[ERROR] 纹理背景替换失败: {e}")
            raise
    
    def replace_with_blur(self, image: np.ndarray, mask: np.ndarray,
                         blur_strength: int = 30) -> Tuple[np.ndarray, Dict]:
        """
        使用虚化背景替换
        
        Args:
            image: 输入图像
            mask: 人物mask
            blur_strength: 虚化强度 (1-100)
        
        Returns:
            tuple: (处理后的图像, 处理信息)
        """
        try:
            # 限制虚化强度范围
            blur_strength = max(1, min(100, blur_strength))
            
            # 计算高斯模糊的核大小
            kernel_size = int(blur_strength / 2) * 2 + 1
            
            # 创建虚化背景
            blurred_bg = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
            
            # 平滑mask边缘
            mask_smooth = self._smooth_mask_edges(mask)
            
            # 合成图像
            mask_3ch = cv2.cvtColor(mask_smooth, cv2.COLOR_GRAY2BGR) / 255.0
            result = (image * mask_3ch + blurred_bg * (1 - mask_3ch)).astype(np.uint8)
            
            return result, {
                'method': 'blur',
                'blur_strength': blur_strength
            }
        
        except Exception as e:
            print(f"[ERROR] 虚化背景替换失败: {e}")
            raise
    
    def _smooth_mask_edges(self, mask: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """
        平滑mask边缘，避免锯齿
        
        Args:
            mask: 输入mask
            kernel_size: 平滑核大小
        
        Returns:
            np.ndarray: 平滑后的mask
        """
        try:
            # 高斯模糊平滑边缘
            mask_smooth = cv2.GaussianBlur(mask, (kernel_size, kernel_size), 0)
            
            # 形态学操作进一步平滑
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask_smooth = cv2.morphologyEx(mask_smooth, cv2.MORPH_CLOSE, kernel)
            mask_smooth = cv2.morphologyEx(mask_smooth, cv2.MORPH_OPEN, kernel)
            
            return mask_smooth
        
        except Exception as e:
            print(f"[WARNING] mask边缘平滑失败: {e}")
            return mask
    
    def create_gradient_background(self, width: int, height: int,
                                  color1: Tuple[int, int, int],
                                  color2: Tuple[int, int, int],
                                  direction: str = 'vertical') -> np.ndarray:
        """
        创建纯渐变背景
        
        Args:
            width: 宽度
            height: 高度
            color1: 起始颜色
            color2: 结束颜色
            direction: 渐变方向
        
        Returns:
            np.ndarray: 渐变背景图像
        """
        gradient_bg = np.zeros((height, width, 3), dtype=np.uint8)
        
        if direction == 'vertical':
            for y in range(height):
                ratio = y / height
                color = tuple(int(c1 * (1 - ratio) + c2 * ratio) 
                            for c1, c2 in zip(color1, color2))
                gradient_bg[y, :] = color
        
        elif direction == 'horizontal':
            for x in range(width):
                ratio = x / width
                color = tuple(int(c1 * (1 - ratio) + c2 * ratio) 
                            for c1, c2 in zip(color1, color2))
                gradient_bg[:, x] = color
        
        elif direction == 'diagonal':
            for y in range(height):
                for x in range(width):
                    ratio = (x + y) / (width + height)
                    color = tuple(int(c1 * (1 - ratio) + c2 * ratio) 
                                for c1, c2 in zip(color1, color2))
                    gradient_bg[y, x] = color
        
        return gradient_bg
    
    def create_texture_background(self, width: int, height: int,
                                 texture_path: str) -> np.ndarray:
        """
        创建纹理背景
        
        Args:
            width: 宽度
            height: 高度
            texture_path: 纹理图像路径
        
        Returns:
            np.ndarray: 纹理背景图像
        """
        if not os.path.exists(texture_path):
            raise ValueError(f"纹理文件不存在: {texture_path}")
        
        texture = cv2.imread(texture_path)
        if texture is None:
            raise ValueError(f"无法加载纹理: {texture_path}")
        
        # 调整纹理大小
        texture = cv2.resize(texture, (width, height))
        
        return texture
    
    def create_blur_background(self, image: np.ndarray,
                              blur_strength: int = 30) -> np.ndarray:
        """
        创建虚化背景
        
        Args:
            image: 输入图像
            blur_strength: 虚化强度
        
        Returns:
            np.ndarray: 虚化背景图像
        """
        blur_strength = max(1, min(100, blur_strength))
        kernel_size = int(blur_strength / 2) * 2 + 1
        
        blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        
        return blurred
    
    def blend_backgrounds(self, image: np.ndarray, mask: np.ndarray,
                         background: np.ndarray,
                         blend_mode: str = 'normal') -> np.ndarray:
        """
        混合背景
        
        Args:
            image: 输入图像
            mask: 人物mask
            background: 背景图像
            blend_mode: 混合模式 ('normal', 'soft', 'hard')
        
        Returns:
            np.ndarray: 混合后的图像
        """
        try:
            # 平滑mask边缘
            mask_smooth = self._smooth_mask_edges(mask)
            
            # 转换为浮点数进行混合
            mask_3ch = cv2.cvtColor(mask_smooth, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
            image_f = image.astype(np.float32)
            background_f = background.astype(np.float32)
            
            if blend_mode == 'normal':
                # 正常混合
                result = image_f * mask_3ch + background_f * (1 - mask_3ch)
            
            elif blend_mode == 'soft':
                # 软混合（边缘更柔和）
                edge_mask = self._create_soft_edge_mask(mask_smooth)
                edge_mask_3ch = cv2.cvtColor(edge_mask, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
                result = image_f * edge_mask_3ch + background_f * (1 - edge_mask_3ch)
            
            elif blend_mode == 'hard':
                # 硬混合（边缘更清晰）
                _, hard_mask = cv2.threshold(mask_smooth, 127, 255, cv2.THRESH_BINARY)
                hard_mask_3ch = cv2.cvtColor(hard_mask, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
                result = image_f * hard_mask_3ch + background_f * (1 - hard_mask_3ch)
            
            else:
                result = image_f * mask_3ch + background_f * (1 - mask_3ch)
            
            return np.clip(result, 0, 255).astype(np.uint8)
        
        except Exception as e:
            print(f"[ERROR] 背景混合失败: {e}")
            raise
    
    def _create_soft_edge_mask(self, mask: np.ndarray) -> np.ndarray:
        """创建柔和边缘mask"""
        # 使用多层高斯模糊创建柔和边缘
        soft_mask = cv2.GaussianBlur(mask, (11, 11), 0)
        soft_mask = cv2.GaussianBlur(soft_mask, (11, 11), 0)
        return soft_mask
