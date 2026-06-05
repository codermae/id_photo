"""
图像处理视图
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QSlider, QGroupBox, QMessageBox, 
                             QFileDialog, QSpinBox, QCheckBox, QRadioButton, QButtonGroup, QGridLayout, QDialog, 
                             QInputDialog, QScrollArea, QProgressDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from controllers.image_processor import ImageProcessor
from controllers.ai_processor import AIProcessor
from utils.file_helper import FileHelper
from utils.database_helper import DatabaseHelper
from views.crop_dialog import CropDialog
from config.config import PHOTO_SPECS, BACKGROUND_COLORS
import cv2
import os
import os

class ProcessView(QWidget):
    """图像处理视图"""

    def __init__(self):
        super().__init__()
        self.ai_processor = AIProcessor()  # 初始化 AI 处理器
        self.processor = ImageProcessor(ai_processor=self.ai_processor)
        self.current_image_path = None
        self.current_user_id = None  # 添加当前用户ID跟踪
        self.current_collection_id = None  # 添加当前采集任务ID跟踪
        self.original_image = None  # 保存原始图像
        self.is_comparing = False  # 对比模式标志
        try:
            self.init_ui()
            print("[DEBUG] init_ui 调用成功")
        except Exception as e:
            print(f"[ERROR] init_ui 调用失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    def init_ui(self):
        """初始化界面"""
        print("[DEBUG] 开始初始化UI...")
        main_layout = QHBoxLayout(self)
        
        # 左侧：图像预览和基本控制
        left_layout = QVBoxLayout()
        
        # 采集任务和加载图像合并到一行
        top_control_layout = QHBoxLayout()
        
        # 采集任务（紧凑版）
        top_control_layout.addWidget(QLabel("任务:"))
        self.collection_combo = QComboBox()
        self.collection_combo.setMinimumWidth(150)
        self.collection_combo.currentIndexChanged.connect(self.on_collection_changed)
        top_control_layout.addWidget(self.collection_combo)
        
        top_control_layout.addSpacing(10)
        
        # 加载图像按钮
        load_btn = QPushButton("选择图像")
        load_btn.clicked.connect(self.load_image)
        top_control_layout.addWidget(load_btn)
        
        # 对比按钮
        self.compare_btn = QPushButton("对比")
        self.compare_btn.setEnabled(False)
        # 长按显示原图（不再左右双图同时展示）
        self.compare_btn.pressed.connect(self._on_compare_pressed)
        self.compare_btn.released.connect(self._on_compare_released)
        top_control_layout.addWidget(self.compare_btn)
        
        top_control_layout.addStretch()
        left_layout.addLayout(top_control_layout)
        
        # 图像预览（减小尺寸）
        self.preview_container = QWidget()
        self.preview_container_layout = QHBoxLayout(self.preview_container)
        self.preview_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(350, 400)  # 从400x500减小到350x400
        self.preview_label.setStyleSheet("border: 1px solid #ddd; background-color: #f0f0f0;")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_container_layout.addWidget(self.preview_label)
        
        # 原图预览标签（初始隐藏）
        self.original_preview_label = QLabel()
        self.original_preview_label.setMinimumSize(350, 400)
        self.original_preview_label.setStyleSheet("border: 1px solid #ddd; background-color: #f0f0f0;")
        self.original_preview_label.setAlignment(Qt.AlignCenter)
        self.original_preview_label.setVisible(False)
        self.preview_container_layout.addWidget(self.original_preview_label)
        
        left_layout.addWidget(self.preview_container)
        
        # 质量评分（紧凑版）- 显示总体评分和详细指标
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("质量:"))
        self.quality_label = QLabel("未加载")
        self.quality_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        quality_layout.addWidget(self.quality_label)
        
        # 详细指标
        quality_layout.addSpacing(15)
        quality_layout.addWidget(QLabel("清晰度:"))
        self.sharpness_label = QLabel("0")
        quality_layout.addWidget(self.sharpness_label)
        
        quality_layout.addSpacing(15)
        quality_layout.addWidget(QLabel("亮度:"))
        self.brightness_label = QLabel("0")
        quality_layout.addWidget(self.brightness_label)
        
        quality_layout.addSpacing(15)
        quality_layout.addWidget(QLabel("对比度:"))
        self.contrast_label = QLabel("0")
        quality_layout.addWidget(self.contrast_label)
        
        quality_layout.addStretch()
        left_layout.addLayout(quality_layout)
        
        # 右侧：处理参数（使用滚动区域）
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(8)  # 减小间距
        
        # 规格选择（紧凑版 - 单选）
        spec_group = QGroupBox("规格（单选）")
        print("[DEBUG] 创建规格组...")
        spec_layout = QVBoxLayout()
        spec_layout.setSpacing(4)
        
        # 规格单选按钮（折叠显示相同尺寸，保留tooltip）
        print("[DEBUG] 开始创建规格单选按钮...")
        spec_grid = QGridLayout()
        spec_grid.setSpacing(2)
        
        self.spec_radio_buttons = {}
        self.spec_button_group = QButtonGroup(self)  # 创建按钮组实现单选
        print(f"[DEBUG] 初始化 spec_radio_buttons: {type(self.spec_radio_buttons)}")
        print("[DEBUG] 准备进入 try 块...")
        
        try:
            from collections import defaultdict
            size_groups = defaultdict(list)
            for spec_name, size in PHOTO_SPECS.items():
                size_groups[size].append(spec_name)
            
            print(f"[DEBUG] 规格分组完成，共 {len(size_groups)} 个不同尺寸")
            
            row, col = 0, 0
            for size, specs in size_groups.items():
                # 新格式: "590x826px 一寸"
                size_str = f"{size[0]}x{size[1]}px"
                
                if len(specs) == 1:
                    display_name = f"{size_str} {specs[0]}"
                    tooltip = f"尺寸: {size[0]}×{size[1]}px"
                else:
                    display_name = f"{size_str} {specs[0]}"
                    tooltip = f"相同尺寸 {size[0]}×{size[1]}px (共{len(specs)}种):\n" + "\n".join(specs)
                
                radio_button = QRadioButton(display_name)
                radio_button.setToolTip(tooltip)
                radio_button.spec_name = specs[0]  # 保存实际规格名
                
                # 默认选中一寸（精确匹配，不包括"大一寸"）
                if specs[0] == "一寸":
                    radio_button.setChecked(True)
                
                size_key = f"{size[0]}x{size[1]}"
                self.spec_radio_buttons[size_key] = radio_button
                self.spec_button_group.addButton(radio_button)
                spec_grid.addWidget(radio_button, row, col)
                
                col += 1
                if col >= 3:  # 每行3个
                    col = 0
                    row += 1
            
            print(f"[DEBUG] spec_radio_buttons 创建完成，共 {len(self.spec_radio_buttons)} 个")
            spec_layout.addLayout(spec_grid)
            print("[DEBUG] spec_grid 添加到布局完成")
        except Exception as e:
            print(f"[ERROR] 创建规格单选按钮失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        spec_group.setLayout(spec_layout)
        right_layout.addWidget(spec_group)
        
        # 背景色选择（紧凑版 - 单选）
        bg_group = QGroupBox("背景色（单选）")
        bg_layout = QVBoxLayout()
        bg_layout.setSpacing(4)
        
        # 背景色单选按钮（紧凑布局）
        bg_grid = QGridLayout()
        bg_grid.setSpacing(2)
        
        self.bg_radio_buttons = {}
        self.bg_button_group = QButtonGroup(self)  # 创建按钮组实现单选
        row, col = 0, 0
        
        for color_name in BACKGROUND_COLORS.keys():
            radio_button = QRadioButton(color_name)
            
            # 默认选中灰色
            if color_name == '灰色':
                radio_button.setChecked(True)
            
            self.bg_radio_buttons[color_name] = radio_button
            self.bg_button_group.addButton(radio_button)
            bg_grid.addWidget(radio_button, row, col)
            
            col += 1
            if col >= 3:  # 每行3个
                col = 0
                row += 1
        
        bg_layout.addLayout(bg_grid)
        
        # 高级背景选项（保持复选框，可多选）
        advanced_bg_label = QLabel("高级背景效果（可多选）:")
        advanced_bg_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #333;")
        bg_layout.addWidget(advanced_bg_label)
        
        advanced_bg_layout = QHBoxLayout()
        advanced_bg_layout.setSpacing(2)
        
        self.gradient_check = QCheckBox("渐变")
        self.gradient_check.setToolTip("使用渐变背景（从一种颜色渐变到另一种颜色）")
        advanced_bg_layout.addWidget(self.gradient_check)
        
        self.texture_check = QCheckBox("纹理")
        self.texture_check.setToolTip("使用纹理背景（需要提供纹理图像）")
        advanced_bg_layout.addWidget(self.texture_check)
        
        self.blur_check = QCheckBox("虚化")
        self.blur_check.setToolTip("使用虚化背景（模糊原始背景）")
        advanced_bg_layout.addWidget(self.blur_check)
        
        advanced_bg_layout.addStretch()
        bg_layout.addLayout(advanced_bg_layout)
        
        # 处理模式和Alpha Matte在同一行
        mode_alpha_layout = QHBoxLayout()
        
        self.alpha_matting_check = QCheckBox("Alpha Matte边缘增强")
        self.alpha_matting_check.setChecked(True)
        mode_alpha_layout.addWidget(self.alpha_matting_check)
        
        mode_alpha_layout.addStretch()
        
        mode_alpha_layout.addWidget(QLabel("模式:"))
        self.bg_mode_combo = QComboBox()
        self.bg_mode_combo.addItems(['精细', '高保真'])
        self.bg_mode_combo.setCurrentIndex(0)
        self.bg_mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_alpha_layout.addWidget(self.bg_mode_combo)
        
        bg_layout.addLayout(mode_alpha_layout)
        
        bg_group.setLayout(bg_layout)
        right_layout.addWidget(bg_group)
        
        # 美颜选项（紧凑版）
        beautify_group = QGroupBox("美颜")
        beautify_layout = QGridLayout()
        beautify_layout.setSpacing(4)
        
        self.skin_smooth_check = QCheckBox("磨皮")
        self.skin_smooth_check.setChecked(False)
        beautify_layout.addWidget(self.skin_smooth_check, 0, 0)
        
        self.smooth_strength_slider = QSlider(Qt.Horizontal)
        self.smooth_strength_slider.setRange(0, 100)
        self.smooth_strength_slider.setValue(30)
        beautify_layout.addWidget(self.smooth_strength_slider, 0, 1)
        
        self.smooth_strength_label = QLabel("0.3")
        self.smooth_strength_label.setMinimumWidth(30)
        beautify_layout.addWidget(self.smooth_strength_label, 0, 2)
        
        self.remove_blemishes_check = QCheckBox("祛痘")
        self.remove_blemishes_check.setChecked(False)
        beautify_layout.addWidget(self.remove_blemishes_check, 1, 0)
        
        self.blemish_strength_slider = QSlider(Qt.Horizontal)
        self.blemish_strength_slider.setRange(0, 100)
        self.blemish_strength_slider.setValue(50)
        beautify_layout.addWidget(self.blemish_strength_slider, 1, 1)
        
        self.blemish_strength_label = QLabel("0.5")
        self.blemish_strength_label.setMinimumWidth(30)
        beautify_layout.addWidget(self.blemish_strength_label, 1, 2)
        
        # 连接信号
        self.smooth_strength_slider.valueChanged.connect(
            lambda v: self.smooth_strength_label.setText(f"{v/100:.1f}")
        )
        self.blemish_strength_slider.valueChanged.connect(
            lambda v: self.blemish_strength_label.setText(f"{v/100:.1f}")
        )
        
        beautify_group.setLayout(beautify_layout)
        right_layout.addWidget(beautify_group)
        
        # 亮度和对比度（紧凑版）
        adjust_group = QGroupBox("调整")
        adjust_layout = QGridLayout()
        adjust_layout.setSpacing(4)
        
        adjust_layout.addWidget(QLabel("亮度:"), 0, 0)
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        adjust_layout.addWidget(self.brightness_slider, 0, 1)
        self.brightness_adjust_label = QLabel("0")  # 改名为 brightness_adjust_label
        self.brightness_adjust_label.setMinimumWidth(30)
        adjust_layout.addWidget(self.brightness_adjust_label, 0, 2)
        
        adjust_layout.addWidget(QLabel("对比度:"), 1, 0)
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-100, 100)  # 改为 -100 到 100
        self.contrast_slider.setValue(0)  # 改为 0（中立）
        self.contrast_slider.valueChanged.connect(self.on_contrast_changed)
        adjust_layout.addWidget(self.contrast_slider, 1, 1)
        self.contrast_adjust_label = QLabel("0")  # 改名为 contrast_adjust_label
        self.contrast_adjust_label.setMinimumWidth(30)
        adjust_layout.addWidget(self.contrast_adjust_label, 1, 2)
        
        adjust_group.setLayout(adjust_layout)
        right_layout.addWidget(adjust_group)
        
        # 处理和保存按钮（合并）
        action_group = QGroupBox("操作")
        action_layout = QGridLayout()
        action_layout.setSpacing(4)
        
        self.process_btn = QPushButton("一键处理")
        self.process_btn.clicked.connect(self.apply_processing)
        self.process_btn.setEnabled(False)
        action_layout.addWidget(self.process_btn, 0, 0)
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_image)
        self.reset_btn.setEnabled(False)
        action_layout.addWidget(self.reset_btn, 0, 1)
        
        self.manual_crop_btn = QPushButton("裁剪")
        self.manual_crop_btn.clicked.connect(self.manual_crop)
        self.manual_crop_btn.setEnabled(False)
        action_layout.addWidget(self.manual_crop_btn, 1, 0)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)
        action_layout.addWidget(self.save_btn, 1, 1)
        
        action_group.setLayout(action_layout)
        right_layout.addWidget(action_group)
        
        # 批量处理按钮（紧凑版）
        unified_batch_btn = QPushButton("多规格批量生成")
        unified_batch_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        unified_batch_btn.clicked.connect(self.open_unified_batch_processing)
        right_layout.addWidget(unified_batch_btn)
        
        right_layout.addStretch()
        
        right_scroll.setWidget(right_widget)
        
        # 添加到主布局
        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(right_scroll, 1)
        
        # 加载采集任务
        self.load_collections()

    def _on_mode_changed(self, index):
        """切换模式时显示/隐藏对应选项"""
        is_hifi = self.bg_mode_combo.currentText() in ['高保真模式', '高保真']
        self.alpha_matting_check.setVisible(not is_hifi)

    def load_image(self):
        """加载图像"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择图像", "", "图像文件 (*.jpg *.png *.bmp)"
        )
        
        if filepath:
            try:
                image = self.processor.load_image(filepath)
                self.current_image_path = filepath
                self.original_image = image.copy()  # 保存原始图像
                
                # 从文件名中提取身份证号或用户ID
                filename = os.path.basename(filepath)
                # 支持两种文件名格式:
                # 1. raw_{user_id}_{timestamp}.jpg (测试数据格式)
                # 2. {id_number}_{timestamp}.jpg (实际拍照格式)
                parts = filename.split('_')
                self.current_user_id = None
                user_name = None
                
                db = DatabaseHelper()
                
                # 格式1: raw_{user_id}_{timestamp}.jpg
                if filename.startswith('raw_') and len(parts) >= 3:
                    try:
                        user_id = int(parts[1])
                        user = db.get_user_by_id(user_id)
                        if user:
                            # 检查用户是否属于当前采集任务
                            if self.current_collection_id is None or user.collection_id == self.current_collection_id:
                                print(f"[DEBUG] 用户找到 (通过user_id): {user.name} (ID: {user.id})")
                                user_name = user.name
                                self.current_user_id = user.id
                                print(f"[INFO] 用户识别成功: {user.name} (用户ID: {user_id})")
                            else:
                                print(f"[WARNING] 用户 {user.name} 不属于当前采集任务")
                                QMessageBox.warning(
                                    self,
                                    "警告",
                                    f"用户 {user.name} 不属于选定的采集任务\n\n请选择正确的采集任务"
                                )
                                db.close()
                                return
                        else:
                            print(f"[WARNING] 用户ID {user_id} 不存在")
                            QMessageBox.warning(
                                self,
                                "警告",
                                f"用户ID {user_id} 不存在数据库中"
                            )
                            db.close()
                            return
                    except (ValueError, IndexError) as e:
                        print(f"[WARNING] 无法解析用户ID: {filename}, 错误: {e}")
                        QMessageBox.warning(
                            self,
                            "警告",
                            f"文件名格式错误，无法解析用户ID\n\n格式应为: raw_{{用户ID}}_{{时间戳}}.jpg"
                        )
                        db.close()
                        return
                
                # 格式2: {id_number}_{timestamp}.jpg
                elif len(parts) >= 2:
                    potential_id = parts[0]
                    # 验证是否是有效的身份证号（15或18位数字）
                    if potential_id.isdigit() and len(potential_id) in [15, 18]:
                        print(f"[DEBUG] 查询身份证号: {potential_id}")
                        print(f"[DEBUG] 采集任务ID: {self.current_collection_id}")
                        
                        # 按照身份证号和采集任务一起查询
                        user = db.get_user_by_id_number(potential_id, collection_id=self.current_collection_id)
                        
                        if user:
                            print(f"[DEBUG] 用户找到: {user.name} (ID: {user.id}, 采集任务ID: {user.collection_id})")
                            user_name = user.name
                            self.current_user_id = user.id
                            print(f"[INFO] 用户识别成功: {user.name} (身份证: {potential_id})")
                        else:
                            print(f"[WARNING] 身份证号 {potential_id} 在采集任务中不存在")
                            QMessageBox.warning(
                                self,
                                "警告",
                                f"身份证号 {potential_id} 在选定的采集任务中不存在\n\n请检查：\n1. 是否选择了正确的采集任务\n2. 用户是否已添加到该采集任务"
                            )
                            db.close()
                            return
                    else:
                        print(f"[WARNING] 无法从文件名中提取有效的身份证号: {filename}")
                        QMessageBox.warning(
                            self,
                            "警告",
                            f"文件名格式错误，无法识别身份证号\n\n支持的格式：\n1. raw_{{用户ID}}_{{时间戳}}.jpg\n2. {{身份证号}}_{{时间戳}}.jpg"
                        )
                        db.close()
                        return
                else:
                    print(f"[WARNING] 文件名格式不符合预期: {filename}")
                    QMessageBox.warning(
                        self,
                        "警告",
                        f"文件名格式错误\n\n支持的格式：\n1. raw_{{用户ID}}_{{时间戳}}.jpg\n2. {{身份证号}}_{{时间戳}}.jpg"
                    )
                    db.close()
                    return
                
                db.close()
                
                # 只有用户识别成功才显示图像
                self.display_image(image)
                self.display_original_image(self.original_image)  # 显示原图
                self.update_quality_score()
                
                self.manual_crop_btn.setEnabled(True)  # 启用手动裁剪按钮
                self.process_btn.setEnabled(True)
                self.reset_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
                self.compare_btn.setEnabled(True)  # 启用对比按钮
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载图像失败: {e}")
                import traceback
                traceback.print_exc()

    def display_image(self, image):
        """显示图像"""
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = 3 * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaledToWidth(400, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"显示图像失败: {e}")

    def display_original_image(self, image):
        """显示原始图像"""
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = 3 * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaledToWidth(400, Qt.SmoothTransformation)
            self.original_preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"显示原始图像失败: {e}")

    def _on_compare_pressed(self):
        """长按：只显示原图"""
        if self.original_image is None:
            QMessageBox.warning(self, "警告", "没有原始图像可供对比")
            return

        self.is_comparing = True

        # 只展示原图，避免出现“处理后+原图”两张同时展示
        self.preview_label.setVisible(False)
        self.original_preview_label.setVisible(True)

        # 兼容旧的左右对比模式（如果页面中已插入对应label）
        if hasattr(self, 'processed_label'):
            self.processed_label.setVisible(False)
        if hasattr(self, 'original_label'):
            self.original_label.setVisible(True)

    def _on_compare_released(self):
        """松开：恢复显示处理后图像"""
        self.is_comparing = False

        self.original_preview_label.setVisible(False)
        self.preview_label.setVisible(True)

        # 兼容旧的左右对比模式（如果页面中已插入对应label）
        if hasattr(self, 'processed_label'):
            self.processed_label.setVisible(True)
        if hasattr(self, 'original_label'):
            self.original_label.setVisible(False)

    def toggle_compare_view(self):
        """切换对比视图"""
        if self.original_image is None:
            QMessageBox.warning(self, "警告", "没有原始图像可供对比")
            return
        
        self.is_comparing = not self.is_comparing
        
        if self.is_comparing:
            # 显示对比模式
            self.original_preview_label.setVisible(True)
            self.compare_btn.setText("📷 关闭")
            
            # 添加标签
            if not hasattr(self, 'processed_label'):
                self.processed_label = QLabel("处理后")
                self.processed_label.setAlignment(Qt.AlignCenter)
                self.processed_label.setStyleSheet("font-weight: bold; color: #007bff;")
                self.preview_container_layout.insertWidget(0, self.processed_label)
                
                self.original_label = QLabel("原图")
                self.original_label.setAlignment(Qt.AlignCenter)
                self.original_label.setStyleSheet("font-weight: bold; color: #28a745;")
                self.preview_container_layout.addWidget(self.original_label)
            else:
                self.processed_label.setVisible(True)
                self.original_label.setVisible(True)
        else:
            # 隐藏对比模式
            self.original_preview_label.setVisible(False)
            self.compare_btn.setText("📷 对比")
            
            if hasattr(self, 'processed_label'):
                self.processed_label.setVisible(False)
                self.original_label.setVisible(False)

    def update_quality_score(self):
        """更新质量评分 - 显示详细指标"""
        quality_info = self.processor.get_quality_score()
        
        print(f"[DEBUG] update_quality_score 收到的数据: {quality_info}, 类型: {type(quality_info)}")
        print(f"[DEBUG] 标签对象 - quality_label: {self.quality_label}, sharpness_label: {self.sharpness_label}, brightness_label: {self.brightness_label}, contrast_label: {self.contrast_label}")
        
        # 处理新旧格式兼容
        if isinstance(quality_info, dict):
            overall_score = quality_info.get('overall_score', 0)
            sharpness = quality_info.get('sharpness', 0)
            brightness = quality_info.get('brightness', 0)
            contrast = quality_info.get('contrast', 0)
            print(f"[DEBUG] 字典格式 - 总体: {overall_score}, 清晰度: {sharpness}, 亮度: {brightness}, 对比度: {contrast}")
        else:
            overall_score = quality_info if quality_info else 0
            sharpness = brightness = contrast = 0
            print(f"[DEBUG] 非字典格式 - 总体: {overall_score}")
        
        # 设置颜色
        if overall_score >= 70:
            color = "green"
        elif overall_score >= 50:
            color = "orange"
        else:
            color = "red"
        
        # 显示总体评分
        quality_text = f"<span style='color: {color}; font-weight: bold;'>{overall_score}/100</span>"
        self.quality_label.setText(quality_text)
        print(f"[DEBUG] 设置quality_label文本: {quality_text}")
        
        # 显示详细指标
        self.sharpness_label.setText(f"{sharpness}")
        self.brightness_label.setText(f"{brightness}")
        self.contrast_label.setText(f"{contrast}")
        
        print(f"[DEBUG] 设置标签文本 - 清晰度: {sharpness}, 亮度: {brightness}, 对比度: {contrast}")
        print(f"[DEBUG] 标签当前文本 - quality: {self.quality_label.text()}, sharpness: {self.sharpness_label.text()}, brightness: {self.brightness_label.text()}, contrast: {self.contrast_label.text()}")
        print(f"[DEBUG] UI已更新 - 质量标签: {overall_score}/100, 清晰度: {sharpness}, 亮度: {brightness}, 对比度: {contrast}")

    def apply_processing(self):
        """应用处理"""
        if self.processor.current_image is None:
            QMessageBox.warning(self, "警告", "没有加载图像")
            return

        # 获取选中的规格和颜色（单选）
        selected_spec = None
        for rb in self.spec_radio_buttons.values():
            if rb.isChecked():
                selected_spec = rb.spec_name
                break
        
        selected_color = None
        for name, rb in self.bg_radio_buttons.items():
            if rb.isChecked():
                selected_color = name
                break
        
        if not selected_spec:
            QMessageBox.warning(self, "警告", "请选择一个规格")
            return
        
        if not selected_color:
            QMessageBox.warning(self, "警告", "请选择一个背景色")
            return
        
        # 单规格单颜色处理
        try:
            spec = selected_spec
            bg_color = selected_color
            
            # 新的美颜处理 - 使用独立控制
            beautify_options = {
                'skin_smooth': self.skin_smooth_check.isChecked(),
                'remove_blemishes': self.remove_blemishes_check.isChecked(),
            }
            
            beautify_strengths = {
                'smooth_strength': self.smooth_strength_slider.value() / 100.0,
                'blemish_strength': self.blemish_strength_slider.value() / 100.0,
            }
            
            # 裁切
            self.processor.crop_to_spec(spec)
            
            # 更换背景
            mode = self.bg_mode_combo.currentText()
            if mode in ['高保真模式', '高保真']:
                print("[INFO] 使用高保真管线（InsightFace + MODNet + CodeFormer）")
                success, info = self.processor.change_background_hifi(
                    bg_color,
                    beautify_options=beautify_options,
                    beautify_strengths=beautify_strengths,
                )
                if not success:
                    raise Exception(info.get('error', '高保真处理失败'))
            else:
                # 精细模式：先美颜再换背景
                if any(beautify_options.values()):
                    print(f"[DEBUG] 应用美颜选项: {beautify_options}")
                    self.processor.apply_selective_beautify(beautify_options, beautify_strengths)
                use_alpha_matting = self.alpha_matting_check.isChecked()
                print("[INFO] 使用精细模式进行背景替换")
                self.processor.change_background(bg_color, method='refined', use_alpha_matting=use_alpha_matting)
            
            # 应用高级背景效果
            self._apply_advanced_background_effects()
            
            # 显示处理后的图像
            self.display_image(self.processor.get_current_image())
            self.update_quality_score()
            
            # 关键修改：更新realtime_adjuster的基础图像为处理后的图像
            # 这样后续的亮度/对比度调整就会基于处理后的图像
            self.processor.realtime_adjuster.set_image(self.processor.get_current_image())
            
            # 重置亮度和对比度滑块
            self.brightness_slider.blockSignals(True)
            self.contrast_slider.blockSignals(True)
            self.brightness_slider.setValue(0)
            self.contrast_slider.setValue(0)
            self.brightness_slider.blockSignals(False)
            self.contrast_slider.blockSignals(False)
            
            print("[INFO] 处理完成，已更新亮度/对比度基础图像")
            
            QMessageBox.information(self, "成功", "图像处理完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_multi_spec(self, selected_specs, selected_colors):
        """直接生成多规格照片"""
        try:
            from controllers.image_processor import ImageProcessor
            from utils.file_helper import FileHelper
            from utils.database_helper import DatabaseHelper
            import time
            
            # 检查用户是否存在
            if self.current_user_id is None:
                QMessageBox.warning(self, "警告", "用户不存在，无法生成照片")
                return
            
            total = len(selected_specs) * len(selected_colors)
            
            # 获取用户信息
            db = DatabaseHelper()
            user = db.get_user_by_id(self.current_user_id)
            if not user:
                QMessageBox.warning(self, "错误", f"用户ID {self.current_user_id} 不存在")
                db.close()
                return
            
            user_id_number = user.id_number
            user_name = user.name
            db.close()
            
            print(f"[INFO] 开始多规格生成: 用户={user_name}, 规格数={len(selected_specs)}, 颜色数={len(selected_colors)}")
            
            # 创建进度对话框
            from PyQt5.QtWidgets import QProgressDialog
            progress = QProgressDialog("正在生成照片...", "取消", 0, total, self)
            progress.setWindowTitle("多规格生成")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            
            generated_files = []
            current = 0
            
            # 获取美颜选项
            beautify_options = {
                'skin_smooth': self.skin_smooth_check.isChecked(),
                'remove_blemishes': self.remove_blemishes_check.isChecked(),
            }
            
            beautify_strengths = {
                'smooth_strength': self.smooth_strength_slider.value() / 100.0,
                'blemish_strength': self.blemish_strength_slider.value() / 100.0,
            }
            
            mode = self.bg_mode_combo.currentText()
            use_alpha_matting = self.alpha_matting_check.isChecked()
            
            # 生成所有组合
            for spec in selected_specs:
                for color in selected_colors:
                    if progress.wasCanceled():
                        break
                    
                    current += 1
                    progress.setValue(current)
                    progress.setLabelText(f"生成 {spec} - {color} ({current}/{total})")
                    
                    # 创建新的处理器实例
                    ai_processor = AIProcessor()
                    processor = ImageProcessor(ai_processor=ai_processor)
                    processor.load_image_from_array(self.original_image.copy())
                    
                    # 应用美颜
                    if any(beautify_options.values()):
                        processor.apply_selective_beautify(beautify_options, beautify_strengths)
                    
                    # 裁剪
                    processor.crop_to_spec(spec)
                    
                    # 更换背景
                    if mode == '高保真模式':
                        processor.change_background_hifi(color, beautify_options=beautify_options, beautify_strengths=beautify_strengths)
                    else:
                        processor.change_background(color, method='refined', use_alpha_matting=use_alpha_matting)
                    
                    # 保存文件
                    try:
                        filepath = FileHelper.save_processed_photo(
                            user_id_number,
                            processor.current_image,
                            spec=spec,
                            bg_color=color
                        )
                        generated_files.append({
                            'spec': spec,
                            'color': color,
                            'filepath': filepath
                        })
                    except Exception as e:
                        print(f"保存失败 {spec}-{color}: {e}")
                    
                    time.sleep(0.01)  # 让界面更新
            
            progress.close()
            
            # 显示结果
            if generated_files:
                QMessageBox.information(
                    self, "生成完成", 
                    f"成功生成 {len(generated_files)} 张照片！\n\n"
                    f"规格: {', '.join(selected_specs)}\n"
                    f"颜色: {', '.join(selected_colors)}"
                )
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    def apply_multi_spec_processing(self, selected_specs=None, selected_colors=None):
        """应用多规格处理（已废弃，保留兼容性）"""
        pass

    def reset_image(self):
        """重置图像"""
        self.processor.reset_image()
        
        # 重置realtime_adjuster的基础图像
        self.processor.realtime_adjuster.set_image(self.processor.get_current_image())
        
        self.display_image(self.processor.get_current_image())
        self.update_quality_score()
        
        # 重置滑块
        self.brightness_slider.blockSignals(True)
        self.contrast_slider.blockSignals(True)
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)
        self.brightness_slider.blockSignals(False)
        self.contrast_slider.blockSignals(False)

    def on_brightness_changed(self, value):
        """亮度改变"""
        self.brightness_adjust_label.setText(str(value))
        if self.processor.current_image is not None:
            self.processor.adjust_brightness(value)
            self.display_image(self.processor.get_current_image())

    def on_contrast_changed(self, value):
        """对比度改变"""
        self.contrast_adjust_label.setText(str(value))  # 直接显示值
        if self.processor.current_image is not None:
            self.processor.adjust_contrast(value)  # 直接传递值
            self.display_image(self.processor.get_current_image())

    def save_image(self):
        """保存图像"""
        if self.processor.current_image is None:
            QMessageBox.warning(self, "警告", "没有要保存的图像")
            return
        
        # 检查是否选择了采集任务
        if self.current_collection_id is None:
            QMessageBox.warning(self, "警告", "请先选择采集任务")
            return
        
        # 检查是否识别到用户
        if self.current_user_id is None:
            QMessageBox.warning(
                self, 
                "警告", 
                "用户不存在\n\n请确保：\n1. 加载了正确的图片文件\n2. 文件名包含身份证号\n3. 用户属于选定的采集任务"
            )
            return
        
        try:
            # 获取用户信息
            db = DatabaseHelper()
            user = db.get_user_by_id(self.current_user_id)
            
            if not user:
                QMessageBox.warning(self, "错误", f"用户ID {self.current_user_id} 不存在（数据库错误）")
                db.close()
                return
            
            # 再次验证用户是否属于选定的采集任务
            collection = db.get_collection_by_id(self.current_collection_id)
            if collection and hasattr(collection, 'users'):
                user_in_collection = user.id in [u.id for u in collection.users]
                if not user_in_collection:
                    QMessageBox.warning(
                        self,
                        "错误",
                        f"用户 {user.name} 不属于选定的采集任务\n\n请选择正确的采集任务"
                    )
                    db.close()
                    return
            
            # 在关闭数据库前保存用户信息
            user_name = user.name
            user_id_number = user.id_number
            
            # 获取当前选择的规格和背景色（单选）
            selected_spec = None
            for rb in self.spec_radio_buttons.values():
                if rb.isChecked():
                    selected_spec = rb.spec_name
                    break
            
            selected_color = None
            for name, rb in self.bg_radio_buttons.items():
                if rb.isChecked():
                    selected_color = name
                    break
            
            if not selected_spec:
                QMessageBox.warning(self, "警告", "请选择一个规格")
                db.close()
                return
            
            if not selected_color:
                QMessageBox.warning(self, "警告", "请选择一个背景色")
                db.close()
                return
            
            spec = selected_spec
            bg_color = selected_color
            
            print(f"[INFO] 开始保存处理后照片: 用户={user_name}, 规格={spec}, 背景={bg_color}")
            
            # 使用FileHelper保存处理后的照片
            filepath = FileHelper.save_processed_photo(
                user_id_number,
                self.processor.current_image,
                spec=spec,
                bg_color=bg_color
            )
            
            # 验证文件是否成功保存
            if not os.path.exists(filepath):
                raise Exception(f"文件保存失败，文件不存在: {filepath}")
            
            file_size = os.path.getsize(filepath)
            print(f"[INFO] 照片已保存: {filepath}, 大小: {file_size} bytes")
            
            # 添加照片记录
            photo = db.add_photo(
                user_id=self.current_user_id,
                photo_type='processed',
                file_path=filepath,
                file_size=file_size
            )
            print(f"[INFO] 添加照片记录: photo_id={photo.id}")
            
            # 创建或更新采集记录（处理后状态为已完成）
            existing_records = db.get_records_by_user(self.current_user_id)
            if existing_records:
                # 更新最新的记录为已完成
                latest_record = existing_records[-1]
                latest_record.status = 'completed'
                latest_record.notes = f'处理后照片已保存: {os.path.basename(filepath)}'
                db.db.commit()
                print(f"[INFO] 更新采集记录状态为 completed: record_id={latest_record.id}")
            else:
                # 创建新的采集记录
                import getpass
                operator = getpass.getuser()
                record = db.add_record(
                    user_id=self.current_user_id,
                    operator=operator,
                    status='completed',
                    notes=f'处理后照片已保存: {os.path.basename(filepath)}',
                    collection_id=self.current_collection_id
                )
                print(f"[INFO] 创建采集记录: record_id={record.id}, status=completed")
            
            db.close()
            
            # 通知主窗口更新统计
            self.notify_data_changed()
            
            # 使用保存的用户信息显示提示
            QMessageBox.information(
                self, 
                "保存成功", 
                f"照片已保存\n\n用户: {user_name}\n规格: {spec}\n背景: {bg_color}\n路径: {filepath}"
            )
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
            import traceback
            traceback.print_exc()

    def open_unified_batch_processing(self):
        """打开融合的批量处理窗口"""
        from views.unified_batch_dialog import UnifiedBatchDialog
        
        dialog = UnifiedBatchDialog(self)
        dialog.exec_()
    
    
    def _apply_advanced_background_effects(self):
        """应用高级背景效果（渐变、纹理、虚化）"""
        try:
            import cv2
            import numpy as np
            
            # 检查是否选择了高级背景效果
            gradient_enabled = self.gradient_check.isChecked()
            texture_enabled = self.texture_check.isChecked()
            blur_enabled = self.blur_check.isChecked()
            
            if not (gradient_enabled or texture_enabled or blur_enabled):
                print("[DEBUG] 没有选择任何高级背景效果")
                return  # 没有选择任何高级效果
            
            current_image = self.processor.get_current_image()
            if current_image is None:
                print("[WARNING] 当前图像为空")
                return
            
            # 检查是否有保存的mask
            if self.processor.current_mask is None:
                print("[WARNING] 没有保存的mask，无法应用高级背景效果")
                return
            
            print(f"[DEBUG] 高级背景效果: 渐变={gradient_enabled}, 纹理={texture_enabled}, 虚化={blur_enabled}")
            
            h, w = current_image.shape[:2]
            
            # 获取背景色（单选）
            selected_color = None
            for name, rb in self.bg_radio_buttons.items():
                if rb.isChecked():
                    selected_color = name
                    break
            
            if selected_color:
                from config.config import BACKGROUND_COLORS
                # 转换RGB到BGR
                color1_rgb = BACKGROUND_COLORS.get(selected_color, (67, 142, 219))
                color1 = (color1_rgb[2], color1_rgb[1], color1_rgb[0])  # RGB转BGR
            else:
                color1 = (67, 142, 219)  # 默认蓝色
            
            # 使用保存的mask
            print("[DEBUG] 使用保存的mask进行高级背景效果处理...")
            try:
                # 获取mask并归一化到0-1
                mask = self.processor.current_mask.astype(np.float32) / 255.0
                person_mask_float = mask
                
                print(f"[DEBUG] mask获取成功，人物像素比例: {np.mean(person_mask_float)*100:.1f}%")
                
            except Exception as e:
                print(f"[ERROR] mask处理失败: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # 创建纯色背景
            background = np.full((h, w, 3), color1, dtype=np.uint8)
            
            # 应用虚化效果
            if blur_enabled:
                print("[INFO] 应用虚化背景效果")
                try:
                    # 虚化效果：创建一个有微妙纹理变化的背景，然后模糊
                    # 这样可以看出虚化的效果
                    
                    # 1. 创建基础背景
                    blur_bg = background.copy()
                    
                    # 2. 添加微妙的纹理变化（这样模糊后才能看出效果）
                    noise = np.random.randint(-10, 10, (h, w, 3), dtype=np.int16)
                    blur_bg = np.clip(blur_bg.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                    
                    # 3. 进行高斯模糊
                    blurred_bg = cv2.GaussianBlur(blur_bg, (51, 51), 0)
                    background = blurred_bg
                    print(f"[INFO] 虚化效果应用完成")
                except Exception as e:
                    print(f"[ERROR] 虚化效果应用失败: {e}")
            
            # 应用渐变效果
            if gradient_enabled:
                print("[INFO] 应用渐变背景效果")
                try:
                    color2 = (255, 255, 255)  # 白色
                    # 创建渐变背景
                    for y in range(h):
                        # 从 color1 渐变到 color2
                        alpha = y / h
                        for c in range(3):
                            background[y, :, c] = int(color1[c] * (1 - alpha) + color2[c] * alpha)
                    print(f"[INFO] 渐变效果应用完成")
                except Exception as e:
                    print(f"[ERROR] 渐变效果应用失败: {e}")
            
            # 应用纹理效果
            if texture_enabled:
                print("[INFO] 应用纹理背景效果")
                try:
                    # 创建棋盘纹理
                    texture = self._create_default_texture(h, w)
                    # 将纹理与背景混合
                    background = cv2.addWeighted(background, 0.7, texture, 0.3, 0)
                    print(f"[INFO] 纹理效果应用完成")
                except Exception as e:
                    print(f"[ERROR] 纹理效果应用失败: {e}")
            
            # 使用mask进行合成
            print("[DEBUG] 使用mask进行合成...")
            try:
                # 3通道 mask
                person_mask_3ch = np.stack([person_mask_float] * 3, axis=-1)
                
                # 合成：人物 * person_mask + 处理后背景 * (1 - person_mask)
                result = (current_image.astype(np.float32) * person_mask_3ch +
                         background.astype(np.float32) * (1 - person_mask_3ch))
                
                result = result.astype(np.uint8)
                
                # 更新处理器中的图像
                self.processor.current_image = result
                print("[DEBUG] 高级背景效果应用完成")
                
            except Exception as e:
                print(f"[ERROR] 合成失败: {e}")
                import traceback
                traceback.print_exc()
            
        except Exception as e:
            print(f"[WARNING] 应用高级背景效果失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_default_texture(self, height, width):
        """创建默认纹理（棋盘纹理）"""
        import numpy as np
        import cv2
        
        # 创建棋盘纹理
        square_size = 20
        texture = np.zeros((height, width, 3), dtype=np.uint8)
        
        for i in range(0, height, square_size):
            for j in range(0, width, square_size):
                if ((i // square_size) + (j // square_size)) % 2 == 0:
                    texture[i:i+square_size, j:j+square_size] = (200, 200, 200)
                else:
                    texture[i:i+square_size, j:j+square_size] = (150, 150, 150)
        
        return texture
    
    def _get_texture_path(self):
        """获取纹理文件路径"""
        import os
        # 尝试从resources目录获取默认纹理
        texture_dir = os.path.join(os.path.dirname(__file__), '..', 'resources', 'textures')
        if os.path.exists(texture_dir):
            textures = [f for f in os.listdir(texture_dir) if f.endswith(('.jpg', '.png', '.bmp'))]
            if textures:
                return os.path.join(texture_dir, textures[0])
        
        # 如果没有默认纹理，返回None
        return None
    
    def notify_data_changed(self):
        """通知主窗口数据已更改，需要刷新统计"""
        try:
            # 查找主窗口并刷新统计
            from PyQt5.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'update_status_bar'):
                    widget.update_status_bar()
                    print("[INFO] 已通知主窗口更新统计")
                    break
        except Exception as e:
            print(f"[WARNING] 通知主窗口失败: {e}")
    
    def manual_crop(self):
        """手动裁剪"""
        if self.processor.current_image is None:
            QMessageBox.warning(self, '警告', '请先加载图片')
            return
        
        try:
            # 打开裁剪对话框
            dialog = CropDialog(self.processor.current_image, self)
            
            # 设置当前选择的规格
            current_spec = "一寸"
            for rb in self.spec_radio_buttons.values():
                if rb.isChecked():
                    current_spec = rb.spec_name
                    break
            dialog.spec_combo.setCurrentText(current_spec)
            
            if dialog.exec_() == QDialog.Accepted:
                # 获取裁剪后的图像
                cropped = dialog.get_cropped_image()
                if cropped is not None:
                    # 更新处理器中的图像
                    self.processor.current_image = cropped
                    
                    # 更新显示
                    self.display_image(cropped)
                    self.update_quality_score()
                    
                    QMessageBox.information(self, '成功', '裁剪完成！')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'裁剪失败: {e}')
            import traceback
            traceback.print_exc()

    def load_collections(self):
        """加载采集任务列表"""
        try:
            db = DatabaseHelper()
            collections = db.get_active_collections()
            db.close()
            
            self.collection_combo.clear()
            for collection in collections:
                self.collection_combo.addItem(
                    f"{collection.name} ({collection.organization})",
                    collection.id
                )
            
            # 默认选择第一个
            if self.collection_combo.count() > 0:
                self.collection_combo.setCurrentIndex(0)
        except Exception as e:
            print(f"[WARNING] 加载采集任务失败: {e}")
    
    def on_collection_changed(self, index):
        """采集任务切换时的处理"""
        if index >= 0:
            self.current_collection_id = self.collection_combo.currentData()
            print(f"[DEBUG] 采集任务切换: index={index}, collection_id={self.current_collection_id}")
            
            if self.current_collection_id is not None:
                db = DatabaseHelper()
                collection = db.get_collection_by_id(self.current_collection_id)
                
                if collection:
                    print(f"[INFO] 已选择采集任务: {collection.name} (ID: {self.current_collection_id})")
                    if hasattr(collection, 'users'):
                        print(f"[DEBUG] 采集任务中的用户数: {len(collection.users)}")
                        for user in collection.users:
                            print(f"[DEBUG]   - {user.name} (ID: {user.id}, 身份证: {user.id_number})")
                    else:
                        print(f"[DEBUG] 采集任务没有users属性")
                else:
                    print(f"[WARNING] 采集任务不存在: {self.current_collection_id}")
                
                db.close()
            else:
                print(f"[DEBUG] 采集任务ID为None")
