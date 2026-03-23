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
        
        # 裁剪规格
        params_layout.addWidget(QLabel("裁剪规格:"), 0, 0)
        self.crop_combo = QComboBox()
        self.crop_combo.addItems(['一寸', '二寸', '小二寸', '大一寸', '五寸'])
        params_layout.addWidget(self.crop_combo, 0, 1)
        
        # 背景颜色
        params_layout.addWidget(QLabel("背景颜色:"), 0, 2)
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(['白色', '蓝色', '红色', '浅蓝色', '灰色'])
        params_layout.addWidget(self.bg_combo, 0, 3)
        
        # 背景处理模式
        params_layout.addWidget(QLabel("背景模式:"), 0, 4)
        self.bg_mode_combo = QComboBox()
        self.bg_mode_combo.addItems(['精细模式(推荐)', '智能模式'])
        self.bg_mode_combo.setCurrentIndex(0)  # 默认选择精细模式
        self.bg_mode_combo.setToolTip("精细模式: 最佳边缘质量，处理时间较长\n智能模式: 平衡质量和速度")
        params_layout.addWidget(self.bg_mode_combo, 0, 5)
        
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
            
        # 设置处理参数
        # 解析背景模式
        bg_mode_text = self.bg_mode_combo.currentText()
        if "精细模式" in bg_mode_text:
            bg_mode = 'refined'
        else:  # 智能模式
            bg_mode = 'auto'
        
        params = {
            'crop_spec': self.crop_combo.currentText(),
            'background_color': self.bg_combo.currentText(),
            'background_mode': bg_mode,  # 新增背景模式参数
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
        
        self.add_status("开始批量处理...")
        
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
        
    def add_status(self, message):
        """添加状态信息"""
        self.status_text.append(message)
        # 滚动到底部
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