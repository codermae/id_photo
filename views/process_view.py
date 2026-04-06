"""
图像处理视图
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QSlider, QGroupBox, QMessageBox, 
                             QFileDialog, QSpinBox, QCheckBox, QGridLayout, QDialog, 
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
        load_btn = QPushButton("📁 选择图像")
        load_btn.clicked.connect(self.load_image)
        top_control_layout.addWidget(load_btn)
        
        # 对比按钮
        self.compare_btn = QPushButton("📷 对比")
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
        
        # 质量评分（紧凑版）
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("质量:"))
        self.quality_label = QLabel("未加载")
        quality_layout.addWidget(self.quality_label)
        quality_layout.addStretch()
        left_layout.addLayout(quality_layout)
        
        # 右侧：处理参数（使用滚动区域）
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(8)  # 减小间距
        
        # 规格选择（紧凑版）
        spec_group = QGroupBox("规格")
        print("[DEBUG] 创建规格组...")
        spec_layout = QVBoxLayout()
        spec_layout.setSpacing(4)
        
        # 快速选择按钮
        spec_quick_btn_layout = QHBoxLayout()
        select_all_spec_btn = QPushButton("全选")
        select_all_spec_btn.setMaximumWidth(60)
        select_all_spec_btn.clicked.connect(self.select_all_specs)
        spec_quick_btn_layout.addWidget(select_all_spec_btn)
        
        select_common_spec_btn = QPushButton("常用")
        select_common_spec_btn.setMaximumWidth(60)
        select_common_spec_btn.clicked.connect(self.select_common_specs)
        spec_quick_btn_layout.addWidget(select_common_spec_btn)
        
        clear_spec_btn = QPushButton("清空")
        clear_spec_btn.setMaximumWidth(60)
        clear_spec_btn.clicked.connect(self.clear_specs)
        spec_quick_btn_layout.addWidget(clear_spec_btn)
        
        spec_quick_btn_layout.addStretch()
        spec_layout.addLayout(spec_quick_btn_layout)
        
        # 规格复选框（折叠显示相同尺寸，保留tooltip）
        print("[DEBUG] 开始创建规格复选框...")
        spec_grid = QGridLayout()
        spec_grid.setSpacing(2)
        
        self.spec_checkboxes = {}
        print(f"[DEBUG] 初始化 spec_checkboxes: {type(self.spec_checkboxes)}")
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
                    display_name = f"{size_str} {specs[0]} 等{len(specs)}种"
                    tooltip = f"相同尺寸 {size[0]}×{size[1]}px:\n" + "\n".join(specs)
                
                checkbox = QCheckBox(display_name)
                checkbox.setToolTip(tooltip)
                checkbox.spec_name = specs[0]  # 保存实际规格名
                
                # 默认选中一寸
                if "一寸" in display_name:
                    checkbox.setChecked(True)
                
                size_key = f"{size[0]}x{size[1]}"
                self.spec_checkboxes[size_key] = checkbox
                spec_grid.addWidget(checkbox, row, col)
                
                col += 1
                if col >= 3:  # 每行3个
                    col = 0
                    row += 1
            
            print(f"[DEBUG] spec_checkboxes 创建完成，共 {len(self.spec_checkboxes)} 个")
            spec_layout.addLayout(spec_grid)
            print("[DEBUG] spec_grid 添加到布局完成")
        except Exception as e:
            print(f"[ERROR] 创建规格复选框失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        spec_group.setLayout(spec_layout)
        right_layout.addWidget(spec_group)
        
        # 背景色选择（紧凑版）
        bg_group = QGroupBox("背景色")
        bg_layout = QVBoxLayout()
        bg_layout.setSpacing(4)
        
        # 快速选择按钮
        bg_quick_btn_layout = QHBoxLayout()
        select_all_bg_btn = QPushButton("全选")
        select_all_bg_btn.setMaximumWidth(60)
        select_all_bg_btn.clicked.connect(self.select_all_colors)
        bg_quick_btn_layout.addWidget(select_all_bg_btn)
        
        select_basic_bg_btn = QPushButton("基础")
        select_basic_bg_btn.setMaximumWidth(60)
        select_basic_bg_btn.clicked.connect(self.select_basic_colors)
        bg_quick_btn_layout.addWidget(select_basic_bg_btn)
        
        clear_bg_btn = QPushButton("清空")
        clear_bg_btn.setMaximumWidth(60)
        clear_bg_btn.clicked.connect(self.clear_colors)
        bg_quick_btn_layout.addWidget(clear_bg_btn)
        
        bg_quick_btn_layout.addStretch()
        bg_layout.addLayout(bg_quick_btn_layout)
        
        # 背景色复选框（紧凑布局）
        bg_grid = QGridLayout()
        bg_grid.setSpacing(2)
        
        self.bg_checkboxes = {}
        row, col = 0, 0
        
        for color_name in BACKGROUND_COLORS.keys():
            checkbox = QCheckBox(color_name)
            
            # 默认选中蓝色
            if color_name == '蓝色':
                checkbox.setChecked(True)
            
            self.bg_checkboxes[color_name] = checkbox
            bg_grid.addWidget(checkbox, row, col)
            
            col += 1
            if col >= 3:  # 每行3个
                col = 0
                row += 1
        
        bg_layout.addLayout(bg_grid)
        
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
        self.brightness_label = QLabel("0")
        self.brightness_label.setMinimumWidth(30)
        adjust_layout.addWidget(self.brightness_label, 0, 2)
        
        adjust_layout.addWidget(QLabel("对比:"), 1, 0)
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(50, 200)
        self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self.on_contrast_changed)
        adjust_layout.addWidget(self.contrast_slider, 1, 1)
        self.contrast_label = QLabel("1.0")
        self.contrast_label.setMinimumWidth(30)
        adjust_layout.addWidget(self.contrast_label, 1, 2)
        
        adjust_group.setLayout(adjust_layout)
        right_layout.addWidget(adjust_group)
        
        # 处理和保存按钮（合并）
        action_group = QGroupBox("操作")
        action_layout = QGridLayout()
        action_layout.setSpacing(4)
        
        self.process_btn = QPushButton("应用处理")
        self.process_btn.clicked.connect(self.apply_processing)
        self.process_btn.setEnabled(False)
        action_layout.addWidget(self.process_btn, 0, 0)
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_image)
        self.reset_btn.setEnabled(False)
        action_layout.addWidget(self.reset_btn, 0, 1)
        
        self.manual_crop_btn = QPushButton("✂️ 裁剪")
        self.manual_crop_btn.clicked.connect(self.manual_crop)
        self.manual_crop_btn.setEnabled(False)
        action_layout.addWidget(self.manual_crop_btn, 1, 0)
        
        self.save_btn = QPushButton("💾 保存")
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)
        action_layout.addWidget(self.save_btn, 1, 1)
        
        action_group.setLayout(action_layout)
        right_layout.addWidget(action_group)
        
        # 批量处理按钮（紧凑版）
        unified_batch_btn = QPushButton("🚀 多规格批量生成")
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
                
                # 从文件名中提取身份证号
                filename = os.path.basename(filepath)
                # 文件名格式: {id_number}_{timestamp}.jpg 或 {id_number}_{spec}_{bg_color}_{timestamp}.jpg
                parts = filename.split('_')
                self.current_user_id = None
                user_name = None
                
                if len(parts) >= 2:
                    potential_id = parts[0]
                    # 验证是否是有效的身份证号（15或18位数字）
                    if potential_id.isdigit() and len(potential_id) in [15, 18]:
                        # 查询用户是否存在
                        db = DatabaseHelper()
                        print(f"[DEBUG] 查询身份证号: {potential_id}")
                        print(f"[DEBUG] 采集任务ID: {self.current_collection_id}")
                        
                        # 按照身份证号和采集任务一起查询
                        user = db.get_user_by_id_number(potential_id, collection_id=self.current_collection_id)
                        
                        if user:
                            print(f"[DEBUG] 用户找到: {user.name} (ID: {user.id}, 采集任务ID: {user.collection_id})")
                            user_name = user.name
                            # 用户已经通过采集任务过滤，所以一定属于该采集任务
                            self.current_user_id = user.id
                            print(f"[INFO] 用户识别成功: {user.name} (身份证: {potential_id}, 采集任务: {self.current_collection_id})")
                        else:
                            print(f"[WARNING] 身份证号 {potential_id} 在采集任务 {self.current_collection_id} 中不存在")
                            QMessageBox.warning(
                                self,
                                "警告",
                                f"身份证号 {potential_id} 在选定的采集任务中不存在\n\n请检查：\n1. 是否选择了正确的采集任务\n2. 用户是否已添加到该采集任务"
                            )
                            db.close()
                            return  # 不显示图像
                        db.close()
                    else:
                        print(f"[WARNING] 无法从文件名中提取有效的身份证号: {filename}")
                        QMessageBox.warning(
                            self,
                            "警告",
                            f"文件名格式错误，无法识别身份证号\n\n格式应为: {{身份证号}}_{{时间戳}}.jpg"
                        )
                        return  # 不显示图像
                else:
                    print(f"[WARNING] 文件名格式不符合预期: {filename}")
                    QMessageBox.warning(
                        self,
                        "警告",
                        f"文件名格式错误\n\n格式应为: {{身份证号}}_{{时间戳}}.jpg"
                    )
                    return  # 不显示图像
                
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
        """更新质量评分"""
        score = self.processor.get_quality_score()
        
        if score >= 70:
            self.quality_label.setText(f"<span style='color: green;'>{score}/100</span>")
        elif score >= 50:
            self.quality_label.setText(f"<span style='color: orange;'>{score}/100</span>")
        else:
            self.quality_label.setText(f"<span style='color: red;'>{score}/100</span>")

    def apply_processing(self):
        """应用处理"""
        if self.processor.current_image is None:
            QMessageBox.warning(self, "警告", "没有加载图像")
            return

        # 获取选中的规格和颜色
        selected_specs = [cb.spec_name for cb in self.spec_checkboxes.values() if cb.isChecked()]
        selected_colors = [name for name, cb in self.bg_checkboxes.items() if cb.isChecked()]
        
        if not selected_specs:
            QMessageBox.warning(self, "警告", "请至少选择一个规格")
            return
        
        if not selected_colors:
            QMessageBox.warning(self, "警告", "请至少选择一个背景色")
            return
        
        # 如果选择了多个规格或颜色，直接生成多规格
        if len(selected_specs) > 1 or len(selected_colors) > 1:
            self.generate_multi_spec(selected_specs, selected_colors)
            return
        
        # 单规格单颜色处理
        try:
            spec = selected_specs[0]
            bg_color = selected_colors[0]
            
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
            self.contrast_slider.setValue(100)
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
        self.display_image(self.processor.get_current_image())
        self.update_quality_score()
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(100)

    def on_brightness_changed(self, value):
        """亮度改变"""
        self.brightness_label.setText(str(value))
        if self.processor.current_image is not None:
            self.processor.adjust_brightness(value)
            self.display_image(self.processor.get_current_image())

    def on_contrast_changed(self, value):
        """对比度改变"""
        contrast_value = value / 100.0
        self.contrast_label.setText(f"{contrast_value:.1f}")
        if self.processor.current_image is not None:
            self.processor.adjust_contrast(contrast_value)
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
            
            # 获取当前选择的规格和背景色
            selected_specs = [cb.spec_name for cb in self.spec_checkboxes.values() if cb.isChecked()]
            selected_colors = [name for name, cb in self.bg_checkboxes.items() if cb.isChecked()]
            
            if not selected_specs:
                QMessageBox.warning(self, "警告", "请至少选择一个规格")
                db.close()
                return
            
            if not selected_colors:
                QMessageBox.warning(self, "警告", "请至少选择一个背景色")
                db.close()
                return
            
            spec = selected_specs[0]
            bg_color = selected_colors[0]
            
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
            
            # 创建或更新采集记录
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
    
    def select_all_specs(self):
        """全选规格"""
        for checkbox in self.spec_checkboxes.values():
            checkbox.setChecked(True)
    
    def select_common_specs(self):
        """选择常用规格"""
        common_sizes = [(590, 826), (826, 1158), (826, 1252), (780, 1134)]
        for size_key, checkbox in self.spec_checkboxes.items():
            w, h = map(int, size_key.split('x'))
            checkbox.setChecked((w, h) in common_sizes)
    
    def clear_specs(self):
        """清空规格选择"""
        for checkbox in self.spec_checkboxes.values():
            checkbox.setChecked(False)
    
    def select_all_colors(self):
        """全选颜色"""
        for checkbox in self.bg_checkboxes.values():
            checkbox.setChecked(True)
    
    def select_basic_colors(self):
        """选择基础颜色"""
        basic_colors = ['白色', '蓝色', '红色', '灰色']
        for name, checkbox in self.bg_checkboxes.items():
            checkbox.setChecked(name in basic_colors)
    
    def clear_colors(self):
        """清空颜色选择"""
        for checkbox in self.bg_checkboxes.values():
            checkbox.setChecked(False)
    
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
            selected_specs = [cb.spec_name for cb in self.spec_checkboxes.values() if cb.isChecked()]
            current_spec = selected_specs[0] if selected_specs else "一寸"
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
