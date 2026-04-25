"""
批量处理对话框
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QProgressBar, QTextEdit,
                             QGroupBox, QComboBox, QSpinBox, QCheckBox,
                             QListWidget, QMessageBox, QGridLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.batch_processor import BatchProcessor
from controllers.ai_processor import AIProcessor

class BatchProcessingThread(QThread):
    """批量处理线程"""
    progress_updated = pyqtSignal(int, int, str)  # current, total, filename
    status_updated = pyqtSignal(str, str)  # message, level
    finished = pyqtSignal(dict)  # final stats
    
    def __init__(self, batch_processor, output_dir):
        super().__init__()
        self.batch_processor = batch_processor
        self.output_dir = output_dir
        
    def run(self):
        """运行批量处理"""
        try:
            # 设置回调函数
            self.batch_processor.progress_callback = self.progress_updated.emit
            self.batch_processor.status_callback = self.status_updated.emit
            
            # 开始处理
            success = self.batch_processor.start_batch_processing(self.output_dir)
            
            if success:
                # 等待处理完成
                while self.batch_processor.get_processing_status()['is_processing']:
                    self.msleep(100)
                
                # 获取最终统计
                final_status = self.batch_processor.get_processing_status()
                self.finished.emit(final_status['stats'])
            else:
                self.status_updated.emit("批量处理启动失败", "error")
                
        except Exception as e:
            self.status_updated.emit(f"批量处理出错: {e}", "error")

class BatchProcessingDialog(QDialog):
    """批量处理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量处理")
        self.setGeometry(200, 200, 800, 600)
        self.setModal(True)
        
        # 初始化处理器
        self.ai_processor = AIProcessor()
        self.batch_processor = BatchProcessor(self.ai_processor)
        self.processing_thread = None
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("批量处理证件照")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 文件选择区域
        file_group = QGroupBox("选择图片文件")
        file_layout = QVBoxLayout(file_group)
        
        # 文件选择按钮
        file_btn_layout = QHBoxLayout()
        self.select_files_btn = QPushButton("选择图片文件")
        self.select_files_btn.clicked.connect(self.select_files)
        self.select_folder_btn = QPushButton("选择文件夹")
        self.select_folder_btn.clicked.connect(self.select_folder)
        file_btn_layout.addWidget(self.select_files_btn)
        file_btn_layout.addWidget(self.select_folder_btn)
        file_layout.addLayout(file_btn_layout)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(150)
        file_layout.addWidget(self.file_list)
        
        layout.addWidget(file_group)
        
        # 处理参数区域
        params_group = QGroupBox("处理参数")
        params_layout = QGridLayout(params_group)
        
        # 裁剪规格 - 使用优化后的规格列表
        params_layout.addWidget(QLabel("裁剪规格:"), 0, 0)
        self.crop_combo = QComboBox()
        
        # 导入配置
        from config.config import PHOTO_SPECS
        from collections import defaultdict
        
        # 按尺寸分组去重
        size_groups = defaultdict(list)
        for spec_name, size in PHOTO_SPECS.items():
            size_groups[size].append(spec_name)
        
        # 添加优化后的规格选项
        for size, specs in size_groups.items():
            # 新格式: "590x826px 一寸"
            size_str = f"{size[0]}x{size[1]}px"
            
            if len(specs) == 1:
                # 单一规格
                display_name = f"{size_str} {specs[0]}"
                tooltip = f"尺寸: {size[0]}×{size[1]}px"
            else:
                # 多规格组
                display_name = f"{size_str} {specs[0]} 等{len(specs)}种"
                tooltip = f"相同尺寸 {size[0]}×{size[1]}px:\n" + "\n".join(specs)
            
            self.crop_combo.addItem(display_name, specs[0])  # 使用第一个作为代表
            self.crop_combo.setItemData(self.crop_combo.count()-1, tooltip, Qt.ToolTipRole)
        
        # 默认选择一寸
        for i in range(self.crop_combo.count()):
            if "一寸" in self.crop_combo.itemText(i):
                self.crop_combo.setCurrentIndex(i)
                break
        
        params_layout.addWidget(self.crop_combo, 0, 1)
        
        # 背景颜色 - 使用优化后的颜色列表
        params_layout.addWidget(QLabel("背景颜色:"), 0, 2)
        self.bg_combo = QComboBox()
        
        # 导入背景色配置
        from config.config import BACKGROUND_COLORS
        
        # 添加常用背景色（优先显示基础色）
        basic_colors = ['白色', '蓝色', '红色', '灰色']
        for color in basic_colors:
            if color in BACKGROUND_COLORS:
                self.bg_combo.addItem(color)
        
        # 添加分隔符
        self.bg_combo.insertSeparator(self.bg_combo.count())
        
        # 添加国际标准色
        intl_colors = ['美国护照蓝', '欧盟护照灰', '英国签证蓝', '日本护照白']
        for color in intl_colors:
            if color in BACKGROUND_COLORS:
                self.bg_combo.addItem(color)
        
        # 默认选择蓝色
        self.bg_combo.setCurrentText('蓝色')
        params_layout.addWidget(self.bg_combo, 0, 3)
        
        # 背景处理模式
        params_layout.addWidget(QLabel("背景模式:"), 0, 4)
        self.bg_mode_combo = QComboBox()
        self.bg_mode_combo.addItems(['精细模式(推荐)'])
        self.bg_mode_combo.setCurrentIndex(0)  # 默认选择精细模式
        self.bg_mode_combo.setToolTip("精细模式: 最佳边缘质量，处理时间较长")
        params_layout.addWidget(self.bg_mode_combo, 0, 5)
        
        # Alpha Matte选项
        self.alpha_matting_check = QCheckBox("启用Alpha Matte（提升边缘质量）")
        self.alpha_matting_check.setChecked(True)
        self.alpha_matting_check.setToolTip("启用后可提升头发丝等边缘细节质量，但处理时间略长")
        params_layout.addWidget(self.alpha_matting_check, 1, 5)
        
        # 美颜选项
        self.beautify_check = QCheckBox("启用美颜")
        self.beautify_check.setChecked(True)
        params_layout.addWidget(self.beautify_check, 1, 0)
        
        # 亮度调整
        params_layout.addWidget(QLabel("亮度:"), 1, 1)
        self.brightness_spin = QSpinBox()
        self.brightness_spin.setRange(-100, 100)
        self.brightness_spin.setValue(10)
        params_layout.addWidget(self.brightness_spin, 1, 2)
        
        # 对比度调整
        params_layout.addWidget(QLabel("对比度:"), 1, 3)
        self.contrast_spin = QSpinBox()
        self.contrast_spin.setRange(-100, 100)
        self.contrast_spin.setValue(15)
        params_layout.addWidget(self.contrast_spin, 1, 4)
        
        # 批量模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("批量模式:"))
        self.batch_mode_combo = QComboBox()
        self.batch_mode_combo.addItems(['单规格处理', '多规格生成'])
        self.batch_mode_combo.setCurrentIndex(0)
        self.batch_mode_combo.setToolTip(
            "单规格处理: 每张图片生成一种规格\n"
            "多规格生成: 每张图片生成多种规格（类似多规格同时生成功能）"
        )
        self.batch_mode_combo.currentIndexChanged.connect(self._on_batch_mode_changed)
        mode_layout.addWidget(self.batch_mode_combo)
        mode_layout.addStretch()
        params_layout.addLayout(mode_layout, 2, 5)
        
        # 多规格选择按钮（初始隐藏）
        self.multi_spec_btn = QPushButton("📋 选择多种规格")
        self.multi_spec_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.multi_spec_btn.clicked.connect(self._open_multi_spec_selection)
        self.multi_spec_btn.setVisible(False)
        params_layout.addWidget(self.multi_spec_btn, 3, 5)
        
        # 存储选中的多规格
        self.selected_multi_specs = []
        self.selected_multi_colors = []
        
        # 饱和度调整
        params_layout.addWidget(QLabel("饱和度:"), 2, 0)
        self.saturation_spin = QSpinBox()
        self.saturation_spin.setRange(-100, 100)
        self.saturation_spin.setValue(5)
        params_layout.addWidget(self.saturation_spin, 2, 1)
        
        # 锐化程度
        params_layout.addWidget(QLabel("锐化:"), 2, 2)
        self.sharpness_spin = QSpinBox()
        self.sharpness_spin.setRange(0, 100)
        self.sharpness_spin.setValue(20)
        params_layout.addWidget(self.sharpness_spin, 2, 3)
        
        layout.addWidget(params_group)
        
        # 输出设置区域
        output_group = QGroupBox("输出设置")
        output_layout = QHBoxLayout(output_group)
        
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_path_label = QLabel("未选择")
        self.output_path_label.setStyleSheet("color: #666; font-style: italic;")
        output_layout.addWidget(self.output_path_label)
        
        self.select_output_btn = QPushButton("选择输出目录")
        self.select_output_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.select_output_btn)
        
        layout.addWidget(output_group)
        
        # 进度区域
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        progress_layout.addWidget(self.status_text)
        
        layout.addWidget(progress_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始处理")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.start_btn.clicked.connect(self.start_processing)
        
        self.stop_btn = QPushButton("停止处理")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def select_files(self):
        """选择图片文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "", 
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff)"
        )
        
        if files:
            self.file_list.clear()
            for file in files:
                self.file_list.addItem(os.path.basename(file))
            
            # 添加到批量处理器
            added_count = self.batch_processor.add_images(files)
            self.add_status(f"成功添加 {added_count} 个文件")
            
    def select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        
        if folder:
            # 扫描文件夹中的图片
            image_files = []
            for filename in os.listdir(folder):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                    image_files.append(os.path.join(folder, filename))
            
            if image_files:
                self.file_list.clear()
                for file in image_files:
                    self.file_list.addItem(os.path.basename(file))
                
                # 添加到批量处理器
                added_count = self.batch_processor.add_images(image_files)
                self.add_status(f"从文件夹扫描到 {len(image_files)} 个图片文件，成功添加 {added_count} 个")
            else:
                QMessageBox.warning(self, "警告", "所选文件夹中没有找到图片文件")
                
    def select_output_dir(self):
        """选择输出目录"""
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        
        if folder:
            self.output_path_label.setText(folder)
            self.output_path_label.setStyleSheet("color: #333;")
            
    def start_processing(self):
        """开始批量处理"""
        # 检查是否有文件
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先选择要处理的图片文件")
            return
            
        # 检查输出目录
        if self.output_path_label.text() == "未选择":
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return
        
        # 检查批量模式
        is_multi_spec = self.batch_mode_combo.currentText() == '多规格生成'
        
        if is_multi_spec:
            # 多规格模式：检查是否已配置
            if not self.selected_multi_specs or not self.selected_multi_colors:
                QMessageBox.warning(self, "警告", "请先点击'选择多种规格'按钮配置要生成的规格和颜色")
                return
            
            # 显示确认信息
            total_per_image = len(self.selected_multi_specs) * len(self.selected_multi_colors)
            total_images = self.file_list.count()
            total_output = total_per_image * total_images
            
            message = f"""多规格批量处理确认

📊 处理统计:
• 输入图片: {total_images} 张
• 每张生成: {len(self.selected_multi_specs)} 规格 × {len(self.selected_multi_colors)} 颜色 = {total_per_image} 张
• 总输出: {total_output} 张照片

📋 选中规格: {', '.join(self.selected_multi_specs[:3])}{'...' if len(self.selected_multi_specs) > 3 else ''}
🎨 选中颜色: {', '.join(self.selected_multi_colors[:3])}{'...' if len(self.selected_multi_colors) > 3 else ''}

⏱️ 预计耗时: {total_output * 3 // 60} 分钟

确定要开始处理吗？"""
            
            reply = QMessageBox.question(self, "确认批量处理", message, QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        
        # 设置处理参数
        if is_multi_spec:
            # 多规格模式参数
            params = {
                'batch_mode': 'multi_spec',
                'multi_specs': self.selected_multi_specs,
                'multi_colors': self.selected_multi_colors,
                'background_mode': 'refined',  # 多规格模式使用精细模式
                'use_alpha_matting': self.alpha_matting_check.isChecked(),
                'beautify_enabled': self.beautify_check.isChecked(),
                'brightness': self.brightness_spin.value(),
                'contrast': self.contrast_spin.value(),
                'saturation': self.saturation_spin.value(),
                'sharpness': self.sharpness_spin.value(),
                'output_format': 'jpg',
                'output_quality': 95
            }
        else:
            # 单规格模式参数
            bg_mode_text = self.bg_mode_combo.currentText()
            if "精细模式" in bg_mode_text:
                bg_mode = 'refined'
            
            # 获取实际规格名（处理去重显示）
            selected_spec_text = self.crop_combo.currentText()
            actual_spec = self.crop_combo.currentData()  # 获取存储的实际规格名
            
            params = {
                'batch_mode': 'single_spec',
                'crop_spec': actual_spec,  # 使用实际规格名
                'background_color': self.bg_combo.currentText(),
                'background_mode': bg_mode,
                'use_alpha_matting': self.alpha_matting_check.isChecked(),
                'beautify_enabled': self.beautify_check.isChecked(),
                'brightness': self.brightness_spin.value(),
                'contrast': self.contrast_spin.value(),
                'saturation': self.saturation_spin.value(),
                'sharpness': self.sharpness_spin.value(),
                'output_format': 'jpg',
                'output_quality': 95
            }
        
        self.batch_processor.set_batch_params(params)
        
        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_text.clear()
        
        mode_text = "多规格生成" if is_multi_spec else "单规格处理"
        self.add_status(f"开始批量处理 ({mode_text})...")
        
        # 启动处理线程
        self.processing_thread = BatchProcessingThread(
            self.batch_processor, 
            self.output_path_label.text()
        )
        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.status_updated.connect(self.update_status)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.start()
        
    def stop_processing(self):
        """停止批量处理"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.batch_processor.stop_batch_processing()
            self.processing_thread.quit()
            self.processing_thread.wait()
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.add_status("处理已停止")
        
    def update_progress(self, current, total, filename):
        """更新进度"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            
        self.add_status(f"处理进度: {current}/{total} - {os.path.basename(filename)}")
        
    def update_status(self, message, level):
        """更新状态"""
        self.add_status(f"[{level.upper()}] {message}")
        
    def processing_finished(self, stats):
        """处理完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        
        # 显示完成统计
        self.add_status("\n=== 批量处理完成 ===")
        self.add_status(f"总文件数: {stats['total_files']}")
        self.add_status(f"处理成功: {stats['successful_files']}")
        self.add_status(f"处理失败: {stats['failed_files']}")
        self.add_status(f"总耗时: {stats['processing_time']:.2f} 秒")
        self.add_status(f"平均耗时: {stats['average_time_per_file']:.2f} 秒/文件")
        
        # 显示完成对话框
        QMessageBox.information(
            self, "处理完成", 
            f"批量处理已完成！\n\n"
            f"成功处理: {stats['successful_files']} 个文件\n"
            f"失败: {stats['failed_files']} 个文件\n"
            f"输出目录: {self.output_path_label.text()}"
        )
        
    def _on_batch_mode_changed(self, index):
        """批量模式切换时显示/隐藏多规格选择"""
        is_multi_spec = self.batch_mode_combo.currentText() == '多规格生成'
        self.multi_spec_btn.setVisible(is_multi_spec)
        
        # 切换到多规格模式时，隐藏单规格选择
        self.crop_combo.setVisible(not is_multi_spec)
        self.bg_combo.setVisible(not is_multi_spec)
        
        # 更新标签显示
        if is_multi_spec:
            self.add_status("💡 多规格模式：点击'选择多种规格'按钮配置要生成的规格和颜色")
        else:
            self.add_status("📋 单规格模式：每张图片生成一种规格")
    
    def _open_multi_spec_selection(self):
        """打开多规格选择对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QGroupBox, QScrollArea, QWidget, QGridLayout, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("选择多种规格和颜色")
        dialog.setFixedSize(700, 600)
        
        layout = QVBoxLayout(dialog)
        
        # 规格选择
        spec_group = QGroupBox("选择证件照规格")
        spec_scroll = QScrollArea()
        spec_widget = QWidget()
        spec_layout = QGridLayout(spec_widget)
        
        spec_checkboxes = {}
        row, col = 0, 0
        
        # 按尺寸分组显示规格
        from collections import defaultdict
        from config.config import PHOTO_SPECS
        
        size_groups = defaultdict(list)
        for spec_name in PHOTO_SPECS.keys():
            size = PHOTO_SPECS[spec_name]
            size_groups[size].append(spec_name)
        
        # 为每个尺寸组创建复选框
        for size, specs in size_groups.items():
            if len(specs) == 1:
                spec_name = specs[0]
                checkbox = QCheckBox(spec_name)
            else:
                group_name = f"{specs[0]} 等{len(specs)}种"
                checkbox = QCheckBox(group_name)
                checkbox.setToolTip(f"相同尺寸 {size[0]}×{size[1]}px:\n" + "\n".join(specs))
                checkbox.specs_group = specs
            
            # 默认选中常用规格
            if any(spec in ['一寸', '小二寸', '美国护照', '欧盟护照'] for spec in specs):
                checkbox.setChecked(True)
            
            size_key = f"{size[0]}x{size[1]}"
            spec_checkboxes[size_key] = checkbox
            spec_layout.addWidget(checkbox, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        spec_scroll.setWidget(spec_widget)
        spec_scroll.setFixedHeight(200)
        
        spec_group_layout = QVBoxLayout()
        spec_group_layout.addWidget(spec_scroll)
        spec_group.setLayout(spec_group_layout)
        layout.addWidget(spec_group)
        
        # 背景色选择
        color_group = QGroupBox("选择背景颜色")
        color_layout = QGridLayout()
        
        color_checkboxes = {}
        row, col = 0, 0
        
        from config.config import BACKGROUND_COLORS
        for color_name in BACKGROUND_COLORS.keys():
            checkbox = QCheckBox(color_name)
            
            # 默认选中常用颜色
            if color_name in ['白色', '蓝色', '美国护照蓝', '欧盟护照灰']:
                checkbox.setChecked(True)
            
            color_checkboxes[color_name] = checkbox
            color_layout.addWidget(checkbox, row, col)
            
            col += 1
            if col >= 6:
                col = 0
                row += 1
        
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 获取选中的规格
            selected_specs = []
            for size_key, checkbox in spec_checkboxes.items():
                if checkbox.isChecked():
                    if hasattr(checkbox, 'specs_group'):
                        selected_specs.append(checkbox.specs_group[0])  # 选择代表
                    else:
                        selected_specs.append(checkbox.text())
            
            # 获取选中的颜色
            selected_colors = [name for name, checkbox in color_checkboxes.items() if checkbox.isChecked()]
            
            if selected_specs and selected_colors:
                self.selected_multi_specs = selected_specs
                self.selected_multi_colors = selected_colors
                
                total_count = len(selected_specs) * len(selected_colors)
                self.multi_spec_btn.setText(f"📋 已选择 {len(selected_specs)}规格×{len(selected_colors)}色={total_count}张")
                self.add_status(f"✅ 多规格配置完成：{len(selected_specs)}种规格 × {len(selected_colors)}种颜色 = {total_count}张/图片")
            else:
                QMessageBox.warning(dialog, "警告", "请至少选择一个规格和一个颜色")
        
    def add_status(self, message):
        """添加状态信息"""
        self.status_text.append(message)
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self, "确认关闭", 
                "批量处理正在进行中，确定要关闭吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.stop_processing()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()