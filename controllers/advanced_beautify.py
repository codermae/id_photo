"""
高级美颜系统
提供分层美颜控制、特征保护、强度调节等功能
"""
import cv2
import numpy as np
from typing import Dict, Tuple, Optional
import math

class AdvancedBeautify:
    """高级美颜处理器"""
    
    def __init__(self, face_detector=None):
        """
        初始化美颜处理器
        
        Args:
            face_detector: 人脸检测器实例
        """
        self.face_detector = face_detector
        
        # 美颜选项定义
        self.beautify_options = {
            'skin_smooth': False,      # 磨皮
            'remove_blemishes': False, # 祛痘
            'eye_enhance': False,      # 眼部增强
            'lip_enhance': False,      # 唇部增强
            'teeth_whiten': False,     # 牙齿美白
            'face_slim': False,        # 瘦脸
            'eye_enlarge': False,      # 大眼
            'nose_enhance': False      # 鼻部增强
        }
        
        # 强度设置
        self.strength_settings = {
            'smooth_strength': 0.5,    # 磨皮强度 (0-1)
            'eye_enhance_strength': 0.3, # 眼部增强强度 (0-1)
            'lip_enhance_strength': 0.2, # 唇部增强强度 (0-1)
            'slim_strength': 0.2,      # 瘦脸强度 (0-1)
            'enlarge_strength': 0.1    # 大眼强度 (0-1)
        }
    
    def selective_beautify(self, image: np.ndarray, 
                          options: Dict, strengths: Dict = None) -> Tuple[np.ndarray, Dict]:
        """
        选择性美颜处理 - 重新设计版
        
        Args:
            image: 输入图像
            options: 美颜选项字典 (每个选项独立控制)
            strengths: 强度设置字典 (每个功能独立强度)
            
        Returns:
            tuple: (处理后的图像, 处理信息)
        """
        if strengths:
            self.strength_settings.update(strengths)
        
        result = image.copy()
        process_info = {
            'face_detected': False,
            'operations_applied': [],
            'processing_time': 0,
            'parameter_details': {}  # 添加参数详情输出
        }
        
        import time
        start_time = time.time()
        
        # 检测人脸区域
        face_mask, face_landmarks = self._get_face_regions(image)
        
        if face_mask is None:
            process_info['face_detected'] = False
            print("[DEBUG] 美颜处理: 未检测到人脸")
            return result, process_info
        
        process_info['face_detected'] = True
        print("[DEBUG] 美颜处理: 检测到人脸，开始处理")
        
        # 1. 磨皮处理 - 独立控制
        if options.get('skin_smooth', False):
            smooth_strength = strengths.get('smooth_strength', self.strength_settings['smooth_strength'])
            result = self._skin_smoothing(result, face_mask, face_landmarks)
            process_info['operations_applied'].append('skin_smooth')
            process_info['parameter_details']['skin_smooth'] = {
                'strength': smooth_strength,
                'method': 'bilateral_filter',
                'kernel_size': int(15 * smooth_strength)
            }
            print(f"[DEBUG] 磨皮处理完成 - 强度: {smooth_strength:.2f}")
        
        # 2. 祛痘处理 - 独立控制
        if options.get('remove_blemishes', False):
            blemish_strength = strengths.get('blemish_strength', self.strength_settings.get('blemish_strength', 0.5))
            # 更新强度设置
            self.strength_settings['blemish_strength'] = blemish_strength
            blemish_count = self._count_blemishes(image, face_mask)
            result = self._blemish_removal(result, face_mask)
            process_info['operations_applied'].append('remove_blemishes')
            process_info['parameter_details']['remove_blemishes'] = {
                'strength': blemish_strength,
                'detected_blemishes': blemish_count,
                'method': 'inpainting',
                'area_threshold': f'{int(2 * (1 - blemish_strength) + 1)}-{int(30 + 20 * blemish_strength)} pixels'
            }
            print(f"[DEBUG] 祛痘处理完成 - 强度: {blemish_strength:.2f}, 检测到瑕疵: {blemish_count}个")
        
        # 3. 眼部增强 - 独立控制
        if options.get('eye_enhance', False) and face_landmarks:
            eye_strength = strengths.get('eye_enhance_strength', self.strength_settings['eye_enhance_strength'])
            result = self._eye_enhancement(result, face_landmarks)
            process_info['operations_applied'].append('eye_enhance')
            process_info['parameter_details']['eye_enhance'] = {
                'strength': eye_strength,
                'contrast_boost': 1 + eye_strength * 0.3,
                'brightness_boost': eye_strength * 10
            }
            print(f"[DEBUG] 眼部增强完成 - 强度: {eye_strength:.2f}")
        
        # 5. 唇部增强 - 独立控制
        if options.get('lip_enhance', False) and face_landmarks:
            lip_strength = strengths.get('lip_enhance_strength', self.strength_settings['lip_enhance_strength'])
            result = self._lip_enhancement(result, face_landmarks)
            process_info['operations_applied'].append('lip_enhance')
            process_info['parameter_details']['lip_enhance'] = {
                'strength': lip_strength,
                'red_channel_boost': lip_strength * 30,
                'area': 'ellipse(25x12)'
            }
            print(f"[DEBUG] 唇部增强完成 - 强度: {lip_strength:.2f}")
        
        # 6. 牙齿美白 - 独立控制
        if options.get('teeth_whiten', False) and face_landmarks:
            result = self._teeth_whitening(result, face_landmarks)
            process_info['operations_applied'].append('teeth_whiten')
            process_info['parameter_details']['teeth_whiten'] = {
                'brightness_increase': 20,
                'area': 'ellipse(15x5)',
                'color_space': 'LAB'
            }
            print("[DEBUG] 牙齿美白完成")
        
        # 7. 瘦脸处理 - 独立控制
        if options.get('face_slim', False) and face_landmarks:
            slim_strength = strengths.get('slim_strength', self.strength_settings['slim_strength'])
            result = self._face_slimming(result, face_landmarks)
            process_info['operations_applied'].append('face_slim')
            process_info['parameter_details']['face_slim'] = {
                'strength': slim_strength,
                'warp_factor': slim_strength * 0.02,
                'affected_areas': ['left_cheek', 'right_cheek']
            }
            print(f"[DEBUG] 瘦脸处理完成 - 强度: {slim_strength:.2f}")
        
        # 8. 大眼处理 - 独立控制
        if options.get('eye_enlarge', False) and face_landmarks:
            enlarge_strength = strengths.get('enlarge_strength', self.strength_settings['enlarge_strength'])
            result = self._eye_enlargement(result, face_landmarks)
            process_info['operations_applied'].append('eye_enlarge')
            process_info['parameter_details']['eye_enlarge'] = {
                'strength': enlarge_strength,
                'warp_factor': enlarge_strength * 0.03,
                'radius': 40
            }
            print(f"[DEBUG] 大眼处理完成 - 强度: {enlarge_strength:.2f}")
        
        # 9. 鼻部增强 - 独立控制
        if options.get('nose_enhance', False) and face_landmarks:
            result = self._nose_enhancement(result, face_landmarks)
            process_info['operations_applied'].append('nose_enhance')
            process_info['parameter_details']['nose_enhance'] = {
                'brightness_increase': 15,
                'area': 'ellipse(8x15)',
                'position_offset': '(0, -5)'
            }
            print("[DEBUG] 鼻部增强完成")
        
        process_info['processing_time'] = time.time() - start_time
        
        # 输出总体处理统计
        print(f"[DEBUG] 美颜处理完成 - 总耗时: {process_info['processing_time']:.3f}秒")
        print(f"[DEBUG] 应用的操作: {', '.join(process_info['operations_applied'])}")
        
        return result, process_info
    
    def _count_blemishes(self, image: np.ndarray, face_mask: np.ndarray) -> int:
        """统计瑕疵数量"""
        blemish_strength = self.strength_settings.get('blemish_strength', 0.5)
        
        face_region = cv2.bitwise_and(image, image, mask=face_mask)
        gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        
        # 使用形态学检测
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        tophat = cv2.morphologyEx(gray_face, cv2.MORPH_TOPHAT, kernel)
        blackhat = cv2.morphologyEx(gray_face, cv2.MORPH_BLACKHAT, kernel)
        combined = cv2.add(tophat, blackhat)
        
        threshold_value = int(20 - 15 * blemish_strength)
        threshold_value = max(5, threshold_value)
        _, blemish_mask = cv2.threshold(combined, threshold_value, 255, cv2.THRESH_BINARY)
        blemish_mask = cv2.bitwise_and(blemish_mask, face_mask)
        
        contours, _ = cv2.findContours(blemish_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        blemish_count = 0
        
        min_area = 2
        max_area = int(50 + 100 * blemish_strength)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity > 0.3:
                        blemish_count += 1
        
        return blemish_count
    
    def _get_face_regions(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
        """获取人脸区域和关键点"""
        if not self.face_detector:
            return None, None
        
        # 检测人脸
        try:
            face = self.face_detector.detect_face(image)
            # 修复数组比较问题
            if face is None or (hasattr(face, '__len__') and len(face) == 0):
                return None, None
        except Exception as e:
            print(f"[DEBUG] 人脸检测异常: {e}")
            return None, None
        
        x, y, w, h = face
        
        # 创建人脸mask
        face_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        
        # 创建椭圆形人脸区域
        center = (x + w//2, y + h//2)
        axes = (w//2, h//2)
        cv2.ellipse(face_mask, center, axes, 0, 0, 360, 255, -1)
        
        # 简化的关键点（基于人脸框估算）
        landmarks = self._estimate_landmarks(x, y, w, h)
        
        return face_mask, landmarks
    
    def _estimate_landmarks(self, x: int, y: int, w: int, h: int) -> Dict:
        """基于人脸框估算关键点位置"""
        landmarks = {
            'left_eye': (x + int(w * 0.3), y + int(h * 0.35)),
            'right_eye': (x + int(w * 0.7), y + int(h * 0.35)),
            'nose_tip': (x + int(w * 0.5), y + int(h * 0.55)),
            'mouth_center': (x + int(w * 0.5), y + int(h * 0.75)),
            'left_mouth': (x + int(w * 0.35), y + int(h * 0.75)),
            'right_mouth': (x + int(w * 0.65), y + int(h * 0.75)),
            'chin': (x + int(w * 0.5), y + int(h * 0.95)),
            'left_cheek': (x + int(w * 0.2), y + int(h * 0.6)),
            'right_cheek': (x + int(w * 0.8), y + int(h * 0.6))
        }
        return landmarks
    
    def _skin_smoothing(self, image: np.ndarray, face_mask: np.ndarray, 
                       landmarks: Dict) -> np.ndarray:
        """智能磨皮，保护重要特征 - 改进版"""
        # 创建特征保护mask
        protect_mask = self._create_feature_protection_mask(image.shape[:2], landmarks)
        
        # 只在皮肤区域进行磨皮
        skin_only_mask = cv2.bitwise_and(face_mask, cv2.bitwise_not(protect_mask))
        
        # 改进的双边滤波参数 - 确保效果明显
        smooth_strength = self.strength_settings['smooth_strength']
        
        # 核大小：9-35（确保最小值也有效果）
        d = max(9, int(15 + 20 * smooth_strength))
        
        # 颜色标准差：调整为更温和的范围 30-100
        sigma_color = max(30, int(40 + 60 * smooth_strength))
        
        # 空间标准差：调整为更温和的范围 30-100
        sigma_space = max(30, int(40 + 60 * smooth_strength))
        
        # 迭代次数：1-3次（减少迭代避免过度平滑）
        iterations = max(1, int(1 + smooth_strength * 2))
        
        # 多次双边滤波以获得更好的磨皮效果
        smoothed = image.copy()
        
        for i in range(iterations):
            smoothed = cv2.bilateralFilter(smoothed, d, sigma_color, sigma_space)
        
        # 按强度和mask混合
        result = image.copy().astype(np.float32)
        mask_norm = skin_only_mask.astype(np.float32) / 255.0
        
        # 温和的混合强度 - 避免过度处理
        blend_strength = min(0.8, smooth_strength * 1.0)  # 降低混合强度上限
        
        for c in range(3):
            result[:, :, c] = (
                image[:, :, c].astype(np.float32) * (1 - mask_norm * blend_strength) +
                smoothed[:, :, c].astype(np.float32) * (mask_norm * blend_strength)
            )
        
        print(f"[DEBUG] 磨皮处理 - 迭代次数: {iterations}, 核大小: {d}, sigma: {sigma_color}/{sigma_space}, 强度: {smooth_strength}, 混合强度: {blend_strength:.2f}")
        
        return result.astype(np.uint8)
    
    def _create_feature_protection_mask(self, image_shape: Tuple, 
                                      landmarks: Dict) -> np.ndarray:
        """创建特征保护mask（眼睛、眉毛、嘴唇、鼻孔）"""
        h, w = image_shape
        protect_mask = np.zeros((h, w), dtype=np.uint8)
        
        # 保护眼部区域
        if 'left_eye' in landmarks:
            eye_pos = landmarks['left_eye']
            cv2.circle(protect_mask, eye_pos, 15, 255, -1)
        
        if 'right_eye' in landmarks:
            eye_pos = landmarks['right_eye']
            cv2.circle(protect_mask, eye_pos, 15, 255, -1)
        
        # 保护嘴部区域
        if 'mouth_center' in landmarks:
            mouth_pos = landmarks['mouth_center']
            cv2.ellipse(protect_mask, mouth_pos, (20, 10), 0, 0, 360, 255, -1)
        
        # 保护鼻孔区域
        if 'nose_tip' in landmarks:
            nose_pos = landmarks['nose_tip']
            cv2.circle(protect_mask, nose_pos, 8, 255, -1)
        
        return protect_mask
    
    def _blemish_removal(self, image: np.ndarray, face_mask: np.ndarray) -> np.ndarray:
        """
        祛痘祛瑕疵 - 只去痘，不模糊脸
        
        核心思路：
        1. 精确检测痘痘位置
        2. 只对痘痘区域使用inpaint修复
        3. 其他区域完全不动
        
        这样可以去掉痘痘，同时保持脸部清晰
        """
        blemish_strength = self.strength_settings.get('blemish_strength', 0.5)
        
        if blemish_strength <= 0:
            return image
        
        print(f"[DEBUG] 祛痘处理开始 - 强度: {blemish_strength}")
        
        # 转换为灰度图
        face_region = cv2.bitwise_and(image, image, mask=face_mask)
        gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        
        # 创建保护mask - 保护眼睛、眉毛和嘴巴（扩大保护区域）
        h, w = face_mask.shape
        protect_mask = np.zeros_like(face_mask)
        
        face_contours, _ = cv2.findContours(face_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(face_contours) > 0:
            face_contour = max(face_contours, key=cv2.contourArea)
            x, y, fw, fh = cv2.boundingRect(face_contour)
            
            # 保护眼睛区域（扩大到30像素半径）
            eye_y = y + int(fh * 0.35)
            cv2.circle(protect_mask, (x + int(fw * 0.3), eye_y), 30, 255, -1)
            cv2.circle(protect_mask, (x + int(fw * 0.7), eye_y), 30, 255, -1)
            
            # 保护眉毛区域
            eyebrow_y = y + int(fh * 0.25)
            cv2.ellipse(protect_mask, (x + int(fw * 0.3), eyebrow_y), (20, 10), 0, 0, 360, 255, -1)
            cv2.ellipse(protect_mask, (x + int(fw * 0.7), eyebrow_y), (20, 10), 0, 0, 360, 255, -1)
            
            # 保护嘴巴区域（扩大）
            mouth_y = y + int(fh * 0.75)
            cv2.ellipse(protect_mask, (x + int(fw * 0.5), mouth_y), (30, 15), 0, 0, 360, 255, -1)
        
        # ===== 检测痘痘 =====
        # 痘痘特征：局部暗点
        
        # 1. 使用形态学Top-Hat检测暗点
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        tophat = cv2.morphologyEx(gray_face, cv2.MORPH_TOPHAT, kernel)
        
        # 2. 使用形态学Black-Hat检测暗点
        blackhat = cv2.morphologyEx(gray_face, cv2.MORPH_BLACKHAT, kernel)
        
        # 3. 组合检测
        combined = cv2.add(tophat, blackhat)
        
        # 根据强度调整阈值
        threshold_value = int(20 - 15 * blemish_strength)  # 强度越高，阈值越低，检测越多
        threshold_value = max(5, threshold_value)  # 最低5
        
        _, blemish_mask = cv2.threshold(combined, threshold_value, 255, cv2.THRESH_BINARY)
        
        # 应用人脸mask和保护mask
        blemish_mask = cv2.bitwise_and(blemish_mask, face_mask)
        blemish_mask = cv2.bitwise_and(blemish_mask, cv2.bitwise_not(protect_mask))
        
        # 形态学清理
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        blemish_mask = cv2.morphologyEx(blemish_mask, cv2.MORPH_OPEN, kernel_clean)
        blemish_mask = cv2.morphologyEx(blemish_mask, cv2.MORPH_CLOSE, kernel_clean)
        
        # 过滤大小 - 只保留痘痘大小的区域
        contours, _ = cv2.findContours(blemish_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        final_mask = np.zeros_like(blemish_mask)
        blemish_count = 0
        
        # 痘痘大小范围
        min_area = 2
        max_area = int(50 + 100 * blemish_strength)  # 50-150像素
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                # 检查圆度 - 痘痘通常比较圆
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity > 0.3:  # 比较宽松的圆度要求
                        cv2.fillPoly(final_mask, [contour], 255)
                        blemish_count += 1
        
        print(f"[DEBUG] 检测到痘痘: {blemish_count}个")
        print(f"[DEBUG] 检测阈值: {threshold_value}, 大小范围: {min_area}-{max_area}像素")
        
        # ===== 只修复检测到的痘痘，其他区域不动 =====
        if np.sum(final_mask) > 0:
            # 使用inpaint修复痘痘
            inpaint_radius = int(5 + 5 * blemish_strength)  # 5-10像素
            result = cv2.inpaint(image, final_mask, inpaint_radius, cv2.INPAINT_TELEA)
            
            print(f"[DEBUG] 痘痘修复完成 - inpaint半径: {inpaint_radius}")
            return result
        else:
            print("[DEBUG] 未检测到痘痘")
            return image
    
    def _eye_enhancement(self, image: np.ndarray, landmarks: Dict) -> np.ndarray:
        """眼部增强"""
        result = image.copy()
        enhance_strength = self.strength_settings['eye_enhance_strength']
        
        # 增强左眼
        if 'left_eye' in landmarks:
            result = self._enhance_single_eye(result, landmarks['left_eye'], enhance_strength)
        
        # 增强右眼
        if 'right_eye' in landmarks:
            result = self._enhance_single_eye(result, landmarks['right_eye'], enhance_strength)
        
        return result
    
    def _enhance_single_eye(self, image: np.ndarray, eye_center: Tuple, 
                           strength: float) -> np.ndarray:
        """增强单个眼部"""
        x, y = eye_center
        radius = 20
        
        # 创建眼部区域mask
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), radius, 255, -1)
        
        # 提取眼部区域
        eye_region = cv2.bitwise_and(image, image, mask=mask)
        
        # 增加对比度和锐化
        lab = cv2.cvtColor(eye_region, cv2.COLOR_BGR2LAB).astype(np.float32)
        l, a, b = cv2.split(lab)
        
        # 增强亮度对比度
        l_enhanced = cv2.convertScaleAbs(l, alpha=1 + strength * 0.3, beta=strength * 10)
        
        # 重新合成
        lab_enhanced = cv2.merge([l_enhanced.astype(np.float32), a, b])
        eye_enhanced = cv2.cvtColor(lab_enhanced.astype(np.uint8), cv2.COLOR_LAB2BGR)
        
        # 混合回原图
        mask_norm = mask.astype(np.float32) / 255.0
        result = image.copy()
        for c in range(3):
            result[:, :, c] = (
                image[:, :, c] * (1 - mask_norm) +
                eye_enhanced[:, :, c] * mask_norm
            ).astype(np.uint8)
        
        return result
    
    def _lip_enhancement(self, image: np.ndarray, landmarks: Dict) -> np.ndarray:
        """唇部增强"""
        if 'mouth_center' not in landmarks:
            return image
        
        result = image.copy()
        enhance_strength = self.strength_settings['lip_enhance_strength']
        
        mouth_center = landmarks['mouth_center']
        x, y = mouth_center
        
        # 创建嘴唇区域mask
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.ellipse(mask, (x, y), (25, 12), 0, 0, 360, 255, -1)
        
        # 增强红色通道
        mask_norm = mask.astype(np.float32) / 255.0
        result[:, :, 2] = np.clip(
            result[:, :, 2] + mask_norm * enhance_strength * 30, 0, 255
        ).astype(np.uint8)
        
        return result
    
    def _teeth_whitening(self, image: np.ndarray, landmarks: Dict) -> np.ndarray:
        """牙齿美白"""
        if 'mouth_center' not in landmarks:
            return image
        
        # 简化的牙齿区域检测和美白
        mouth_center = landmarks['mouth_center']
        x, y = mouth_center
        
        # 创建牙齿区域mask（嘴部下方小区域）
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.ellipse(mask, (x, y + 3), (15, 5), 0, 0, 360, 255, -1)
        
        # 美白处理
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
        l, a, b = cv2.split(lab)
        
        mask_norm = mask.astype(np.float32) / 255.0
        l_whitened = l + mask_norm * 20  # 增加亮度
        l_whitened = np.clip(l_whitened, 0, 255)
        
        lab_whitened = cv2.merge([l_whitened, a, b])
        result = cv2.cvtColor(lab_whitened.astype(np.uint8), cv2.COLOR_LAB2BGR)
        
        return result
    
    def _face_slimming(self, image: np.ndarray, landmarks: Dict) -> np.ndarray:
        """瘦脸处理"""
        # 简化的瘦脸实现（收缩脸颊区域）
        slim_strength = self.strength_settings['slim_strength']
        
        if 'left_cheek' not in landmarks or 'right_cheek' not in landmarks:
            return image
        
        result = image.copy()
        h, w = image.shape[:2]
        
        # 创建变形映射
        map_x = np.arange(w, dtype=np.float32)
        map_y = np.arange(h, dtype=np.float32)
        map_x, map_y = np.meshgrid(map_x, map_y)
        
        # 对脸颊区域进行收缩
        left_cheek = landmarks['left_cheek']
        right_cheek = landmarks['right_cheek']
        
        # 左脸颊收缩
        self._apply_local_warp(map_x, map_y, left_cheek, slim_strength * 0.02, 'inward')
        
        # 右脸颊收缩
        self._apply_local_warp(map_x, map_y, right_cheek, slim_strength * 0.02, 'inward')
        
        # 应用变形
        result = cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR)
        
        return result
    
    def _eye_enlargement(self, image: np.ndarray, landmarks: Dict) -> np.ndarray:
        """大眼处理"""
        enlarge_strength = self.strength_settings['enlarge_strength']
        
        result = image.copy()
        h, w = image.shape[:2]
        
        # 创建变形映射
        map_x = np.arange(w, dtype=np.float32)
        map_y = np.arange(h, dtype=np.float32)
        map_x, map_y = np.meshgrid(map_x, map_y)
        
        # 放大左眼
        if 'left_eye' in landmarks:
            self._apply_local_warp(map_x, map_y, landmarks['left_eye'], 
                                 enlarge_strength * 0.03, 'outward')
        
        # 放大右眼
        if 'right_eye' in landmarks:
            self._apply_local_warp(map_x, map_y, landmarks['right_eye'], 
                                 enlarge_strength * 0.03, 'outward')
        
        # 应用变形
        result = cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR)
        
        return result
    
    def _nose_enhancement(self, image: np.ndarray, landmarks: Dict) -> np.ndarray:
        """鼻部增强"""
        if 'nose_tip' not in landmarks:
            return image
        
        # 简单的鼻部高光增强
        nose_pos = landmarks['nose_tip']
        x, y = nose_pos
        
        # 创建鼻部高光mask
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.ellipse(mask, (x, y - 5), (8, 15), 0, 0, 360, 255, -1)
        
        # 增加亮度
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
        l, a, b = cv2.split(lab)
        
        mask_norm = mask.astype(np.float32) / 255.0
        l_enhanced = l + mask_norm * 15
        l_enhanced = np.clip(l_enhanced, 0, 255)
        
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        result = cv2.cvtColor(lab_enhanced.astype(np.uint8), cv2.COLOR_LAB2BGR)
        
        return result
    
    def _apply_local_warp(self, map_x: np.ndarray, map_y: np.ndarray, 
                         center: Tuple, strength: float, direction: str):
        """应用局部变形"""
        cx, cy = center
        radius = 40
        
        # 计算距离
        dx = map_x - cx
        dy = map_y - cy
        distance = np.sqrt(dx**2 + dy**2)
        
        # 创建变形mask
        mask = distance < radius
        
        if direction == 'outward':
            # 向外扩张
            factor = 1 + strength * (1 - distance / radius)
        else:
            # 向内收缩
            factor = 1 - strength * (1 - distance / radius)
        
        # 应用变形
        map_x[mask] = cx + dx[mask] * factor[mask]
        map_y[mask] = cy + dy[mask] * factor[mask]
    
    def get_available_options(self) -> Dict:
        """获取可用的美颜选项"""
        return {
            'skin_smooth': '磨皮',
            'remove_blemishes': '祛痘',
            'eye_enhance': '眼部增强',
            'lip_enhance': '唇部增强',
            'teeth_whiten': '牙齿美白',
            'face_slim': '瘦脸',
            'eye_enlarge': '大眼',
            'nose_enhance': '鼻部增强'
        }
    
    def get_strength_ranges(self) -> Dict:
        """获取强度设置范围"""
        return {
            'smooth_strength': (0.0, 1.0, 0.1),
            'eye_enhance_strength': (0.0, 1.0, 0.1),
            'lip_enhance_strength': (0.0, 1.0, 0.1),
            'slim_strength': (0.0, 1.0, 0.1),
            'enlarge_strength': (0.0, 1.0, 0.1)
        }
    
    def create_preset(self, name: str, options: Dict, strengths: Dict) -> Dict:
        """创建美颜预设"""
        return {
            'name': name,
            'options': options.copy(),
            'strengths': strengths.copy()
        }
    
    def get_default_presets(self) -> Dict:
        """获取默认预设"""
        return {
            '自然美颜': {
                'options': {
                    'skin_smooth': True,
                    'skin_brighten': True,
                    'remove_blemishes': True
                },
                'strengths': {
                    'smooth_strength': 0.3,
                    'brighten_strength': 0.2
                }
            },
            '标准美颜': {
                'options': {
                    'skin_smooth': True,
                    'skin_brighten': True,
                    'remove_blemishes': True,
                    'eye_enhance': True,
                    'lip_enhance': True
                },
                'strengths': {
                    'smooth_strength': 0.5,
                    'brighten_strength': 0.3,
                    'eye_enhance_strength': 0.3,
                    'lip_enhance_strength': 0.2
                }
            },
            '强效美颜': {
                'options': {
                    'skin_smooth': True,
                    'skin_brighten': True,
                    'remove_blemishes': True,
                    'eye_enhance': True,
                    'lip_enhance': True,
                    'teeth_whiten': True,
                    'face_slim': True,
                    'eye_enlarge': True
                },
                'strengths': {
                    'smooth_strength': 0.7,
                    'brighten_strength': 0.4,
                    'eye_enhance_strength': 0.4,
                    'lip_enhance_strength': 0.3,
                    'slim_strength': 0.3,
                    'enlarge_strength': 0.2
                }
            }
        }