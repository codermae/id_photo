"""
实时参数调整系统
提供实时预览的图像参数调整功能
"""
import cv2
import numpy as np
from typing import Dict, Callable, Optional, Tuple
import json
import os

class RealTimeAdjuster:
    """实时参数调整器"""
    
    def __init__(self, update_callback: Optional[Callable] = None):
        """
        初始化调整器
        
        Args:
            update_callback: 图像更新回调函数
        """
        self.original_image = None
        self.current_image = None
        self.update_callback = update_callback
        
        # 参数定义
        self.params = {
            'brightness': 0,      # 亮度 (-100 到 100)
            'contrast': 0,        # 对比度 (-100 到 100)
            'saturation': 0,      # 饱和度 (-100 到 100)
            'sharpness': 0,       # 锐化 (0 到 100)
            'gamma': 1.0,         # 伽马校正 (0.1 到 3.0)
            'hue': 0,             # 色调 (-180 到 180)
            'warmth': 0,          # 色温 (-100 到 100)
            'vibrance': 0,        # 自然饱和度 (-100 到 100)
            'highlights': 0,      # 高光 (-100 到 100)
            'shadows': 0,         # 阴影 (-100 到 100)
            'clarity': 0          # 清晰度 (-100 到 100)
        }
        
        # 参数范围定义
        self.param_ranges = {
            'brightness': (-100, 100, 1),
            'contrast': (-100, 100, 1),
            'saturation': (-100, 100, 1),
            'sharpness': (0, 100, 1),
            'gamma': (0.1, 3.0, 0.1),
            'hue': (-180, 180, 1),
            'warmth': (-100, 100, 1),
            'vibrance': (-100, 100, 1),
            'highlights': (-100, 100, 1),
            'shadows': (-100, 100, 1),
            'clarity': (-100, 100, 1)
        }
        
        # 预设参数
        self.presets = {
            '原始': {param: 0 if param != 'gamma' else 1.0 for param in self.params},
            '标准证件照': {
                'brightness': 10,
                'contrast': 15,
                'saturation': -5,
                'sharpness': 20,
                'gamma': 1.1,
                'hue': 0,
                'warmth': 5,
                'vibrance': 10,
                'highlights': -10,
                'shadows': 15,
                'clarity': 10
            },
            '护照照片': {
                'brightness': 5,
                'contrast': 10,
                'saturation': -10,
                'sharpness': 15,
                'gamma': 1.05,
                'hue': 0,
                'warmth': 0,
                'vibrance': 5,
                'highlights': -5,
                'shadows': 10,
                'clarity': 5
            },
            '签证照片': {
                'brightness': 8,
                'contrast': 12,
                'saturation': 0,
                'sharpness': 25,
                'gamma': 1.15,
                'hue': 0,
                'warmth': 3,
                'vibrance': 8,
                'highlights': -8,
                'shadows': 12,
                'clarity': 8
            },
            '柔和风格': {
                'brightness': 15,
                'contrast': -5,
                'saturation': 10,
                'sharpness': 5,
                'gamma': 0.9,
                'hue': 0,
                'warmth': 10,
                'vibrance': 15,
                'highlights': 10,
                'shadows': 20,
                'clarity': -10
            },
            '高对比度': {
                'brightness': 0,
                'contrast': 30,
                'saturation': 15,
                'sharpness': 40,
                'gamma': 1.2,
                'hue': 0,
                'warmth': -5,
                'vibrance': 20,
                'highlights': -20,
                'shadows': -10,
                'clarity': 25
            }
        }
    
    def set_image(self, image: np.ndarray):
        """设置原始图像"""
        self.original_image = image.copy()
        self.current_image = image.copy()
        self._update_display()
    
    def adjust_parameter(self, param_name: str, value: float):
        """调整单个参数"""
        if param_name not in self.params:
            raise ValueError(f"未知参数: {param_name}")
        
        # 检查参数范围
        min_val, max_val, _ = self.param_ranges[param_name]
        value = max(min_val, min(max_val, value))
        
        # 输出参数调整信息
        old_value = self.params[param_name]
        self.params[param_name] = value
        
        print(f"[DEBUG] 参数调整: {param_name} = {old_value} -> {value}")
        print(f"[DEBUG] 参数范围: [{min_val}, {max_val}]")
        
        self._apply_adjustments()
    
    def adjust_brightness(self, value: int):
        """调整亮度"""
        self.adjust_parameter('brightness', value)
    
    def adjust_contrast(self, value: int):
        """调整对比度"""
        self.adjust_parameter('contrast', value)
    
    def adjust_saturation(self, value: int):
        """调整饱和度"""
        self.adjust_parameter('saturation', value)
    
    def adjust_sharpness(self, value: int):
        """调整锐化"""
        self.adjust_parameter('sharpness', value)
    
    def adjust_gamma(self, value: float):
        """调整伽马值"""
        self.adjust_parameter('gamma', value)
    
    def adjust_hue(self, value: int):
        """调整色调"""
        self.adjust_parameter('hue', value)
    
    def adjust_warmth(self, value: int):
        """调整色温"""
        self.adjust_parameter('warmth', value)
    
    def adjust_vibrance(self, value: int):
        """调整自然饱和度"""
        self.adjust_parameter('vibrance', value)
    
    def adjust_highlights(self, value: int):
        """调整高光"""
        self.adjust_parameter('highlights', value)
    
    def adjust_shadows(self, value: int):
        """调整阴影"""
        self.adjust_parameter('shadows', value)
    
    def adjust_clarity(self, value: int):
        """调整清晰度"""
        self.adjust_parameter('clarity', value)
    
    def apply_preset(self, preset_name: str):
        """应用预设参数"""
        if preset_name not in self.presets:
            raise ValueError(f"未知预设: {preset_name}")
        
        self.params.update(self.presets[preset_name])
        self._apply_adjustments()
    
    def reset_parameters(self):
        """重置所有参数"""
        self.apply_preset('原始')
    
    def _apply_adjustments(self):
        """应用所有调整"""
        if self.original_image is None:
            return
        
        print("[DEBUG] 开始应用图像调整...")
        print(f"[DEBUG] 当前参数: {self.params}")
        
        # 关键修改：从original_image开始，而不是从current_image
        # 这样可以确保所有参数都是相对于原始图像的
        result = self.original_image.astype(np.float32)
        
        # 1. 亮度调整
        if self.params['brightness'] != 0:
            result = self._adjust_brightness(result, self.params['brightness'])
            print(f"[DEBUG] 亮度调整完成: {self.params['brightness']}")
        
        # 2. 对比度调整
        if self.params['contrast'] != 0:
            result = self._adjust_contrast(result, self.params['contrast'])
            print(f"[DEBUG] 对比度调整完成: {self.params['contrast']}")
        
        # 3. 伽马校正
        if self.params['gamma'] != 1.0:
            result = self._adjust_gamma(result, self.params['gamma'])
            print(f"[DEBUG] 伽马校正完成: {self.params['gamma']}")
        
        # 4. 色彩调整
        color_params = ['saturation', 'hue', 'warmth', 'vibrance']
        if any(self.params[p] != 0 for p in color_params):
            result = self._adjust_colors(result)
            active_color_params = {p: self.params[p] for p in color_params if self.params[p] != 0}
            print(f"[DEBUG] 色彩调整完成: {active_color_params}")
        
        # 5. 高光阴影调整
        if self.params['highlights'] != 0 or self.params['shadows'] != 0:
            result = self._adjust_highlights_shadows(result)
            print(f"[DEBUG] 高光阴影调整完成: 高光={self.params['highlights']}, 阴影={self.params['shadows']}")
        
        # 6. 锐化和清晰度
        if self.params['sharpness'] != 0 or self.params['clarity'] != 0:
            result = self._adjust_sharpness_clarity(result)
            print(f"[DEBUG] 锐化清晰度调整完成: 锐化={self.params['sharpness']}, 清晰度={self.params['clarity']}")
        
        # 限制范围并更新
        result = np.clip(result, 0, 255).astype(np.uint8)
        self.current_image = result
        
        # 输出最终统计信息
        orig_mean = np.mean(self.original_image)
        result_mean = np.mean(result)
        orig_std = np.std(self.original_image)
        result_std = np.std(result)
        
        print(f"[DEBUG] 调整完成 - 原始图像: 均值={orig_mean:.1f}, 标准差={orig_std:.1f}")
        print(f"[DEBUG] 调整完成 - 处理后: 均值={result_mean:.1f}, 标准差={result_std:.1f}")
        
        self._update_display()
    
    def _adjust_brightness(self, image: np.ndarray, brightness: int) -> np.ndarray:
        """调整亮度"""
        return image + brightness
    
    def _adjust_contrast(self, image: np.ndarray, contrast: int) -> np.ndarray:
        """调整对比度 - 改进版，效果明显且不会变灰"""
        print(f"[DEBUG] 对比度调整: {contrast}")
        
        if contrast == 0:
            return image
        
        # 改进的对比度调整算法 - 避免变灰问题
        # 使用标准的对比度公式：output = (input - 128) * factor + 128
        
        if contrast > 0:
            # 增加对比度
            # 范围: 0-100 映射到 1.0-3.0 的因子
            factor = 1.0 + (contrast / 50.0)  # 更平缓的增长
            
            # 使用标准的对比度调整公式
            result = image.astype(np.float32)
            result = (result - 128) * factor + 128
            result = np.clip(result, 0, 255).astype(np.uint8)
            
            print(f"[DEBUG] 增加对比度, factor={factor:.2f}")
        else:
            # 降低对比度
            # 范围: -100-0 映射到 0.3-1.0 的因子
            factor = max(0.3, 1.0 + (contrast / 100.0))  # 更平缓的衰减
            
            # 使用标准的对比度调整公式
            result = image.astype(np.float32)
            result = (result - 128) * factor + 128
            result = np.clip(result, 0, 255).astype(np.uint8)
            
            print(f"[DEBUG] 降低对比度, factor={factor:.2f}")
        
        return result
    
    def _apply_s_curve_contrast(self, image: np.ndarray, factor: float) -> np.ndarray:
        """应用S曲线对比度增强"""
        # 归一化到0-1范围
        normalized = image.astype(np.float32) / 255.0
        
        # 应用S曲线变换
        # 使用sigmoid函数的变体
        midpoint = 0.5
        steepness = factor * 4  # 控制S曲线的陡峭程度
        
        # S曲线公式: 1 / (1 + exp(-steepness * (x - midpoint)))
        s_curve = 1.0 / (1.0 + np.exp(-steepness * (normalized - midpoint)))
        
        # 重新映射到0-255范围
        result = s_curve * 255.0
        
        return np.clip(result, 0, 255)
    
    def _adjust_gamma(self, image: np.ndarray, gamma: float) -> np.ndarray:
        """伽马校正"""
        # 构建查找表
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        
        # 应用伽马校正
        return cv2.LUT(image.astype(np.uint8), table).astype(np.float32)
    
    def _adjust_colors(self, image: np.ndarray) -> np.ndarray:
        """调整色彩（饱和度、色调、色温、自然饱和度）"""
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # 色调调整
        if self.params['hue'] != 0:
            hsv[:, :, 0] = (hsv[:, :, 0] + self.params['hue']) % 180
        
        # 饱和度调整
        if self.params['saturation'] != 0:
            saturation_factor = 1 + self.params['saturation'] / 100.0
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_factor, 0, 255)
        
        # 自然饱和度调整（对低饱和度区域影响更大）
        if self.params['vibrance'] != 0:
            vibrance_factor = self.params['vibrance'] / 100.0
            # 计算当前饱和度的权重
            sat_weight = 1 - (hsv[:, :, 1] / 255.0)
            vibrance_adjustment = vibrance_factor * sat_weight * 255
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] + vibrance_adjustment, 0, 255)
        
        # 转换回BGR
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
        
        # 色温调整
        if self.params['warmth'] != 0:
            result = self._adjust_temperature(result, self.params['warmth'])
        
        return result
    
    def _adjust_temperature(self, image: np.ndarray, warmth: int) -> np.ndarray:
        """调整色温"""
        # 色温调整通过调整蓝色和红色通道实现
        temp_factor = warmth / 100.0
        
        if temp_factor > 0:  # 暖色调
            image[:, :, 2] = np.clip(image[:, :, 2] * (1 + temp_factor * 0.3), 0, 255)  # 增加红色
            image[:, :, 0] = np.clip(image[:, :, 0] * (1 - temp_factor * 0.2), 0, 255)  # 减少蓝色
        else:  # 冷色调
            image[:, :, 0] = np.clip(image[:, :, 0] * (1 - temp_factor * 0.3), 0, 255)  # 增加蓝色
            image[:, :, 2] = np.clip(image[:, :, 2] * (1 + temp_factor * 0.2), 0, 255)  # 减少红色
        
        return image
    
    def _adjust_highlights_shadows(self, image: np.ndarray) -> np.ndarray:
        """调整高光和阴影"""
        # 转换到LAB色彩空间进行亮度调整
        lab = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
        l_channel = lab[:, :, 0]
        
        # 创建高光和阴影mask
        highlights_mask = (l_channel > 128).astype(np.float32)
        shadows_mask = (l_channel <= 128).astype(np.float32)
        
        # 应用调整
        if self.params['highlights'] != 0:
            highlight_adjustment = self.params['highlights'] * highlights_mask
            l_channel += highlight_adjustment
        
        if self.params['shadows'] != 0:
            shadow_adjustment = self.params['shadows'] * shadows_mask
            l_channel += shadow_adjustment
        
        # 限制范围
        lab[:, :, 0] = np.clip(l_channel, 0, 255)
        
        # 转换回BGR
        return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    
    def _adjust_sharpness_clarity(self, image: np.ndarray) -> np.ndarray:
        """调整锐化和清晰度"""
        result = image.copy()
        
        # 锐化
        if self.params['sharpness'] != 0:
            result = self._apply_sharpening(result, self.params['sharpness'])
        
        # 清晰度（局部对比度增强）
        if self.params['clarity'] != 0:
            result = self._apply_clarity(result, self.params['clarity'])
        
        return result
    
    def _apply_sharpening(self, image: np.ndarray, strength: int) -> np.ndarray:
        """应用锐化"""
        # 创建锐化核
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        
        # 应用锐化
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # 按强度混合
        alpha = strength / 100.0
        return cv2.addWeighted(image, 1 - alpha, sharpened, alpha, 0)
    
    def _apply_clarity(self, image: np.ndarray, clarity: int) -> np.ndarray:
        """应用清晰度（局部对比度增强）"""
        # 转换到LAB色彩空间
        lab = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
        l_channel = lab[:, :, 0]
        
        # 创建高斯模糊版本
        blurred = cv2.GaussianBlur(l_channel, (0, 0), 2.0)
        
        # 计算局部对比度
        local_contrast = l_channel - blurred
        
        # 应用清晰度调整
        clarity_factor = clarity / 100.0
        enhanced_l = l_channel + local_contrast * clarity_factor
        
        # 限制范围
        lab[:, :, 0] = np.clip(enhanced_l, 0, 255)
        
        # 转换回BGR
        return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    
    def _update_display(self):
        """更新显示"""
        if self.update_callback and self.current_image is not None:
            self.update_callback(self.current_image)
    
    def get_current_image(self) -> Optional[np.ndarray]:
        """获取当前处理后的图像"""
        return self.current_image
    
    def get_parameters(self) -> Dict:
        """获取当前参数"""
        return self.params.copy()
    
    def set_parameters(self, params: Dict):
        """设置参数"""
        for key, value in params.items():
            if key in self.params:
                self.adjust_parameter(key, value)
    
    def get_presets(self) -> Dict:
        """获取所有预设"""
        return self.presets.copy()
    
    def save_preset(self, name: str):
        """保存当前参数为预设"""
        self.presets[name] = self.params.copy()
    
    def delete_preset(self, name: str):
        """删除预设"""
        if name in self.presets and name != '原始':
            del self.presets[name]
    
    def export_parameters(self, filepath: str):
        """导出参数到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'parameters': self.params,
                'presets': self.presets
            }, f, indent=2, ensure_ascii=False)
    
    def import_parameters(self, filepath: str):
        """从文件导入参数"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'parameters' in data:
                    self.set_parameters(data['parameters'])
                if 'presets' in data:
                    self.presets.update(data['presets'])
    
    def get_parameter_ranges(self) -> Dict:
        """获取参数范围"""
        return self.param_ranges.copy()
    
    def compare_with_original(self) -> Tuple[np.ndarray, Dict]:
        """与原图对比"""
        if self.original_image is None or self.current_image is None:
            return None, {}
        
        # 创建对比图像（左原图，右处理后）
        h, w = self.original_image.shape[:2]
        comparison = np.zeros((h, w * 2, 3), dtype=np.uint8)
        comparison[:, :w] = self.original_image
        comparison[:, w:] = self.current_image
        
        # 添加分割线
        cv2.line(comparison, (w, 0), (w, h), (255, 255, 255), 2)
        
        # 计算差异统计
        diff_stats = {
            'mean_difference': np.mean(np.abs(self.current_image.astype(np.float32) - 
                                            self.original_image.astype(np.float32))),
            'max_difference': np.max(np.abs(self.current_image.astype(np.float32) - 
                                          self.original_image.astype(np.float32))),
            'parameters_changed': sum(1 for p in self.params.values() if p != 0 and p != 1.0)
        }
        
        return comparison, diff_stats