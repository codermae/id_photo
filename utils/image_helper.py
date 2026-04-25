"""
图像处理助手
"""
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from config.config import PHOTO_SPECS, BACKGROUND_COLORS

class ImageHelper:
    """图像处理助手类"""

    @staticmethod
    def load_image(filepath):
        """加载图像"""
        return cv2.imread(filepath)

    @staticmethod
    def save_image(filepath, image):
        """保存图像"""
        cv2.imwrite(filepath, image)

    @staticmethod
    def resize_image(image, width, height):
        """调整图像大小"""
        return cv2.resize(image, (width, height), interpolation=cv2.INTER_LANCZOS4)

    @staticmethod
    def crop_image(image, x, y, width, height):
        """裁切图像"""
        return image[y:y+height, x:x+width]

    @staticmethod
    def rotate_image(image, angle):
        """旋转图像"""
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, matrix, (w, h))

    @staticmethod
    def change_background(image, color_name='白色', ai_processor=None):
        """更换背景色 - 专业级版本"""
        if color_name not in BACKGROUND_COLORS:
            color_name = '白色'
        
        bg_color = BACKGROUND_COLORS[color_name]
        bg_color_bgr = (bg_color[2], bg_color[1], bg_color[0])
        
        try:
            # 方法1：优先使用 AI 处理器的分割
            if ai_processor is not None:
                try:
                    mask = ai_processor.get_segmentation_mask(image)
                    if mask is not None:
                        # 优化掩码
                        mask = ImageHelper._optimize_segmentation_mask(mask, image)
                        
                        # 创建背景
                        background = np.full_like(image, bg_color_bgr)
                        
                        # 使用掩码进行混合
                        mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(float) / 255.0
                        
                        result = (image.astype(float) * mask_3channel + 
                                 background.astype(float) * (1 - mask_3channel)).astype(np.uint8)
                        
                        print("使用 AI 分割成功")
                        return result
                except Exception as e:
                    print(f"AI 分割失败: {e}")
            
            # 方法2：高级肤色检测 + 边缘优化
            result = ImageHelper._advanced_skin_segmentation(image, bg_color_bgr)
            if result is not None:
                print("使用高级肤色检测成功")
                return result
            
            # 方法3：基础肤色检测（备用）
            result = ImageHelper._basic_skin_segmentation(image, bg_color_bgr)
            print("使用基础肤色检测")
            return result
            
        except Exception as e:
            print(f"背景替换失败: {e}")
            return image
    
    @staticmethod
    def _optimize_segmentation_mask(mask, image):
        """优化分割掩码"""
        try:
            # 1. 形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # 2. 边缘平滑
            mask = cv2.GaussianBlur(mask, (21, 21), 0)
            
            # 3. 边缘细化
            edges = cv2.Canny(image, 50, 150)
            edge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            edges = cv2.dilate(edges, edge_kernel, iterations=1)
            
            # 在边缘区域减少掩码强度
            edge_mask = edges.astype(float) / 255.0
            mask = mask.astype(float)
            mask = mask * (1 - edge_mask * 0.3)
            mask = np.clip(mask, 0, 255).astype(np.uint8)
            
            return mask
        except:
            return mask
    
    @staticmethod
    def _advanced_skin_segmentation(image, bg_color_bgr):
        """高级肤色分割"""
        try:
            h, w = image.shape[:2]
            
            # 1. 多色彩空间肤色检测
            # HSV 空间
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 多个肤色范围
            skin_ranges_hsv = [
                ([0, 20, 70], [20, 255, 255]),      # 浅肤色
                ([0, 30, 60], [25, 255, 255]),      # 中等肤色
                ([0, 40, 50], [30, 255, 255]),      # 深肤色
            ]
            
            hsv_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in skin_ranges_hsv:
                lower = np.array(lower, dtype=np.uint8)
                upper = np.array(upper, dtype=np.uint8)
                mask_range = cv2.inRange(hsv, lower, upper)
                hsv_mask = cv2.bitwise_or(hsv_mask, mask_range)
            
            # YCrCb 空间
            ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
            lower_ycrcb = np.array([0, 133, 77], dtype=np.uint8)
            upper_ycrcb = np.array([255, 173, 127], dtype=np.uint8)
            ycrcb_mask = cv2.inRange(ycrcb, lower_ycrcb, upper_ycrcb)
            
            # 组合掩码
            combined_mask = cv2.bitwise_or(hsv_mask, ycrcb_mask)
            
            # 2. 形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
            
            # 3. 区域填充（填充人体内部的空洞）
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                # 找到最大的轮廓（假设是人体）
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > w * h * 0.05:  # 至少占图像5%
                    # 填充轮廓
                    cv2.fillPoly(combined_mask, [largest_contour], 255)
            
            # 4. 边缘平滑
            combined_mask = cv2.GaussianBlur(combined_mask, (21, 21), 0)
            
            # 5. 创建背景并混合
            background = np.full_like(image, bg_color_bgr)
            mask_3channel = cv2.cvtColor(combined_mask, cv2.COLOR_GRAY2BGR).astype(float) / 255.0
            
            result = (image.astype(float) * mask_3channel + 
                     background.astype(float) * (1 - mask_3channel)).astype(np.uint8)
            
            return result
            
        except Exception as e:
            print(f"高级肤色分割失败: {e}")
            return None
    
    @staticmethod
    def _basic_skin_segmentation(image, bg_color_bgr):
        """基础肤色分割（备用方法）"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 基础肤色范围
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            
            # 基本形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
            mask = cv2.dilate(mask, kernel, iterations=2)
            mask = cv2.erode(mask, kernel, iterations=1)
            mask = cv2.GaussianBlur(mask, (21, 21), 0)
            
            # 创建背景
            background = np.full_like(image, bg_color_bgr)
            mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(float) / 255.0
            
            result = (image.astype(float) * mask_3channel + 
                     background.astype(float) * (1 - mask_3channel)).astype(np.uint8)
            
            return result
            
        except Exception as e:
            print(f"基础肤色分割失败: {e}")
            return image
        mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(float) / 255.0
        
        result = (image.astype(float) * mask_3channel + 
                 background.astype(float) * (1 - mask_3channel)).astype(np.uint8)
        
        return result

    @staticmethod
    def beautify_face(image, ai_processor=None, strength=1.0):
        """美颜处理 - 专业级版本"""
        try:
            result = image.copy().astype(np.float32)
            h, w = result.shape[:2]
            
            # 第一步：智能人脸区域检测和处理
            face_mask = None
            if ai_processor is not None:
                try:
                    face = ai_processor.detect_face(image)
                    if face:
                        x, y, fw, fh = face
                        # 创建人脸掩码，扩大处理区域
                        face_mask = np.zeros((h, w), dtype=np.uint8)
                        
                        # 扩大人脸区域
                        padding = max(20, min(fw, fh) // 4)
                        x1 = max(0, x - padding)
                        y1 = max(0, y - padding)
                        x2 = min(w, x + fw + padding)
                        y2 = min(h, y + fh + padding)
                        
                        # 创建椭圆形掩码（更自然）
                        center = ((x1 + x2) // 2, (y1 + y2) // 2)
                        axes = ((x2 - x1) // 2, (y2 - y1) // 2)
                        cv2.ellipse(face_mask, center, axes, 0, 0, 360, 255, -1)
                        
                        # 高斯模糊掩码边缘
                        face_mask = cv2.GaussianBlur(face_mask, (51, 51), 0)
                        face_mask = face_mask.astype(np.float32) / 255.0
                        
                        print(f"人脸区域美颜: ({x1}, {y1}) 到 ({x2}, {y2})")
                except Exception as e:
                    print(f"人脸检测失败，使用全图处理: {e}")
            
            # 第二步：多层次磨皮
            # 2.1 保边磨皮（双边滤波）
            smooth1 = cv2.bilateralFilter(result.astype(np.uint8), 15, 80, 80).astype(np.float32)
            
            # 2.2 表面模糊（更强的磨皮）
            smooth2 = cv2.GaussianBlur(result, (15, 15), 0)
            
            # 2.3 混合两种磨皮效果
            smooth_blend = cv2.addWeighted(smooth1, 0.7, smooth2, 0.3, 0)
            
            # 2.4 保留细节的磨皮
            if strength > 0.5:
                # 提取高频细节
                high_freq = result - smooth_blend
                # 减弱高频细节（磨皮效果）
                high_freq *= (1.0 - strength * 0.4)
                smooth_blend = smooth_blend + high_freq
            
            # 应用人脸掩码
            if face_mask is not None:
                face_mask_3ch = np.stack([face_mask] * 3, axis=-1)
                result = result * (1 - face_mask_3ch) + smooth_blend * face_mask_3ch
            else:
                result = cv2.addWeighted(result, 1 - strength * 0.6, smooth_blend, strength * 0.6, 0)
            
            # 第三步：肤色优化
            if strength > 0.3:
                # 转换到 LAB 色彩空间
                lab = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
                l, a, b = cv2.split(lab)
                
                # 肤色检测
                hsv = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_BGR2HSV)
                lower_skin = np.array([0, 30, 60])
                upper_skin = np.array([20, 255, 255])
                skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
                skin_mask = cv2.GaussianBlur(skin_mask, (21, 21), 0).astype(np.float32) / 255.0
                
                # 肤色均匀化
                a_smooth = cv2.GaussianBlur(a, (31, 31), 0)
                b_smooth = cv2.GaussianBlur(b, (31, 31), 0)
                
                a = a * (1 - skin_mask * strength * 0.3) + a_smooth * (skin_mask * strength * 0.3)
                b = b * (1 - skin_mask * strength * 0.3) + b_smooth * (skin_mask * strength * 0.3)
                
                result = cv2.cvtColor(cv2.merge([l, a, b]).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
            
            # 第四步：对比度和亮度优化
            lab = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
            l, a, b = cv2.split(lab)
            
            # 自适应直方图均衡化
            clahe = cv2.createCLAHE(clipLimit=2.0 + strength, tileGridSize=(8, 8))
            l = clahe.apply(l.astype(np.uint8)).astype(np.float32)
            
            result = cv2.cvtColor(cv2.merge([l, a, b]).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
            
            # 第五步：色彩增强
            if strength > 0.4:
                hsv = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
                h, s, v = cv2.split(hsv)
                
                # 轻微增加饱和度
                s = np.clip(s * (1.0 + (strength - 0.4) * 0.2), 0, 255)
                
                # 轻微增加亮度
                v = np.clip(v * (1.0 + (strength - 0.4) * 0.1), 0, 255)
                
                result = cv2.cvtColor(cv2.merge([h, s, v]).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
            
            # 第六步：轻微锐化（增强细节）
            if strength < 1.5:
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]]) * 0.15
                sharpened = cv2.filter2D(result, -1, kernel)
                result = cv2.addWeighted(result, 0.85, sharpened, 0.15, 0)
            
            # 第七步：最终调整
            result = np.clip(result, 0, 255).astype(np.uint8)
            
            return result
            
        except Exception as e:
            print(f"美颜处理失败: {e}")
            return image

    @staticmethod
    def adjust_brightness_contrast(image, brightness=0, contrast=1.0):
        """调整亮度和对比度"""
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # 调整亮度
        enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = enhancer.enhance(1 + brightness / 100)
        
        # 调整对比度
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(contrast)
        
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    @staticmethod
    def get_image_quality_score(image):
        """计算图像质量评分 (0-100) - 返回详细指标"""
        try:
            # 清晰度检测（拉普拉斯算子）
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(100, int(laplacian_var / 5))
            
            # 亮度检测 - 最佳范围 100-150
            brightness = np.mean(gray)
            if 100 <= brightness <= 150:
                brightness_score = 100
            elif 80 <= brightness <= 170:
                brightness_score = 85
            elif 60 <= brightness <= 190:
                brightness_score = 70
            elif 40 <= brightness <= 210:
                brightness_score = 50
            else:
                brightness_score = 30
            
            # 对比度检测 - 最佳范围 60-80
            contrast = np.std(gray)
            if 60 <= contrast <= 80:
                contrast_score = 100
            elif 50 <= contrast <= 90:
                contrast_score = 85
            elif 40 <= contrast <= 100:
                contrast_score = 70
            elif 30 <= contrast <= 110:
                contrast_score = 50
            else:
                contrast_score = 30
            
            # 综合评分
            overall_score = int(sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
            
            # 调试输出
            print(f"[DEBUG] 质量评分计算:")
            print(f"  - 拉普拉斯方差: {laplacian_var:.2f}")
            print(f"  - 清晰度: {sharpness_score}")
            print(f"  - 亮度值: {brightness:.2f} (最佳范围: 100-150)")
            print(f"  - 亮度评分: {brightness_score}")
            print(f"  - 对比度值: {contrast:.2f} (最佳范围: 60-80)")
            print(f"  - 对比度评分: {contrast_score}")
            print(f"  - 综合评分: {overall_score}")
            
            # 返回详细指标
            return {
                'overall_score': overall_score,
                'sharpness': sharpness_score,
                'brightness': brightness_score,
                'contrast': contrast_score
            }
        except Exception as e:
            print(f"[ERROR] 质量评分计算失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'overall_score': 0,
                'sharpness': 0,
                'brightness': 0,
                'contrast': 0
            }
    
    @staticmethod
    def get_image_quality_score_simple(image):
        """获取简单的质量评分（向后兼容）"""
        result = ImageHelper.get_image_quality_score(image)
        if isinstance(result, dict):
            return result['overall_score']
        return result

    @staticmethod
    def crop_to_spec(image, spec='一寸', face_landmarks=None):
        """按规格裁切图像 - 智能版本，基于人脸位置"""
        if spec not in PHOTO_SPECS:
            spec = '一寸'
        
        target_width, target_height = PHOTO_SPECS[spec]
        h, w = image.shape[:2]
        
        # 如果有人脸信息，基于人脸位置进行智能裁切
        if face_landmarks is not None:
            try:
                # 这里可以基于人脸关键点进行智能裁切
                # 暂时使用简单的居中裁切
                pass
            except:
                pass
        
        # 计算缩放比例，确保图像完全覆盖目标尺寸
        scale = max(target_width / w, target_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 高质量缩放
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        
        # 智能裁切：优先保持人脸在合适位置
        # 证件照通常人脸应该在上半部分
        x = (new_w - target_width) // 2
        y = max(0, (new_h - target_height) // 3)  # 稍微偏上
        
        # 确保不超出边界
        if y + target_height > new_h:
            y = new_h - target_height
        
        cropped = resized[y:y+target_height, x:x+target_width]
        
        return cropped

    @staticmethod
    def enhance_image_quality(image):
        """综合图像质量增强"""
        try:
            result = image.copy()
            
            # 1. 去噪
            result = cv2.fastNlMeansDenoisingColored(result, None, 10, 10, 7, 21)
            
            # 2. 锐化
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(result, -1, kernel)
            result = cv2.addWeighted(result, 0.8, sharpened, 0.2, 0)
            
            # 3. 对比度增强
            lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            result = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
            
            return result
        except Exception as e:
            print(f"图像质量增强失败: {e}")
            return image

    @staticmethod
    def auto_white_balance(image):
        """自动白平衡"""
        try:
            # 灰度世界算法
            result = image.copy().astype(np.float64)
            
            # 计算每个通道的平均值
            avg_b = np.mean(result[:, :, 0])
            avg_g = np.mean(result[:, :, 1])
            avg_r = np.mean(result[:, :, 2])
            
            # 计算灰度平均值
            gray_avg = (avg_b + avg_g + avg_r) / 3
            
            # 调整每个通道
            result[:, :, 0] = result[:, :, 0] * (gray_avg / avg_b)
            result[:, :, 1] = result[:, :, 1] * (gray_avg / avg_g)
            result[:, :, 2] = result[:, :, 2] * (gray_avg / avg_r)
            
            # 限制值范围
            result = np.clip(result, 0, 255).astype(np.uint8)
            
            return result
        except Exception as e:
            print(f"自动白平衡失败: {e}")
            return image

    @staticmethod
    def detect_face_landmarks(image):
        """检测人脸关键点"""
        try:
            # 尝试新版本的导入方式
            try:
                from mediapipe import solutions
                face_mesh = solutions.face_mesh.FaceMesh(static_image_mode=True)
            except ImportError:
                # 尝试旧版本的导入方式
                import mediapipe as mp
                face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=True)
            
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_image)
            
            if results.multi_face_landmarks:
                return results.multi_face_landmarks[0]
        except Exception as e:
            print(f"人脸关键点检测失败: {e}")
        
        return None

    @staticmethod
    def draw_face_detection_box(image, face_landmarks=None):
        """绘制人脸检测框"""
        try:
            # 尝试新版本的导入方式
            try:
                from mediapipe import solutions
                from mediapipe.python.solutions import drawing_utils
                face_mesh_connections = solutions.face_mesh.FACEMESH_TESSELATION
            except ImportError:
                # 尝试旧版本的导入方式
                import mediapipe as mp
                drawing_utils = mp.solutions.drawing_utils
                face_mesh_connections = mp.solutions.face_mesh.FACEMESH_TESSELATION
            
            if face_landmarks:
                drawing_utils.draw_landmarks(
                    image,
                    face_landmarks,
                    face_mesh_connections,
                    landmark_drawing_spec=drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=1),
                    connection_drawing_spec=drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=1)
                )
        except Exception as e:
            print(f"绘制人脸检测框失败: {e}")
        
        return image
