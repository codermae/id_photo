"""
图像处理控制器 - 升级版
集成智能裁剪、精确背景替换、实时参数调整等高级功能
"""
import cv2
import numpy as np
from utils.image_helper import ImageHelper
from utils.file_helper import FileHelper
from config.config import PHOTO_SPECS, BACKGROUND_COLORS, QUALITY_SCORE_THRESHOLD
from .smart_cropper import SmartCropper
from .background_replacer import PreciseBackgroundReplacer
from .realtime_adjuster import RealTimeAdjuster
from typing import List, Dict, Tuple, Optional, Union

class ImageProcessor:
    """图像处理控制器 - 升级版"""

    def __init__(self, ai_processor=None, update_callback=None):
        self.current_image = None
        self.original_image = None
        self.quality_score = 0
        self.ai_processor = ai_processor  # AI 处理器
        self.beautify_strength = 1.0  # 美颜强度 (0.0-2.0)
        
        # 新增的高级处理器
        self.smart_cropper = SmartCropper()
        self.bg_replacer = PreciseBackgroundReplacer()
        self.realtime_adjuster = RealTimeAdjuster(update_callback)
        
        # 处理历史记录
        self.processing_history = []
        self.current_step = -1

    def load_image(self, filepath):
        """加载图像"""
        self.original_image = ImageHelper.load_image(filepath)
        self.current_image = self.original_image.copy()
        self.quality_score = ImageHelper.get_image_quality_score(self.current_image)
        
        # 设置到实时调整器
        self.realtime_adjuster.set_image(self.current_image)
        
        # 重置处理历史
        self.processing_history = [self.current_image.copy()]
        self.current_step = 0
        
        return self.current_image

    def get_current_image(self):
        """获取当前图像"""
        return self.current_image

    def reset_image(self):
        """重置为原始图像"""
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
            self.quality_score = ImageHelper.get_image_quality_score(self.current_image)

    def crop_to_spec(self, spec='一寸'):
        """按规格裁切 - 升级为智能裁剪"""
        if self.current_image is None:
            return False, {}

        try:
            # 使用智能裁剪
            cropped_image, crop_info = self.smart_cropper.smart_crop(
                self.current_image, spec, self.ai_processor
            )
            
            self.current_image = cropped_image
            self._add_to_history(f"智能裁剪到{spec}")
            
            return True, crop_info
        except Exception as e:
            print(f"智能裁切失败: {e}")
            return False, {'error': str(e)}
    
    def preview_crop(self, spec='一寸'):
        """预览裁剪效果"""
        if self.current_image is None:
            return None, {}
        
        try:
            preview_image, crop_info = self.smart_cropper.preview_crop_area(
                self.current_image, spec, self.ai_processor
            )
            return preview_image, crop_info
        except Exception as e:
            print(f"预览裁剪失败: {e}")
            return None, {'error': str(e)}
    
    def manual_crop(self, crop_area: Tuple[int, int, int, int], spec='一寸'):
        """手动裁剪"""
        if self.current_image is None:
            return False
        
        try:
            cropped_image = self.smart_cropper.manual_crop(
                self.current_image, crop_area, spec
            )
            self.current_image = cropped_image
            self._add_to_history(f"手动裁剪到{spec}")
            return True
        except Exception as e:
            print(f"手动裁剪失败: {e}")
            return False

    def change_background(self, color_name='白色', method='auto', refine_edges=True):
        """更换背景色 - 升级为精确背景替换"""
        if self.current_image is None:
            return False, {}

        try:
            # 使用精确背景替换
            result_image, process_info = self.bg_replacer.replace_background(
                self.current_image, color_name, method, refine_edges
            )
            
            self.current_image = result_image
            self._add_to_history(f"背景替换为{color_name}")
            
            return True, process_info
        except Exception as e:
            print(f"背景替换失败: {e}")
            return False, {'error': str(e)}
    
    def preview_segmentation(self, method='auto'):
        """预览分割效果"""
        if self.current_image is None:
            return None
        
        try:
            return self.bg_replacer.preview_segmentation(self.current_image, method)
        except Exception as e:
            print(f"预览分割失败: {e}")
            return None

    def beautify(self):
        """美颜处理"""
        if self.current_image is None:
            return False

        try:
            self.current_image = ImageHelper.beautify_face(
                self.current_image,
                ai_processor=self.ai_processor,
                strength=self.beautify_strength
            )
            return True
        except Exception as e:
            print(f"美颜失败: {e}")
            return False
    
    def apply_selective_beautify(self, options: dict, strengths: dict):
        """应用选择性美颜处理"""
        if self.current_image is None:
            return False
        
        try:
            from controllers.advanced_beautify import AdvancedBeautify
            
            # 创建美颜处理器
            beautify_processor = AdvancedBeautify(self.ai_processor)
            
            # 应用美颜
            result, info = beautify_processor.selective_beautify(
                self.current_image, options, strengths
            )
            
            if result is not None:
                self.current_image = result
                print(f"[DEBUG] 选择性美颜完成 - 应用的操作: {info['operations_applied']}")
                return True
            else:
                print("[DEBUG] 选择性美颜失败")
                return False
                
        except Exception as e:
            print(f"选择性美颜处理失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def set_beautify_strength(self, strength):
        """设置美颜强度 (0.0-2.0)"""
        self.beautify_strength = max(0.0, min(2.0, strength))

    def adjust_brightness(self, value):
        """调整亮度 (-100 ~ 100) - 升级为实时调整"""
        if self.current_image is None:
            return False

        try:
            self.realtime_adjuster.adjust_brightness(value)
            self.current_image = self.realtime_adjuster.get_current_image()
            return True
        except Exception as e:
            print(f"调整亮度失败: {e}")
            return False

    def adjust_contrast(self, value):
        """调整对比度 (-100 ~ 100) - 升级为实时调整"""
        if self.current_image is None:
            return False

        try:
            self.realtime_adjuster.adjust_contrast(value)
            self.current_image = self.realtime_adjuster.get_current_image()
            return True
        except Exception as e:
            print(f"调整对比度失败: {e}")
            return False
    
    def adjust_saturation(self, value):
        """调整饱和度 (-100 ~ 100)"""
        if self.current_image is None:
            return False

        try:
            self.realtime_adjuster.adjust_saturation(value)
            self.current_image = self.realtime_adjuster.get_current_image()
            return True
        except Exception as e:
            print(f"调整饱和度失败: {e}")
            return False
    
    def adjust_sharpness(self, value):
        """调整锐化 (0 ~ 100)"""
        if self.current_image is None:
            return False

        try:
            self.realtime_adjuster.adjust_sharpness(value)
            self.current_image = self.realtime_adjuster.get_current_image()
            return True
        except Exception as e:
            print(f"调整锐化失败: {e}")
            return False
    
    def adjust_gamma(self, value):
        """调整伽马值 (0.1 ~ 3.0)"""
        if self.current_image is None:
            return False

        try:
            self.realtime_adjuster.adjust_gamma(value)
            self.current_image = self.realtime_adjuster.get_current_image()
            return True
        except Exception as e:
            print(f"调整伽马失败: {e}")
            return False
    
    def apply_preset(self, preset_name):
        """应用参数预设"""
        if self.current_image is None:
            return False

        try:
            self.realtime_adjuster.apply_preset(preset_name)
            self.current_image = self.realtime_adjuster.get_current_image()
            self._add_to_history(f"应用预设: {preset_name}")
            return True
        except Exception as e:
            print(f"应用预设失败: {e}")
            return False
    
    def reset_adjustments(self):
        """重置所有调整"""
        if self.original_image is None:
            return False
        
        try:
            self.realtime_adjuster.reset_parameters()
            self.current_image = self.realtime_adjuster.get_current_image()
            self._add_to_history("重置参数")
            return True
        except Exception as e:
            print(f"重置失败: {e}")
            return False
    
    def get_current_parameters(self):
        """获取当前参数"""
        return self.realtime_adjuster.get_parameters()
    
    def get_available_presets(self):
        """获取可用预设"""
        return self.realtime_adjuster.get_presets()
    
    def save_custom_preset(self, name):
        """保存自定义预设"""
        self.realtime_adjuster.save_preset(name)
    
    def compare_with_original(self):
        """与原图对比"""
        return self.realtime_adjuster.compare_with_original()

    def _add_to_history(self, operation_name):
        """添加到处理历史"""
        # 如果当前不在最新步骤，删除后续历史
        if self.current_step < len(self.processing_history) - 1:
            self.processing_history = self.processing_history[:self.current_step + 1]
        
        # 添加新的历史记录
        self.processing_history.append({
            'image': self.current_image.copy(),
            'operation': operation_name,
            'parameters': self.get_current_parameters()
        })
        
        self.current_step += 1
        
        # 限制历史记录数量
        max_history = 20
        if len(self.processing_history) > max_history:
            self.processing_history.pop(0)
            self.current_step -= 1
    
    def undo(self):
        """撤销操作"""
        if self.current_step > 0:
            self.current_step -= 1
            if isinstance(self.processing_history[self.current_step], dict):
                self.current_image = self.processing_history[self.current_step]['image'].copy()
            else:
                self.current_image = self.processing_history[self.current_step].copy()
            
            # 更新实时调整器
            self.realtime_adjuster.set_image(self.current_image)
            return True
        return False
    
    def redo(self):
        """重做操作"""
        if self.current_step < len(self.processing_history) - 1:
            self.current_step += 1
            if isinstance(self.processing_history[self.current_step], dict):
                self.current_image = self.processing_history[self.current_step]['image'].copy()
                # 恢复参数
                if 'parameters' in self.processing_history[self.current_step]:
                    self.realtime_adjuster.set_parameters(
                        self.processing_history[self.current_step]['parameters']
                    )
            else:
                self.current_image = self.processing_history[self.current_step].copy()
            
            # 更新实时调整器
            self.realtime_adjuster.set_image(self.current_image)
            return True
        return False
    
    def get_history_info(self):
        """获取历史信息"""
        history_info = []
        for i, item in enumerate(self.processing_history):
            if isinstance(item, dict):
                history_info.append({
                    'step': i,
                    'operation': item.get('operation', f'步骤 {i}'),
                    'is_current': i == self.current_step
                })
            else:
                history_info.append({
                    'step': i,
                    'operation': f'步骤 {i}',
                    'is_current': i == self.current_step
                })
        return history_info
        """旋转图像"""
        if self.current_image is None:
            return False

        try:
            self.current_image = ImageHelper.rotate_image(self.current_image, angle)
            return True
        except Exception as e:
            print(f"旋转失败: {e}")
            return False

    def resize(self, width, height):
        """调整大小"""
        if self.current_image is None:
            return False

        try:
            self.current_image = ImageHelper.resize_image(self.current_image, width, height)
            return True
        except Exception as e:
            print(f"调整大小失败: {e}")
            return False

    def get_quality_score(self):
        """获取质量评分"""
        if self.current_image is None:
            return 0
        
        self.quality_score = ImageHelper.get_image_quality_score(self.current_image)
        return self.quality_score

    def is_quality_acceptable(self):
        """检查质量是否可接受"""
        return self.get_quality_score() >= QUALITY_SCORE_THRESHOLD

    def save_processed_image(self, id_number, spec='一寸', bg_color='白色'):
        """保存处理后的图像"""
        if self.current_image is None:
            return None

        try:
            filepath = FileHelper.save_processed_photo(id_number, self.current_image, spec, bg_color)
            return filepath
        except Exception as e:
            print(f"保存图像失败: {e}")
            return None

    def advanced_beautify(self, strength=1.0):
        """高级美颜处理"""
        if self.current_image is None:
            return False

        try:
            # 使用新的专业级美颜算法
            self.current_image = ImageHelper.beautify_face(
                self.current_image,
                ai_processor=self.ai_processor,
                strength=strength
            )
            print(f"高级美颜完成，强度: {strength}")
            return True
        except Exception as e:
            print(f"高级美颜失败: {e}")
            return False

    def professional_background_change(self, color_name='白色'):
        """专业背景替换"""
        if self.current_image is None:
            return False

        try:
            # 使用新的专业级背景替换算法
            self.current_image = ImageHelper.change_background(
                self.current_image, 
                color_name,
                ai_processor=self.ai_processor
            )
            print(f"专业背景替换完成: {color_name}")
            return True
        except Exception as e:
            print(f"专业背景替换失败: {e}")
            return False

    def skin_tone_adjustment(self, adjustment=0.0):
        """肤色调整 (-1.0 到 1.0)"""
        if self.current_image is None:
            return False

        try:
            # 转换到 LAB 色彩空间
            lab = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # 调整 a 通道（绿-红）
            a = cv2.add(a, int(adjustment * 20))
            
            # 重新合成
            self.current_image = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
            return True
        except Exception as e:
            print(f"肤色调整失败: {e}")
            return False

    def remove_blemishes(self):
        """去除瑕疵"""
        if self.current_image is None:
            return False

        try:
            # 使用 inpainting 技术去除小瑕疵
            gray = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2GRAY)
            
            # 检测小的暗点（可能是瑕疵）
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 形态学操作找到小的暗点
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask = cv2.morphologyEx(255 - thresh, cv2.MORPH_OPEN, kernel)
            
            # 只保留小的区域
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            small_blemish_mask = np.zeros_like(mask)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 5 < area < 100:  # 小瑕疵的面积范围
                    cv2.fillPoly(small_blemish_mask, [contour], 255)
            
            # 使用 inpainting 修复
            if np.sum(small_blemish_mask) > 0:
                self.current_image = cv2.inpaint(self.current_image, small_blemish_mask, 3, cv2.INPAINT_TELEA)
                print("瑕疵去除完成")
            
            return True
        except Exception as e:
            print(f"瑕疵去除失败: {e}")
            return False

    def batch_process_advanced(self, image_list, spec='一寸', bg_color='白色', 
                             beautify=True, enhance_quality=True, auto_wb=True):
        """高级批量处理图像"""
        results = []
        
        for image_path in image_list:
            try:
                self.load_image(image_path)
                
                # 自动白平衡
                if auto_wb:
                    self.auto_white_balance()
                
                # 图像质量增强
                if enhance_quality:
                    self.enhance_quality()
                
                # 美颜处理
                if beautify:
                    self.beautify()
                
                # 智能裁切
                self.smart_crop_to_spec(spec)
                
                # 背景替换
                self.change_background(bg_color)
                
                # 提取身份证号（从文件名）
                id_number = image_path.split('/')[-1].split('_')[0]
                
                output_path = self.save_processed_image(id_number, spec, bg_color)
                
                results.append({
                    'input': image_path,
                    'output': output_path,
                    'quality_score': self.quality_score,
                    'status': 'success'
                })
            except Exception as e:
                results.append({
                    'input': image_path,
                    'output': None,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results

    def get_available_specs(self):
        """获取可用的规格"""
        return list(PHOTO_SPECS.keys())

    def get_available_colors(self):
        """获取可用的背景色"""
        return list(BACKGROUND_COLORS.keys())
    def rotate(self, angle):
        """旋转图像"""
        if self.current_image is None:
            return False

        try:
            self.current_image = ImageHelper.rotate_image(self.current_image, angle)
            self._add_to_history(f"旋转 {angle}°")
            return True
        except Exception as e:
            print(f"旋转失败: {e}")
            return False

    def resize(self, width, height):
        """调整大小"""
        if self.current_image is None:
            return False

        try:
            self.current_image = ImageHelper.resize_image(self.current_image, width, height)
            self._add_to_history(f"调整大小到 {width}x{height}")
            return True
        except Exception as e:
            print(f"调整大小失败: {e}")
            return False

    def get_available_specs(self):
        """获取可用的证件照规格"""
        return self.smart_cropper.get_available_specs()

    def get_available_colors(self):
        """获取可用的背景颜色"""
        return self.bg_replacer.get_available_colors()
    
    def get_parameter_ranges(self):
        """获取参数调整范围"""
        return self.realtime_adjuster.get_parameter_ranges()
    def auto_enhance(self):
        """自动图像增强"""
        if self.current_image is None:
            return False
        
        try:
            # 自动亮度对比度调整
            lab = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # 自适应直方图均衡化
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # 重新合成
            enhanced = cv2.merge([l, a, b])
            self.current_image = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            self._add_to_history("自动增强")
            return True
        except Exception as e:
            print(f"自动增强失败: {e}")
            return False
    
    def batch_process(self, image_paths: List[str], output_dir: str, 
                     params: Dict) -> List[Dict]:
        """
        批量处理图像（简化版本，用于兼容）
        
        Args:
            image_paths: 图像路径列表
            output_dir: 输出目录
            params: 处理参数
            
        Returns:
            List[Dict]: 处理结果列表
        """
        results = []
        
        for i, image_path in enumerate(image_paths):
            try:
                # 加载图像
                if not self.load_image(image_path):
                    raise Exception("无法加载图像")
                
                # 应用处理参数
                if params.get('preset'):
                    self.apply_preset(params['preset'])
                
                if params.get('crop_spec'):
                    self.crop_to_spec(params['crop_spec'])
                
                if params.get('background_color'):
                    self.change_background(params['background_color'])
                
                if params.get('beautify_enabled'):
                    self.beautify()
                
                # 保存结果
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                output_path = os.path.join(output_dir, f"{base_name}_processed.jpg")
                
                cv2.imwrite(output_path, self.current_image)
                
                results.append({
                    'input': image_path,
                    'output': output_path,
                    'status': 'success',
                    'quality_score': self.get_quality_score()
                })
                
            except Exception as e:
                results.append({
                    'input': image_path,
                    'output': None,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results