"""
批量处理系统
支持批量导入、处理、导出证件照
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Callable, Optional, Tuple
import threading
import time
from datetime import datetime
import json
from .image_processor import ImageProcessor

class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, ai_processor=None, progress_callback=None, 
                 status_callback=None):
        """
        初始化批量处理器
        
        Args:
            ai_processor: AI处理器实例
            progress_callback: 进度回调函数 (current, total, current_file)
            status_callback: 状态回调函数 (message, level)
        """
        self.ai_processor = ai_processor
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        
        # 处理队列
        self.image_queue = []
        self.processing_results = []
        
        # 批量处理参数
        self.batch_params = {
            'crop_spec': '一寸',
            'background_color': 'white',
            'background_mode': 'refined',  # 新增：默认使用精细模式
            'beautify_enabled': True,
            'beautify_strength': 0.5,
            'auto_enhance': True,
            'brightness': 0,
            'contrast': 0,
            'saturation': 0,
            'sharpness': 0,
            'gamma': 1.0,
            'preset': '标准证件照',
            'output_format': 'jpg',
            'output_quality': 95,
            'output_dpi': 300
        }
        
        # 处理状态
        self.is_processing = False
        self.should_stop = False
        self.current_index = 0
        self.start_time = None
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'processing_time': 0,
            'average_time_per_file': 0
        }
    
    def add_images(self, image_paths: List[str]) -> int:
        """
        批量添加图片到处理队列
        
        Args:
            image_paths: 图片路径列表
            
        Returns:
            int: 成功添加的图片数量
        """
        added_count = 0
        
        for path in image_paths:
            if self._validate_image_file(path):
                # 生成输出文件名
                base_name = os.path.splitext(os.path.basename(path))[0]
                output_name = f"{base_name}_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                self.image_queue.append({
                    'input_path': path,
                    'output_name': output_name,
                    'status': 'pending',
                    'result_path': None,
                    'error': None,
                    'processing_time': 0,
                    'quality_score': 0,
                    'file_size_before': os.path.getsize(path) if os.path.exists(path) else 0,
                    'file_size_after': 0
                })
                added_count += 1
            else:
                self._log_status(f"跳过无效文件: {path}", "warning")
        
        self.stats['total_files'] = len(self.image_queue)
        self._log_status(f"成功添加 {added_count} 个文件到处理队列", "info")
        
        return added_count
    
    def remove_image(self, index: int) -> bool:
        """
        从队列中移除图片
        
        Args:
            index: 图片在队列中的索引
            
        Returns:
            bool: 是否成功移除
        """
        if 0 <= index < len(self.image_queue):
            removed_item = self.image_queue.pop(index)
            self.stats['total_files'] = len(self.image_queue)
            self._log_status(f"移除文件: {removed_item['input_path']}", "info")
            return True
        return False
    
    def clear_queue(self):
        """清空处理队列"""
        self.image_queue.clear()
        self.processing_results.clear()
        self._reset_stats()
        self._log_status("处理队列已清空", "info")
    
    def set_batch_params(self, params: Dict):
        """
        设置批量处理参数
        
        Args:
            params: 处理参数字典
        """
        self.batch_params.update(params)
        self._log_status("批量处理参数已更新", "info")
    
    def get_batch_params(self) -> Dict:
        """获取当前批量处理参数"""
        return self.batch_params.copy()
    
    def start_batch_processing(self, output_directory: str) -> bool:
        """
        开始批量处理
        
        Args:
            output_directory: 输出目录
            
        Returns:
            bool: 是否成功开始处理
        """
        if self.is_processing:
            self._log_status("批量处理正在进行中", "warning")
            return False
        
        if not self.image_queue:
            self._log_status("处理队列为空", "warning")
            return False
        
        # 规范化输出目录路径
        output_directory = os.path.normpath(output_directory)
        
        if not os.path.exists(output_directory):
            try:
                os.makedirs(output_directory, exist_ok=True)
                print(f"[INFO] 创建输出目录: {output_directory}")
            except Exception as e:
                self._log_status(f"创建输出目录失败: {e}", "error")
                return False
        
        # 重置状态
        self.is_processing = True
        self.should_stop = False
        self.current_index = 0
        self.start_time = time.time()
        self._reset_stats()
        
        # 在新线程中开始处理
        processing_thread = threading.Thread(
            target=self._process_batch_thread,
            args=(output_directory,)
        )
        processing_thread.daemon = True
        processing_thread.start()
        
        self._log_status("批量处理已开始", "info")
        return True
    
    def stop_batch_processing(self):
        """停止批量处理"""
        if self.is_processing:
            self.should_stop = True
            self._log_status("正在停止批量处理...", "info")
    
    def _process_batch_thread(self, output_directory: str):
        """批量处理线程"""
        try:
            for i, item in enumerate(self.image_queue):
                if self.should_stop:
                    break
                
                self.current_index = i
                self._update_progress(i, len(self.image_queue), item['input_path'])
                
                # 处理单个文件
                success = self._process_single_file(item, output_directory)
                
                # 更新统计
                self.stats['processed_files'] += 1
                if success:
                    self.stats['successful_files'] += 1
                else:
                    self.stats['failed_files'] += 1
                
                # 短暂延迟，避免CPU占用过高
                time.sleep(0.1)
            
            # 处理完成
            self.stats['processing_time'] = time.time() - self.start_time
            if self.stats['processed_files'] > 0:
                self.stats['average_time_per_file'] = (
                    self.stats['processing_time'] / self.stats['processed_files']
                )
            
            self._finalize_processing()
            
        except Exception as e:
            self._log_status(f"批量处理异常: {e}", "error")
        finally:
            self.is_processing = False
    
    def _process_single_file(self, item: Dict, output_directory: str) -> bool:
        """
        处理单个文件 - 支持多规格多颜色
        
        Args:
            item: 文件信息字典
            output_directory: 输出目录
            
        Returns:
            bool: 是否处理成功
        """
        start_time = time.time()
        
        try:
            print(f"\n[DEBUG] ========== 开始处理文件 ==========")
            print(f"[DEBUG] 输入文件: {item['input_path']}")
            print(f"[DEBUG] 输出目录: {output_directory}")
            
            # 检查是否是多规格多颜色模式
            multi_specs = self.batch_params.get('multi_specs', [])
            multi_colors = self.batch_params.get('multi_colors', [])
            
            if multi_specs and multi_colors:
                # 多规格多颜色模式
                print(f"[DEBUG] 多规格多颜色模式: {len(multi_specs)}规格 × {len(multi_colors)}颜色")
                return self._process_multi_spec_file(item, output_directory, multi_specs, multi_colors)
            else:
                # 单规格单颜色模式
                print(f"[DEBUG] 单规格单颜色模式")
                return self._process_single_spec_file(item, output_directory)
                
        except Exception as e:
            # 处理失败
            item['status'] = 'failed'
            item['error'] = str(e)
            item['processing_time'] = time.time() - start_time
            
            self._log_status(f"处理失败: {item['input_path']} - {e}", "error")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_single_spec_file(self, item: Dict, output_directory: str) -> bool:
        """
        处理单个文件 - 单规格单颜色
        
        Args:
            item: 文件信息字典
            output_directory: 输出目录
            
        Returns:
            bool: 是否处理成功
        """
        start_time = time.time()
        
        try:
            # 创建图像处理器实例
            processor = ImageProcessor(self.ai_processor)
            
            # 加载图像
            print(f"[DEBUG] 正在加载图像...")
            loaded_image = processor.load_image(item['input_path'])
            if loaded_image is None or not isinstance(loaded_image, np.ndarray):
                raise Exception("无法加载图像")
            print(f"[DEBUG] 图像加载成功: {loaded_image.shape}")
            
            # 简化批量处理 - 只做基本处理
            print(f"[DEBUG] 使用简化批量处理模式")
            print(f"[DEBUG] 跳过预设应用，避免复杂参数调整")
            print(f"[DEBUG] 跳过亮度、对比度、饱和度、锐化等复杂调整")
            
            # 美颜处理
            if self.batch_params.get('beautify_enabled', False):
                beautify_strength = self.batch_params.get('beautify_strength', 0.5)
                print(f"[DEBUG] 应用美颜，强度: {beautify_strength}")
                
                # 使用高级美颜功能
                from controllers.advanced_beautify import AdvancedBeautify
                beautify_processor = AdvancedBeautify(self.ai_processor)
                
                # 配置美颜选项
                beautify_options = {
                    'skin_smooth': True,        # 磨皮
                    'remove_blemishes': True,   # 祛痘
                    'eye_enhance': True,        # 眼部增强
                    'lip_enhance': True,        # 唇部增强
                    'teeth_whiten': True,       # 牙齿美白
                    'face_slim': False,
                    'eye_enlarge': False,
                    'nose_enhance': False
                }
                
                # 配置强度
                beautify_strengths = {
                    'smooth_strength': beautify_strength,
                    'eye_enhance_strength': beautify_strength * 0.6,
                    'lip_enhance_strength': beautify_strength * 0.4,
                    'blemish_strength': beautify_strength * 0.8
                }
                
                # 应用美颜
                beautified_image_array, beautify_info = beautify_processor.selective_beautify(
                    processor.get_current_image(),
                    beautify_options,
                    beautify_strengths
                )
                
                if beautified_image_array is not None:
                    processor.load_image_from_array(beautified_image_array)
                    print(f"[DEBUG] 美颜处理成功 - 应用的功能: {beautify_info['operations_applied']}")
                else:
                    print(f"[DEBUG] 美颜处理失败，继续处理")
            else:
                print(f"[DEBUG] 美颜已禁用")
            
            # 智能裁剪
            crop_spec = self.batch_params.get('crop_spec', '一寸')
            print(f"[DEBUG] 智能裁剪到: {crop_spec}")
            success, crop_info = processor.crop_to_spec(crop_spec)
            if success:
                print(f"[DEBUG] 裁剪成功")
            else:
                self._log_status(f"裁剪失败: {item['input_path']}", "warning")
                print(f"[DEBUG] 裁剪信息: {crop_info}")
            
            # 背景替换
            bg_color = self.batch_params.get('background_color', 'white')
            use_alpha_matting = self.batch_params.get('alpha_matting', True)
            print(f"[DEBUG] 背景替换为: {bg_color}, Alpha Matte: {use_alpha_matting}")
            
            # 映射背景颜色名称
            color_mapping = {
                'white': '白色',
                'blue': '蓝色', 
                'red': '红色',
                'light_blue': '浅蓝色',
                'gray': '灰色',
                '白色': '白色',
                '蓝色': '蓝色',
                '红色': '红色',
                '浅蓝色': '浅蓝色',
                '灰色': '灰色'
            }
            bg_color_name = color_mapping.get(bg_color, bg_color)
            
            success, bg_info = processor.change_background(bg_color_name, method='refined', refine_edges=True, use_alpha_matting=use_alpha_matting)
            if success:
                print(f"[DEBUG] 背景替换成功")
            else:
                self._log_status(f"背景替换失败: {item['input_path']}", "warning")
                print(f"[DEBUG] 背景替换信息: {bg_info}")
            
            # 获取最终处理后的图像
            processed_image = processor.get_current_image()
            if processed_image is None or not isinstance(processed_image, np.ndarray):
                raise Exception("处理后的图像无效")
            
            if processed_image.size == 0:
                raise Exception("处理后的图像为空")
            
            print(f"[DEBUG] 处理后图像: {processed_image.shape}, 数据类型: {processed_image.dtype}")
            
            # 保存处理后的图像
            output_path = self._generate_output_path(
                output_directory, item['output_name'], 
                self.batch_params.get('output_format', 'jpg')
            )
            
            print(f"[DEBUG] 准备保存到: {output_path}")
            success = self._save_processed_image(processed_image, output_path)
            
            if success:
                # 更新处理结果
                item['status'] = 'completed'
                item['result_path'] = output_path
                item['processing_time'] = time.time() - start_time
                item['quality_score'] = processor.get_quality_score()
                item['file_size_after'] = os.path.getsize(output_path)
                
                self._log_status(f"处理完成: {item['input_path']}", "success")
                return True
            else:
                raise Exception("保存图像失败")
                
        except Exception as e:
            item['status'] = 'failed'
            item['error'] = str(e)
            item['processing_time'] = time.time() - start_time
            
            self._log_status(f"处理失败: {item['input_path']} - {e}", "error")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_multi_spec_file(self, item: Dict, output_directory: str, 
                                  specs: List[str], colors: List[str]) -> bool:
        """
        处理单个文件 - 多规格多颜色
        
        Args:
            item: 文件信息字典
            output_directory: 输出目录
            specs: 规格列表
            colors: 颜色列表
            
        Returns:
            bool: 是否处理成功
        """
        start_time = time.time()
        total_combinations = len(specs) * len(colors)
        successful_count = 0
        
        try:
            print(f"[DEBUG] 多规格多颜色处理: {len(specs)}规格 × {len(colors)}颜色 = {total_combinations}张")
            
            # 创建图像处理器实例
            processor = ImageProcessor(self.ai_processor)
            
            # 加载原始图像
            print(f"[DEBUG] 正在加载图像...")
            loaded_image = processor.load_image(item['input_path'])
            if loaded_image is None or not isinstance(loaded_image, np.ndarray):
                raise Exception("无法加载图像")
            print(f"[DEBUG] 图像加载成功: {loaded_image.shape}")
            
            # 保存原始图像副本
            original_image = loaded_image.copy()
            
            # 美颜处理（只做一次）
            if self.batch_params.get('beautify_enabled', False):
                beautify_strength = self.batch_params.get('beautify_strength', 0.5)
                print(f"[DEBUG] 应用美颜，强度: {beautify_strength}")
                
                # 使用高级美颜功能
                from controllers.advanced_beautify import AdvancedBeautify
                beautify_processor = AdvancedBeautify(self.ai_processor)
                
                # 配置美颜选项 - 启用多个功能
                beautify_options = {
                    'skin_smooth': True,        # 磨皮
                    'remove_blemishes': True,   # 祛痘
                    'eye_enhance': True,        # 眼部增强
                    'lip_enhance': True,        # 唇部增强
                    'teeth_whiten': True,       # 牙齿美白
                    'face_slim': False,         # 瘦脸（可选）
                    'eye_enlarge': False,       # 大眼（可选）
                    'nose_enhance': False       # 鼻部增强（可选）
                }
                
                # 配置强度
                beautify_strengths = {
                    'smooth_strength': beautify_strength,
                    'eye_enhance_strength': beautify_strength * 0.6,
                    'lip_enhance_strength': beautify_strength * 0.4,
                    'blemish_strength': beautify_strength * 0.8
                }
                
                # 应用美颜
                beautified_image_array, beautify_info = beautify_processor.selective_beautify(
                    processor.get_current_image(),
                    beautify_options,
                    beautify_strengths
                )
                
                if beautified_image_array is not None:
                    processor.load_image_from_array(beautified_image_array)
                    print(f"[DEBUG] 美颜处理成功 - 应用的功能: {beautify_info['operations_applied']}")
                else:
                    print(f"[DEBUG] 美颜处理失败，继续处理")
                
                # 保存美颜后的图像
                beautified_image = processor.get_current_image().copy()
            else:
                beautified_image = original_image.copy()
            
            # 获取高级背景效果参数
            gradient_enabled = self.batch_params.get('gradient_enabled', False)
            texture_enabled = self.batch_params.get('texture_enabled', False)
            blur_enabled = self.batch_params.get('blur_enabled', False)
            use_alpha_matting = self.batch_params.get('alpha_matting', True)
            
            # 循环处理每个规格和颜色组合
            combination_index = 0
            for spec in specs:
                for color in colors:
                    combination_index += 1
                    print(f"\n[DEBUG] === 处理组合 {combination_index}/{total_combinations}: {spec} + {color} ===")
                    
                    try:
                        # 重新加载美颜后的图像
                        processor = ImageProcessor(self.ai_processor)
                        processor.load_image_from_array(beautified_image.copy())
                        
                        # 智能裁剪到指定规格
                        print(f"[DEBUG] 智能裁剪到: {spec}")
                        success, crop_info = processor.crop_to_spec(spec)
                        if not success:
                            print(f"[WARN] 裁剪失败: {crop_info}")
                            continue
                        
                        # 背景替换
                        print(f"[DEBUG] 背景替换为: {color}")
                        success, bg_info = processor.change_background(
                            color, 
                            method='refined', 
                            refine_edges=True, 
                            use_alpha_matting=use_alpha_matting
                        )
                        if not success:
                            print(f"[WARN] 背景替换失败: {bg_info}")
                            continue
                        
                        # 应用高级背景效果
                        if gradient_enabled or texture_enabled or blur_enabled:
                            print(f"[DEBUG] 应用高级背景效果: 渐变={gradient_enabled}, 纹理={texture_enabled}, 虚化={blur_enabled}")
                            current_image = processor.get_current_image()
                            mask = processor.current_mask
                            
                            if mask is not None:
                                from controllers.advanced_background import AdvancedBackgroundProcessor
                                adv_bg = AdvancedBackgroundProcessor()
                                
                                # 应用效果
                                if blur_enabled:
                                    current_image = adv_bg.apply_blur_effect(current_image, mask, strength=50)
                                if gradient_enabled:
                                    current_image = adv_bg.apply_gradient_effect(current_image, mask, direction='vertical')
                                if texture_enabled:
                                    current_image = adv_bg.apply_texture_effect(current_image, mask, texture_type='canvas')
                                
                                processor.load_image_from_array(current_image)
                        
                        # 获取处理后的图像
                        processed_image = processor.get_current_image()
                        if processed_image is None or processed_image.size == 0:
                            print(f"[WARN] 处理后图像无效")
                            continue
                        
                        # 生成输出文件名
                        base_name = os.path.splitext(os.path.basename(item['input_path']))[0]
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        
                        # 映射规格和颜色到英文
                        spec_mapping = {
                            '一寸': '1inch', '小一寸': 'small1inch', '大一寸': 'large1inch',
                            '小二寸': 'small2inch', '二寸': '2inch', '大二寸': 'large2inch',
                            '美国护照': 'us_passport', '欧盟护照': 'eu_passport',
                            '英国签证': 'uk_visa', '日本护照': 'jp_passport'
                        }
                        color_mapping = {
                            '白色': 'white', '蓝色': 'blue', '红色': 'red',
                            '灰色': 'gray', '浅蓝色': 'lightblue',
                            '美国护照蓝': 'us_blue', '欧盟护照灰': 'eu_gray'
                        }
                        
                        spec_en = spec_mapping.get(spec, spec.replace(' ', '_'))
                        color_en = color_mapping.get(color, color.replace(' ', '_'))
                        
                        output_filename = f"{base_name}_{timestamp}_{spec_en}_{color_en}.jpg"
                        output_path = os.path.join(output_directory, output_filename)
                        output_path = os.path.normpath(output_path)
                        
                        # 保存图像
                        print(f"[DEBUG] 保存到: {output_path}")
                        success = self._save_processed_image(processed_image, output_path)
                        
                        if success:
                            successful_count += 1
                            print(f"[OK] 成功保存: {spec} + {color}")
                        else:
                            print(f"[WARN] 保存失败: {spec} + {color}")
                            
                    except Exception as e:
                        print(f"[ERROR] 处理组合失败 ({spec} + {color}): {e}")
                        continue
            
            # 更新处理结果
            if successful_count > 0:
                item['status'] = 'completed'
                item['processing_time'] = time.time() - start_time
                self._log_status(f"多规格处理完成: {item['input_path']} - 成功 {successful_count}/{total_combinations}", "success")
                return True
            else:
                raise Exception(f"所有组合都处理失败 (0/{total_combinations})")
                
        except Exception as e:
            item['status'] = 'failed'
            item['error'] = str(e)
            item['processing_time'] = time.time() - start_time
            
            self._log_status(f"多规格处理失败: {item['input_path']} - {e}", "error")
            import traceback
            traceback.print_exc()
            return False
    
    def _save_processed_image(self, image: np.ndarray, output_path: str) -> bool:
        """保存处理后的图像（支持中文路径）"""
        try:
            # 检查图像是否有效
            if image is None or not isinstance(image, np.ndarray) or image.size == 0:
                self._log_status("图像数据无效", "error")
                return False
            
            # 规范化路径（统一使用正斜杠或反斜杠）
            output_path = os.path.normpath(output_path)
            print(f"[DEBUG] 准备保存图像到: {output_path}")
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                if not os.path.exists(output_dir):
                    print(f"[DEBUG] 输出目录不存在，正在创建: {output_dir}")
                    os.makedirs(output_dir, exist_ok=True)
                    print(f"[INFO] 创建输出目录: {output_dir}")
                else:
                    print(f"[DEBUG] 输出目录已存在: {output_dir}")
            
            # 检查目录是否可写
            if not os.access(output_dir, os.W_OK):
                raise Exception(f"输出目录没有写入权限: {output_dir}")
            
            # 根据输出格式设置保存参数
            output_format = self.batch_params.get('output_format', 'jpg').lower()
            
            print(f"[DEBUG] 图像形状: {image.shape}, 数据类型: {image.dtype}")
            print(f"[DEBUG] 输出格式: {output_format}")
            
            # 使用 imencode + 文件写入来支持中文路径
            # 这是解决 OpenCV 不支持中文路径的标准方法
            if output_format == 'jpg' or output_format == 'jpeg':
                quality = self.batch_params.get('output_quality', 95)
                print(f"[DEBUG] JPEG质量: {quality}")
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                success, encoded_image = cv2.imencode('.jpg', image, encode_param)
            elif output_format == 'png':
                compression = 9 - (self.batch_params.get('output_quality', 95) // 10)
                print(f"[DEBUG] PNG压缩: {compression}")
                encode_param = [int(cv2.IMWRITE_PNG_COMPRESSION), compression]
                success, encoded_image = cv2.imencode('.png', image, encode_param)
            else:
                print(f"[DEBUG] 使用默认格式保存")
                success, encoded_image = cv2.imencode('.jpg', image)
            
            if not success:
                raise Exception(f"cv2.imencode 失败")
            
            # 写入文件（支持中文路径）
            with open(output_path, 'wb') as f:
                f.write(encoded_image.tobytes())
            
            # 验证文件是否真的被创建
            if not os.path.exists(output_path):
                raise Exception(f"文件保存后不存在: {output_path}")
            
            file_size = os.path.getsize(output_path)
            print(f"[DEBUG] 文件保存成功: {output_path} ({file_size} bytes)")
            
            return True
        except Exception as e:
            self._log_status(f"保存图像失败: {e}", "error")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_output_path(self, output_dir: str, base_name: str, 
                            format_ext: str) -> str:
        """生成输出文件路径"""
        # 规范化输出目录路径
        output_dir = os.path.normpath(output_dir)
        
        # 添加处理参数到文件名，使用英文避免编码问题
        spec = self.batch_params.get('crop_spec', '一寸')
        bg_color = self.batch_params.get('background_color', 'white')
        
        # 映射中文规格到英文
        spec_mapping = {
            '一寸': '1inch',
            '小二寸': 'small2inch', 
            '二寸': '2inch',
            '大一寸': 'large1inch'
        }
        spec_en = spec_mapping.get(spec, spec)
        
        filename = f"{base_name}_{spec_en}_{bg_color}.{format_ext}"
        output_path = os.path.join(output_dir, filename)
        
        # 再次规范化完整路径
        return os.path.normpath(output_path)
    
    def _validate_image_file(self, filepath: str) -> bool:
        """验证图像文件"""
        if not os.path.exists(filepath):
            return False
        
        # 检查文件扩展名
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext not in valid_extensions:
            return False
        
        # 尝试读取图像
        try:
            img = cv2.imread(filepath)
            return img is not None and img.size > 0
        except:
            return False
    
    def _update_progress(self, current: int, total: int, current_file: str):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(current, total, current_file)
    
    def _log_status(self, message: str, level: str = "info"):
        """记录状态信息"""
        if self.status_callback:
            self.status_callback(message, level)
        
        # 同时输出到控制台
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level.upper()}] {message}")
    
    def _reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_files': len(self.image_queue),
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'processing_time': 0,
            'average_time_per_file': 0
        }
    
    def _finalize_processing(self):
        """完成处理"""
        if self.should_stop:
            self._log_status("批量处理已停止", "warning")
        else:
            self._log_status("批量处理已完成", "success")
        
        # 生成处理报告
        self._generate_processing_report()
    
    def _generate_processing_report(self):
        """生成处理报告"""
        report = {
            'processing_summary': self.stats,
            'batch_parameters': self.batch_params,
            'processing_results': []
        }
        
        for item in self.image_queue:
            if item['status'] != 'pending':
                report['processing_results'].append({
                    'input_file': os.path.basename(item['input_path']),
                    'output_file': os.path.basename(item['result_path']) if item['result_path'] else None,
                    'status': item['status'],
                    'processing_time': item['processing_time'],
                    'quality_score': item['quality_score'],
                    'file_size_reduction': self._calculate_size_reduction(item),
                    'error': item['error']
                })
        
        self.processing_results = report
        self._log_status(f"处理报告已生成: 成功 {self.stats['successful_files']}/{self.stats['total_files']}", "info")
    
    def _calculate_size_reduction(self, item: Dict) -> float:
        """计算文件大小变化百分比"""
        if item['file_size_before'] > 0 and item['file_size_after'] > 0:
            reduction = (item['file_size_before'] - item['file_size_after']) / item['file_size_before']
            return round(reduction * 100, 2)
        return 0.0
    
    def get_processing_status(self) -> Dict:
        """获取处理状态"""
        return {
            'is_processing': self.is_processing,
            'current_index': self.current_index,
            'total_files': len(self.image_queue),
            'stats': self.stats,
            'estimated_time_remaining': self._estimate_remaining_time()
        }
    
    def _estimate_remaining_time(self) -> float:
        """估算剩余处理时间"""
        if not self.is_processing or self.stats['processed_files'] == 0:
            return 0.0
        
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        avg_time = elapsed_time / self.stats['processed_files']
        remaining_files = self.stats['total_files'] - self.stats['processed_files']
        
        return remaining_files * avg_time
    
    def get_queue_info(self) -> List[Dict]:
        """获取队列信息"""
        return [{
            'index': i,
            'filename': os.path.basename(item['input_path']),
            'status': item['status'],
            'file_size': item['file_size_before'],
            'error': item['error']
        } for i, item in enumerate(self.image_queue)]
    
    def export_results(self, export_path: str) -> bool:
        """导出处理结果"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.processing_results, f, indent=2, ensure_ascii=False)
            
            self._log_status(f"处理结果已导出到: {export_path}", "success")
            return True
        except Exception as e:
            self._log_status(f"导出结果失败: {e}", "error")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的输出格式"""
        return ['jpg', 'jpeg', 'png', 'bmp', 'tiff']
    
    def estimate_processing_time(self) -> float:
        """估算总处理时间"""
        # 基于文件数量和平均处理时间估算
        base_time_per_file = 2.0  # 基础处理时间（秒）
        
        # 根据处理参数调整时间
        time_multiplier = 1.0
        
        # 背景模式时间调整
        bg_mode = self.batch_params.get('background_mode', 'auto')
        if bg_mode == 'refined':
            time_multiplier += 1.5  # 精细模式增加1.5倍时间
        elif bg_mode == 'auto':
            time_multiplier += 0.8  # 智能模式增加0.8倍时间
        # 快速模式不增加时间
        
        if self.batch_params.get('beautify_enabled', False):
            time_multiplier += 0.5
        if self.batch_params.get('auto_enhance', False):
            time_multiplier += 0.3
        
        return len(self.image_queue) * base_time_per_file * time_multiplier