"""
融合的批量处理对话框 - 多规格批量生成（支持单张或多张）
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QProgressBar, QTextEdit,
                             QGroupBox, QComboBox, QSpinBox, QCheckBox,
                             QListWidget, QMessageBox, QGridLayout,
                             QWidget, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import os
import sys
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.batch_processor import BatchProcessor
from controllers.ai_processor import AIProcessor
from config.config import PHOTO_SPECS, BACKGROUND_COLORS


class UnifiedBatchDialog(QDialog):
    """融合的批量处理对话框 - 多规格批量生成"""
    
    # 定义信号用于线程安全的UI更新
    progress_signal = pyqtSignal(int, int, str)
    status_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("多规格批量生成")
        self.setGeometry(100, 100, 900, 750)
        self.setModal(True)
        # 删除右上角的问号
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.ai_processor = AIProcessor()
        self.batch_processor = BatchProcessor(self.ai_processor)
        self.processing_thread = None
        self.selected_files = []
        
        # 连接信号到槽
        self.progress_signal.connect(self._safe_update_progress)
        self.status_signal.connect(self._safe_update_status)
        
        # 从父窗口（ProcessView）获取采集任务信息
        self.parent_view = parent
        self.current_collection_id = parent.current_collection_id if parent else None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        # title_label = QLabel("🚀 多规格批量生成")
        # title_font = QFont()
        # title_font.setPointSize(16)
        # title_font.setBold(True)
        # title_label.setFont(title_font)
        # title_label.setAlignment(Qt.AlignCenter)
        # layout.addWidget(title_label)
        
        # 功能说明
        # info_label = QLabel(
        #     "💡 支持单张或多张图片，每张图片生成多种规格和颜色组合\n"
        #     "   选择图片并勾选规格与颜色即可开始"
        # )
        # info_label.setStyleSheet("color: #666; padding: 10px; background-color: #f8f9fa; border-radius: 4px;")
        # info_label.setWordWrap(True)
        # layout.addWidget(info_label)

        # 图片选择区域
        file_group = QGroupBox("选择图片（支持单张或多张）")
        file_layout = QVBoxLayout(file_group)
        
        file_btn_layout = QHBoxLayout()
        select_files_btn = QPushButton("选择图片文件")
        select_files_btn.clicked.connect(self.select_files)
        select_folder_btn = QPushButton("选择文件夹")
        select_folder_btn.clicked.connect(self.select_folder)
        file_btn_layout.addWidget(select_files_btn)
        file_btn_layout.addWidget(select_folder_btn)
        file_layout.addLayout(file_btn_layout)
        
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(100)
        file_layout.addWidget(self.file_list)
        
        self.file_count_label = QLabel("未选择图片")
        self.file_count_label.setStyleSheet("color: #666; font-style: italic;")
        file_layout.addWidget(self.file_count_label)
        
        layout.addWidget(file_group)
        
        # 规格选择区域
        spec_group = QGroupBox("选择证件照规格")
        spec_scroll = QScrollArea()
        spec_widget = QWidget()
        spec_layout = QGridLayout(spec_widget)
        
        self.spec_checkboxes = {}
        row, col = 0, 0
        
        size_groups = defaultdict(list)
        for spec_name in PHOTO_SPECS.keys():
            size = PHOTO_SPECS[spec_name]
            size_groups[size].append(spec_name)
        
        for size, specs in size_groups.items():
            # 新格式: "590x826px 一寸"
            size_str = f"{size[0]}x{size[1]}px"
            
            if len(specs) == 1:
                checkbox = QCheckBox(f"{size_str} {specs[0]}")
            else:
                checkbox = QCheckBox(f"{size_str} {specs[0]}")
                checkbox.setToolTip(f"相同尺寸 {size[0]}×{size[1]}px:\n" + "\n".join(specs))
                checkbox.specs_group = specs
            
            if any(spec in ['一寸', '小二寸', '美国护照', '欧盟护照'] for spec in specs):
                checkbox.setChecked(True)
            
            checkbox.stateChanged.connect(self.update_generation_count)
            
            size_key = f"{size[0]}x{size[1]}"
            self.spec_checkboxes[size_key] = checkbox
            spec_layout.addWidget(checkbox, row, col)
            
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        spec_scroll.setWidget(spec_widget)
        spec_scroll.setFixedHeight(120)
        
        spec_group_layout = QVBoxLayout()
        
        # 快速选择按钮
        quick_btn_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all_specs)
        quick_btn_layout.addWidget(select_all_btn)
        
        select_common_btn = QPushButton("常用")
        select_common_btn.clicked.connect(self.select_common_specs)
        quick_btn_layout.addWidget(select_common_btn)
        
        select_intl_btn = QPushButton("国际")
        select_intl_btn.clicked.connect(self.select_intl_specs)
        quick_btn_layout.addWidget(select_intl_btn)
        
        quick_btn_layout.addStretch()
        spec_group_layout.addLayout(quick_btn_layout)
        spec_group_layout.addWidget(spec_scroll)
        spec_group.setLayout(spec_group_layout)
        layout.addWidget(spec_group)
        
        # 背景色选择区域
        color_group = QGroupBox("选择背景颜色（每种规格都会生成这些颜色）")
        color_layout = QGridLayout()
        
        self.color_checkboxes = {}
        row, col = 0, 0
        
        for color_name in BACKGROUND_COLORS.keys():
            checkbox = QCheckBox(color_name)
            if color_name in ['白色', '蓝色', '美国护照蓝', '欧盟护照灰']:
                checkbox.setChecked(True)
            
            checkbox.stateChanged.connect(self.update_generation_count)
            
            self.color_checkboxes[color_name] = checkbox
            color_layout.addWidget(checkbox, row, col)
            
            col += 1
            if col >= 7:
                col = 0
                row += 1
        
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        # 生成数量显示
        self.generation_info = QLabel()
        self.generation_info.setStyleSheet("""
            background-color: #e7f3ff;
            border: 2px solid #2196F3;
            border-radius: 6px;
            padding: 10px;
            font-weight: bold;
            color: #1976D2;
        """)
        self.generation_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.generation_info)
        self.update_generation_count()
        
        # 处理选项
        options_group = QGroupBox("处理选项")
        options_layout = QGridLayout()
        options_layout.setSpacing(8)
        
        # 背景模式
        options_layout.addWidget(QLabel("背景模式:"), 0, 0)
        self.bg_mode_combo = QComboBox()
        self.bg_mode_combo.addItems(['精细模式', '高保真模式'])
        self.bg_mode_combo.setCurrentIndex(0)
        self.bg_mode_combo.currentTextChanged.connect(self.on_mode_changed)
        options_layout.addWidget(self.bg_mode_combo, 0, 1, 1, 2)
        
        # Alpha Matte（仅在精细模式显示）
        self.alpha_matting_check = QCheckBox("启用Alpha Matte")
        self.alpha_matting_check.setChecked(True)
        options_layout.addWidget(self.alpha_matting_check, 0, 3)
        
        # 美颜 - 已注释（暂时禁用）
        # self.beautify_check = QCheckBox("美颜")
        # self.beautify_check.setChecked(False)
        # self.beautify_check.stateChanged.connect(self.on_beautify_changed)
        # options_layout.addWidget(self.beautify_check, 1, 0)
        # 
        # options_layout.addWidget(QLabel("强度:"), 1, 1)
        # self.beautify_strength_spin = QSpinBox()
        # self.beautify_strength_spin.setRange(0, 100)
        # self.beautify_strength_spin.setValue(30)
        # self.beautify_strength_spin.setSuffix("%")
        # self.beautify_strength_spin.setEnabled(False)
        # options_layout.addWidget(self.beautify_strength_spin, 1, 2)
        
        # 亮度
        options_layout.addWidget(QLabel("亮度:"), 2, 0)
        self.brightness_spin = QSpinBox()
        self.brightness_spin.setRange(-100, 100)
        self.brightness_spin.setValue(0)
        options_layout.addWidget(self.brightness_spin, 2, 1, 1, 2)
        
        # 对比度
        options_layout.addWidget(QLabel("对比度:"), 3, 0)
        self.contrast_spin = QSpinBox()
        self.contrast_spin.setRange(-100, 100)
        self.contrast_spin.setValue(0)
        options_layout.addWidget(self.contrast_spin, 3, 1, 1, 2)
        
        # 高级背景效果
        options_layout.addWidget(QLabel("高级背景效果:"), 4, 0)
        self.gradient_check = QCheckBox("渐变")
        self.gradient_check.setChecked(False)
        options_layout.addWidget(self.gradient_check, 4, 1)
        
        self.texture_check = QCheckBox("纹理")
        self.texture_check.setChecked(False)
        options_layout.addWidget(self.texture_check, 4, 2)
        
        self.blur_check = QCheckBox("虚化")
        self.blur_check.setChecked(False)
        options_layout.addWidget(self.blur_check, 4, 3)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 输出目录
        output_group = QGroupBox("输出设置")
        output_layout = QHBoxLayout()
        
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_label = QLabel("未选择")
        self.output_label.setStyleSheet("color: #666; font-style: italic;")
        output_layout.addWidget(self.output_label)
        
        select_output_btn = QPushButton("选择")
        select_output_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(select_output_btn)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # 进度区域
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(80)
        self.status_text.setReadOnly(True)
        progress_layout.addWidget(self.status_text)
        
        layout.addWidget(progress_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始生成")
        self.start_btn.setFixedHeight(40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.start_btn.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)
        button_layout.addWidget(self.stop_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.setFixedHeight(40)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)

    
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
    
    def select_intl_specs(self):
        """选择国际规格"""
        intl_sizes = [(1200, 1200), (826, 1063), (944, 1181)]
        for size_key, checkbox in self.spec_checkboxes.items():
            w, h = map(int, size_key.split('x'))
            checkbox.setChecked((w, h) in intl_sizes)
    
    def update_generation_count(self):
        """更新生成数量显示"""
        # 统计选中的规格和颜色
        selected_specs = sum(1 for cb in self.spec_checkboxes.values() if cb.isChecked())
        selected_colors = sum(1 for cb in self.color_checkboxes.values() if cb.isChecked())
        
        # 获取图片数量
        image_count = len(self.selected_files) if self.selected_files else 1
        
        # 计算总数
        per_image = selected_specs * selected_colors
        total = image_count * per_image
        
        # 估算时间和存储
        time_sec = total * 3
        time_min = time_sec / 60
        storage_mb = total * 0.4
        
        # 更新显示
        if image_count == 1 and not self.selected_files:
            info_text = f"将生成: {selected_specs} 规格 × {selected_colors} 颜色 = {per_image} 张照片/图片"
        else:
            info_text = f"将生成: {image_count} 张图片 × {selected_specs} 规格 × {selected_colors} 颜色 = {total} 张照片"
        
        info_text += f"\n预计时间: {time_min:.1f} 分钟  |  存储空间: {storage_mb:.1f} MB"
        
        self.generation_info.setText(info_text)
    
    # def on_beautify_changed(self):
    #     """美颜复选框改变时的处理 - 已注释（暂时禁用）"""
    #     self.beautify_strength_spin.setEnabled(self.beautify_check.isChecked())
    
    def on_mode_changed(self):
        """背景模式改变时的处理"""
        is_hifi = self.bg_mode_combo.currentText() == '高保真模式'
        self.alpha_matting_check.setVisible(not is_hifi)
    
    def select_files(self):
        """选择图片文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp)"
        )
        if files:
            self.file_list.clear()
            for file in files:
                self.file_list.addItem(os.path.basename(file))
            self.selected_files = files
            self.file_count_label.setText(f"已选择 {len(files)} 张图片")
            self.file_count_label.setStyleSheet("color: #28a745; font-weight: bold;")
            self.update_generation_count()
            self.add_status(f"已选择 {len(files)} 张图片")
    
    def select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            image_files = []
            for filename in os.listdir(folder):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    image_files.append(os.path.join(folder, filename))
            
            if image_files:
                self.file_list.clear()
                for file in image_files:
                    self.file_list.addItem(os.path.basename(file))
                self.selected_files = image_files
                self.file_count_label.setText(f"已选择 {len(image_files)} 张图片")
                self.file_count_label.setStyleSheet("color: #28a745; font-weight: bold;")
                self.update_generation_count()
                self.add_status(f"从文件夹选择了 {len(image_files)} 张图片")
            else:
                QMessageBox.warning(self, "警告", "所选文件夹中没有找到图片文件")
    
    def select_output_dir(self):
        """选择输出目录"""
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if folder:
            self.output_label.setText(folder)
            self.output_label.setStyleSheet("color: #333;")
            self.output_dir = folder
            self.add_status(f"输出目录: {folder}")
    
    def start_processing(self):
        """开始处理"""
        # 检查是否选择了采集任务
        if not self.current_collection_id:
            QMessageBox.warning(self, "警告", "请先在图像处理界面选择采集任务")
            return
        
        # 检查是否选择了图片
        if not self.selected_files:
            QMessageBox.warning(self, "警告", "请先选择图片文件")
            return
        
        # 检查是否选择了输出目录
        if not hasattr(self, 'output_dir'):
            QMessageBox.warning(self, "警告", "请先选择输出目录")
            return
        
        # 获取选中的规格和颜色
        selected_specs = []
        for size_key, checkbox in self.spec_checkboxes.items():
            if checkbox.isChecked():
                if hasattr(checkbox, 'specs_group'):
                    selected_specs.append(checkbox.specs_group[0])
                else:
                    selected_specs.append(checkbox.text())
        
        selected_colors = [name for name, cb in self.color_checkboxes.items() if cb.isChecked()]
        
        if not selected_specs or not selected_colors:
            QMessageBox.warning(self, "警告", "请至少选择一个规格和一个颜色")
            return
        
        # 计算总数
        image_count = len(self.selected_files)
        per_image = len(selected_specs) * len(selected_colors)
        total = image_count * per_image
        
        # 确认对话框
        message = f"""多规格批量生成确认

处理统计:
• 输入图片: {image_count} 张
• 每张生成: {len(selected_specs)} 规格 × {len(selected_colors)} 颜色 = {per_image} 张
• 总输出: {total} 张照片

选中规格: {', '.join(selected_specs[:3])}{'...' if len(selected_specs) > 3 else ''}
选中颜色: {', '.join(selected_colors[:3])}{'...' if len(selected_colors) > 3 else ''}

预计耗时: {total * 3 // 60} 分钟
存储空间: {total * 0.4:.0f} MB

确定要开始处理吗？"""
        
        reply = QMessageBox.question(self, "确认批量处理", message, QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.add_status("=" * 50)
            self.add_status(f"开始多规格批量生成...")
            self.add_status(f"输入: {image_count} 张图片")
            self.add_status(f"每张生成: {per_image} 张 ({len(selected_specs)}规格 × {len(selected_colors)}颜色)")
            self.add_status(f"总输出: {total} 张")
            self.add_status("=" * 50)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(0)
            
            # 保存总数用于进度计算
            self.total_photos = total
            self.per_image_count = per_image
            
            # 配置批量处理器
            batch_params = {
                'multi_specs': selected_specs,
                'multi_colors': selected_colors,
                'background_mode': 'hifi' if self.bg_mode_combo.currentIndex() == 1 else 'refined',
                'alpha_matting': self.alpha_matting_check.isChecked(),
                'beautify_enabled': False,  # 美颜已禁用
                'beautify_strength': 0.0,   # 美颜已禁用
                'brightness': self.brightness_spin.value(),
                'contrast': self.contrast_spin.value(),
                'gradient_enabled': self.gradient_check.isChecked(),
                'texture_enabled': self.texture_check.isChecked(),
                'blur_enabled': self.blur_check.isChecked(),
            }
            self.batch_processor.set_batch_params(batch_params)
            
            # 添加图片到处理队列
            self.batch_processor.add_images(self.selected_files)
            
            # 设置回调函数
            self.batch_processor.progress_callback = self.on_progress_update
            self.batch_processor.status_callback = self.on_status_update
            
            # 启动处理
            success = self.batch_processor.start_batch_processing(self.output_dir)
            
            if not success:
                QMessageBox.critical(self, "错误", "启动批量处理失败")
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.progress_bar.setVisible(False)
    
    def on_progress_update(self, current, total, current_file):
        """进度更新回调 - 发射信号"""
        self.progress_signal.emit(current, total, current_file)
    
    def _safe_update_progress(self, current, total, current_file):
        """安全的进度更新（在主线程中执行）"""
        try:
            # 计算已处理的照片总数
            if hasattr(self, 'per_image_count') and hasattr(self, 'total_photos'):
                completed_photos = current * self.per_image_count
                self.progress_bar.setMaximum(self.total_photos)
                self.progress_bar.setValue(completed_photos)
                percentage = (completed_photos / self.total_photos * 100) if self.total_photos > 0 else 0
                self.progress_bar.setFormat(f"处理中... {percentage:.1f}% ({completed_photos}/{self.total_photos})")
            else:
                self.progress_bar.setMaximum(total)
                self.progress_bar.setValue(current)
                percentage = (current / total * 100) if total > 0 else 0
                self.progress_bar.setFormat(f"处理中... {percentage:.1f}% ({current}/{total})")
            
            filename = os.path.basename(current_file) if current_file else "未知"
            self.add_status(f"[{current+1}/{total}] 处理中: {filename}")
        except Exception as e:
            print(f"[ERROR] 更新进度失败: {e}")
    
    def on_status_update(self, message, level):
        """状态更新回调 - 发射信号"""
        self.status_signal.emit(message, level)
    
    def _safe_update_status(self, message, level):
        """安全的状态更新（在主线程中执行）"""
        try:
            # 根据级别添加前缀
            prefix_map = {
                'info': '[INFO]',
                'warning': '[WARN]',
                'error': '[ERROR]',
                'success': '[OK]'
            }
            prefix = prefix_map.get(level, '[*]')
            
            # 添加到状态文本
            self.add_status(f"{prefix} {message}")
            
            # 如果处理完成，更新按钮状态和进度条
            if level == 'success' or '完成' in message:
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                
                # 将进度条设置为 100%
                if hasattr(self, 'total_photos'):
                    self.progress_bar.setMaximum(self.total_photos)
                    self.progress_bar.setValue(self.total_photos)
                    self.progress_bar.setFormat(f"处理完成！ 100% ({self.total_photos}/{self.total_photos})")
                else:
                    self.progress_bar.setFormat("处理完成！")
        except Exception as e:
            print(f"[ERROR] 更新状态失败: {e}")
    
    def stop_processing(self):
        """停止处理"""
        if self.batch_processor:
            self.batch_processor.stop_batch_processing()
            self.add_status("正在停止批量处理，请稍候...")
            self.add_status("当前正在处理的文件将完成后停止")
        else:
            self.add_status("处理已停止")
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def add_status(self, message):
        """添加状态信息"""
        self.status_text.append(message)
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
