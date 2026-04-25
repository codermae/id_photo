"""
摄像头拍照视图
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QSlider, QGroupBox, QMessageBox, QSpinBox, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage
from controllers.camera import CameraController
from controllers.ai_processor import AIProcessor
from controllers.duplicate_checker import DuplicateChecker
from controllers.identity_verifier import IdentityVerifier
from utils.database_helper import DatabaseHelper
from utils.file_helper import FileHelper
from utils.voice_helper import get_voice_helper
import cv2
import numpy as np
import os

class SimilarityCalculationThread(QThread):
    """相似度计算线程 - 在后台计算相似度，不阻塞 UI"""
    similarity_ready = pyqtSignal(float)  # 相似度
    
    def __init__(self, id_card_photo, current_frame, identity_verifier):
        super().__init__()
        self.id_card_photo = id_card_photo
        self.current_frame = current_frame
        self.identity_verifier = identity_verifier
    
    def run(self):
        """运行相似度计算"""
        try:
            # 如果是二进制数据，转换为图像
            id_card_photo = self.id_card_photo
            if isinstance(id_card_photo, bytes):
                nparr = np.frombuffer(id_card_photo, np.uint8)
                id_card_photo = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if id_card_photo is None:
                self.similarity_ready.emit(0.0)
                return
            
            id_card_photo = cv2.cvtColor(id_card_photo, cv2.COLOR_BGR2RGB)
            
            # 提取特征
            id_card_encoding = self.identity_verifier.face_manager.encode_face(id_card_photo)
            current_encoding = self.identity_verifier.face_manager.encode_face(self.current_frame)
            
            if id_card_encoding is not None and current_encoding is not None:
                # 计算相似度
                distance = np.linalg.norm(id_card_encoding - current_encoding)
                similarity = 1.0 - min(distance / 2.0, 1.0)
                self.similarity_ready.emit(similarity)
            else:
                self.similarity_ready.emit(0.0)
        
        except Exception as e:
            print(f"[ERROR] 相似度计算失败: {e}")
            self.similarity_ready.emit(0.0)

class SavePhotoThread(QThread):
    """保存照片线程 - 在后台执行所有耗时的保存操作"""
    save_complete = pyqtSignal(bool, str)  # (success, message)
    
    def __init__(self, user_id, frame, duplicate_checker, user_name, collection_id=None):
        super().__init__()
        self.user_id = user_id
        self.frame = frame
        self.duplicate_checker = duplicate_checker
        self.user_name = user_name
        self.collection_id = collection_id
    
    def run(self):
        """运行保存"""
        try:
            db = DatabaseHelper()
            user = db.get_user_by_id(self.user_id)
            
            if not user:
                self.save_complete.emit(False, f"用户ID {self.user_id} 不存在")
                db.close()
                return
            
            # 1. 保存原始照片
            print("[INFO] 保存原始照片...")
            filepath = FileHelper.save_raw_photo(user.id_number, self.frame)
            file_size = FileHelper.get_file_size(filepath)
            
            # 2. 添加照片记录
            print("[INFO] 添加照片记录...")
            photo = db.add_photo(
                user_id=self.user_id,
                photo_type='raw',
                file_path=filepath,
                file_size=file_size
            )
            
            # 3. 保存人脸特征（用于身份核验）
            print("[INFO] 提取并保存人脸特征...")
            self.duplicate_checker.save_face_encoding(self.user_id, self.frame)
            
            # 4. 创建或更新采集记录（拍照后更新为processing待处理状态）
            print("[INFO] 更新采集记录...")
            existing_records = db.get_records_by_user(self.user_id)
            if existing_records:
                # 拍照后更新状态为processing（待处理）
                latest_record = existing_records[-1]
                latest_record.status = 'processing'
                latest_record.notes = f'照片已采集: {os.path.basename(filepath)}'
                db.db.commit()
                print(f"[INFO] 更新采集记录: record_id={latest_record.id}, status=processing")
            else:
                # 创建新的采集记录（processing状态）
                import getpass
                operator = getpass.getuser()
                record = db.add_record(
                    user_id=self.user_id,
                    operator=operator,
                    status='processing',
                    notes=f'照片已采集: {os.path.basename(filepath)}',
                    collection_id=self.collection_id
                )
                print(f"[INFO] 创建采集记录: record_id={record.id}, status=processing, collection_id={self.collection_id}")
            
            db.close()
            
            # 保存成功
            message = f"照片已保存\n用户: {self.user_name}\n路径: {filepath}"
            self.save_complete.emit(True, message)
            
        except Exception as e:
            print(f"[ERROR] 保存照片失败: {e}")
            import traceback
            traceback.print_exc()
            self.save_complete.emit(False, f"保存照片失败: {e}")

class CameraThread(QThread):
    """摄像头线程"""
    frame_ready = pyqtSignal(np.ndarray)

    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        self.running = False

    def run(self):
        """运行"""
        print("[DEBUG] CameraThread.run() - 开始运行")
        self.running = True
        
        print("[DEBUG] 调用 camera.start()...")
        result = self.camera.start(self.on_frame)
        
        if result:
            print("[DEBUG] camera.start() 成功")
        else:
            print("[ERROR] camera.start() 失败")

    def on_frame(self, frame):
        """帧回调"""
        if self.running:
            self.frame_ready.emit(frame)
    
    def stop(self):
        """停止线程"""
        print("[DEBUG] CameraThread.stop() - 停止线程")
        self.running = False

class CameraView(QWidget):
    """摄像头拍照视图"""

    def __init__(self):
        super().__init__()
        print("[DEBUG] CameraView.__init__() - 开始初始化")
        
        self.camera = None
        self.camera_thread = None
        
        print("[DEBUG] 初始化 AIProcessor...")
        self.ai_processor = AIProcessor()
        
        print("[DEBUG] 初始化 DuplicateChecker...")
        self.duplicate_checker = DuplicateChecker()
        
        print("[DEBUG] 初始化 IdentityVerifier...")
        self.identity_verifier = IdentityVerifier()
        
        print("[DEBUG] 初始化 VoiceHelper...")
        self.voice_helper = get_voice_helper()
        
        print("[DEBUG] 设置实例变量...")
        self.current_frame = None
        self.current_user_id = None
        self.current_user_name = None
        self.current_id_photo = None  # 当前身份证照片（从 id_card_view 传入）
        self.current_collection_id = None  # 当前采集任务ID
        self.last_voice_feedback = {}  # 记录上次播放的语音反馈，避免重复播放
        
        # 相似度计算线程
        self.similarity_thread = None
        self.is_calculating_similarity = False
        self.last_similarity_frame = None  # 用于帧差检测，减少不必要的相似度计算
        
        # 打开摄像头线程
        self.open_camera_thread = None
        
        # 自动拍照相关
        self.auto_photo_timer = None
        self.auto_photo_countdown = 0
        self.last_quality_score = 0
        self.last_similarity = 0
        
        # 保存照片线程
        self.save_photo_thread = None
        self.is_saving_photo = False
        
        print("[DEBUG] 开始初始化UI...")
        self.init_ui()
        print("[DEBUG] CameraView 初始化完成")

    def init_ui(self):
        """初始化界面"""
        main_layout = QHBoxLayout(self)
        
        # 左侧：摄像头预览
        left_layout = QVBoxLayout()
        
        # 摄像头选择
        camera_group = QGroupBox("摄像头设置")
        camera_layout = QVBoxLayout()
        
        camera_select_layout = QHBoxLayout()
        camera_select_layout.addWidget(QLabel("选择摄像头:"))
        self.camera_combo = QComboBox()
        self.refresh_cameras()
        camera_select_layout.addWidget(self.camera_combo)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.setMaximumWidth(80)
        refresh_btn.clicked.connect(self.refresh_cameras)
        camera_select_layout.addWidget(refresh_btn)
        
        camera_layout.addLayout(camera_select_layout)
        camera_group.setLayout(camera_layout)
        left_layout.addWidget(camera_group)
        
        # 摄像头预览
        preview_group = QGroupBox("实时预览")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(640, 480)
        self.preview_label.setStyleSheet("border: 1px solid #ddd; background-color: black;")
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        left_layout.addWidget(preview_group)
        
        # 摄像头控制
        control_group = QGroupBox("摄像头控制")
        control_layout = QVBoxLayout()
        
        self.open_btn = QPushButton("打开摄像头")
        self.open_btn.clicked.connect(self.open_camera)
        control_layout.addWidget(self.open_btn)
        
        self.close_btn = QPushButton("关闭摄像头")
        self.close_btn.clicked.connect(self.close_camera)
        self.close_btn.setEnabled(False)
        control_layout.addWidget(self.close_btn)
        
        control_group.setLayout(control_layout)
        left_layout.addWidget(control_group)
        
        # 右侧：拍照和质量检测
        right_layout = QVBoxLayout()
        
        # 用户选择
        user_group = QGroupBox("用户选择")
        user_layout = QVBoxLayout()
        
        user_select_layout = QHBoxLayout()
        user_select_layout.addWidget(QLabel("当前用户:"))
        self.user_id_label = QLabel("未选择")
        self.user_id_label.setStyleSheet("font-weight: bold; color: blue; font-size: 12px;")
        user_select_layout.addWidget(self.user_id_label)
        
        user_select_layout.addWidget(QLabel("用户名:"))
        self.user_name_label = QLabel("未选择")
        self.user_name_label.setStyleSheet("font-weight: bold; color: blue; font-size: 12px;")
        user_select_layout.addWidget(self.user_name_label)
        
        user_select_layout.addStretch()
        
        # 手动选择按钮（如果没有读取到身份证）
        manual_select_btn = QPushButton("手动选择")
        manual_select_btn.setMaximumWidth(100)
        manual_select_btn.clicked.connect(self.manual_select_user)
        user_select_layout.addWidget(manual_select_btn)
        
        user_layout.addLayout(user_select_layout)
        user_group.setLayout(user_layout)
        right_layout.addWidget(user_group)
        
        # 存储当前用户信息
        self.current_user_id = None
        self.current_user_name = None
        
        # 质量检测
        quality_group = QGroupBox("质量检测")
        quality_layout = QVBoxLayout()
        
        self.quality_label = QLabel("等待检测...")
        self.quality_label.setStyleSheet("color: #666;")
        quality_layout.addWidget(self.quality_label)
        
        self.feedback_label = QLabel()
        self.feedback_label.setWordWrap(True)
        quality_layout.addWidget(self.feedback_label)
        
        quality_group.setLayout(quality_layout)
        right_layout.addWidget(quality_group)
        
        # 亮度和对比度调整
        adjust_group = QGroupBox("摄像头调整")
        adjust_layout = QVBoxLayout()
        
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("亮度:"))
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        brightness_layout.addWidget(self.brightness_slider)
        adjust_layout.addLayout(brightness_layout)
        
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("对比度:"))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-100, 100)  # 改为 -100 到 100
        self.contrast_slider.setValue(0)  # 改为 0
        self.contrast_slider.valueChanged.connect(self.on_contrast_changed)
        contrast_layout.addWidget(self.contrast_slider)
        adjust_layout.addLayout(contrast_layout)
        
        adjust_group.setLayout(adjust_layout)
        right_layout.addWidget(adjust_group)
        
        # 美颜处理
        beautify_group = QGroupBox("美颜处理")
        beautify_layout = QVBoxLayout()
        
        beautify_strength_layout = QHBoxLayout()
        beautify_strength_layout.addWidget(QLabel("美颜强度:"))
        self.beautify_strength_slider = QSlider(Qt.Horizontal)
        self.beautify_strength_slider.setRange(0, 200)
        self.beautify_strength_slider.setValue(0)  # 改为 0
        self.beautify_strength_label = QLabel("0.0x")  # 改为 0.0x
        self.beautify_strength_label.setMinimumWidth(40)
        self.beautify_strength_slider.valueChanged.connect(self.on_beautify_strength_changed)
        beautify_strength_layout.addWidget(self.beautify_strength_slider)
        beautify_strength_layout.addWidget(self.beautify_strength_label)
        beautify_layout.addLayout(beautify_strength_layout)
        
        beautify_group.setLayout(beautify_layout)
        right_layout.addWidget(beautify_group)
        
        # 拍照按钮
        photo_group = QGroupBox("拍照")
        photo_layout = QVBoxLayout()
        
        # 自动拍照勾选框
        auto_photo_layout = QHBoxLayout()
        self.auto_photo_checkbox = QCheckBox("自动拍照")
        self.auto_photo_checkbox.setToolTip("启用后，当状态完美时将在3秒后自动拍照")
        auto_photo_layout.addWidget(self.auto_photo_checkbox)
        auto_photo_layout.addStretch()
        photo_layout.addLayout(auto_photo_layout)
        
        self.take_photo_btn = QPushButton("拍照")
        self.take_photo_btn.setMinimumHeight(50)
        self.take_photo_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.take_photo_btn.clicked.connect(self.take_photo)
        self.take_photo_btn.setEnabled(False)
        photo_layout.addWidget(self.take_photo_btn)
        
        # 身份核验按钮
        self.verify_identity_btn = QPushButton("身份核验")
        self.verify_identity_btn.setMinimumHeight(50)
        self.verify_identity_btn.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #4CAF50; color: white;")
        self.verify_identity_btn.clicked.connect(self.verify_identity)
        self.verify_identity_btn.setEnabled(False)
        photo_layout.addWidget(self.verify_identity_btn)
        
        photo_group.setLayout(photo_layout)
        right_layout.addWidget(photo_group)
        
        right_layout.addStretch()
        
        # 添加到主布局
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        
        # 定时器用于质量检测 - 降低频率减少卡顿
        self.quality_timer = QTimer()
        self.quality_timer.timeout.connect(self.check_quality)
        self.quality_timer.start(1000)  # 改为1秒一次，减少身份核验计算频率

    def refresh_cameras(self):
        """刷新摄像头列表"""
        self.camera_combo.clear()
        cameras = CameraController.list_cameras()
        for camera_id in cameras:
            self.camera_combo.addItem(f"摄像头 {camera_id}", camera_id)

    def open_camera(self):
        """打开摄像头"""
        print("[DEBUG] 开始打开摄像头...")
        
        camera_id = self.camera_combo.currentData()
        if camera_id is None:
            QMessageBox.warning(self, "警告", "没有可用的摄像头")
            return

        print(f"[DEBUG] 选择的摄像头ID: {camera_id}")

        # 禁用按钮，防止重复点击
        self.open_btn.setEnabled(False)
        self.open_btn.setText("正在打开...")
        
        print("[DEBUG] 按钮已禁用，开始后台线程...")
        
        # 在后台线程打开摄像头
        def open_camera_in_thread():
            try:
                print("[DEBUG] 后台线程开始执行...")
                print("[DEBUG] 创建CameraController...")
                self.camera = CameraController(camera_id)
                
                print("[DEBUG] 调用camera.open()...")
                # 使用快速模式减少延迟
                if self.camera.open(fast_mode=True):
                    print("[INFO] 摄像头已打开")
                else:
                    print("[ERROR] 摄像头打开失败")
                    self.open_btn.setEnabled(True)
                    self.open_btn.setText("打开摄像头")
                    QMessageBox.critical(self, "错误", "打开摄像头失败")
            except Exception as e:
                print(f"[ERROR] 打开摄像头异常: {e}")
                import traceback
                traceback.print_exc()
                self.open_btn.setEnabled(True)
                self.open_btn.setText("打开摄像头")
                QMessageBox.critical(self, "错误", f"打开摄像头失败: {e}")
        
        # 启动后台线程打开摄像头
        print("[DEBUG] 创建并启动后台线程...")
        self.open_camera_thread = QThread()
        self.open_camera_thread.run = open_camera_in_thread
        self.open_camera_thread.finished.connect(self.on_camera_opened)
        self.open_camera_thread.start()
        print("[DEBUG] 后台线程已启动，等待完成...")
    
    def on_camera_opened(self):
        """摄像头打开完成回调（在主线程中执行）"""
        print("[DEBUG] on_camera_opened 回调被调用...")
        
        if self.camera:
            print("[DEBUG] 摄像头对象存在，开始初始化...")
            
            # 在主线程中启动摄像头线程和定时器
            print("[DEBUG] 创建CameraThread...")
            self.camera_thread = CameraThread(self.camera)
            self.camera_thread.frame_ready.connect(self.on_frame_ready)
            
            print("[DEBUG] 启动CameraThread...")
            self.camera_thread.start()
            
            # 在主线程中启动质量检测定时器 - 降低频率减少卡顿
            print("[DEBUG] 启动质量检测定时器...")
            if hasattr(self, 'quality_timer'):
                self.quality_timer.start(1000)  # 改为1秒一次
            
            print("[DEBUG] 更新UI状态...")
            self.open_btn.setText("打开摄像头")
            self.close_btn.setEnabled(True)
            self.take_photo_btn.setEnabled(True)
            self.verify_identity_btn.setEnabled(True)
            
            print("[INFO] 质量检测已启动")
            print("[DEBUG] 摄像头初始化完成！")
        else:
            print("[ERROR] 摄像头对象为空！")
            self.open_btn.setEnabled(True)
            self.open_btn.setText("打开摄像头")

    def close_camera(self):
        """关闭摄像头"""
        # 停止自动拍照定时器
        if self.auto_photo_timer:
            self.auto_photo_timer.stop()
            self.auto_photo_timer = None
            self.auto_photo_countdown = 0
        
        # 清理打开摄像头的线程
        if self.open_camera_thread:
            self.open_camera_thread.quit()
            self.open_camera_thread.wait(1000)
            self.open_camera_thread = None
        
        # 1. 停止质量检查定时器
        if hasattr(self, 'quality_timer'):
            self.quality_timer.stop()
        
        # 2. 停止线程
        if self.camera_thread:
            self.camera_thread.stop()  # 设置停止标志
            self.camera_thread.quit()  # 退出事件循环
            self.camera_thread.wait(1000)  # 等待最多1秒
            self.camera_thread = None
        
        # 3. 关闭摄像头
        if self.camera:
            self.camera.close()
            self.camera = None
        
        # 4. 停止AI处理器的调试输出
        if self.ai_processor:
            self.ai_processor.debug_mode = False
            self.ai_processor.last_debug_time = 0
        
        # 5. 清空当前帧
        self.current_frame = None
        
        # 6. 清空显示
        self.preview_label.clear()
        self.preview_label.setText("摄像头已关闭")
        
        # 7. 清空质量信息
        if hasattr(self, 'quality_label'):
            self.quality_label.setText("质量检测已停止")
        
        # 8. 更新按钮状态
        self.open_btn.setEnabled(True)
        self.close_btn.setEnabled(False)
        self.take_photo_btn.setEnabled(False)
        self.verify_identity_btn.setEnabled(False)
        
        print("[INFO] 摄像头已关闭，所有处理已停止")

    def on_frame_ready(self, frame):
        """帧准备好回调"""
        # 只在前几帧输出调试信息，避免刷屏
        if not hasattr(self, '_frame_count'):
            self._frame_count = 0
        
        self._frame_count += 1
        if self._frame_count <= 5:
            print(f"[DEBUG] on_frame_ready - 收到第 {self._frame_count} 帧")
        elif self._frame_count == 6:
            print("[DEBUG] 帧接收正常，停止输出帧调试信息")
        
        self.current_frame = frame
        self.display_frame(frame)

    def display_frame(self, frame):
        """显示帧"""
        try:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = 3 * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # 缩放到标签大小
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaledToWidth(640, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"显示帧失败: {e}")

    def check_quality(self):
        """检查质量 - 实时更新"""
        if self.current_frame is None:
            return

        try:
            quality_info = self.ai_processor.check_face_quality(self.current_frame)
            
            # 更新质量标签
            score = quality_info['overall_score']
            self.last_quality_score = score  # 保存质量评分
            self.quality_label.setText(f"质量评分: {score}/100")
            self.last_quality_score = score
            
            if score >= 70:
                self.quality_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            elif score >= 50:
                self.quality_label.setStyleSheet("color: orange; font-weight: bold; font-size: 14px;")
            else:
                self.quality_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            
            # 获取反馈信息
            feedback = self.ai_processor.get_quality_feedback(quality_info)
            feedback_text = "\n".join(feedback)
            
            # ========== 添加持续显示的身份核验相似度 ==========
            if self.current_user_id is not None and self.current_id_photo is not None:
                # 添加当前的相似度信息（如果有的话）
                if hasattr(self, 'last_similarity') and self.last_similarity is not None:
                    similarity_text = f"身份核验相似度: {self.last_similarity:.0%}"
                    feedback_text += f"\n{similarity_text}"
                else:
                    feedback_text += f"\n身份核验相似度: 计算中..."
            
            # ========== 优化：智能身份核验相似度计算 ==========
            if self.current_user_id is not None and self.current_id_photo is not None:
                # 如果上一个相似度计算还没完成，就跳过这次计算
                if not self.is_calculating_similarity:
                    # 只有当帧发生明显变化时才重新计算相似度，减少不必要的计算
                    should_calculate = True
                    if hasattr(self, 'last_similarity_frame') and self.last_similarity_frame is not None:
                        # 简单的帧差检测，如果变化不大就跳过计算
                        try:
                            frame_diff = cv2.absdiff(self.current_frame, self.last_similarity_frame)
                            diff_mean = np.mean(frame_diff)
                            if diff_mean < 10:  # 如果帧差很小，跳过计算
                                should_calculate = False
                        except:
                            pass  # 如果出错，还是进行计算
                    
                    if should_calculate:
                        self.is_calculating_similarity = True
                        self.last_similarity_frame = self.current_frame.copy()
                        self.similarity_thread = SimilarityCalculationThread(
                            self.current_id_photo,
                            self.current_frame,
                            self.identity_verifier
                        )
                        self.similarity_thread.similarity_ready.connect(self.on_similarity_ready)
                        self.similarity_thread.start()
            
            # 更新反馈标签
            self.feedback_label.setText(feedback_text)
            
            # ========== 语音提示 ==========
            self._play_voice_feedback(feedback)
            
            # ========== 根据相似度设置颜色 ==========
            if self.current_user_id is not None and hasattr(self, 'last_similarity') and self.last_similarity is not None:
                # 如果有相似度信息，根据相似度设置颜色
                if self.last_similarity >= 0.6:
                    self.feedback_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.feedback_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                # 没有相似度信息时，根据质量设置颜色
                if score >= 70:
                    self.feedback_label.setStyleSheet("color: green; font-weight: bold;")
                elif score >= 50:
                    self.feedback_label.setStyleSheet("color: orange;")
                else:
                    self.feedback_label.setStyleSheet("color: red;")
                
        except Exception as e:
            print(f"质量检查失败: {e}")
    
    def on_similarity_ready(self, similarity):
        """相似度计算完成回调"""
        self.is_calculating_similarity = False
        self.last_similarity = similarity
        
        # 检查自动拍照条件
        score = self.last_quality_score
        self._check_auto_photo(score, similarity)
    
    def _check_auto_photo(self, score: float, similarity: float):
        """检查是否应该自动拍照"""
        if not self.auto_photo_checkbox.isChecked():
            # 自动拍照未启用，停止计时器
            if self.auto_photo_timer:
                self.auto_photo_timer.stop()
                self.auto_photo_timer = None
                self.auto_photo_countdown = 0
            return
        
        # 检查状态是否完美
        is_perfect = score >= 70 and similarity >= 0.6
        
        if is_perfect:
            # 状态完美，启动倒计时
            if self.auto_photo_countdown == 0:
                self.auto_photo_countdown = 3
                self.voice_helper.speak("状态完美，3秒后自动拍照", force=True)
                
                # 启动倒计时定时器
                if not self.auto_photo_timer:
                    self.auto_photo_timer = QTimer()
                    self.auto_photo_timer.timeout.connect(self._auto_photo_countdown)
                    self.auto_photo_timer.start(1000)  # 每秒更新一次
        else:
            # 状态不完美，停止倒计时
            if self.auto_photo_countdown > 0:
                self.auto_photo_countdown = 0
                if self.auto_photo_timer:
                    self.auto_photo_timer.stop()
                    self.auto_photo_timer = None
                self.voice_helper.speak("状态改变，已取消自动拍照", force=True)
    
    def _auto_photo_countdown(self):
        """自动拍照倒计时"""
        self.auto_photo_countdown -= 1
        
        if self.auto_photo_countdown > 0:
            # 继续倒计时
            self.quality_label.setText(f"质量评分: {self.last_quality_score}/100\n自动拍照倒计时: {self.auto_photo_countdown}秒")
        else:
            # 倒计时结束，执行自动拍照
            self.auto_photo_timer.stop()
            self.auto_photo_timer = None
            self.take_photo()
            # 拍照完成后播放提示
            self.voice_helper.speak("拍照完成", force=True)
    
    def _play_voice_feedback(self, feedback_list):
        """播放语音反馈"""
        if not self.voice_helper.available:
            return
        
        # 将反馈列表转换为字符串
        feedback_str = "".join(feedback_list)
        
        # 避免重复播放相同的反馈
        if feedback_str in self.last_voice_feedback:
            return
        
        # 记录本次反馈
        self.last_voice_feedback = {feedback_str: True}
        
        # 播放语音
        if feedback_list:
            # 只播放第一条反馈
            text = feedback_list[0]
            self.voice_helper.speak(text, async_mode=True)

    def take_photo(self):
        """拍照"""
        if self.current_frame is None:
            QMessageBox.warning(self, "警告", "没有可用的帧")
            return

        if self.current_user_id is None:
            QMessageBox.warning(self, "警告", "请先选择用户或读取身份证")
            return

        # 防止重复点击
        if self.is_saving_photo:
            QMessageBox.warning(self, "提示", "正在保存照片，请稍候...")
            return

        try:
            db = DatabaseHelper()
            user = db.get_user_by_id(self.current_user_id)
            
            if not user:
                QMessageBox.warning(self, "警告", f"用户ID {self.current_user_id} 不存在")
                db.close()
                return
            
            db.close()
            
            # 禁用拍照按钮，显示保存中的提示
            self.take_photo_btn.setEnabled(False)
            self.take_photo_btn.setText("保存中...")
            self.is_saving_photo = True
            
            # 在后台线程中保存照片
            print("[INFO] 启动保存照片线程...")
            self.save_photo_thread = SavePhotoThread(
                self.current_user_id,
                self.current_frame,
                self.duplicate_checker,
                self.current_user_name,
                self.current_collection_id
            )
            self.save_photo_thread.save_complete.connect(self.on_save_photo_complete)
            self.save_photo_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"拍照失败: {e}")
            self.take_photo_btn.setEnabled(True)
            self.take_photo_btn.setText("拍照")
            self.is_saving_photo = False
            import traceback
            traceback.print_exc()
    
    def on_save_photo_complete(self, success, message):
        """保存照片完成回调"""
        try:
            # 恢复按钮状态
            self.take_photo_btn.setEnabled(True)
            self.take_photo_btn.setText("拍照")
            self.is_saving_photo = False
            
            if success:
                # 通知主窗口更新统计
                self.notify_data_changed()
                
                # 显示成功消息
                QMessageBox.information(self, "成功", message)
                print("[INFO] 照片保存成功")
            else:
                # 显示错误消息
                QMessageBox.critical(self, "错误", message)
                print(f"[ERROR] 照片保存失败: {message}")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理保存结果失败: {e}")
            import traceback
            traceback.print_exc()
    
    def on_brightness_changed(self, value):
        """亮度改变"""
        if self.camera:
            self.camera.set_brightness(value)

    def on_contrast_changed(self, value):
        """对比度改变"""
        if self.camera:
            self.camera.set_contrast(value)  # 直接传递值

    def on_beautify_strength_changed(self, value):
        """美颜强度改变"""
        strength = value / 100.0
        self.beautify_strength_label.setText(f"{strength:.1f}x")

    def cleanup(self):
        """清理资源"""
        self.quality_timer.stop()
        
        # 清理打开摄像头的线程
        if self.open_camera_thread:
            self.open_camera_thread.quit()
            self.open_camera_thread.wait(1000)
            self.open_camera_thread = None
        
        # 停止保存照片线程
        if self.save_photo_thread:
            self.save_photo_thread.quit()
            self.save_photo_thread.wait(1000)
            self.save_photo_thread = None
        
        self.close_camera()
        if self.ai_processor:
            self.ai_processor.close()
        if self.duplicate_checker:
            self.duplicate_checker.close()
        if self.identity_verifier:
            self.identity_verifier.close()
        if self.voice_helper:
            self.voice_helper.close()
    
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

    def set_current_user(self, user_id, user_name, id_photo=None, collection_id=None):
        """设置当前用户（从身份证读卡器调用）"""
        self.current_user_id = user_id
        self.current_user_name = user_name
        self.current_id_photo = id_photo  # 保存身份证照片到内存
        self.current_collection_id = collection_id  # 保存采集任务ID
        
        # 重置相似度信息
        self.last_similarity = None
        self.last_similarity_frame = None
        self.is_calculating_similarity = False
        
        self.user_id_label.setText(str(user_id))
        self.user_name_label.setText(user_name)
        self.user_id_label.setStyleSheet("font-weight: bold; color: green; font-size: 12px;")
        self.user_name_label.setStyleSheet("font-weight: bold; color: green; font-size: 12px;")
        print(f"[INFO] 设置当前用户: ID={user_id}, 名称={user_name}, 有照片={id_photo is not None}, 采集任务ID={collection_id}")

    def clear_current_user(self):
        """清空当前用户选择（从身份证读卡器调用）"""
        self.current_user_id = None
        self.current_user_name = None
        self.current_id_photo = None
        self.current_collection_id = None
        
        # 重置相似度信息
        self.last_similarity = None
        self.last_similarity_frame = None
        self.is_calculating_similarity = False
        
        self.user_id_label.setText("未选择")
        self.user_name_label.setText("未选择")
        self.user_id_label.setStyleSheet("font-weight: normal; color: gray; font-size: 12px;")
        self.user_name_label.setStyleSheet("font-weight: normal; color: gray; font-size: 12px;")
        print("[INFO] 已清空用户选择")

    def manual_select_user(self):
        """手动选择用户"""
        from PyQt5.QtWidgets import QInputDialog
        
        user_id, ok = QInputDialog.getInt(
            self, "手动选择用户", "请输入用户ID:",
            value=1, min=1, max=999999
        )
        
        if ok:
            try:
                db = DatabaseHelper()
                user = db.get_user_by_id(user_id)
                db.close()
                
                if user:
                    self.set_current_user(user.id, user.name)
                    QMessageBox.information(self, "成功", f"已选择用户: {user.name}")
                else:
                    QMessageBox.warning(self, "警告", f"用户ID {user_id} 不存在")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"查询失败: {e}")

    def verify_identity(self):
        """身份核验 - 比对采集照片和身份证照片"""
        if self.current_frame is None:
            QMessageBox.warning(self, "警告", "没有可用的帧")
            return

        if self.current_user_id is None:
            QMessageBox.warning(self, "警告", "请先选择用户或读取身份证")
            return
        
        if self.current_id_photo is None:
            QMessageBox.warning(self, "警告", "该用户没有身份证照片，无法进行身份核验")
            return

        try:
            # 从内存获取身份证照片
            id_card_photo = self.current_id_photo
            
            # 如果是二进制数据，转换为图像
            if isinstance(id_card_photo, bytes):
                nparr = np.frombuffer(id_card_photo, np.uint8)
                id_card_photo = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if id_card_photo is None:
                QMessageBox.warning(self, "警告", "身份证照片解析失败")
                return
            
            # 转换为 RGB
            id_card_photo = cv2.cvtColor(id_card_photo, cv2.COLOR_BGR2RGB)
            
            # 进行身份核验
            print("[INFO] 开始身份核验...")
            verify_result = self.identity_verifier.verify_identity(
                id_card_photo,
                self.current_frame,
                self.current_user_id
            )
            
            # 显示核验结果
            if verify_result['verified']:
                # 核验通过
                message = (
                    f"✓ 身份核验通过！\n\n"
                    f"用户: {self.current_user_name}\n"
                    f"相似度: {verify_result['similarity']:.2%}\n\n"
                    f"该用户的采集照片与身份证照片匹配"
                )
                QMessageBox.information(self, "核验通过", message)
            else:
                # 核验失败 - 提供更清晰的失败原因
                similarity = verify_result['similarity']
                threshold = 0.6  # 60%
                message = (
                    f"✗ 身份核验失败\n\n"
                    f"用户: {self.current_user_name}\n"
                    f"相似度: {similarity:.2%}\n"
                    f"所需阈值: {threshold:.0%}\n\n"
                    f"原因: 采集照片与身份证照片相似度不足\n"
                    f"请确保光线充足、面部清晰、表情自然"
                )
                QMessageBox.warning(self, "核验失败", message)
            
            print(f"[INFO] 身份核验完成: {verify_result['message']}")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"身份核验失败: {e}")
            import traceback
            traceback.print_exc()
