"""
多规格同时生成对话框
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QCheckBox, QGroupBox, QMessageBox, 
                             QProgressBar, QScrollArea, QWidget, QGridLayout,
                             QComboBox, QSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont
from controllers.image_processor import ImageProcessor
from controllers.ai_processor import AIProcessor
from utils.file_helper import FileHelper
from utils.database_helper import DatabaseHelper
from config.config import PHOTO_SPECS, BACKGROUND_COLORS, PHOTO_SPEC_DETAILS
import cv2
import os
import time


class MultiSpecGenerationThread(QThread):
    """多规格生成线程"""
    progress_updated = pyqtSignal(int, str)
    generation_completed = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, image, user_id, selected_specs, selected_colors, beautify_options, mode):
        super().__init__()
        self.image = image
        self.user_id = user_id
        self.selected_specs = selected_specs
        self.selected_colors = selected_colors
        self.beautify_options = beautify_options
        self.mode = mode

    def run(self):
        """执行多规格生成"""
        try:
            ai_processor = AIProcessor()
            processor = ImageProcessor(ai_processor=ai_processor)
            generated_files = []
            
            total_tasks = len(self.selected_specs) * len(self.selected_colors)
            current_task = 0
            
            # 获取用户信息
            db = DatabaseHelper()
            user = db.get_user_by_id(self.user_id) if self.user_id else None
            user_id_number = user.id_number if user else "unknown"
            db.close()
            
            for spec in self.selected_specs:
                for color in self.selected_colors:
                    current_task += 1
                    progress = int((current_task / total_tasks) * 100)
                    
                    self.progress_updated.emit(progress, f"生成 {spec} - {color}")
                    
                    # 处理图像
                    processor.load_image_from_array(self.image.copy())
                    
                    # 应用美颜（如果启用）
                    if any(self.beautify_options.values()):
                        processor.apply_selective_beautify(self.beautify_options, {
                            'smooth_strength': 0.3,
                            'blemish_strength': 0.5
                        })
                    
                    # 裁剪到规格
                    processor.crop_to_spec(spec)
                    
                    # 更换背景
                    if self.mode == '高保真模式':
                        processor.change_background_hifi(color, beautify_options=self.beautify_options)
                    else:
                        processor.change_background(color, method='refined', use_alpha_matting=True)
                    
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
                            'filepath': filepath,
                            'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0
                        })
                    except Exception as e:
                        print(f"保存失败 {spec}-{color}: {e}")
                    
                    # 短暂延迟，让界面更新
                    time.sleep(0.1)
            
            self.generation_completed.emit(generated_files)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class MultiSpecDialog(QDialog):
    """多规格同时生成对话框"""

    def __init__(self, image, user_id, parent=None):
        super().__init__(parent)
        self.image = image
        self.user_id = user_id
        self.generated_files = []
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("多规格同时生成")
        self.setFixedSize(800, 700)
        
        layout = QVBoxLayout(self)
        
        # 预览区域
        preview_group = QGroupBox("原图预览")
        preview_layout = QHBoxLayout()
        
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(200, 250)
        self.preview_label.setStyleSheet("border: 1px solid #ddd; background-color: #f0f0f0;")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.display_preview()
        preview_layout.addWidget(self.preview_label)
        
        # 图像信息
        info_layout = QVBoxLayout()
        h, w = self.image.shape[:2]
        info_layout.addWidget(QLabel(f"尺寸: {w} × {h} 像素"))
        info_layout.addWidget(QLabel(f"格式: BGR"))
        info_layout.addWidget(QLabel(f"用户ID: {self.user_id or '未知'}"))
        info_layout.addStretch()
        preview_layout.addLayout(info_layout)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # 规格选择
        spec_group = QGroupBox("选择证件照规格")
        spec_scroll = QScrollArea()
        spec_widget = QWidget()
        spec_layout = QGridLayout(spec_widget)
        
        self.spec_checkboxes = {}
        row, col = 0, 0
        
        # 按尺寸分组显示规格
        from collections import defaultdict
        size_groups = defaultdict(list)
        for spec_name in PHOTO_SPECS.keys():
            size = PHOTO_SPECS[spec_name]
            size_groups[size].append(spec_name)
        
        # 为每个尺寸组创建复选框
        for size, specs in size_groups.items():
            if len(specs) == 1:
                # 单一规格
                spec_name = specs[0]
                checkbox = QCheckBox(spec_name)
            else:
                # 多个相同尺寸的规格，显示为组
                group_name = f"{specs[0]} 等{len(specs)}种"
                checkbox = QCheckBox(group_name)
                checkbox.setToolTip(f"相同尺寸 {size[0]}×{size[1]}px:\n" + "\n".join(specs))
                # 存储所有相同尺寸的规格
                checkbox.specs_group = specs
            
            # 添加详细信息
            if len(specs) == 1 and specs[0] in PHOTO_SPEC_DETAILS:
                details = PHOTO_SPEC_DETAILS[specs[0]]
                tooltip = f"{details['usage']}\n尺寸: {details['size_mm'][0]}×{details['size_mm'][1]}mm\n国家: {details['country']}"
                checkbox.setToolTip(tooltip)
            
            # 默认选中常用规格
            if any(spec in ['一寸', '小二寸', '美国护照', '欧盟护照'] for spec in specs):
                checkbox.setChecked(True)
            
            # 使用尺寸作为键，避免重复
            size_key = f"{size[0]}x{size[1]}"
            self.spec_checkboxes[size_key] = checkbox
            spec_layout.addWidget(checkbox, row, col)
            
            col += 1
            if col >= 3:  # 每行3个（因为现在只有10个不同尺寸）
                col = 0
                row += 1
        
        spec_scroll.setWidget(spec_widget)
        spec_scroll.setFixedHeight(150)  # 减少高度
        
        spec_group_layout = QVBoxLayout()
        
        # 智能去重提示
        dedup_info = QLabel("💡 智能去重：22种规格已优化为10种不同尺寸，避免生成重复照片\n" +
                           "📊 节省比例：54.5% | 🎯 推荐：常用4种+基础4色=16张")
        dedup_info.setStyleSheet("color: #666; font-style: italic; padding: 5px; background-color: #f8f9fa; border-radius: 4px;")
        dedup_info.setWordWrap(True)
        spec_group_layout.addWidget(dedup_info)
        
        # 快速选择按钮
        quick_select_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all_specs)
        quick_select_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("全不选")
        select_none_btn.clicked.connect(self.select_none_specs)
        quick_select_layout.addWidget(select_none_btn)
        
        select_common_btn = QPushButton("选择常用")
        select_common_btn.clicked.connect(self.select_common_specs)
        quick_select_layout.addWidget(select_common_btn)
        
        select_intl_btn = QPushButton("选择国际")
        select_intl_btn.clicked.connect(self.select_international_specs)
        quick_select_layout.addWidget(select_intl_btn)
        
        quick_select_layout.addStretch()
        
        spec_group_layout.addLayout(quick_select_layout)
        spec_group_layout.addWidget(spec_scroll)
        spec_group.setLayout(spec_group_layout)
        layout.addWidget(spec_group)
        
        # 背景色选择
        color_group = QGroupBox("选择背景颜色")
        color_layout = QGridLayout()
        
        self.color_checkboxes = {}
        row, col = 0, 0
        
        for color_name in BACKGROUND_COLORS.keys():
            checkbox = QCheckBox(color_name)
            
            # 默认选中常用颜色
            if color_name in ['白色', '蓝色', '美国护照蓝', '欧盟护照灰']:
                checkbox.setChecked(True)
            
            self.color_checkboxes[color_name] = checkbox
            color_layout.addWidget(checkbox, row, col)
            
            col += 1
            if col >= 6:  # 每行6个
                col = 0
                row += 1
        
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        # 处理选项
        options_group = QGroupBox("处理选项")
        options_layout = QVBoxLayout()
        
        # 处理模式
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("处理模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(['精细模式', '高保真模式'])
        self.mode_combo.setCurrentIndex(1)  # 默认高保真
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        options_layout.addLayout(mode_layout)
        
        # 美颜选项
        beautify_layout = QHBoxLayout()
        self.skin_smooth_check = QCheckBox("磨皮")
        self.remove_blemishes_check = QCheckBox("祛痘")
        beautify_layout.addWidget(self.skin_smooth_check)
        beautify_layout.addWidget(self.remove_blemishes_check)
        beautify_layout.addStretch()
        options_layout.addLayout(beautify_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🚀 开始生成")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.generate_btn.clicked.connect(self.start_generation)
        button_layout.addWidget(self.generate_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)

    def display_preview(self):
        """显示预览图"""
        try:
            rgb_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = 3 * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(200, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"显示预览失败: {e}")

    def select_all_specs(self):
        """全选规格"""
        for checkbox in self.spec_checkboxes.values():
            checkbox.setChecked(True)

    def select_none_specs(self):
        """全不选规格"""
        for checkbox in self.spec_checkboxes.values():
            checkbox.setChecked(False)

    def select_common_specs(self):
        """选择常用规格"""
        # 常用规格的尺寸
        common_sizes = [
            (590, 826),   # 一寸等
            (826, 1158),  # 小二寸
            (826, 1252),  # 二寸
            (780, 1134),  # 大一寸
        ]
        
        for size_key, checkbox in self.spec_checkboxes.items():
            # 从 size_key 解析尺寸
            w, h = map(int, size_key.split('x'))
            checkbox.setChecked((w, h) in common_sizes)

    def select_international_specs(self):
        """选择国际规格"""
        # 国际规格的尺寸
        intl_sizes = [
            (1200, 1200), # 美国护照、印度签证
            (826, 1063),  # 欧盟护照等
            (944, 1181),  # 泰国签证
        ]
        
        for size_key, checkbox in self.spec_checkboxes.items():
            # 从 size_key 解析尺寸
            w, h = map(int, size_key.split('x'))
            checkbox.setChecked((w, h) in intl_sizes)

    def start_generation(self):
        """开始生成"""
        # 获取选中的规格（去重后的实际规格）
        selected_specs = []
        for size_key, checkbox in self.spec_checkboxes.items():
            if checkbox.isChecked():
                if hasattr(checkbox, 'specs_group'):
                    # 多规格组，只选择第一个作为代表
                    selected_specs.append(checkbox.specs_group[0])
                else:
                    # 单一规格，从文本获取
                    spec_name = checkbox.text()
                    selected_specs.append(spec_name)
        
        selected_colors = [name for name, checkbox in self.color_checkboxes.items() if checkbox.isChecked()]
        
        if not selected_specs:
            QMessageBox.warning(self, "警告", "请至少选择一个证件照规格")
            return
        
        if not selected_colors:
            QMessageBox.warning(self, "警告", "请至少选择一个背景颜色")
            return
        
        # 显示实际生成数量
        total_count = len(selected_specs) * len(selected_colors)
        
        # 构建详细信息
        spec_info = []
        for size_key, checkbox in self.spec_checkboxes.items():
            if checkbox.isChecked():
                if hasattr(checkbox, 'specs_group'):
                    specs = checkbox.specs_group
                    w, h = map(int, size_key.split('x'))
                    spec_info.append(f"• {w}×{h}px: {specs[0]} (代表{len(specs)}种相同尺寸规格)")
                else:
                    spec_name = checkbox.text()
                    size = PHOTO_SPECS[spec_name]
                    spec_info.append(f"• {size[0]}×{size[1]}px: {spec_name}")
        
        message = f"""将生成 {len(selected_specs)} 种规格 × {len(selected_colors)} 种颜色 = {total_count} 张照片

