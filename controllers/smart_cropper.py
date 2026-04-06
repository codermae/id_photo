"""
智能裁剪系统
实现基于人脸检测的智能裁剪，确保人物居中且符合证件照标准
"""
import cv2
import numpy as np
from typing import Tuple, Dict, Optional
import math

class SmartCropper:
    """智能裁剪器"""
    
    def __init__(self):
        """初始化裁剪器"""
        # 证件照规格定义 (像素尺寸, DPI=600 保证高质量)
        # 注：打印时可以缩小到 300 DPI，但处理时保持高分辨率避免模糊
        self.crop_specs = {
            # 中国标准
            '一寸': {
                'width': 590, 'height': 826, 'dpi': 600,
                'mm_width': 25, 'mm_height': 35,
                'description': '25mm×35mm 一寸照片（身份证、学生证等）'
            },
            '小二寸': {
                'width': 826, 'height': 1158, 'dpi': 600,
                'mm_width': 35, 'mm_height': 49,
                'description': '35mm×49mm 小二寸照片（护照、港澳通行证）'
            },
            '二寸': {
                'width': 826, 'height': 1252, 'dpi': 600,
                'mm_width': 35, 'mm_height': 53,
                'description': '35mm×53mm 二寸照片（签证、毕业证等）'
            },
            '大一寸': {
                'width': 780, 'height': 1134, 'dpi': 600,
                'mm_width': 33, 'mm_height': 48,
                'description': '33mm×48mm 大一寸照片（港澳通行证等）'
            },
            
            # 国际标准
            '美国护照': {
                'width': 1200, 'height': 1200, 'dpi': 600,
                'mm_width': 51, 'mm_height': 51,
                'description': '51mm×51mm 美国护照标准（正方形）'
            },
            '欧盟护照': {
                'width': 826, 'height': 1063, 'dpi': 600,
                'mm_width': 35, 'mm_height': 45,
                'description': '35mm×45mm 欧盟护照标准'
            },
            '英国签证': {
                'width': 826, 'height': 1063, 'dpi': 600,
                'mm_width': 35, 'mm_height': 45,
                'description': '35mm×45mm 英国签证标准'
            },
            '日本护照': {
                'width': 826, 'height': 1063, 'dpi': 600,
                'mm_width': 35, 'mm_height': 45,
                'description': '35mm×45mm 日本护照标准'
            },
            '印度签证': {
                'width': 1200, 'height': 1200, 'dpi': 600,
                'mm_width': 51, 'mm_height': 51,
                'description': '51mm×51mm 印度签证标准（正方形）'
            },
            '泰国签证': {
                'width': 944, 'height': 1181, 'dpi': 600,
                'mm_width': 40, 'mm_height': 50,
                'description': '40mm×50mm 泰国签证标准'
            },
            
            # 特殊规格
            '驾驶证': {
                'width': 472, 'height': 630, 'dpi': 600,
                'mm_width': 20, 'mm_height': 26.7,
                'description': '20mm×26.7mm 中国驾驶证'
            },
            '社保卡': {
                'width': 590, 'height': 826, 'dpi': 600,
                'mm_width': 25, 'mm_height': 35,
                'description': '25mm×35mm 中国社保卡'
            },
            
            # 大尺寸
            '五寸': {
                'width': 2100, 'height': 3000, 'dpi': 600,
                'mm_width': 89, 'mm_height': 127,
                'description': '89mm×127mm 五寸照片'
            },
            '六寸': {
                'width': 2400, 'height': 3600, 'dpi': 600,
                'mm_width': 102, 'mm_height': 152,
                'description': '102mm×152mm 六寸照片'
            }
        }
        
        # 人脸位置标准（符合证件照要求）
        self.face_position_ratios = {
            'face_center_y': 0.35,  # 人脸中心在照片35%高度处
            'face_width_ratio': 0.6,  # 人脸宽度占照片宽度的60%
            'top_margin_ratio': 0.12,  # 头顶留白12%
            'bottom_margin_ratio': 0.08  # 下巴留白8%
        }
    
    def smart_crop(self, image: np.ndarray, spec: str = '一寸', 
                   face_detector=None) -> Tuple[np.ndarray, Dict]:
        """
        智能裁剪，保持人物居中且符合证件照标准
        
        Args:
            image: 输入图像
            spec: 证件照规格
            face_detector: 人脸检测器实例
            
        Returns:
            tuple: (裁剪后的图像, 裁剪信息)
        """
        print(f"[DEBUG] 开始智能裁剪 - 规格: {spec}")
        
        if spec not in self.crop_specs:
            raise ValueError(f"不支持的规格: {spec}")
        
        spec_info = self.crop_specs[spec]
        h, w = image.shape[:2]
        
        print(f"[DEBUG] 原始图像尺寸: {w}x{h}")
        print(f"[DEBUG] 目标规格: {spec_info['width']}x{spec_info['height']} ({spec_info['mm_width']}x{spec_info['mm_height']}mm)")
        
        # 检测人脸
        face_info = None
        if face_detector:
            face_info = self._detect_face_info(image, face_detector)
        
        if face_info:
            print(f"[DEBUG] 检测到人脸: 位置({face_info['bbox'][0]}, {face_info['bbox'][1]}), 大小({face_info['width']}x{face_info['height']})")
            print(f"[DEBUG] 人脸中心: {face_info['center']}")
            # 基于人脸的智能裁剪
            crop_area = self._calculate_face_based_crop(
                image.shape, face_info, spec_info
            )
            method = 'face_based'
        else:
            print("[DEBUG] 未检测到人脸，使用中心裁剪")
            # 中心裁剪作为备选
            crop_area = self._calculate_center_crop(
                image.shape, spec_info
            )
            method = 'center_based'
        
        print(f"[DEBUG] 裁剪区域: ({crop_area[0]}, {crop_area[1]}, {crop_area[2]}, {crop_area[3]})")
        
        # 执行裁剪
        cropped_image = self._crop_image(image, crop_area)
        print(f"[DEBUG] 裁剪后尺寸: {cropped_image.shape[1]}x{cropped_image.shape[0]}")
        
        # 调整到目标尺寸
        final_image = self._resize_to_spec(cropped_image, spec_info)
        print(f"[DEBUG] 最终尺寸: {final_image.shape[1]}x{final_image.shape[0]}")
        
        # 返回裁剪信息
        crop_info = {
            'method': method,
            'spec': spec,
            'original_size': (w, h),
            'crop_area': crop_area,
            'final_size': (spec_info['width'], spec_info['height']),
            'face_detected': face_info is not None,
            'face_info': face_info
        }
        
        print(f"[DEBUG] 智能裁剪完成 - 方法: {method}")
        
        return final_image, crop_info
    
    def _detect_face_info(self, image: np.ndarray, face_detector) -> Optional[Dict]:
        """检测人脸信息"""
        try:
            face = face_detector.detect_face(image)
            # 修复数组比较问题
            if face is None or (hasattr(face, '__len__') and len(face) == 0):
                return None
            
            x, y, fw, fh = face
            
            # 计算人脸关键信息
            face_center = (x + fw // 2, y + fh // 2)
            face_top = y
            face_bottom = y + fh
            face_left = x
            face_right = x + fw
            
            return {
                'bbox': (x, y, fw, fh),
                'center': face_center,
                'top': face_top,
                'bottom': face_bottom,
                'left': face_left,
                'right': face_right,
                'width': fw,
                'height': fh
            }
        except Exception as e:
            print(f"人脸检测失败: {e}")
            return None
    
    def _calculate_face_based_crop(self, image_shape: Tuple, 
                                  face_info: Dict, spec_info: Dict) -> Tuple:
        """
        基于人脸位置计算裁剪区域 - 改进版，保留头发和头顶空间
        
        参考专业证件照标准：
        - 头顶到照片顶部：留出足够空间（约头部高度的30-50%）
        - 人脸宽度：占照片宽度的50-60%（不是60%，给两侧留空间）
        - 下巴到照片底部：留出适当空间
        """
        h, w = image_shape[:2]
        target_ratio = spec_info['width'] / spec_info['height']
        
        face_center = face_info['center']
        face_width = face_info['width']
        face_height = face_info['height']
        face_top = face_info['top']
        face_bottom = face_info['bottom']
        
        # 改进1: 估算完整头部高度（包括头发）
        # 人脸检测通常只检测到眉毛到下巴，头发在上面
        # 假设头发高度约为人脸高度的40%
        estimated_hair_height = int(face_height * 0.4)
        full_head_top = max(0, face_top - estimated_hair_height)
        full_head_height = face_bottom - full_head_top
        
        print(f"[DEBUG] 人脸高度: {face_height}px, 估算头发高度: {estimated_hair_height}px")
        print(f"[DEBUG] 完整头部高度: {full_head_height}px (从 {full_head_top} 到 {face_bottom})")
        
        # 改进2: 根据证件照标准计算照片高度
        # 头顶留白：头部高度的30-40%
        # 下巴留白：头部高度的20-30%
        top_margin = int(full_head_height * 0.35)  # 头顶留白35%
        bottom_margin = int(full_head_height * 0.25)  # 下巴留白25%
        
        estimated_photo_height = full_head_height + top_margin + bottom_margin
        estimated_photo_width = int(estimated_photo_height * target_ratio)
        
        print(f"[DEBUG] 估算照片尺寸: {estimated_photo_width}x{estimated_photo_height}")
        print(f"[DEBUG] 头顶留白: {top_margin}px, 下巴留白: {bottom_margin}px")
        
        # 改进3: 确保不超出图像边界
        crop_width = min(estimated_photo_width, w)
        crop_height = min(estimated_photo_height, h)
        
        # 如果估算尺寸太大，按比例缩小
        if crop_width > w or crop_height > h:
            scale = min(w / crop_width, h / crop_height) * 0.95  # 留5%余量
            crop_width = int(crop_width * scale)
            crop_height = int(crop_height * scale)
            print(f"[DEBUG] 缩放比例: {scale:.2f}, 调整后尺寸: {crop_width}x{crop_height}")
        
        # 改进4: 计算裁剪位置
        # 让完整头部（包括头发）的顶部距离照片顶部有 top_margin 的距离
        crop_y = max(0, full_head_top - top_margin)
        
        # 水平居中
        crop_x = max(0, min(w - crop_width, face_center[0] - crop_width // 2))
        
        # 确保不超出边界
        if crop_y + crop_height > h:
            crop_y = max(0, h - crop_height)
        if crop_x + crop_width > w:
            crop_x = max(0, w - crop_width)
        
        print(f"[DEBUG] 最终裁剪位置: ({crop_x}, {crop_y})")
        print(f"[DEBUG] 最终裁剪尺寸: {crop_width}x{crop_height}")
        
        return (crop_x, crop_y, crop_width, crop_height)
    
    def _calculate_center_crop(self, image_shape: Tuple, spec_info: Dict) -> Tuple:
        """计算中心裁剪区域"""
        h, w = image_shape[:2]
        target_ratio = spec_info['width'] / spec_info['height']
        
        if w / h > target_ratio:
            # 图片太宽，以高度为准
            crop_height = h
            crop_width = int(h * target_ratio)
            crop_x = (w - crop_width) // 2
            crop_y = 0
        else:
            # 图片太高，以宽度为准
            crop_width = w
            crop_height = int(w / target_ratio)
            crop_x = 0
            crop_y = (h - crop_height) // 2
        
        return (crop_x, crop_y, crop_width, crop_height)
    
    def _crop_image(self, image: np.ndarray, crop_area: Tuple) -> np.ndarray:
        """执行图像裁剪"""
        x, y, w, h = crop_area
        return image[y:y+h, x:x+w]
    
    def _resize_to_spec(self, image: np.ndarray, spec_info: Dict) -> np.ndarray:
        """调整图像到规格尺寸 - 智能缩放，避免不必要的质量损失"""
        target_width = spec_info['width']
        target_height = spec_info['height']
        current_h, current_w = image.shape[:2]
        
        # 如果当前尺寸已经是目标尺寸，直接返回
        if current_w == target_width and current_h == target_height:
            print(f"[DEBUG] 尺寸已匹配，跳过 resize")
            return image
        
        # 计算缩放比例
        scale_w = target_width / current_w
        scale_h = target_height / current_h
        
        # 如果需要放大，使用 INTER_CUBIC（更平滑）
        # 如果需要缩小，使用 INTER_AREA（更清晰，避免模糊）
        if scale_w > 1.0 or scale_h > 1.0:
            interpolation = cv2.INTER_CUBIC
            print(f"[DEBUG] 放大图像: {current_w}x{current_h} -> {target_width}x{target_height}")
        else:
            interpolation = cv2.INTER_AREA
            print(f"[DEBUG] 缩小图像: {current_w}x{current_h} -> {target_width}x{target_height}")
        
        resized = cv2.resize(
            image, 
            (target_width, target_height), 
            interpolation=interpolation
        )
        
        return resized
    
    def get_available_specs(self) -> Dict:
        """获取所有可用的证件照规格"""
        return self.crop_specs.copy()
    
    def preview_crop_area(self, image: np.ndarray, spec: str = '一寸', 
                         face_detector=None) -> Tuple[np.ndarray, Dict]:
        """预览裁剪区域（在原图上绘制裁剪框）"""
        if spec not in self.crop_specs:
            raise ValueError(f"不支持的规格: {spec}")
        
        spec_info = self.crop_specs[spec]
        preview_image = image.copy()
        
        # 检测人脸
        face_info = None
        if face_detector:
            face_info = self._detect_face_info(image, face_detector)
        
        if face_info:
            crop_area = self._calculate_face_based_crop(
                image.shape, face_info, spec_info
            )
            # 绘制人脸框
            face_bbox = face_info['bbox']
            cv2.rectangle(preview_image, 
                         (face_bbox[0], face_bbox[1]), 
                         (face_bbox[0] + face_bbox[2], face_bbox[1] + face_bbox[3]),
                         (0, 255, 0), 2)
            cv2.putText(preview_image, 'Face', 
                       (face_bbox[0], face_bbox[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            crop_area = self._calculate_center_crop(image.shape, spec_info)
        
        # 绘制裁剪框
        x, y, w, h = crop_area
        cv2.rectangle(preview_image, (x, y), (x + w, y + h), (255, 0, 0), 3)
        
        # 添加规格信息
        cv2.putText(preview_image, f'{spec} ({spec_info["mm_width"]}x{spec_info["mm_height"]}mm)', 
                   (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        
        crop_info = {
            'crop_area': crop_area,
            'spec': spec,
            'face_detected': face_info is not None
        }
        
        return preview_image, crop_info
    
    def manual_crop(self, image: np.ndarray, crop_area: Tuple, 
                   spec: str = '一寸') -> np.ndarray:
        """手动裁剪到指定区域"""
        if spec not in self.crop_specs:
            raise ValueError(f"不支持的规格: {spec}")
        
        spec_info = self.crop_specs[spec]
        
        # 执行裁剪
        cropped = self._crop_image(image, crop_area)
        
        # 调整到目标尺寸
        final_image = self._resize_to_spec(cropped, spec_info)
        
        return final_image