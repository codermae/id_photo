"""
图像处理视图
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QSlider, QGroupBox, QMessageBox, 
                             QFileDialog, QSpinBox, QCheckBox, QGridLayout, QDialog, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from controllers.image_processor import ImageProcessor
from controllers.ai_processor import AIProcessor
from utils.file_helper import FileHelper
from utils.database_helper import DatabaseHelper
from views.crop_dialog import CropDialog
import cv2
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
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        main_layout = QHBoxLayout(self)
        
        # 左侧：图像预览
        left_layout = QVBoxLayout()
        
        # 采集任务选择
        collection_group = QGroupBox("采集任务")
        collection_layout = QVBoxLayout()
        
        collection_layout.addWidget(QLabel("当前任务:"))
        self.collection_label = QLabel("未选择")
        self.collection_label.setStyleSheet("color: red; font-weight: bold;")
        collection_layout.addWidget(self.collection_label)
        
        self.collection_combo = QComboBox()
        self.collection_combo.currentIndexChanged.connect(self.on_collection_changed)
        collection_layout.addWidget(self.collection_combo)
        
        collection_group.setLayout(collection_layout)
        left_layout.addWidget(collection_group)
        
        # 图像加载
        load_group = QGroupBox("加载图像")
        load_layout = QVBoxLayout()
        
        load_btn = QPushButton("选择图像")
        load_btn.clicked.connect(self.load_image)
        load_layout.addWidget(load_btn)
        
        load_group.setLayout(load_layout)
        left_layout.addWidget(load_group)
        
        # 图像预览
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(400, 500)
        self.preview_label.setStyleSheet("border: 1px solid #ddd; background-color: #f0f0f0;")
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        left_layout.addWidget(preview_group)
        
        # 质量评分
        quality_group = QGroupBox("质量评分")
        quality_layout = QVBoxLayout()
        
        self.quality_label = QLabel("未加载图像")
        quality_layout.addWidget(self.quality_label)
        
        quality_group.setLayout(quality_layout)
        left_layout.addWidget(quality_group)
        
        # 右侧：处理参数
        right_layout = QVBoxLayout()
        
        # 规格选择
        spec_group = QGroupBox("证件照规格")
        spec_layout = QVBoxLayout()
        
        spec_select_layout = QHBoxLayout()
        spec_select_layout.addWidget(QLabel("规格:"))
        self.spec_combo = QComboBox()
        self.spec_combo.addItems(['一寸', '小二寸', '二寸', '大一寸'])
        spec_select_layout.addWidget(self.spec_combo)
        spec_layout.addLayout(spec_select_layout)
        
        spec_group.setLayout(spec_layout)
        right_layout.addWidget(spec_group)
        
        # 背景色选择
        bg_group = QGroupBox("背景色")
        bg_layout = QVBoxLayout()
        
        bg_select_layout = QHBoxLayout()
        bg_select_layout.addWidget(QLabel("颜色:"))
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(['白色', '蓝色', '红色', '灰色'])
        bg_select_layout.addWidget(self.bg_combo)
        bg_layout.addLayout(bg_select_layout)
        
        # 处理模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("模式:"))
        self.bg_mode_combo = QComboBox()
        self.bg_mode_combo.addItems(['智能模式', '精细模式'])
        self.bg_mode_combo.setCurrentIndex(0)  # 默认选择智能模式
        self.bg_mode_combo.setToolTip("智能模式: AI模型，效果好\n精细模式: AI+边缘优化，处理头发丝等细节")
        mode_layout.addWidget(self.bg_mode_combo)
        bg_layout.addLayout(mode_layout)
        
        bg_group.setLayout(bg_layout)
        right_layout.addWidget(bg_group)
        
        # 美颜选项 - 独立控制
        beautify_group = QGroupBox("美颜处理")
        beautify_layout = QVBoxLayout()
        
        # 美颜选项
        beautify_options_layout = QGridLayout()
        
        self.skin_smooth_check = QCheckBox("磨皮")
        self.skin_smooth_check.setChecked(True)
        beautify_options_layout.addWidget(self.skin_smooth_check, 0, 0)
        
        self.remove_blemishes_check = QCheckBox("祛痘")
        self.remove_blemishes_check.setChecked(True)  # 默认启用祛痘
        beautify_options_layout.addWidget(self.remove_blemishes_check, 0, 1)
        
        beautify_layout.addLayout(beautify_options_layout)
        
        # 美颜强度控制
        strength_layout = QGridLayout()
        
        # 磨皮强度
        strength_layout.addWidget(QLabel("磨皮强度:"), 0, 0)
        self.smooth_strength_slider = QSlider(Qt.Horizontal)
        self.smooth_strength_slider.setRange(0, 100)
        self.smooth_strength_slider.setValue(30)  # 默认0.3
        strength_layout.addWidget(self.smooth_strength_slider, 0, 1)
        self.smooth_strength_label = QLabel("0.3")
        strength_layout.addWidget(self.smooth_strength_label, 0, 2)
        
        # 祛痘强度
        strength_layout.addWidget(QLabel("祛痘强度:"), 1, 0)
        self.blemish_strength_slider = QSlider(Qt.Horizontal)
        self.blemish_strength_slider.setRange(0, 100)
        self.blemish_strength_slider.setValue(50)
        strength_layout.addWidget(self.blemish_strength_slider, 1, 1)
        self.blemish_strength_label = QLabel("0.5")
        strength_layout.addWidget(self.blemish_strength_label, 1, 2)
        
        # 连接信号
        self.smooth_strength_slider.valueChanged.connect(
            lambda v: self.smooth_strength_label.setText(f"{v/100:.1f}")
        )
        self.blemish_strength_slider.valueChanged.connect(
            lambda v: self.blemish_strength_label.setText(f"{v/100:.1f}")
        )
        
        beautify_layout.addLayout(strength_layout)
        
        beautify_group.setLayout(beautify_layout)
        right_layout.addWidget(beautify_group)
        
        # 亮度和对比度
        adjust_group = QGroupBox("亮度和对比度")
        adjust_layout = QVBoxLayout()
        
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("亮度:"))
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        brightness_layout.addWidget(self.brightness_slider)
        self.brightness_label = QLabel("0")
        brightness_layout.addWidget(self.brightness_label)
        adjust_layout.addLayout(brightness_layout)
        
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("对比度:"))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(50, 200)
        self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self.on_contrast_changed)
        contrast_layout.addWidget(self.contrast_slider)
        self.contrast_label = QLabel("1.0")
        contrast_layout.addWidget(self.contrast_label)
        adjust_layout.addLayout(contrast_layout)
        
        adjust_group.setLayout(adjust_layout)
        right_layout.addWidget(adjust_group)
        
        # 处理按钮
        process_group = QGroupBox("处理")
        process_layout = QVBoxLayout()
        
        # 手动裁剪按钮（新增）
        self.manual_crop_btn = QPushButton("✂️ 手动裁剪")
        self.manual_crop_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
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
        self.manual_crop_btn.clicked.connect(self.manual_crop)
        self.manual_crop_btn.setEnabled(False)
        process_layout.addWidget(self.manual_crop_btn)
        
        self.process_btn = QPushButton("应用处理")
        self.process_btn.clicked.connect(self.apply_processing)
        self.process_btn.setEnabled(False)
        process_layout.addWidget(self.process_btn)
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_image)
        self.reset_btn.setEnabled(False)
        process_layout.addWidget(self.reset_btn)
        
        process_group.setLayout(process_layout)
        right_layout.addWidget(process_group)
        
        # 保存按钮
        save_group = QGroupBox("保存")
        save_layout = QVBoxLayout()
        
        self.save_btn = QPushButton("保存处理后的图像")
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)
        save_layout.addWidget(self.save_btn)
        
        save_group.setLayout(save_layout)
        right_layout.addWidget(save_group)
        
        # 批量处理按钮
        batch_group = QGroupBox("批量处理")
        batch_layout = QVBoxLayout()
        
        batch_btn = QPushButton("批量处理")
        batch_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        batch_btn.clicked.connect(self.open_batch_processing)
        batch_layout.addWidget(batch_btn)
        
        batch_group.setLayout(batch_layout)
        right_layout.addWidget(batch_group)
        
        right_layout.addStretch()
        
        # 添加到主布局
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)
        
        # 加载采集任务
        self.load_collections()

    def load_image(self):
        """加载图像"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择图像", "", "图像文件 (*.jpg *.png *.bmp)"
        )
        
        if filepath:
            try:
                image = self.processor.load_image(filepath)
                self.current_image_path = filepath
                
                # 从文件名中提取身份证号
                filename = os.path.basename(filepath)
                # 文件名格式: {id_number}_{timestamp}.jpg 或 {id_number}_{spec}_{bg_color}_{timestamp}.jpg
                parts = filename.split('_')
                if len(parts) >= 2:
                    potential_id = parts[0]
                    # 验证是否是有效的身份证号（15或18位数字）
                    if potential_id.isdigit() and len(potential_id) in [15, 18]:
                        # 查询用户是否存在
                        db = DatabaseHelper()
                        user = db.get_user_by_id_number(potential_id)
                        if user:
                            self.current_user_id = user.id
                            print(f"[INFO] 从文件名识别用户: {user.name} (ID: {user.id}, 身份证: {potential_id})")
                        else:
                            self.current_user_id = None
                            print(f"[WARNING] 文件名中的身份证号 {potential_id} 在数据库中不存在")
                        db.close()
                    else:
                        self.current_user_id = None
                        print(f"[WARNING] 无法从文件名中提取有效的身份证号: {filename}")
                else:
                    self.current_user_id = None
                    print(f"[WARNING] 文件名格式不符合预期: {filename}")
                
                self.display_image(image)
                self.update_quality_score()
                
                self.manual_crop_btn.setEnabled(True)  # 启用手动裁剪按钮
                self.process_btn.setEnabled(True)
                self.reset_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
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

    def update_quality_score(self):
        """更新质量评分"""
        score = self.processor.get_quality_score()
        self.quality_label.setText(f"质量评分: {score}/100")
        
        if score >= 70:
            self.quality_label.setStyleSheet("color: green; font-weight: bold;")
        elif score >= 50:
            self.quality_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.quality_label.setStyleSheet("color: red; font-weight: bold;")

    def apply_processing(self):
        """应用处理"""
        if self.processor.current_image is None:
            QMessageBox.warning(self, "警告", "没有加载图像")
            return

        try:
            spec = self.spec_combo.currentText()
            bg_color = self.bg_combo.currentText()
            
            # 新的美颜处理 - 使用独立控制
            beautify_options = {
                'skin_smooth': self.skin_smooth_check.isChecked(),
                'remove_blemishes': self.remove_blemishes_check.isChecked(),
            }
            
            beautify_strengths = {
                'smooth_strength': self.smooth_strength_slider.value() / 100.0,
                'blemish_strength': self.blemish_strength_slider.value() / 100.0,
            }
            
            # 应用美颜处理
            if any(beautify_options.values()):
                print(f"[DEBUG] 应用美颜选项: {beautify_options}")
                print(f"[DEBUG] 美颜强度: {beautify_strengths}")
                self.processor.apply_selective_beautify(beautify_options, beautify_strengths)
            
            # 裁切
            self.processor.crop_to_spec(spec)
            
            # 更换背景 - 根据选择的模式
            bg_mode = self.bg_mode_combo.currentText()
            if "精细模式" in bg_mode:
                # 使用AI模型 + 高级边缘优化
                print("[INFO] 使用精细模式进行背景替换（专门处理头发丝和边缘细节）")
                self.processor.change_background(bg_color, method='refined')
            else:
                # 使用AI模型，效果好
                print("[INFO] 使用智能模式进行背景替换")
                self.processor.change_background(bg_color, method='auto')
            
            # 显示处理后的图像
            self.display_image(self.processor.get_current_image())
            self.update_quality_score()
            
            QMessageBox.information(self, "成功", "图像处理完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理失败: {e}")
            import traceback
            traceback.print_exc()

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
                "无法识别用户信息\n\n请确保加载的图片文件名包含身份证号\n格式: {身份证号}_{时间戳}.jpg"
            )
            return
        
        try:
            # 获取用户信息
            db = DatabaseHelper()
            user = db.get_user_by_id(self.current_user_id)
            
            if not user:
                QMessageBox.warning(self, "警告", f"用户ID {self.current_user_id} 不存在")
                db.close()
                return
            
            # 在关闭数据库前保存用户信息
            user_name = user.name
            user_id_number = user.id_number
            
            # 获取当前选择的规格和背景色
            spec = self.spec_combo.currentText()
            bg_color = self.bg_combo.currentText()
            
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

    def open_batch_processing(self):
        """打开批量处理窗口"""
        from views.batch_processing_dialog import BatchProcessingDialog
        
        dialog = BatchProcessingDialog(self)
        dialog.exec_()
    
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
            current_spec = self.spec_combo.currentText()
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
            
            if self.current_collection_id is None:
                self.collection_label.setText("未选择")
                self.collection_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                db = DatabaseHelper()
                collection = db.get_collection_by_id(self.current_collection_id)
                db.close()
                
                if collection:
                    self.collection_label.setText(f"{collection.name} ({collection.organization})")
                    self.collection_label.setStyleSheet("color: green; font-weight: bold;")
                    print(f"[INFO] 已选择采集任务: {collection.name} (ID: {self.current_collection_id})")