📋 选中的规格:
{chr(10).join(spec_info)}

🎨 选中的颜色: {', '.join(selected_colors)}

💡 智能去重: 相同尺寸的规格已合并，避免重复生成

确定要继续吗？"""
        
        reply = QMessageBox.question(
            self, "确认生成", message,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 获取美颜选项
        beautify_options = {
            'skin_smooth': self.skin_smooth_check.isChecked(),
            'remove_blemishes': self.remove_blemishes_check.isChecked()
        }
        
        # 获取处理模式
        mode = self.mode_combo.currentText()
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.generate_btn.setEnabled(False)
        
        # 启动生成线程
        self.generation_thread = MultiSpecGenerationThread(
            self.image, self.user_id, selected_specs, selected_colors, beautify_options, mode
        )
        self.generation_thread.progress_updated.connect(self.update_progress)
        self.generation_thread.generation_completed.connect(self.on_generation_completed)
        self.generation_thread.error_occurred.connect(self.on_generation_error)
        self.generation_thread.start()

    def update_progress(self, progress, message):
        """更新进度"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)

    def on_generation_completed(self, generated_files):
        """生成完成"""
        self.generated_files = generated_files
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.generate_btn.setEnabled(True)
        
        # 显示结果
        success_count = len([f for f in generated_files if os.path.exists(f['filepath'])])
        total_count = len(generated_files)
        
        message = f"生成完成！\n\n成功: {success_count}/{total_count}\n\n生成的文件："
        for file_info in generated_files[:10]:  # 只显示前10个
            if os.path.exists(file_info['filepath']):
                filename = os.path.basename(file_info['filepath'])
                message += f"\n✓ {file_info['spec']} - {file_info['color']}: {filename}"
        
        if len(generated_files) > 10:
            message += f"\n... 还有 {len(generated_files) - 10} 个文件"
        
        QMessageBox.information(self, "生成完成", message)
        self.accept()

    def on_generation_error(self, error_message):
        """生成错误"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.generate_btn.setEnabled(True)
        
        QMessageBox.critical(self, "生成失败", f"生成过程中发生错误:\n{error_message}")