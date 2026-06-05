"""
精确背景替换系统 - 集成PP-Matting
使用PP-Matting + 传统算法实现高质量的人像抠图和背景替换
"""
import cv2
import numpy as np
from typing import Tuple, Dict, Optional, Union
import os

class PreciseBackgroundReplacer:
    """精确背景替换器 - 集成PP-Matting版本"""
    
    def __init__(self):
        """初始化背景替换器"""
        # 常用证件照背景色 (支持中英文)
        self.background_colors = {
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'blue': (67, 142, 219),
            'light_blue': (173, 216, 230),
            'gray': (192, 192, 192),
            'light_gray': (220, 220, 220),
            # 中文支持
            '白色': (255, 255, 255),
            '红色': (255, 0, 0),
            '蓝色': (67, 142, 219),
            '浅蓝色': (173, 216, 230),
            '灰色': (192, 192, 192),
            '浅灰色': (220, 220, 220),
            # 国际标准背景色
            '美国护照蓝': (51, 122, 183),
            '泰国签证蓝': (65, 105, 225),
            '欧盟护照灰': (240, 240, 240)
        }
        
        # 肤色检测范围 (HSV)
        self.skin_ranges = [
            # 肤色范围1 (偏黄)
            {'lower': np.array([0, 20, 70]), 'upper': np.array([20, 255, 255])},
            # 肤色范围2 (偏红)
            {'lower': np.array([170, 20, 70]), 'upper': np.array([180, 255, 255])}
        ]
        
        # 延迟初始化rembg（避免在子进程中导入失败）
        self.rembg_available = False
        self.rembg = None
        self.rembg_session = None
        self._rembg_initialized = False
        
        # 保存最后生成的mask（用于高级背景效果）
        self.last_mask = None
    
    def _ensure_rembg_initialized(self):
        """确保rembg已初始化（延迟加载）- 支持GPU加速"""
        if self._rembg_initialized:
            return
        
        self._rembg_initialized = True
        
        try:
            print("[DEBUG] 开始初始化rembg模型...")
            import time
            start_time = time.time()
            
            # 导入配置
            try:
                from config.config import USE_GPU, GPU_DEVICE_ID, AUTO_FALLBACK_TO_CPU
            except ImportError:
                USE_GPU = True
                GPU_DEVICE_ID = 0
                AUTO_FALLBACK_TO_CPU = True
            
            # 检测GPU可用性（在重定向之前）
            gpu_available = False
            device_info = "CPU"
            
            if USE_GPU:
                try:
                    import torch
                    if torch.cuda.is_available():
                        gpu_available = True
                        device_info = f"GPU (CUDA {torch.version.cuda}, Device {GPU_DEVICE_ID})"
                        # 设置GPU设备
                        import os
                        os.environ['CUDA_VISIBLE_DEVICES'] = str(GPU_DEVICE_ID)
                        print(f"[DEBUG] 检测到GPU，将使用GPU加速")
                    else:
                        print(f"[DEBUG] 未检测到GPU，将使用CPU")
                except Exception as e:
                    print(f"[DEBUG] GPU检测失败: {e}，将使用CPU")
            
            # 完全静默导入，避免子进程中的任何输出
            import sys
            import io
            import os
            
            # 保存原始的stderr和stdout
            old_stderr = sys.stderr
            old_stdout = sys.stdout
            
            # 重定向到null
            sys.stderr = open(os.devnull, 'w')
            sys.stdout = open(os.devnull, 'w')
            
            try:
                import rembg
                self.rembg = rembg
                
                # 创建rembg session，优先使用GPU
                if gpu_available:
                    try:
                        # 尝试使用GPU（CUDA Execution Provider）
                        self.rembg_session = rembg.new_session(
                            'u2net',
                            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
                        )
                    except Exception as e:
                        if AUTO_FALLBACK_TO_CPU:
                            self.rembg_session = rembg.new_session(
                                'u2net',
                                providers=['CPUExecutionProvider']
                            )
                            device_info = "CPU (GPU fallback)"
                        else:
                            raise
                else:
                    # 使用CPU
                    self.rembg_session = rembg.new_session(
                        'u2net',
                        providers=['CPUExecutionProvider']
                    )
                
                self.rembg_available = True
                
                # 恢复输出
                sys.stderr.close()
                sys.stdout.close()
                sys.stderr = old_stderr
                sys.stdout = old_stdout
                
                elapsed_time = time.time() - start_time
                print(f"[INFO] rembg (U2-Net) 已启用，运行设备: {device_info}，模型加载耗时: {elapsed_time:.2f}秒")
            except:
                # 恢复输出
                if sys.stderr != old_stderr:
                    sys.stderr.close()
                if sys.stdout != old_stdout:
                    sys.stdout.close()
                sys.stderr = old_stderr
                sys.stdout = old_stdout
                raise
                
        except ImportError:
            print("[WARNING] rembg未安装，将使用传统算法")
        except Exception as e:
            print(f"[WARNING] rembg初始化失败: {e}，将使用传统算法")
    
    def replace_background(self, image: np.ndarray, 
                          bg_color: Union[str, Tuple[int, int, int]], 
                          method: str = 'auto',
                          refine_edges: bool = False,
                          expand_pixels: int = 0,
                          use_alpha_matting: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        替换背景 - 使用rembg (U2-Net)高精度算法，支持Alpha Matte
        
        Args:
            image: 输入图像
            bg_color: 背景颜色（颜色名称或RGB值）
            method: 抠图方法 ('auto', 'rembg', 'traditional', 'grabcut', 'skin_detection', 'combined')
            refine_edges: 是否进行边缘优化（默认False，推荐直接用原始）
            expand_pixels: 边缘调整像素数（默认0，推荐不调整）
            use_alpha_matting: 是否启用Alpha Matte（默认True，提升边缘质量）
            
        Returns:
            tuple: (处理后的图像, 处理信息)
        """
        # 延迟初始化rembg
        self._ensure_rembg_initialized()
        
        # 解析背景颜色
        if isinstance(bg_color, str):
            if bg_color not in self.background_colors:
                raise ValueError(f"不支持的背景颜色: {bg_color}")
            bg_rgb = self.background_colors[bg_color]
        else:
            bg_rgb = bg_color
        
        # 选择最佳方法 - 只使用rembg
        if method == 'auto':
            method = 'rembg'
        
        # 精细模式 - 使用改进的边缘处理
        if method == 'refined':
            try:
                print("[INFO] 使用改进精细模式进行背景替换（保持颜色稳定）")
                result, process_info = self._improved_refined_replace_background(image, bg_rgb)
                process_info['method_used'] = 'improved_refined'
                return result, process_info
            except Exception as e:
                print(f"[WARNING] 改进精细模式处理失败: {e}")
                print("[INFO] 切换到rembg模式")
                method = 'rembg'
        
        # 使用rembg
        if method == 'rembg' and self.rembg_available:
            try:
                print("[INFO] 使用rembg (U2-Net) 进行背景替换")
                result, process_info = self._rembg_replace_background(image, bg_rgb, refine_edges=False, expand_pixels=0, use_alpha_matting=use_alpha_matting)
                process_info['method_used'] = 'rembg_raw'
                return result, process_info
            except Exception as e:
                print(f"[WARNING] rembg处理失败: {e}")
                raise
        
        # 如果method是traditional，报错
        if method == 'traditional':
            raise ValueError("传统算法已废弃")
        
        # 其他方法也报错
        raise ValueError(f"不支持的方法: {method}")
    
    def _select_best_method(self, image: np.ndarray) -> str:
        """自动选择最佳抠图方法 - 只返回rembg"""
        return 'rembg'
    
    def _generate_mask(self, image: np.ndarray, method: str) -> Tuple[np.ndarray, Dict]:
        """生成分割mask"""
        mask_info = {'method_used': method}
        
        if method == 'rembg' and self.rembg_available:
            mask = self._rembg_segment(image, use_alpha_matting=True)
            mask_info['ai_model'] = 'u2net'
        else:
            # 默认使用rembg
            mask = self._rembg_segment(image, use_alpha_matting=True)
            mask_info['ai_model'] = 'u2net'
        
        return mask, mask_info
    
    def _rembg_segment(self, image: np.ndarray, post_process: bool = False, 
                      expand_pixels: int = 0, smooth_edges: bool = False,
                      use_alpha_matting: bool = True) -> np.ndarray:
        """
        使用rembg进行AI抠图 - 优化版，支持Alpha Matte和GPU加速
        
        Args:
            image: 输入图像
            post_process: 是否进行后处理优化（默认False，直接用原始结果）
            expand_pixels: 边缘扩展像素数（默认0，不调整）
            smooth_edges: 是否平滑边缘（默认False，保持原始）
            use_alpha_matting: 是否启用Alpha Matte（默认True，提升边缘质量）
        """
        try:
            from PIL import Image
            
            # GPU内存管理
            try:
                from config.config import USE_GPU, AUTO_FALLBACK_TO_CPU
            except ImportError:
                USE_GPU = True
                AUTO_FALLBACK_TO_CPU = True
            
            if USE_GPU:
                try:
                    import torch
                    if torch.cuda.is_available():
                        # 清理GPU缓存，避免内存不足
                        torch.cuda.empty_cache()
                except:
                    pass
            
            # 转换为PIL图像
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            try:
                # AI抠图 - 使用U2-Net模型，启用Alpha Matte提升边缘质量
                # 优化参数：针对人像优化
                if use_alpha_matting:
                    output = self.rembg.remove(
                        pil_image, 
                        session=self.rembg_session,
                        alpha_matting=True,
                        alpha_matting_foreground_threshold=235,
                        alpha_matting_background_threshold=5,
                        alpha_matting_erode_size=15
                    )
                else:
                    output = self.rembg.remove(pil_image, session=self.rembg_session)
                    
            except RuntimeError as e:
                # 处理GPU内存不足的情况
                if "out of memory" in str(e).lower() or "cuda" in str(e).lower():
                    print(f"[WARNING] GPU内存不足: {e}")
                    
                    if AUTO_FALLBACK_TO_CPU:
                        print("[INFO] 自动降级到CPU处理...")
                        
                        # 清理GPU内存
                        try:
                            import torch
                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()
                        except:
                            pass
                        
                        # 重新创建CPU session
                        import rembg
                        self.rembg_session = rembg.new_session(
                            'u2net',
                            providers=['CPUExecutionProvider']
                        )
                        
                        # 使用CPU重试
                        if use_alpha_matting:
                            output = self.rembg.remove(
                                pil_image, 
                                session=self.rembg_session,
                                alpha_matting=True,
                                alpha_matting_foreground_threshold=235,
                                alpha_matting_background_threshold=5,
                                alpha_matting_erode_size=15
                            )
                        else:
                            output = self.rembg.remove(pil_image, session=self.rembg_session)
                    else:
                        raise
                else:
                    raise
            
            # 转换回OpenCV格式并提取alpha通道作为mask
            output_array = np.array(output)
            if output_array.shape[2] == 4:  # RGBA
                mask = output_array[:, :, 3]  # Alpha通道
            else:
                # 如果没有alpha通道，使用亮度作为mask
                gray = cv2.cvtColor(output_array, cv2.COLOR_RGB2GRAY)
                mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)[1]
            
            # 只做最基本的二值化，不做任何其他处理
            _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
            
            print(f"[INFO] rembg分割完成（使用原始输出），mask覆盖率: {np.sum(mask > 128) / mask.size * 100:.1f}%")
            return mask
        except Exception as e:
            print(f"[ERROR] rembg抠图失败: {e}")
            # 回退到肤色检测
            return self._skin_detection_segment(image)
    
    def _optimize_rembg_mask(self, mask: np.ndarray, expand_pixels: int = -3, 
                            smooth_edges: bool = True) -> np.ndarray:
        """
        优化rembg生成的mask，解决边缘问题
        
        Args:
            mask: 原始mask
            expand_pixels: 边缘调整像素数（负数=收缩解决白边，正数=扩展解决黑边）
            smooth_edges: 是否平滑边缘
        """
        print(f"[DEBUG] 优化rembg mask - 调整: {expand_pixels}px, 平滑: {smooth_edges}")
        
        # 1. 先填充小孔洞
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
        
        # 2. 分离头发区域和身体区域
        hair_mask, body_mask = self._separate_hair_and_body(mask)
        
        # 3. 对身体区域进行收缩（解决白边）
        if expand_pixels != 0:
            kernel_size = abs(expand_pixels) * 2 + 1
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            
            if expand_pixels > 0:
                # 扩展（解决黑边）
                iterations = max(1, expand_pixels // 3)
                body_mask = cv2.dilate(body_mask, kernel, iterations=iterations)
                print(f"[DEBUG] 身体边缘扩展完成，扩展了 {expand_pixels} 像素")
            else:
                # 收缩（解决白边）
                iterations = max(1, abs(expand_pixels) // 3)
                body_mask = cv2.erode(body_mask, kernel, iterations=iterations)
                print(f"[DEBUG] 身体边缘收缩完成，收缩了 {abs(expand_pixels)} 像素")
        
        # 4. 对头发区域也进行收缩（解决白色残留）
        # 头发区域的白色残留说明 rembg 的 mask 不准确，需要收缩而不是扩展
        hair_shrink = 1  # 头发区域收缩3像素（解决白色残留）
        kernel_hair = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        hair_mask = cv2.erode(hair_mask, kernel_hair, iterations=hair_shrink)
        print(f"[DEBUG] 头发区域收缩 {hair_shrink} 像素（解决白色残留）")
        
        # 5. 合并头发和身体mask
        mask = cv2.bitwise_or(hair_mask, body_mask)
        
        # 6. 再次填充可能产生的小孔洞
        kernel_close2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close2)
        
        # 7. 边缘平滑
        if smooth_edges:
            # 轻微平滑，保留头发细节
            mask = cv2.GaussianBlur(mask, (3, 3), 0.5)
            _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
            print(f"[DEBUG] 边缘平滑完成（保留头发细节）")
        
        return mask
    
    def _separate_hair_and_body(self, mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        分离头发区域和身体区域
        
        Returns:
            tuple: (头发mask, 身体mask)
        """
        h, w = mask.shape
        
        # 找到mask的边界框
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return mask.copy(), mask.copy()
        
        # 找到最大轮廓
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, cw, ch = cv2.boundingRect(largest_contour)
        
        # 头发区域：上部35%（适中的头发区域范围）
        hair_height = int(ch * 0.25)
        hair_mask = np.zeros_like(mask)
        hair_mask[y:y+hair_height, x:x+cw] = mask[y:y+hair_height, x:x+cw]
        
        # 身体区域：下部65%
        body_mask = np.zeros_like(mask)
        body_mask[y+hair_height:y+ch, x:x+cw] = mask[y+hair_height:y+ch, x:x+cw]
        
        # 添加一些重叠区域，避免断层
        overlap_height = int(hair_height * 0.2)
        if overlap_height > 0:
            overlap_region = mask[y+hair_height:y+hair_height+overlap_height, x:x+cw]
            hair_mask[y+hair_height:y+hair_height+overlap_height, x:x+cw] = cv2.bitwise_or(
                hair_mask[y+hair_height:y+hair_height+overlap_height, x:x+cw],
                overlap_region
            )
        
        print(f"[DEBUG] 分离头发和身体区域 - 头发区域高度: {hair_height}px")
        
        return hair_mask, body_mask
    
    def _rembg_replace_background(self, image: np.ndarray, bg_color: Tuple[int, int, int], 
                                 refine_edges: bool = False, expand_pixels: int = 0, 
                                 use_alpha_matting: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        使用rembg进行完整的背景替换 - 直接使用原始输出
        
        Args:
            image: 输入图像
            bg_color: 背景颜色
            refine_edges: 是否进行边缘优化（默认False，直接用原始）
            expand_pixels: 边缘扩展像素数（默认0，不调整）
            use_alpha_matting: 是否启用Alpha Matte（默认True，提升边缘质量）
        """
        import time
        start_time = time.time()
        
        # 1. 使用rembg分割（不做后处理，直接用原始输出）
        mask = self._rembg_segment(image, post_process=False, 
                                   expand_pixels=0, 
                                   smooth_edges=False,
                                   use_alpha_matting=True)
        
        # 2. 应用背景（不做任何额外处理）
        result = self._apply_background(image, mask, bg_color)
        
        # 3. 质量评估
        quality_info = self._evaluate_mask_quality(mask)
        
        processing_time = time.time() - start_time
        
        # 4. 处理信息
        process_info = {
            'method': 'rembg',
            'model': 'U2-Net',
            'background_color': bg_color,
            'edges_refined': False,
            'expand_pixels': 0,
            'processing_time': processing_time,
            'mask_quality': quality_info,
            'mask_pixels': np.sum(mask > 128),
            'total_pixels': mask.size,
            'note': '使用rembg原始输出，未做额外处理'
        }
        
        print(f"[INFO] rembg背景替换完成（原始输出），耗时: {processing_time:.2f}秒")
        
        return result, process_info
    
    def _grabcut_segment(self, image: np.ndarray) -> np.ndarray:
        """使用GrabCut算法进行抠图"""
        h, w = image.shape[:2]
        
        # 创建初始mask（假设中心区域是前景）
        mask = np.zeros((h, w), np.uint8)
        
        # 定义前景区域（中心80%区域）
        margin_h = int(h * 0.1)
        margin_w = int(w * 0.1)
        rect = (margin_w, margin_h, w - 2*margin_w, h - 2*margin_h)
        
        # 初始化前景和背景模型
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        # 执行GrabCut
        cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        
        # 生成最终mask
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        final_mask = mask2 * 255
        
        return final_mask
    
    def _skin_detection_segment(self, image: np.ndarray) -> np.ndarray:
        """基于肤色检测的分割 - 保守策略，避免误判衣服"""
        print("[DEBUG] 开始保守肤色检测分割...")
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        h, w = image.shape[:2]
        
        # 更保守的HSV肤色范围 - 避免误判衣服
        hsv_ranges = [
            # 主要肤色范围（更严格）
            {'lower': np.array([0, 30, 60]), 'upper': np.array([20, 150, 255])},
            # 偏红肤色（更严格）
            {'lower': np.array([160, 30, 60]), 'upper': np.array([180, 150, 255])},
        ]
        
        # 更严格的YCrCb肤色范围
        ycrcb_lower = np.array([0, 140, 90])  # 提高下限
        ycrcb_upper = np.array([255, 165, 120])  # 降低上限
        
        # HSV肤色检测
        hsv_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for i, skin_range in enumerate(hsv_ranges):
            skin_mask = cv2.inRange(hsv, skin_range['lower'], skin_range['upper'])
            hsv_mask = cv2.bitwise_or(hsv_mask, skin_mask)
            print(f"[DEBUG] 保守HSV肤色范围 {i+1} 检测到像素: {np.sum(skin_mask > 0)}")
        
        # YCrCb肤色检测
        ycrcb_mask = cv2.inRange(ycrcb, ycrcb_lower, ycrcb_upper)
        print(f"[DEBUG] 保守YCrCb肤色检测到像素: {np.sum(ycrcb_mask > 0)}")
        
        # 使用交集提高精度，避免误判
        combined_mask = cv2.bitwise_and(hsv_mask, ycrcb_mask)
        print(f"[DEBUG] 保守组合肤色mask像素数: {np.sum(combined_mask > 0)}")
        
        # 如果交集太小，使用更宽松的策略
        if np.sum(combined_mask > 0) < h * w * 0.02:  # 少于2%
            print("[DEBUG] 交集太小，使用HSV mask")
            combined_mask = hsv_mask
        
        # 形态学操作去噪和连接
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
        
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel_close)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel_open)
        
        print(f"[DEBUG] 保守形态学处理后mask像素数: {np.sum(combined_mask > 0)}")
        
        # 扩展到包含头发和衣服
        final_mask = self._conservative_extend_to_person(image, combined_mask)
        
        print(f"[DEBUG] 保守最终mask像素数: {np.sum(final_mask > 0)}")
        print(f"[DEBUG] 保守mask覆盖率: {np.sum(final_mask > 0) / (h * w) * 100:.1f}%")
        
        return final_mask
    
    def _conservative_extend_to_person(self, image: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
        """
        保守的人物扩展策略 - 避免误判衣服为背景
        """
        h, w = image.shape[:2]
        
        # 如果没有检测到肤色，使用保守的中心区域检测
        if np.sum(skin_mask) == 0:
            print("[DEBUG] 未检测到肤色，使用保守中心区域检测")
            return self._conservative_fallback_detection(image)
        
        # 找到肤色区域的边界框
        contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return self._conservative_fallback_detection(image)
        
        # 找到最大的肤色区域
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, cw, ch = cv2.boundingRect(largest_contour)
        
        print(f"[DEBUG] 保守策略 - 人脸区域: ({x}, {y}, {cw}, {ch})")
        
        # 保守的扩展策略 - 避免过度扩展
        face_area_ratio = (cw * ch) / (w * h)
        print(f"[DEBUG] 保守策略 - 人脸面积比例: {face_area_ratio:.3f}")
        
        # 更保守的扩展比例
        if face_area_ratio > 0.15:  # 大特写 - 小幅扩展
            expand_w_ratio = 0.4
            expand_h_ratio = 0.8
            body_extend_ratio = 1.2
        elif face_area_ratio > 0.08:  # 半身照 - 中等扩展
            expand_w_ratio = 0.6
            expand_h_ratio = 1.2
            body_extend_ratio = 1.8
        else:  # 全身照 - 适度扩展
            expand_w_ratio = 0.8
            expand_h_ratio = 1.5
            body_extend_ratio = 2.2
        
        # 计算保守扩展区域
        expand_w = int(cw * expand_w_ratio)
        expand_h = int(ch * expand_h_ratio)
        
        # 头部区域（包含头发，但更保守）
        head_x1 = max(0, x - expand_w // 3)  # 减少左右扩展
        head_y1 = max(0, y - int(ch * 0.3))  # 减少向上扩展
        head_x2 = min(w, x + cw + expand_w // 3)
        head_y2 = y + ch
        
        # 身体区域（更保守的扩展）
        body_x1 = max(0, x - expand_w // 2)  # 减少左右扩展
        body_y1 = head_y2
        body_x2 = min(w, x + cw + expand_w // 2)
        body_y2 = min(h, y + ch + int(ch * body_extend_ratio))
        
        print(f"[DEBUG] 保守头部区域: ({head_x1}, {head_y1}) 到 ({head_x2}, {head_y2})")
        print(f"[DEBUG] 保守身体区域: ({body_x1}, {body_y1}) 到 ({body_x2}, {body_y2})")
        
        # 创建保守的人物mask
        final_mask = np.zeros((h, w), dtype=np.uint8)
        
        # 1. 头部区域处理 - 基于肤色扩展
        if head_y2 > head_y1 and head_x2 > head_x1:
            head_roi = image[head_y1:head_y2, head_x1:head_x2]
            head_skin_mask = skin_mask[head_y1:head_y2, head_x1:head_x2]
            
            # 保守的头部扩展 - 主要基于肤色相似性
            head_mask = self._conservative_head_expansion(head_roi, head_skin_mask)
            final_mask[head_y1:head_y2, head_x1:head_x2] = cv2.bitwise_or(
                final_mask[head_y1:head_y2, head_x1:head_x2], head_mask
            )
        
        # 2. 身体区域处理 - 基于连通性，避免误判衣服
        if body_y2 > body_y1 and body_x2 > body_x1:
            body_roi = image[body_y1:body_y2, body_x1:body_x2]
            
            # 保守的身体检测 - 只扩展与头部连通的区域
            body_mask = self._conservative_body_expansion(body_roi, head_mask if head_y2 > head_y1 else None)
            final_mask[body_y1:body_y2, body_x1:body_x2] = cv2.bitwise_or(
                final_mask[body_y1:body_y2, body_x1:body_x2], body_mask
            )
        
        # 3. 与原始肤色mask合并
        final_mask = cv2.bitwise_or(skin_mask, final_mask)
        
        # 4. 保守的后处理 - 避免过度平滑
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))  # 减小核大小
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)
        
        # 5. 轻微的边缘平滑
        final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0)
        _, final_mask = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)
        
        print(f"[DEBUG] 保守扩展完成 - mask像素数: {np.sum(final_mask > 0)}")
        print(f"[DEBUG] 保守覆盖率: {np.sum(final_mask > 0) / (h * w) * 100:.1f}%")
        
        return final_mask
    
    def _conservative_fallback_detection(self, image: np.ndarray) -> np.ndarray:
        """保守的备用检测 - 只使用中心区域"""
        h, w = image.shape[:2]
        
        # 使用更小的中心区域，避免误判
        margin_w = int(w * 0.25)  # 左右各留25%
        margin_h = int(h * 0.2)   # 上下各留20%
        
        mask = np.zeros((h, w), dtype=np.uint8)
        mask[margin_h:h-margin_h, margin_w:w-margin_w] = 255
        
        print(f"[DEBUG] 保守备用检测 - 中心区域: ({margin_w}, {margin_h}) 到 ({w-margin_w}, {h-margin_h})")
        
        return mask
    
    def _conservative_head_expansion(self, head_roi: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
        """保守的头部扩展 - 主要基于肤色相似性"""
        h, w = head_roi.shape[:2]
        
        if np.sum(skin_mask) == 0:
            return skin_mask
        
        # 基于肤色的保守扩展
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))  # 减小扩展核
        expanded_skin = cv2.dilate(skin_mask, kernel, iterations=1)  # 减少迭代次数
        
        # 简单的头发检测 - 只检测明显的深色区域
        hsv = cv2.cvtColor(head_roi, cv2.COLOR_BGR2HSV)
        
        # 更严格的头发检测范围
        hair_lower = np.array([0, 0, 0])
        hair_upper = np.array([180, 80, 60])  # 降低亮度上限
        
        hair_mask = cv2.inRange(hsv, hair_lower, hair_upper)
        
        # 只保留与肤色区域相邻的头发
        hair_mask = cv2.bitwise_and(hair_mask, cv2.bitwise_not(skin_mask))
        
        # 只保留头部上方的头发
        hair_mask[h//2:, :] = 0  # 清除下半部分
        
        # 组合头部mask
        head_mask = cv2.bitwise_or(expanded_skin, hair_mask)
        
        return head_mask
    
    def _conservative_body_expansion(self, body_roi: np.ndarray, head_reference: np.ndarray = None) -> np.ndarray:
        """保守的身体扩展 - 避免误判衣服"""
        h, w = body_roi.shape[:2]
        
        # 如果身体区域很小，直接返回空mask
        if h < 50 or w < 50:
            return np.zeros((h, w), dtype=np.uint8)
        
        # 使用简单的中心区域作为身体
        # 避免复杂的颜色检测，减少误判
        center_mask = np.zeros((h, w), dtype=np.uint8)
        
        # 只使用中心60%的区域作为身体
        margin_w = int(w * 0.2)
        margin_h = int(h * 0.1)
        
        center_mask[margin_h:h-margin_h, margin_w:w-margin_w] = 255
        
        # 形态学处理使边缘更自然
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        center_mask = cv2.morphologyEx(center_mask, cv2.MORPH_CLOSE, kernel)
        
        return center_mask
    
    def _advanced_person_detection(self, image: np.ndarray) -> np.ndarray:
        """先进的无监督人物检测 - 当肤色检测失败时使用"""
        h, w = image.shape[:2]
        
        print("[DEBUG] 启动先进无监督人物检测")
        
        # 1. 多尺度边缘检测
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 不同尺度的边缘检测
        edges_fine = cv2.Canny(gray, 50, 150)
        edges_coarse = cv2.Canny(gray, 30, 100)
        edges_combined = cv2.bitwise_or(edges_fine, edges_coarse)
        
        # 2. 基于显著性的前景检测
        saliency_mask = self._compute_saliency_mask(image)
        
        # 3. 基于颜色聚类的分割
        cluster_mask = self._advanced_color_clustering(image)
        
        # 4. 智能组合多种方法
        # 边缘填充
        contours, _ = cv2.findContours(edges_combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        edge_filled = np.zeros_like(gray)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > h * w * 0.05:  # 面积大于5%
                cv2.fillPoly(edge_filled, [contour], 255)
        
        # 组合所有方法
        combined_score = (
            edge_filled.astype(np.float32) * 0.3 +
            saliency_mask.astype(np.float32) * 0.4 +
            cluster_mask.astype(np.float32) * 0.3
        )
        
        # 阈值化
        _, final_mask = cv2.threshold(combined_score.astype(np.uint8), 127, 255, cv2.THRESH_BINARY)
        
        # 形态学处理
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)
        
        print(f"[DEBUG] 无监督检测完成 - 覆盖率: {np.sum(final_mask > 0) / (h * w) * 100:.1f}%")
        
        return final_mask
    
    def _advanced_head_segmentation(self, head_roi: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
        """先进的头部分割 - 包含头发丝处理"""
        h, w = head_roi.shape[:2]
        
        # 1. 基于肤色的初始分割
        if np.sum(skin_mask) > 0:
            # 扩展肤色区域到头发
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
            expanded_skin = cv2.dilate(skin_mask, kernel, iterations=2)
        else:
            expanded_skin = np.zeros((h, w), dtype=np.uint8)
        
        # 2. 头发检测 - 基于颜色和纹理
        hair_mask = self._detect_hair_region(head_roi, expanded_skin)
        
        # 3. 组合头部mask
        head_mask = cv2.bitwise_or(expanded_skin, hair_mask)
        
        # 4. 细节优化 - 头发丝处理
        head_mask = self._refine_hair_edges(head_roi, head_mask)
        
        return head_mask
    
    def _advanced_body_segmentation(self, body_roi: np.ndarray, head_reference: np.ndarray = None) -> np.ndarray:
        """先进的身体分割 - 衣服检测"""
        h, w = body_roi.shape[:2]
        
        # 1. 基于颜色一致性的衣服检测
        clothing_mask = self._detect_clothing_region(body_roi)
        
        # 2. 基于纹理的衣服检测
        texture_mask = self._detect_clothing_texture(body_roi)
        
        # 3. 组合身体mask
        body_mask = cv2.bitwise_or(clothing_mask, texture_mask)
        
        # 4. 形态学处理
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        body_mask = cv2.morphologyEx(body_mask, cv2.MORPH_CLOSE, kernel)
        
        return body_mask
    
    def _detect_hair_region(self, head_roi: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
        """检测头发区域"""
        h, w = head_roi.shape[:2]
        
        # 转换到HSV进行头发检测
        hsv = cv2.cvtColor(head_roi, cv2.COLOR_BGR2HSV)
        
        # 头发通常是低饱和度、低亮度
        hair_lower = np.array([0, 0, 0])
        hair_upper = np.array([180, 100, 80])
        
        hair_mask = cv2.inRange(hsv, hair_lower, hair_upper)
        
        # 排除肤色区域
        hair_mask = cv2.bitwise_and(hair_mask, cv2.bitwise_not(skin_mask))
        
        # 只保留头部上方区域
        hair_mask[:h//2, :] = hair_mask[:h//2, :]  # 保留上半部分
        hair_mask[h//2:, :] = 0  # 清除下半部分
        
        return hair_mask
    
    def _detect_clothing_region(self, body_roi: np.ndarray) -> np.ndarray:
        """检测衣服区域"""
        h, w = body_roi.shape[:2]
        
        # 使用K-means聚类检测主要颜色区域
        data = body_roi.reshape((-1, 3)).astype(np.float32)
        
        # K-means聚类
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(data, 3, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # 重塑标签
        labels = labels.reshape((h, w))
        
        # 选择最大的聚类作为衣服
        unique_labels, counts = np.unique(labels, return_counts=True)
        dominant_label = unique_labels[np.argmax(counts)]
        
        clothing_mask = (labels == dominant_label).astype(np.uint8) * 255
        
        return clothing_mask
    
    def _detect_clothing_texture(self, body_roi: np.ndarray) -> np.ndarray:
        """基于纹理检测衣服"""
        gray = cv2.cvtColor(body_roi, cv2.COLOR_BGR2GRAY)
        
        # 计算局部二值模式 (简化版)
        # 使用方差滤波检测纹理
        kernel = np.ones((9, 9), np.float32) / 81
        mean_filtered = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        sqr_filtered = cv2.filter2D((gray.astype(np.float32))**2, -1, kernel)
        variance = sqr_filtered - mean_filtered**2
        
        # 中等纹理区域可能是衣服
        texture_mask = ((variance > 50) & (variance < 500)).astype(np.uint8) * 255
        
        return texture_mask
    
    def _compute_saliency_mask(self, image: np.ndarray) -> np.ndarray:
        """计算显著性mask"""
        # 简化的显著性检测
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 使用高斯模糊计算显著性
        blurred = cv2.GaussianBlur(gray, (0, 0), 2.0)
        saliency = cv2.absdiff(gray, blurred)
        
        # 阈值化
        _, saliency_mask = cv2.threshold(saliency, 30, 255, cv2.THRESH_BINARY)
        
        return saliency_mask
    
    def _advanced_color_clustering(self, image: np.ndarray) -> np.ndarray:
        """先进的颜色聚类"""
        h, w = image.shape[:2]
        
        # 转换到LAB色彩空间进行更好的聚类
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        data = lab.reshape((-1, 3)).astype(np.float32)
        
        # K-means聚类
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(data, 4, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # 重塑标签
        labels = labels.reshape((h, w))
        
        # 选择中心区域的主要聚类作为前景
        center_region = labels[h//4:3*h//4, w//4:3*w//4]
        unique_labels, counts = np.unique(center_region, return_counts=True)
        dominant_label = unique_labels[np.argmax(counts)]
        
        cluster_mask = (labels == dominant_label).astype(np.uint8) * 255
        
        return cluster_mask
    
    def _modnet_style_edge_refinement(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """MODNet风格的边缘优化"""
        # 1. 三边滤波平滑边缘
        refined_mask = cv2.bilateralFilter(mask, 9, 75, 75)
        
        # 2. 基于图像梯度的边缘优化
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # 在强边缘处收缩mask，在弱边缘处扩展
        edge_threshold = np.percentile(gradient_magnitude, 70)
        strong_edges = (gradient_magnitude > edge_threshold).astype(np.uint8)
        
        # 形态学操作
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        # 在强边缘处腐蚀
        mask_eroded = cv2.erode(refined_mask, kernel_small, iterations=1)
        # 在弱边缘处膨胀
        mask_dilated = cv2.dilate(refined_mask, kernel_small, iterations=1)
        
        # 组合结果
        final_mask = np.where(strong_edges, mask_eroded, mask_dilated)
        
        # 3. 最终平滑
        final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0)
        _, final_mask = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)
        
        return final_mask
    
    def _refine_hair_edges(self, head_roi: np.ndarray, hair_mask: np.ndarray) -> np.ndarray:
        """优化头发边缘 - 处理头发丝"""
        # 使用形态学梯度检测头发边缘
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        gradient = cv2.morphologyEx(hair_mask, cv2.MORPH_GRADIENT, kernel)
        
        # 在梯度区域应用更精细的处理
        refined_mask = hair_mask.copy()
        
        # 使用双边滤波平滑边缘
        refined_mask = cv2.bilateralFilter(refined_mask, 5, 50, 50)
        
        return refined_mask
    
    def _improved_region_growing(self, image: np.ndarray, seed_mask: np.ndarray) -> np.ndarray:
        """改进的区域增长算法"""
        h, w = image.shape[:2]
        
        # 转换到LAB色彩空间进行更好的颜色比较
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
        
        # 计算种子区域的颜色统计
        seed_pixels = lab[seed_mask > 0]
        if len(seed_pixels) == 0:
            return np.zeros((h, w), dtype=np.uint8)
        
        mean_color = np.mean(seed_pixels, axis=0)
        std_color = np.std(seed_pixels, axis=0)
        
        print(f"[DEBUG] 种子区域颜色统计 - 均值: {mean_color}, 标准差: {std_color}")
        
        # 自适应阈值 - 根据颜色变化调整
        base_threshold = np.mean(std_color) * 2.5
        adaptive_threshold = max(15, min(40, base_threshold))
        
        print(f"[DEBUG] 区域增长阈值: {adaptive_threshold:.1f}")
        
        # 计算颜色距离
        color_diff = np.sqrt(np.sum((lab - mean_color) ** 2, axis=2))
        region_mask = (color_diff < adaptive_threshold).astype(np.uint8) * 255
        
        # 形态学操作连接相近区域
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        region_mask = cv2.morphologyEx(region_mask, cv2.MORPH_CLOSE, kernel)
        
        return region_mask
    
    def _edge_texture_segment(self, image: np.ndarray) -> np.ndarray:
        """基于边缘和纹理的分割"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. 边缘检测
        edges = cv2.Canny(gray, 30, 80)
        
        # 2. 纹理分析 - 使用局部二值模式
        # 简化的纹理检测：使用方差滤波
        kernel = np.ones((9, 9), np.float32) / 81
        mean_filtered = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        sqr_mean_filtered = cv2.filter2D((gray.astype(np.float32))**2, -1, kernel)
        texture_variance = sqr_mean_filtered - mean_filtered**2
        
        # 3. 组合边缘和纹理信息
        # 低纹理区域（如皮肤、衣服）更可能是前景
        texture_mask = (texture_variance < np.percentile(texture_variance, 70)).astype(np.uint8) * 255
        
        # 边缘膨胀以连接区域
        edge_dilated = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
        
        # 填充边缘围成的区域
        contours, _ = cv2.findContours(edge_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        edge_filled = np.zeros_like(gray)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # 过滤小区域
                cv2.fillPoly(edge_filled, [contour], 255)
        
        # 组合纹理和边缘信息
        combined_mask = cv2.bitwise_or(texture_mask, edge_filled)
        
        return combined_mask
    
    def _color_clustering_segment(self, image: np.ndarray, seed_mask: np.ndarray) -> np.ndarray:
        """基于颜色聚类的分割"""
        h, w = image.shape[:2]
        
        # 将图像重塑为像素向量
        pixels = image.reshape(-1, 3).astype(np.float32)
        
        # 使用K-means聚类（简化版本，使用固定K=4）
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(pixels, 4, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # 重塑标签回图像形状
        labels = labels.reshape(h, w)
        
        # 找到种子区域主要属于哪个聚类
        seed_labels = labels[seed_mask > 0]
        if len(seed_labels) == 0:
            return np.zeros((h, w), dtype=np.uint8)
        
        # 统计种子区域的聚类分布
        unique_labels, counts = np.unique(seed_labels, return_counts=True)
        dominant_labels = unique_labels[counts > len(seed_labels) * 0.1]  # 占比超过10%的聚类
        
        print(f"[DEBUG] 主要聚类标签: {dominant_labels}")
        
        # 创建基于聚类的mask
        cluster_mask = np.zeros((h, w), dtype=np.uint8)
        for label in dominant_labels:
            cluster_mask[labels == label] = 255
        
        return cluster_mask
    
    def _combine_masks(self, masks: list) -> np.ndarray:
        """智能组合多个mask"""
        if not masks:
            return np.zeros((100, 100), dtype=np.uint8)
        
        # 计算每个mask的权重（基于覆盖率和连通性）
        weights = []
        for mask in masks:
            coverage = np.sum(mask > 0) / mask.size
            num_components = cv2.connectedComponents(mask)[0] - 1
            # 权重 = 覆盖率 * 连通性因子
            weight = coverage * max(0.1, 1.0 / max(1, num_components - 1))
            weights.append(weight)
        
        print(f"[DEBUG] Mask权重: {weights}")
        
        # 加权组合
        combined = np.zeros_like(masks[0], dtype=np.float32)
        total_weight = sum(weights)
        
        if total_weight > 0:
            for mask, weight in zip(masks, weights):
                combined += mask.astype(np.float32) * (weight / total_weight)
        
        # 阈值化
        _, final_mask = cv2.threshold(combined.astype(np.uint8), 127, 255, cv2.THRESH_BINARY)
        
        return final_mask
    
    def _region_growing_segment(self, image: np.ndarray, seed_mask: np.ndarray) -> np.ndarray:
        """基于区域增长的分割"""
        h, w = image.shape[:2]
        
        # 转换为LAB色彩空间进行更好的颜色比较
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # 计算种子区域的平均颜色
        seed_pixels = lab[seed_mask > 0]
        if len(seed_pixels) == 0:
            return np.zeros((h, w), dtype=np.uint8)
        
        mean_color = np.mean(seed_pixels, axis=0)
        std_color = np.std(seed_pixels, axis=0)
        
        # 基于颜色距离创建mask
        color_diff = np.sqrt(np.sum((lab - mean_color) ** 2, axis=2))
        threshold = np.mean(std_color) * 3  # 3倍标准差作为阈值
        
        region_mask = (color_diff < threshold).astype(np.uint8) * 255
        
        return region_mask
    
    def _edge_based_segment(self, image: np.ndarray) -> np.ndarray:
        """基于边缘的分割"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 使用自适应阈值
        adaptive_thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # 反转阈值图像
        mask = 255 - adaptive_thresh
        
        # 形态学操作填充
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    def _extend_to_person(self, image: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
        """将肤色mask扩展到整个人物"""
        h, w = image.shape[:2]
        
        # 找到肤色区域的边界框
        contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return skin_mask
        
        # 找到最大的肤色区域
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, cw, ch = cv2.boundingRect(largest_contour)
        
        # 扩展区域以包含头发和衣服
        expand_ratio = 0.3
        expand_w = int(cw * expand_ratio)
        expand_h = int(ch * expand_ratio)
        
        # 计算扩展后的区域
        x1 = max(0, x - expand_w)
        y1 = max(0, y - expand_h)
        x2 = min(w, x + cw + expand_w)
        y2 = min(h, y + ch + expand_h)
        
        # 在扩展区域内进行更精细的分割
        roi = image[y1:y2, x1:x2]
        roi_mask = self._watershed_segment(roi)
        
        # 将结果合并到原mask
        extended_mask = skin_mask.copy()
        extended_mask[y1:y2, x1:x2] = cv2.bitwise_or(
            extended_mask[y1:y2, x1:x2], roi_mask
        )
        
        return extended_mask
    
    def _watershed_segment(self, image: np.ndarray) -> np.ndarray:
        """使用分水岭算法进行精细分割"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 阈值处理
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 噪声去除
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        
        # 确定背景区域
        sure_bg = cv2.dilate(opening, kernel, iterations=3)
        
        # 确定前景区域
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(), 255, 0)
        
        # 未知区域
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)
        
        # 标记
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0
        
        # 分水岭算法
        markers = cv2.watershed(image, markers)
        
        # 生成mask
        mask = np.zeros(gray.shape, dtype=np.uint8)
        mask[markers > 1] = 255
        
        return mask
    
    def _combined_segment(self, image: np.ndarray) -> np.ndarray:
        """组合多种方法的分割结果"""
        # 肤色检测
        skin_mask = self._skin_detection_segment(image)
        
        # GrabCut
        grabcut_mask = self._grabcut_segment(image)
        
        # 组合结果（取交集以提高精度）
        combined_mask = cv2.bitwise_and(skin_mask, grabcut_mask)
        
        # 如果交集太小，使用并集
        if np.sum(combined_mask) < np.sum(skin_mask) * 0.3:
            combined_mask = cv2.bitwise_or(skin_mask, grabcut_mask)
        
        return combined_mask
    
    def _refine_edges(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """边缘优化，处理头发丝等细节"""
        # 1. 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        refined_mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 2. 高斯模糊柔化边缘
        refined_mask = cv2.GaussianBlur(refined_mask, (3, 3), 0)
        
        # 3. 边缘检测和细化
        edges = cv2.Canny(image, 50, 150)
        
        # 4. 在边缘区域进行精细处理
        edge_dilated = cv2.dilate(edges, kernel, iterations=1)
        edge_regions = cv2.bitwise_and(refined_mask, edge_dilated)
        
        # 5. 对边缘区域使用双边滤波
        if np.sum(edge_regions) > 0:
            bilateral = cv2.bilateralFilter(refined_mask, 9, 75, 75)
            refined_mask = np.where(edge_regions > 0, bilateral, refined_mask)
        
        return refined_mask
    
    def _apply_background(self, image: np.ndarray, mask: np.ndarray, 
                         bg_color: Tuple[int, int, int]) -> np.ndarray:
        """应用新背景 - 修复版"""
        print(f"[DEBUG] 应用背景色: {bg_color}")
        print(f"[DEBUG] Mask统计 - 最小值: {np.min(mask)}, 最大值: {np.max(mask)}, 前景像素: {np.sum(mask > 0)}")
        
        # 确保mask是正确的格式
        if len(mask.shape) == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        
        # 归一化mask到0-1范围
        mask_norm = mask.astype(np.float32) / 255.0
        
        # 创建背景图像 - 注意BGR顺序
        bg_bgr = (bg_color[2], bg_color[1], bg_color[0])  # RGB转BGR
        background = np.full_like(image, bg_bgr, dtype=np.uint8)
        
        print(f"[DEBUG] 背景色BGR: {bg_bgr}")
        
        # 混合前景和背景
        result = np.zeros_like(image, dtype=np.float32)
        for c in range(3):
            # 前景 * mask + 背景 * (1 - mask)
            result[:, :, c] = (
                image[:, :, c].astype(np.float32) * mask_norm +
                background[:, :, c].astype(np.float32) * (1 - mask_norm)
            )
        
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        # 验证结果
        bg_pixels = np.sum(mask_norm < 0.1)
        print(f"[DEBUG] 背景像素数: {bg_pixels}, 背景区域平均色值: {np.mean(result[mask < 25], axis=0) if np.sum(mask < 25) > 0 else 'N/A'}")
        
        return result
    
    def _evaluate_mask_quality(self, mask: np.ndarray) -> Dict:
        """评估mask质量"""
        # 计算前景比例
        foreground_ratio = np.sum(mask > 0) / mask.size
        
        # 计算边缘平滑度
        edges = cv2.Canny(mask, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # 计算连通性
        num_labels, _ = cv2.connectedComponents(mask)
        
        return {
            'foreground_ratio': foreground_ratio,
            'edge_density': edge_density,
            'connected_components': num_labels - 1,  # 减去背景
            'quality_score': self._calculate_quality_score(
                foreground_ratio, edge_density, num_labels
            )
        }
    
    def _calculate_quality_score(self, fg_ratio: float, edge_density: float, 
                               num_components: int) -> float:
        """计算综合质量评分"""
        # 前景比例评分（20%-80%为最佳）
        if 0.2 <= fg_ratio <= 0.8:
            ratio_score = 1.0
        else:
            ratio_score = max(0, 1 - abs(fg_ratio - 0.5) * 2)
        
        # 边缘密度评分（适中为最佳）
        edge_score = max(0, 1 - abs(edge_density - 0.1) * 10)
        
        # 连通性评分（单一连通区域最佳）
        connectivity_score = max(0, 1 - (num_components - 1) * 0.2)
        
        # 综合评分
        quality_score = (ratio_score * 0.5 + edge_score * 0.3 + connectivity_score * 0.2)
        
        return min(1.0, max(0.0, quality_score))
    
    def get_available_colors(self) -> Dict:
        """获取可用的背景颜色"""
        return self.background_colors.copy()
    
    def preview_segmentation(self, image: np.ndarray, method: str = 'auto') -> np.ndarray:
        """预览分割效果"""
        # 选择方法
        if method == 'auto':
            method = self._select_best_method(image)
        
        # 生成mask
        mask, _ = self._generate_mask(image, method)
        
        # 创建预览图像（红色表示前景，蓝色表示背景）
        preview = image.copy()
        preview[mask == 0] = [255, 0, 0]  # 背景区域显示为红色
        
        # 混合原图和预览
        alpha = 0.3
        preview = cv2.addWeighted(image, 1 - alpha, preview, alpha, 0)
        
        return preview
    def _improved_refined_replace_background(self, image: np.ndarray, 
                                           bg_color: Tuple[int, int, int]) -> Tuple[np.ndarray, Dict]:
        """
        改进精细模式背景替换 - 专注边缘处理，保持颜色稳定
        
        Args:
            image: 输入图像
            bg_color: 背景颜色RGB值
            
        Returns:
            tuple: (处理后的图像, 处理信息)
        """
        print("[INFO] 开始改进精细模式处理...")
        
        # 确保rembg已初始化
        self._ensure_rembg_initialized()
        
        if not self.rembg_available:
            print("[WARNING] rembg不可用，切换到传统算法")
            return self._traditional_replace_background(image, bg_color)
        
        try:
            # 1. 使用rembg获取高质量初始mask
            print("[DEBUG] 步骤1: 使用AI模型生成初始mask")
            initial_mask = self._rembg_segment(image, use_alpha_matting=True)
            
            # 2. 改进的边缘优化 - 专注边缘，不改变颜色
            print("[DEBUG] 步骤2: 改进边缘优化处理")
            refined_mask = self._improved_edge_refinement(image, initial_mask)
            
            # 3. 头发丝边缘特殊处理
            print("[DEBUG] 步骤3: 头发丝边缘特殊处理")
            hair_refined_mask = self._hair_edge_refinement(image, refined_mask)
            
            # 4. 衣服边缘平滑处理
            print("[DEBUG] 步骤4: 衣服边缘平滑处理")
            final_mask = self._clothing_edge_smoothing(image, hair_refined_mask)
            
            # 5. 标准背景应用 - 不改变前景颜色
            print("[DEBUG] 步骤5: 标准背景应用")
            result = self._apply_background(image, final_mask, bg_color)
            
            # 6. 轻微后处理 - 只做边缘平滑
            print("[DEBUG] 步骤6: 轻微后处理")
            final_result = self._light_post_processing(result, final_mask)
            
            process_info = {
                'method': 'improved_refined',
                'method_used': 'edge_focused_refined',
                'background_color': bg_color,
                'edge_refined': True,
                'color_stable': True,
                'mask_quality': self._evaluate_mask_quality(final_mask),
                'mask': final_mask  # 保存mask供后续使用
            }
            
            print("[INFO] 改进精细模式处理完成")
            return final_result, process_info
            
        except Exception as e:
            print(f"[ERROR] 改进精细模式处理失败: {e}")
            import traceback
            traceback.print_exc()
            # 回退到普通rembg模式
            return self._rembg_replace_background(image, bg_color)
    
    def _improved_edge_refinement(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """改进的边缘优化 - 专注边缘质量"""
        # 1. 多尺度边缘检测
        edges_fine = cv2.Canny(mask, 30, 80)
        edges_coarse = cv2.Canny(mask, 50, 150)
        
        # 2. 边缘区域膨胀
        kernel_fine = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_coarse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
        edge_region_fine = cv2.dilate(edges_fine, kernel_fine, iterations=1)
        edge_region_coarse = cv2.dilate(edges_coarse, kernel_coarse, iterations=1)
        
        # 3. 分级边缘处理
        refined_mask = mask.copy().astype(np.float32)
        
        # 细边缘 - 轻微平滑
        if np.any(edge_region_fine):
            smooth_fine = cv2.GaussianBlur(mask, (3, 3), 0.8)
            fine_mask = edge_region_fine > 0
            refined_mask[fine_mask] = smooth_fine[fine_mask]
        
        # 粗边缘 - 中等平滑
        if np.any(edge_region_coarse):
            smooth_coarse = cv2.GaussianBlur(mask, (5, 5), 1.5)
            coarse_mask = (edge_region_coarse > 0) & (edge_region_fine == 0)
            refined_mask[coarse_mask] = smooth_coarse[coarse_mask]
        
        return refined_mask.astype(np.uint8)
    
    def _hair_edge_refinement(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """头发丝边缘特殊处理"""
        h, w = mask.shape
        hair_region = mask[:h//2, :]  # 头发区域
        
        if np.sum(hair_region) == 0:
            return mask
        
        # 1. 头发边缘检测
        hair_edges = cv2.Canny(hair_region, 20, 60)
        
        # 2. 轻微膨胀
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        hair_edge_region = cv2.dilate(hair_edges, kernel, iterations=1)
        
        # 3. 在头发边缘区域应用轻微平滑
        if np.any(hair_edge_region):
            smoothed_hair = cv2.GaussianBlur(hair_region, (3, 3), 1.0)
            result = mask.copy()
            edge_mask = hair_edge_region > 0
            result[:h//2, :][edge_mask] = smoothed_hair[edge_mask]
            return result
        
        return mask
    
    def _clothing_edge_smoothing(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """衣服边缘平滑处理"""
        h, w = mask.shape
        clothing_region = mask[h//2:, :]  # 衣服区域
        
        if np.sum(clothing_region) == 0:
            return mask
        
        # 1. 衣服边缘检测
        clothing_edges = cv2.Canny(clothing_region, 40, 120)
        
        # 2. 边缘区域膨胀
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
        clothing_edge_region = cv2.dilate(clothing_edges, kernel, iterations=1)
        
        # 3. 在衣服边缘区域应用平滑
        if np.any(clothing_edge_region):
            smoothed_clothing = cv2.GaussianBlur(clothing_region, (5, 5), 1.5)
            result = mask.copy()
            edge_mask = clothing_edge_region > 0
            result[h//2:, :][edge_mask] = smoothed_clothing[edge_mask]
            return result
        
        return mask
    
    def _light_post_processing(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """轻微后处理 - 只做边缘平滑，不改变颜色"""
        # 检测边缘
        edges = cv2.Canny(mask, 50, 150)
        edge_region = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
        
        # 在边缘区域应用非常轻微的平滑
        if np.any(edge_region):
            smoothed = cv2.GaussianBlur(image, (3, 3), 0.5)  # 修复：使用奇数核大小
            result = image.copy()
            edge_mask = edge_region > 0
            
            # 只应用30%的平滑效果
            result[edge_mask] = (image[edge_mask].astype(np.float32) * 0.7 + 
                               smoothed[edge_mask].astype(np.float32) * 0.3).astype(np.uint8)
            return result
        
        return image
    
    def _deep_edge_detection(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """深度边缘检测 - 结合多种边缘检测算法"""
        print("[DEBUG] 开始深度边缘检测...")
        
        # 1. 多尺度Canny边缘检测
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 超细边缘
        edges_ultra_fine = cv2.Canny(gray, 10, 30)
        # 细边缘
        edges_fine = cv2.Canny(gray, 30, 80)
        # 中等边缘
        edges_medium = cv2.Canny(gray, 50, 150)
        # 粗边缘
        edges_coarse = cv2.Canny(gray, 100, 200)
        
        # 2. Sobel边缘检测
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        sobel_edges = (sobel_magnitude > np.percentile(sobel_magnitude, 85)).astype(np.uint8) * 255
        
        # 3. Laplacian边缘检测
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_edges = (np.abs(laplacian) > np.percentile(np.abs(laplacian), 90)).astype(np.uint8) * 255
        
        # 4. 结构张量边缘检测
        structure_edges = self._structure_tensor_edges(gray)
        
        # 5. 智能边缘融合
        # 给不同类型的边缘分配权重
        edge_map = (
            edges_ultra_fine.astype(np.float32) * 0.4 +  # 超细边缘权重最高
            edges_fine.astype(np.float32) * 0.3 +
            edges_medium.astype(np.float32) * 0.15 +
            edges_coarse.astype(np.float32) * 0.05 +
            sobel_edges.astype(np.float32) * 0.05 +
            laplacian_edges.astype(np.float32) * 0.03 +
            structure_edges.astype(np.float32) * 0.02
        )
        
        # 6. 只保留前景区域的边缘
        mask_dilated = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
        edge_map = edge_map * (mask_dilated.astype(np.float32) / 255.0)
        
        # 7. 归一化和阈值化
        edge_map = np.clip(edge_map, 0, 255).astype(np.uint8)
        _, edge_map = cv2.threshold(edge_map, 30, 255, cv2.THRESH_BINARY)
        
        print(f"[DEBUG] 深度边缘检测完成，检测到边缘像素: {np.sum(edge_map > 0)}")
        return edge_map
    
    def _structure_tensor_edges(self, gray: np.ndarray) -> np.ndarray:
        """结构张量边缘检测"""
        # 计算梯度
        Ix = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        Iy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # 结构张量分量
        Ixx = cv2.GaussianBlur(Ix * Ix, (3, 3), 1.0)
        Iyy = cv2.GaussianBlur(Iy * Iy, (3, 3), 1.0)
        Ixy = cv2.GaussianBlur(Ix * Iy, (3, 3), 1.0)
        
        # 计算特征值
        trace = Ixx + Iyy
        det = Ixx * Iyy - Ixy * Ixy
        
        # 边缘强度
        edge_strength = trace + np.sqrt(np.maximum(0, trace**2 - 4*det))
        
        # 阈值化
        threshold = np.percentile(edge_strength, 88)
        edges = (edge_strength > threshold).astype(np.uint8) * 255
        
        return edges
    
    def _generate_trimap(self, mask: np.ndarray, edge_map: np.ndarray) -> np.ndarray:
        """生成三元图 - 确定前景、背景、未知区域"""
        print("[DEBUG] 开始生成三元图...")
        
        h, w = mask.shape
        trimap = np.zeros((h, w), dtype=np.uint8)
        
        # 1. 确定前景区域 (白色 = 255)
        # 对mask进行腐蚀，得到确定的前景
        fg_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        sure_fg = cv2.erode(mask, fg_kernel, iterations=2)
        trimap[sure_fg > 0] = 255
        
        # 2. 确定背景区域 (黑色 = 0)
        # 对mask取反并腐蚀，得到确定的背景
        bg_mask = 255 - mask
        bg_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
        sure_bg = cv2.erode(bg_mask, bg_kernel, iterations=3)
        trimap[sure_bg > 0] = 0
        
        # 3. 未知区域 (灰色 = 128)
        # 结合边缘信息确定未知区域
        unknown_region = (trimap != 255) & (trimap != 0)
        
        # 扩展边缘区域作为未知区域
        edge_dilated = cv2.dilate(edge_map, np.ones((7, 7), np.uint8), iterations=2)
        edge_unknown = edge_dilated > 0
        
        # 合并未知区域
        final_unknown = unknown_region | edge_unknown
        trimap[final_unknown] = 128
        
        # 4. 特殊处理头发区域
        # 头发区域通常需要更大的未知区域
        hair_region = mask[:h//2, :]
        hair_edges = cv2.Canny(hair_region, 20, 60)
        hair_unknown = cv2.dilate(hair_edges, np.ones((9, 9), np.uint8), iterations=2)
        trimap[:h//2, :][hair_unknown > 0] = 128
        
        # 5. 确保trimap的连续性
        # 使用形态学操作平滑trimap
        trimap = cv2.medianBlur(trimap, 3)
        
        print(f"[DEBUG] 三元图生成完成")
        print(f"[DEBUG] 前景像素: {np.sum(trimap == 255)}")
        print(f"[DEBUG] 背景像素: {np.sum(trimap == 0)}")
        print(f"[DEBUG] 未知像素: {np.sum(trimap == 128)}")
        
        return trimap
    
    def _alpha_matting(self, image: np.ndarray, trimap: np.ndarray) -> np.ndarray:
        """Alpha抠图 - 生成精确的alpha通道"""
        print("[DEBUG] 开始Alpha抠图...")
        
        # 使用改进的Alpha抠图算法
        # 这里实现一个简化但有效的Alpha抠图
        
        h, w = image.shape[:2]
        alpha = np.zeros((h, w), dtype=np.float32)
        
        # 1. 设置已知区域的alpha值
        alpha[trimap == 255] = 1.0  # 前景
        alpha[trimap == 0] = 0.0    # 背景
        
        # 2. 对未知区域进行Alpha估计
        unknown_mask = (trimap == 128)
        
        if np.any(unknown_mask):
            # 使用局部颜色分布估计alpha值
            alpha_unknown = self._estimate_alpha_unknown_regions(image, trimap, unknown_mask)
            alpha[unknown_mask] = alpha_unknown[unknown_mask]
        
        # 3. Alpha值平滑
        alpha = self._smooth_alpha_matte(alpha, image, trimap)
        
        # 4. 转换为0-255范围
        alpha_uint8 = (alpha * 255).astype(np.uint8)
        
        print(f"[DEBUG] Alpha抠图完成")
        return alpha_uint8
    
    def _estimate_alpha_unknown_regions(self, image: np.ndarray, trimap: np.ndarray, 
                                       unknown_mask: np.ndarray) -> np.ndarray:
        """估计未知区域的alpha值"""
        h, w = image.shape[:2]
        alpha = np.zeros((h, w), dtype=np.float32)
        
        # 转换到LAB色彩空间进行更好的颜色分析
        lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
        
        # 获取前景和背景的颜色统计
        fg_pixels = lab_image[trimap == 255]
        bg_pixels = lab_image[trimap == 0]
        
        if len(fg_pixels) == 0 or len(bg_pixels) == 0:
            alpha[unknown_mask] = 0.5
            return alpha
        
        fg_mean = np.mean(fg_pixels, axis=0)
        bg_mean = np.mean(bg_pixels, axis=0)
        
        # 对每个未知像素估计alpha值
        unknown_pixels = lab_image[unknown_mask]
        
        # 计算到前景和背景的距离
        fg_distances = np.sqrt(np.sum((unknown_pixels - fg_mean) ** 2, axis=1))
        bg_distances = np.sqrt(np.sum((unknown_pixels - bg_mean) ** 2, axis=1))
        
        # 基于距离计算alpha值
        total_distances = fg_distances + bg_distances
        alpha_values = np.where(total_distances > 0, 
                               bg_distances / total_distances, 
                               0.5)
        
        alpha[unknown_mask] = alpha_values
        
        return alpha
    
    def _smooth_alpha_matte(self, alpha: np.ndarray, image: np.ndarray, 
                           trimap: np.ndarray) -> np.ndarray:
        """平滑alpha遮罩"""
        # 使用引导滤波平滑alpha值
        try:
            # 转换为uint8进行引导滤波
            alpha_uint8 = (alpha * 255).astype(np.uint8)
            smoothed = self._guided_filter(image, alpha_uint8, radius=5, eps=0.01)
            smoothed_alpha = smoothed.astype(np.float32) / 255.0
        except:
            # 如果引导滤波失败，使用双边滤波
            alpha_uint8 = (alpha * 255).astype(np.uint8)
            smoothed = cv2.bilateralFilter(alpha_uint8, 5, 20, 20)
            smoothed_alpha = smoothed.astype(np.float32) / 255.0
        
        # 保持已知区域的alpha值不变
        smoothed_alpha[trimap == 255] = 1.0
        smoothed_alpha[trimap == 0] = 0.0
        
        return smoothed_alpha
    
    def _optimize_hair_details(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """优化头发细节处理 - 增强版"""
        print("[DEBUG] 开始头发细节优化（增强版）...")
        
        h, w = mask.shape
        
        # 1. 智能头发区域检测
        hair_mask = self._detect_hair_region_advanced(image, mask)
        
        # 2. 头发丝细节保留
        hair_preserved = self._preserve_hair_strands(image, hair_mask)
        
        # 3. 头发边缘柔化
        hair_softened = self._soften_hair_edges(hair_preserved)
        
        # 4. 与身体区域融合
        body_mask = mask.copy()
        body_mask[:h//2, :] = 0  # 清除头发区域
        
        # 融合头发和身体mask
        optimized_mask = cv2.bitwise_or(hair_softened, body_mask)
        
        # 5. 头发与身体连接区域平滑处理
        connection_region = mask[h//3:2*h//3, :]  # 中间区域作为连接区域
        if np.sum(connection_region) > 0:
            # 对连接区域进行特殊平滑
            smoothed_connection = cv2.GaussianBlur(connection_region, (5, 5), 1.0)
            optimized_mask[h//3:2*h//3, :] = smoothed_connection
        
        print("[DEBUG] 头发细节优化完成（增强版）")
        return optimized_mask
    
    def _detect_hair_region_advanced(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """高级头发区域检测"""
        h, w = mask.shape
        
        # 1. 基于颜色的头发检测
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 头发通常是低饱和度、低亮度的区域
        hair_color_mask = cv2.inRange(hsv, 
                                     np.array([0, 0, 0]),      # 下限
                                     np.array([180, 100, 80])) # 上限
        
        # 2. 结合原始mask，只在前景区域检测头发
        hair_candidate = cv2.bitwise_and(hair_color_mask, mask)
        
        # 3. 只保留上半部分的头发
        hair_mask = np.zeros_like(mask)
        hair_mask[:h//2, :] = hair_candidate[:h//2, :]
        
        # 4. 形态学操作连接头发区域
        hair_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_CLOSE, hair_kernel)
        
        return hair_mask
    
    def _preserve_hair_strands(self, image: np.ndarray, hair_mask: np.ndarray) -> np.ndarray:
        """保留头发丝细节"""
        # 1. 使用非常小的核进行形态学操作，保留细小结构
        fine_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        
        # 2. 开运算去除噪点，但保留主要头发结构
        hair_cleaned = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, fine_kernel)
        
        # 3. 使用线性结构元素检测头发丝方向
        # 水平方向的头发丝
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
        horizontal_hair = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, horizontal_kernel)
        
        # 垂直方向的头发丝
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        vertical_hair = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, vertical_kernel)
        
        # 对角线方向的头发丝
        diagonal_kernel1 = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.uint8)
        diagonal_hair1 = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, diagonal_kernel1)
        
        diagonal_kernel2 = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]], dtype=np.uint8)
        diagonal_hair2 = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, diagonal_kernel2)
        
        # 4. 合并所有方向的头发丝
        directional_hair = cv2.bitwise_or(horizontal_hair, vertical_hair)
        directional_hair = cv2.bitwise_or(directional_hair, diagonal_hair1)
        directional_hair = cv2.bitwise_or(directional_hair, diagonal_hair2)
        
        # 5. 与清理后的头发mask合并
        preserved_hair = cv2.bitwise_or(hair_cleaned, directional_hair)
        
        return preserved_hair
    
    def _soften_hair_edges(self, hair_mask: np.ndarray) -> np.ndarray:
        """柔化头发边缘"""
        # 1. 检测头发边缘
        edges = cv2.Canny(hair_mask, 30, 100)
        
        # 2. 膨胀边缘区域
        edge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        edge_region = cv2.dilate(edges, edge_kernel, iterations=1)
        
        # 3. 在边缘区域应用轻微的高斯模糊
        softened = hair_mask.copy().astype(np.float32)
        blurred = cv2.GaussianBlur(hair_mask, (3, 3), 0.8)
        
        # 只在边缘区域应用模糊
        edge_mask = edge_region > 0
        softened[edge_mask] = blurred[edge_mask]
        
        return softened.astype(np.uint8)
    
    def _refine_edge_details(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """边缘细化处理 - 增强版"""
        print("[DEBUG] 开始边缘细化处理（增强版）...")
        
        # 1. 多尺度边缘检测
        edges_fine = cv2.Canny(mask, 30, 80)    # 细边缘
        edges_coarse = cv2.Canny(mask, 50, 150) # 粗边缘
        edges_combined = cv2.bitwise_or(edges_fine, edges_coarse)
        
        # 2. 自适应边缘处理
        refined_mask = self._adaptive_edge_processing(image, mask, edges_combined)
        
        # 3. 衣服边缘特殊处理
        clothing_refined = self._refine_clothing_edges(image, refined_mask)
        
        # 4. 全局边缘平滑
        final_refined = self._global_edge_smoothing(clothing_refined)
        
        print("[DEBUG] 边缘细化处理完成（增强版）")
        return final_refined
    
    def _adaptive_edge_processing(self, image: np.ndarray, mask: np.ndarray, edges: np.ndarray) -> np.ndarray:
        """自适应边缘处理"""
        # 1. 根据图像内容自适应调整处理强度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 计算图像的纹理复杂度
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 根据纹理复杂度调整处理参数
        if laplacian_var > 500:  # 高纹理复杂度
            bilateral_d = 15
            bilateral_sigma = 100
            print("[DEBUG] 检测到高纹理复杂度，使用强边缘处理")
        elif laplacian_var > 200:  # 中等纹理复杂度
            bilateral_d = 9
            bilateral_sigma = 80
            print("[DEBUG] 检测到中等纹理复杂度，使用中等边缘处理")
        else:  # 低纹理复杂度
            bilateral_d = 5
            bilateral_sigma = 50
            print("[DEBUG] 检测到低纹理复杂度，使用轻度边缘处理")
        
        # 2. 膨胀边缘区域
        edge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        edge_region = cv2.dilate(edges, edge_kernel, iterations=1)
        
        # 3. 在边缘区域应用双边滤波
        refined_mask = mask.copy().astype(np.float32)
        
        # 转换为3通道进行双边滤波
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(np.float32)
        bilateral_filtered = cv2.bilateralFilter(mask_3ch, bilateral_d, bilateral_sigma, bilateral_sigma)
        bilateral_mask = cv2.cvtColor(bilateral_filtered, cv2.COLOR_BGR2GRAY)
        
        # 只在边缘区域应用滤波结果
        edge_mask = edge_region > 0
        refined_mask[edge_mask] = bilateral_mask[edge_mask]
        
        # 4. 使用引导滤波进一步细化
        try:
            refined_mask = self._guided_filter(image, refined_mask.astype(np.uint8), radius=8, eps=0.01)
        except:
            # 如果引导滤波失败，使用高斯模糊作为替代
            refined_mask = cv2.GaussianBlur(refined_mask.astype(np.uint8), (5, 5), 1.0)
        
        return refined_mask
    
    def _refine_clothing_edges(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """衣服边缘特殊处理"""
        h, w = mask.shape
        
        # 1. 检测衣服区域（下半部分）
        clothing_region = mask[h//2:, :]
        
        if np.sum(clothing_region) == 0:
            return mask
        
        # 2. 衣服边缘检测
        clothing_edges = cv2.Canny(clothing_region, 40, 120)
        
        # 3. 分析衣服边缘的复杂度
        edge_density = np.sum(clothing_edges > 0) / clothing_edges.size
        
        if edge_density > 0.05:  # 复杂边缘（如毛衣、有纹理的衣服）
            print("[DEBUG] 检测到复杂衣服边缘，使用特殊处理")
            # 使用更强的平滑
            smoothed_clothing = cv2.GaussianBlur(clothing_region, (7, 7), 2.0)
            
            # 形态学闭运算填补小缝隙
            close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            smoothed_clothing = cv2.morphologyEx(smoothed_clothing, cv2.MORPH_CLOSE, close_kernel)
            
        else:  # 简单边缘（如西装、衬衫）
            print("[DEBUG] 检测到简单衣服边缘，使用轻度处理")
            # 使用轻度平滑
            smoothed_clothing = cv2.GaussianBlur(clothing_region, (3, 3), 1.0)
        
        # 4. 更新mask
        refined_mask = mask.copy()
        refined_mask[h//2:, :] = smoothed_clothing
        
        return refined_mask
    
    def _global_edge_smoothing(self, mask: np.ndarray) -> np.ndarray:
        """全局边缘平滑"""
        # 1. 检测所有边缘
        all_edges = cv2.Canny(mask, 50, 150)
        
        # 2. 创建边缘权重图
        edge_weight = cv2.GaussianBlur(all_edges.astype(np.float32), (5, 5), 2.0) / 255.0
        
        # 3. 根据边缘权重进行自适应平滑
        smoothed = cv2.GaussianBlur(mask, (3, 3), 1.0)
        
        # 4. 混合原始mask和平滑mask
        result = mask.astype(np.float32) * (1 - edge_weight) + smoothed.astype(np.float32) * edge_weight
        
        return result.astype(np.uint8)
    
    def _apply_refined_background(self, image: np.ndarray, mask: np.ndarray, 
                                 bg_color: Tuple[int, int, int]) -> np.ndarray:
        """多层混合应用背景 - 增强版"""
        print("[DEBUG] 开始多层混合背景应用（增强版）...")
        
        # 确保mask格式正确
        if len(mask.shape) == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        
        # 归一化mask
        mask_norm = mask.astype(np.float32) / 255.0
        
        # 创建背景
        bg_bgr = (bg_color[2], bg_color[1], bg_color[0])  # RGB to BGR
        background = np.full_like(image, bg_bgr, dtype=np.uint8)
        
        # 1. 基础混合
        result = image.astype(np.float32) * mask_norm[:, :, np.newaxis] + \
                background.astype(np.float32) * (1 - mask_norm[:, :, np.newaxis])
        
        # 2. 多级边缘羽化处理
        result = self._multi_level_edge_feathering(image, background, mask_norm, result)
        
        # 3. 头发丝特殊混合
        result = self._hair_strand_blending(image, background, mask, result)
        
        # 4. 衣服边缘抗锯齿
        result = self._clothing_edge_antialiasing(image, background, mask, result)
        
        print("[DEBUG] 多层混合背景应用完成（增强版）")
        return result.astype(np.uint8)
    
    def _multi_level_edge_feathering(self, image: np.ndarray, background: np.ndarray, 
                                   mask_norm: np.ndarray, result: np.ndarray) -> np.ndarray:
        """多级边缘羽化处理"""
        # 1. 检测不同强度的边缘
        mask_uint8 = (mask_norm * 255).astype(np.uint8)
        
        # 强边缘
        strong_edges = cv2.Canny(mask_uint8, 80, 160)
        strong_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        strong_edge_region = cv2.dilate(strong_edges, strong_kernel, iterations=1)
        
        # 中等边缘
        medium_edges = cv2.Canny(mask_uint8, 40, 120)
        medium_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        medium_edge_region = cv2.dilate(medium_edges, medium_kernel, iterations=1)
        
        # 弱边缘
        weak_edges = cv2.Canny(mask_uint8, 20, 80)
        weak_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        weak_edge_region = cv2.dilate(weak_edges, weak_kernel, iterations=1)
        
        # 2. 对不同强度的边缘应用不同程度的羽化
        # 强边缘 - 轻度羽化
        if np.any(strong_edge_region):
            soft_mask_strong = cv2.GaussianBlur(mask_uint8, (3, 3), 0.8).astype(np.float32) / 255.0
            strong_mask = strong_edge_region > 0
            for c in range(3):
                strong_blend = image[:, :, c].astype(np.float32) * soft_mask_strong + \
                              background[:, :, c].astype(np.float32) * (1 - soft_mask_strong)
                result[:, :, c][strong_mask] = strong_blend[strong_mask]
        
        # 中等边缘 - 中度羽化
        if np.any(medium_edge_region):
            soft_mask_medium = cv2.GaussianBlur(mask_uint8, (5, 5), 1.5).astype(np.float32) / 255.0
            medium_mask = (medium_edge_region > 0) & (strong_edge_region == 0)
            for c in range(3):
                medium_blend = image[:, :, c].astype(np.float32) * soft_mask_medium + \
                              background[:, :, c].astype(np.float32) * (1 - soft_mask_medium)
                result[:, :, c][medium_mask] = medium_blend[medium_mask]
        
        # 弱边缘 - 强度羽化
        if np.any(weak_edge_region):
            soft_mask_weak = cv2.GaussianBlur(mask_uint8, (7, 7), 2.5).astype(np.float32) / 255.0
            weak_mask = (weak_edge_region > 0) & (medium_edge_region == 0) & (strong_edge_region == 0)
            for c in range(3):
                weak_blend = image[:, :, c].astype(np.float32) * soft_mask_weak + \
                            background[:, :, c].astype(np.float32) * (1 - soft_mask_weak)
                result[:, :, c][weak_mask] = weak_blend[weak_mask]
        
        return result
    
    def _hair_strand_blending(self, image: np.ndarray, background: np.ndarray, 
                            mask: np.ndarray, result: np.ndarray) -> np.ndarray:
        """头发丝特殊混合"""
        h, w = mask.shape
        hair_region = mask[:h//2, :]  # 头发区域
        
        if np.sum(hair_region) == 0:
            return result
        
        # 1. 检测头发丝边缘
        hair_edges = cv2.Canny(hair_region, 30, 90)
        
        # 2. 使用非常小的核膨胀，只处理真正的头发丝
        hair_strand_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        hair_strand_region = cv2.dilate(hair_edges, hair_strand_kernel, iterations=1)
        
        # 3. 对头发丝区域使用特殊的alpha混合
        if np.any(hair_strand_region):
            # 创建渐变alpha值，中心更不透明，边缘更透明
            distance_transform = cv2.distanceTransform(hair_strand_region, cv2.DIST_L2, 5)
            max_distance = np.max(distance_transform)
            if max_distance > 0:
                alpha_gradient = distance_transform / max_distance
                alpha_gradient = np.clip(alpha_gradient * 0.8 + 0.2, 0, 1)  # 0.2-1.0范围
                
                # 应用渐变混合
                strand_mask = hair_strand_region > 0
                for c in range(3):
                    gradient_blend = (image[:h//2, :, c].astype(np.float32) * alpha_gradient + 
                                    background[:h//2, :, c].astype(np.float32) * (1 - alpha_gradient))
                    result[:h//2, :, c][strand_mask] = gradient_blend[strand_mask]
        
        return result
    
    def _clothing_edge_antialiasing(self, image: np.ndarray, background: np.ndarray, 
                                  mask: np.ndarray, result: np.ndarray) -> np.ndarray:
        """衣服边缘抗锯齿"""
        h, w = mask.shape
        clothing_region = mask[h//2:, :]  # 衣服区域
        
        if np.sum(clothing_region) == 0:
            return result
        
        # 1. 检测衣服边缘
        clothing_edges = cv2.Canny(clothing_region, 50, 150)
        
        # 2. 创建抗锯齿区域
        aa_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
        aa_region = cv2.dilate(clothing_edges, aa_kernel, iterations=1)
        
        # 3. 在抗锯齿区域应用多重采样
        if np.any(aa_region):
            # 上采样2倍
            upscaled_region = cv2.resize(clothing_region, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            upscaled_image = cv2.resize(image[h//2:, :], None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            upscaled_bg = cv2.resize(background[h//2:, :], None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            
            # 在高分辨率下混合
            upscaled_mask_norm = upscaled_region.astype(np.float32) / 255.0
            upscaled_result = (upscaled_image.astype(np.float32) * upscaled_mask_norm[:, :, np.newaxis] + 
                             upscaled_bg.astype(np.float32) * (1 - upscaled_mask_norm[:, :, np.newaxis]))
            
            # 下采样回原始分辨率
            downscaled_result = cv2.resize(upscaled_result, (w, h//2), interpolation=cv2.INTER_AREA)
            
            # 只在抗锯齿区域应用结果
            aa_mask = aa_region > 0
            for c in range(3):
                result[h//2:, :, c][aa_mask] = downscaled_result[:, :, c][aa_mask]
        
        return result
    
    def _post_process_refined(self, image: np.ndarray, original: np.ndarray, 
                             mask: np.ndarray) -> np.ndarray:
        """后处理优化 - 增强版"""
        print("[DEBUG] 开始后处理优化（增强版）...")
        
        result = image.copy()
        
        # 1. 高级边缘抗锯齿
        result = self._advanced_edge_antialiasing(result, mask)
        
        # 2. 跳过细节增强和锐化 - 避免噪点
        # result = self._detail_enhancement(result, original, mask)  # 已禁用
        
        # 3. 颜色一致性校正
        result = self._color_consistency_correction(result, original, mask)
        
        # 4. 最终质量优化
        result = self._final_quality_optimization(result, mask)
        
        print("[DEBUG] 后处理优化完成（增强版）")
        return result
    
    def _advanced_edge_antialiasing(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """高级边缘抗锯齿"""
        # 1. 多尺度边缘检测
        edges_1 = cv2.Canny(mask, 30, 90)   # 细边缘
        edges_2 = cv2.Canny(mask, 50, 150)  # 中边缘
        edges_3 = cv2.Canny(mask, 70, 200)  # 粗边缘
        
        # 2. 对不同尺度的边缘应用不同强度的抗锯齿
        result = image.copy()
        
        # 细边缘 - 强抗锯齿
        if np.any(edges_1):
            kernel_1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            edge_region_1 = cv2.dilate(edges_1, kernel_1, iterations=1)
            blurred_1 = cv2.GaussianBlur(result, (3, 3), 1.0)
            edge_mask_1 = edge_region_1 > 0
            result[edge_mask_1] = blurred_1[edge_mask_1]
        
        # 中边缘 - 中等抗锯齿
        if np.any(edges_2):
            kernel_2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            edge_region_2 = cv2.dilate(edges_2, kernel_2, iterations=1)
            edge_region_2 = cv2.bitwise_and(edge_region_2, cv2.bitwise_not(edges_1))  # 排除已处理的细边缘
            blurred_2 = cv2.GaussianBlur(result, (2, 2), 0.7)
            edge_mask_2 = edge_region_2 > 0
            result[edge_mask_2] = blurred_2[edge_mask_2]
        
        # 粗边缘 - 轻度抗锯齿
        if np.any(edges_3):
            kernel_3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
            edge_region_3 = cv2.dilate(edges_3, kernel_3, iterations=1)
            edge_region_3 = cv2.bitwise_and(edge_region_3, cv2.bitwise_not(cv2.bitwise_or(edges_1, edges_2)))
            blurred_3 = cv2.GaussianBlur(result, (1, 1), 0.5)
            edge_mask_3 = edge_region_3 > 0
            result[edge_mask_3] = blurred_3[edge_mask_3]
        
        return result
    
    def _detail_enhancement(self, image: np.ndarray, original: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        细节增强 - 移除传统锐化，只信任 CodeFormer 的自然锐度
        
        传统锐化会产生大量噪点，已全部移除
        """
        print("[DEBUG] 跳过传统锐化，保持自然质感")
        return image
    
    def _color_consistency_correction(self, image: np.ndarray, original: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """颜色一致性校正"""
        # 1. 前景区域颜色统计
        foreground_mask = mask > 128
        
        if not np.any(foreground_mask):
            return image
        
        # 2. 计算原始图像和处理后图像的颜色差异
        original_fg = original[foreground_mask]
        processed_fg = image[foreground_mask]
        
        # 计算平均颜色差异
        color_diff = np.mean(original_fg.astype(np.float32) - processed_fg.astype(np.float32), axis=0)
        
        # 3. 如果颜色差异过大，进行校正
        if np.max(np.abs(color_diff)) > 10:  # 颜色差异阈值
            print(f"[DEBUG] 检测到颜色偏移: {color_diff}, 进行校正")
            
            # 应用颜色校正
            corrected = image.astype(np.float32)
            corrected[foreground_mask] += color_diff * 0.3  # 部分校正，避免过度
            corrected = np.clip(corrected, 0, 255)
            
            return corrected.astype(np.uint8)
        
        return image
    
    def _final_quality_optimization(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """最终质量优化"""
        # 1. 噪声抑制
        # 在前景区域应用轻微的降噪
        foreground_mask = mask > 128
        
        if np.any(foreground_mask):
            # 使用双边滤波进行降噪，保持边缘
            denoised = cv2.bilateralFilter(image, 5, 10, 10)
            
            # 只在前景区域应用降噪，且强度很轻
            result = image.copy().astype(np.float32)
            denoised_float = denoised.astype(np.float32)
            
            # 混合原图和降噪图像（90%原图 + 10%降噪）
            result[foreground_mask] = (result[foreground_mask] * 0.9 + 
                                     denoised_float[foreground_mask] * 0.1)
            
            result = np.clip(result, 0, 255).astype(np.uint8)
        else:
            result = image
        
        # 2. 对比度微调
        # 轻微增强对比度，使图像更清晰
        enhanced = cv2.convertScaleAbs(result, alpha=1.02, beta=1)
        
        return enhanced
    
    def _guided_filter(self, guide: np.ndarray, src: np.ndarray, radius: int = 8, eps: float = 0.01) -> np.ndarray:
        """引导滤波实现（简化版）"""
        # 转换为灰度图作为引导图
        if len(guide.shape) == 3:
            guide_gray = cv2.cvtColor(guide, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        else:
            guide_gray = guide.astype(np.float32) / 255.0
        
        src_float = src.astype(np.float32) / 255.0
        
        # 计算均值
        mean_guide = cv2.boxFilter(guide_gray, -1, (radius, radius))
        mean_src = cv2.boxFilter(src_float, -1, (radius, radius))
        
        # 计算协方差和方差
        corr_guide_src = cv2.boxFilter(guide_gray * src_float, -1, (radius, radius))
        cov_guide_src = corr_guide_src - mean_guide * mean_src
        
        var_guide = cv2.boxFilter(guide_gray * guide_gray, -1, (radius, radius)) - mean_guide * mean_guide
        
        # 计算系数
        a = cov_guide_src / (var_guide + eps)
        b = mean_src - a * mean_guide
        
        # 平滑系数
        mean_a = cv2.boxFilter(a, -1, (radius, radius))
        mean_b = cv2.boxFilter(b, -1, (radius, radius))
        
        # 输出
        result = mean_a * guide_gray + mean_b
        
        return (result * 255).astype(np.uint8)
    
    def _ultra_hair_processing(self, image: np.ndarray, alpha_matte: np.ndarray) -> np.ndarray:
        """头发丝超精细处理"""
        print("[DEBUG] 开始头发丝超精细处理...")
        
        h, w = alpha_matte.shape
        hair_region = alpha_matte[:h//2, :]  # 头发区域
        
        if np.sum(hair_region) == 0:
            return alpha_matte
        
        # 1. 头发丝方向检测
        hair_directions = self._detect_hair_directions(image[:h//2, :])
        
        # 2. 沿头发丝方向进行各向异性扩散
        enhanced_hair = self._anisotropic_diffusion_hair(hair_region, hair_directions)
        
        # 3. 头发丝连接性增强
        connected_hair = self._enhance_hair_connectivity(enhanced_hair)
        
        # 更新alpha遮罩
        result = alpha_matte.copy()
        result[:h//2, :] = connected_hair
        
        print("[DEBUG] 头发丝超精细处理完成")
        return result
    
    def _ultra_clothing_processing(self, image: np.ndarray, alpha_matte: np.ndarray) -> np.ndarray:
        """衣服边缘超精细处理"""
        print("[DEBUG] 开始衣服边缘超精细处理...")
        
        h, w = alpha_matte.shape
        clothing_region = alpha_matte[h//2:, :]  # 衣服区域
        
        if np.sum(clothing_region) == 0:
            return alpha_matte
        
        # 1. 衣服纹理分析
        texture_map = self._analyze_clothing_texture(image[h//2:, :])
        
        # 2. 基于纹理的边缘优化
        optimized_clothing = self._texture_based_edge_optimization(clothing_region, texture_map)
        
        # 更新alpha遮罩
        result = alpha_matte.copy()
        result[h//2:, :] = optimized_clothing
        
        print("[DEBUG] 衣服边缘超精细处理完成")
        return result
    
    def _ultra_background_composition(self, image: np.ndarray, alpha_matte: np.ndarray, 
                                    bg_color: Tuple[int, int, int]) -> np.ndarray:
        """高质量背景合成 - 修复版，保持前景颜色不变"""
        print("[DEBUG] 开始高质量背景合成...")
        
        # 归一化alpha值
        alpha_norm = alpha_matte.astype(np.float32) / 255.0
        
        # 创建背景 - 确保颜色顺序正确
        bg_bgr = (bg_color[2], bg_color[1], bg_color[0])  # RGB转BGR
        background = np.full_like(image, bg_bgr, dtype=np.uint8)
        
        print(f"[DEBUG] 背景色BGR: {bg_bgr}")
        
        # 高质量alpha混合 - 保持前景颜色不变
        result = np.zeros_like(image, dtype=np.float32)
        
        # 直接使用原始图像的前景部分，不做任何颜色修改
        for c in range(3):
            result[:, :, c] = (image[:, :, c].astype(np.float32) * alpha_norm + 
                              background[:, :, c].astype(np.float32) * (1 - alpha_norm))
        
        # 确保前景区域完全保持原色
        fg_mask = alpha_norm > 0.9  # 高alpha值区域完全保持原色
        result[fg_mask] = image[fg_mask].astype(np.float32)
        
        print("[DEBUG] 高质量背景合成完成，前景颜色已保护")
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def _ultra_post_processing(self, image: np.ndarray, original: np.ndarray, 
                              alpha_matte: np.ndarray) -> np.ndarray:
        """超精细后处理 - 修复版，避免脸部变色"""
        print("[DEBUG] 开始超精细后处理...")
        
        # 1. 跳过轻微边缘锐化，避免过度处理
        # result = self._conservative_edge_sharpening(image, alpha_matte)  # 已禁用
        result = image.copy()
        
        # 2. 保守的颜色校正，避免脸部变色
        result = self._advanced_color_correction(result, original, alpha_matte)
        
        print("[DEBUG] 超精细后处理完成")
        return result
    
    def _conservative_edge_sharpening(self, image: np.ndarray, alpha_matte: np.ndarray) -> np.ndarray:
        """保守的边缘锐化，避免脸部过度处理"""
        # 只在边缘区域进行轻微锐化
        edges = cv2.Canny(alpha_matte, 50, 150)
        edge_region = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
        
        # 非常轻微的锐化核
        kernel_sharpen = np.array([[-0.1, -0.1, -0.1], 
                                  [-0.1, 1.8, -0.1], 
                                  [-0.1, -0.1, -0.1]])
        sharpened = cv2.filter2D(image, -1, kernel_sharpen)
        
        result = image.copy()
        edge_mask = edge_region > 0
        
        # 只在边缘区域应用轻微锐化
        if np.any(edge_mask):
            result[edge_mask] = sharpened[edge_mask]
        
        return result
    
    def _detect_hair_directions(self, hair_image: np.ndarray) -> np.ndarray:
        """检测头发丝方向"""
        gray = cv2.cvtColor(hair_image, cv2.COLOR_BGR2GRAY)
        
        # 使用Sobel算子计算梯度
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # 计算梯度方向
        directions = np.arctan2(grad_y, grad_x)
        
        return directions
    
    def _anisotropic_diffusion_hair(self, hair_region: np.ndarray, directions: np.ndarray) -> np.ndarray:
        """各向异性扩散处理头发"""
        # 简化的各向异性扩散
        result = hair_region.astype(np.float32)
        
        # 沿主方向进行扩散
        kernel_h = np.array([[0, 0, 0], [1, 1, 1], [0, 0, 0]], dtype=np.float32) / 3
        kernel_v = np.array([[0, 1, 0], [0, 1, 0], [0, 1, 0]], dtype=np.float32) / 3
        
        # 水平扩散
        h_diffused = cv2.filter2D(result, -1, kernel_h)
        # 垂直扩散
        v_diffused = cv2.filter2D(result, -1, kernel_v)
        
        # 根据方向混合
        result = (h_diffused + v_diffused) / 2
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def _enhance_hair_connectivity(self, hair_region: np.ndarray) -> np.ndarray:
        """增强头发连接性"""
        # 使用形态学操作连接断开的头发丝
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        connected = cv2.morphologyEx(hair_region, cv2.MORPH_CLOSE, kernel)
        
        return connected
    
    def _analyze_clothing_texture(self, clothing_image: np.ndarray) -> np.ndarray:
        """分析衣服纹理"""
        gray = cv2.cvtColor(clothing_image, cv2.COLOR_BGR2GRAY)
        
        # 使用局部二值模式分析纹理
        # 简化版本：使用方差滤波
        kernel = np.ones((5, 5), np.float32) / 25
        mean_filtered = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        sqr_filtered = cv2.filter2D((gray.astype(np.float32))**2, -1, kernel)
        texture_map = sqr_filtered - mean_filtered**2
        
        return texture_map
    
    def _texture_based_edge_optimization(self, clothing_region: np.ndarray, 
                                       texture_map: np.ndarray) -> np.ndarray:
        """基于纹理的边缘优化"""
        # 根据纹理复杂度调整边缘处理
        high_texture = texture_map > np.percentile(texture_map, 70)
        
        result = clothing_region.copy()
        
        # 高纹理区域使用更强的平滑
        if np.any(high_texture):
            smoothed = cv2.GaussianBlur(clothing_region, (5, 5), 2.0)
            result[high_texture] = smoothed[high_texture]
        
        return result
    
    def _edge_sharpening(self, image: np.ndarray, alpha_matte: np.ndarray) -> np.ndarray:
        """边缘锐化"""
        # 检测边缘区域
        edges = cv2.Canny(alpha_matte, 50, 150)
        edge_region = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
        
        # 在边缘区域应用锐化
        kernel_sharpen = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(image, -1, kernel_sharpen)
        
        result = image.copy()
        edge_mask = edge_region > 0
        result[edge_mask] = sharpened[edge_mask]
        
        return result
    
    def _advanced_color_correction(self, image: np.ndarray, original: np.ndarray, 
                                 alpha_matte: np.ndarray) -> np.ndarray:
        """高级颜色校正 - 修复版，避免脸部变色"""
        # 保持前景区域的颜色一致性
        fg_mask = alpha_matte > 128
        
        if not np.any(fg_mask):
            return image
        
        # 计算颜色差异，但要非常保守
        original_fg = original[fg_mask].astype(np.float32)
        processed_fg = image[fg_mask].astype(np.float32)
        
        color_diff = np.mean(original_fg - processed_fg, axis=0)
        
        # 只有在颜色差异很大时才进行轻微校正，避免脸部变色
        if np.max(np.abs(color_diff)) > 15:  # 提高阈值，减少不必要的校正
            print(f"[DEBUG] 检测到较大颜色偏移: {color_diff}, 进行轻微校正")
            
            # 非常轻微的校正，只校正10%
            result = image.astype(np.float32)
            result[fg_mask] += color_diff * 0.1  # 从0.2降低到0.1
            result = np.clip(result, 0, 255)
            
            return result.astype(np.uint8)
        else:
            print("[DEBUG] 颜色差异在正常范围内，跳过颜色校正")
            return image
    
    def _evaluate_alpha_quality(self, alpha_matte: np.ndarray) -> Dict:
        """评估alpha遮罩质量"""
        # 计算alpha值分布
        alpha_values = alpha_matte.flatten()
        
        return {
            'alpha_range': f"{np.min(alpha_values)}-{np.max(alpha_values)}",
            'alpha_mean': float(np.mean(alpha_values)),
            'alpha_std': float(np.std(alpha_values)),
            'soft_edges': float(np.sum((alpha_values > 10) & (alpha_values < 245)) / len(alpha_values))
        }
    
    def _traditional_replace_background(self, image: np.ndarray, 
                                      bg_color: Tuple[int, int, int]) -> Tuple[np.ndarray, Dict]:
        """传统算法背景替换（作为超精细模式的回退方案）"""
        mask, mask_info = self._generate_mask(image, 'skin_detection')
        result = self._apply_background(image, mask, bg_color)
        
        process_info = {
            'method': 'traditional_fallback',
            'method_used': 'skin_detection',
            'background_color': bg_color,
            'mask_quality': self._evaluate_mask_quality(mask),
            **mask_info
        }
        
        return result, process_info

    # ------------------------------------------------------------------
    # 高保真管线入口（新增，不影响原有 refined 模式）
    # ------------------------------------------------------------------

    def replace_background_hifi(self, image: np.ndarray,
                                bg_color,
                                beautify_options: dict = None,
                                beautify_strengths: dict = None,
                                use_gfpgan: bool = True):
        """
        高保真管线背景替换
        InsightFace + rembg(isnet) + GFPGAN

        Args:
            image: 输入图像
            bg_color: 背景颜色（颜色名称字符串或 RGB tuple）
            beautify_options: 美颜开关
            beautify_strengths: 美颜强度
            use_gfpgan: 是否启用 GFPGAN 增强

        Returns:
            (处理后图像, 处理信息)
        """
        # 解析颜色 - 从 RGB 转换为 BGR
        if isinstance(bg_color, str):
            if bg_color not in self.background_colors:
                raise ValueError(f"不支持的背景颜色: {bg_color}")
            bg_rgb = self.background_colors[bg_color]
            print(f"[DEBUG] 背景色 '{bg_color}' -> RGB {bg_rgb}")
        else:
            # 假设传入的是 RGB 格式
            bg_rgb = bg_color
            print(f"[DEBUG] 背景色 (直接传入) -> RGB {bg_rgb}")
        
        # RGB 转换为 BGR（OpenCV 使用 BGR 格式）
        bg_bgr = (bg_rgb[2], bg_rgb[1], bg_rgb[0])
        print(f"[DEBUG] 背景色 RGB {bg_rgb} -> BGR {bg_bgr}")

        # 懒加载 HiFi 管线
        if not hasattr(self, '_hifi_pipeline') or self._hifi_pipeline is None:
            from controllers.hifi_pipeline import HiFiPipeline
            self._hifi_pipeline = HiFiPipeline()
            self._hifi_pipeline.initialize()

        result, info = self._hifi_pipeline.process(
            image,
            bg_color=bg_bgr,  # 确保传入 BGR 格式
            beautify_options=beautify_options or {},
            beautify_strengths=beautify_strengths or {},
            use_codeformer=use_gfpgan,
        )
        info['method_used'] = 'hifi_pipeline'
        info['pipeline_status'] = self._hifi_pipeline.get_status()
        return result, info
