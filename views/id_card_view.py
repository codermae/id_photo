"""
身份证读取视图
"""
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QGroupBox, QMessageBox, 
                             QComboBox, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from controllers.id_card_reader import IDCardReader
from utils.database_helper import DatabaseHelper
from utils.file_helper import FileHelper
from utils.id_card_validator import IDCardValidator
import cv2
import numpy as np

class IDCardReaderThread(QThread):
    """身份证读取线程"""
    card_read = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, reader):
        super().__init__()
        self.reader = reader

    def run(self):
        """运行"""
        try:
            self.reader.start_reading(self.on_card_read)
        except Exception as e:
            self.error.emit(str(e))

    def on_card_read(self, card_data):
        """卡片读取回调"""
        self.card_read.emit(card_data)

class IDCardView(QWidget):
    """身份证读取视图"""
    
    # 定义信号：当成功读取身份证并保存用户后发出
    user_selected = pyqtSignal(int, str, object, int)  # user_id, user_name, id_photo, collection_id
    # 定义信号：当拿走身份证时发出，通知清空用户选择
    user_cleared = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.reader = IDCardReader(test_mode=True)  # 启用测试模式
        self.reader_thread = None
        self.current_card_data = None
        self.test_card_index = 0  # 测试卡片索引
        self.current_collection_id = None
        self.current_id_photo = None  # 当前身份证照片（内存中）
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        main_layout = QHBoxLayout(self)
        
        # 左侧：读卡器控制
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
        
        # 自动添加选项
        auto_group = QGroupBox("自动添加选项")
        auto_layout = QVBoxLayout()
        
        self.auto_add_checkbox = QCheckBox("检测到新用户时自动添加到采集任务")
        self.auto_add_checkbox.setChecked(False)
        auto_layout.addWidget(self.auto_add_checkbox)
        
        auto_group.setLayout(auto_layout)
        left_layout.addWidget(auto_group)
        
        # 读卡器状态
        status_group = QGroupBox("读卡器状态")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        left_layout.addWidget(status_group)
        
        # 控制按钮
        button_group = QGroupBox("控制")
        button_layout = QVBoxLayout()
        
        self.connect_btn = QPushButton("连接读卡器")
        self.connect_btn.clicked.connect(self.connect_reader)
        button_layout.addWidget(self.connect_btn)
        
        self.start_btn = QPushButton("开始读取")
        self.start_btn.clicked.connect(self.start_reading)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止读取")
        self.stop_btn.clicked.connect(self.stop_reading)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        self.disconnect_btn = QPushButton("断开连接")
        self.disconnect_btn.clicked.connect(self.disconnect_reader)
        self.disconnect_btn.setEnabled(False)
        button_layout.addWidget(self.disconnect_btn)
        
        button_group.setLayout(button_layout)
        left_layout.addWidget(button_group)
        
        # 测试模拟按钮
        test_group = QGroupBox("测试模拟 (无需硬件)")
        test_layout = QVBoxLayout()
        
        self.insert_card_btn = QPushButton("放身份证")
        self.insert_card_btn.clicked.connect(self.insert_test_card)
        self.insert_card_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 10px;")
        test_layout.addWidget(self.insert_card_btn)
        
        self.remove_card_btn = QPushButton("拿走身份证")
        self.remove_card_btn.clicked.connect(self.remove_test_card)
        self.remove_card_btn.setStyleSheet("background-color: #f44336; color: white; font-size: 14px; padding: 10px;")
        test_layout.addWidget(self.remove_card_btn)
        
        test_group.setLayout(test_layout)
        left_layout.addWidget(test_group)
        
        left_layout.addStretch()
        
        # 右侧：信息显示
        right_layout = QVBoxLayout()
        
        # 身份证照片
        photo_group = QGroupBox("身份证照片")
        photo_layout = QVBoxLayout()
        
        self.photo_label = QLabel()
        self.photo_label.setMinimumSize(200, 280)
        self.photo_label.setStyleSheet("border: 1px solid #ddd; background-color: #f0f0f0;")
        self.photo_label.setAlignment(Qt.AlignCenter)
        photo_layout.addWidget(self.photo_label)
        
        photo_group.setLayout(photo_layout)
        right_layout.addWidget(photo_group)
        
        # 身份信息
        info_group = QGroupBox("身份信息")
        info_layout = QVBoxLayout()
        
        # 姓名
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("姓名:"))
        self.name_input = QLineEdit()
        self.name_input.setReadOnly(True)
        name_layout.addWidget(self.name_input)
        info_layout.addLayout(name_layout)
        
        # 身份证号
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("身份证号:"))
        self.id_input = QLineEdit()
        self.id_input.setReadOnly(True)
        id_layout.addWidget(self.id_input)
        info_layout.addLayout(id_layout)
        
        # 性别
        gender_layout = QHBoxLayout()
        gender_layout.addWidget(QLabel("性别:"))
        self.gender_input = QLineEdit()
        self.gender_input.setReadOnly(True)
        gender_layout.addWidget(self.gender_input)
        info_layout.addLayout(gender_layout)
        
        # 民族
        nation_layout = QHBoxLayout()
        nation_layout.addWidget(QLabel("民族:"))
        self.nation_input = QLineEdit()
        self.nation_input.setReadOnly(True)
        nation_layout.addWidget(self.nation_input)
        info_layout.addLayout(nation_layout)
        
        # 出生日期
        birthday_layout = QHBoxLayout()
        birthday_layout.addWidget(QLabel("出生日期:"))
        self.birthday_input = QLineEdit()
        self.birthday_input.setReadOnly(True)
        birthday_layout.addWidget(self.birthday_input)
        info_layout.addLayout(birthday_layout)
        
        # 地址
        address_layout = QHBoxLayout()
        address_layout.addWidget(QLabel("地址:"))
        self.address_input = QLineEdit()
        self.address_input.setReadOnly(True)
        address_layout.addWidget(self.address_input)
        info_layout.addLayout(address_layout)
        
        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存到数据库")
        self.save_btn.clicked.connect(self.save_to_database)
        self.save_btn.setEnabled(False)
        action_layout.addWidget(self.save_btn)
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_info)
        action_layout.addWidget(self.clear_btn)
        
        right_layout.addLayout(action_layout)
        
        # 添加到主布局
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)
        
        # 加载采集任务
        self.load_collections()

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

    def connect_reader(self):
        """连接读卡器"""
        if self.reader.connect():
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setEnabled(False)
            self.start_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(True)
        else:
            QMessageBox.warning(self, "错误", "连接读卡器失败")

    def disconnect_reader(self):
        """断开连接"""
        self.stop_reading()
        self.reader.disconnect()
        self.status_label.setText("未连接")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.connect_btn.setEnabled(True)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(False)

    def start_reading(self):
        """开始读取"""
        self.reader_thread = IDCardReaderThread(self.reader)
        self.reader_thread.card_read.connect(self.on_card_read)
        self.reader_thread.error.connect(self.on_error)
        self.reader_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_reading(self):
        """停止读取"""
        self.reader.stop_reading()
        if self.reader_thread:
            self.reader_thread.quit()
            self.reader_thread.wait()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def on_card_read(self, card_data):
        """卡片读取回调"""
        if not self.current_collection_id:
            QMessageBox.warning(self, "警告", "请先选择采集任务")
            return
        
        self.current_card_data = card_data
        
        # 保存身份证照片到内存
        self.current_id_photo = card_data.get('id_photo')
        
        # 显示信息
        self.name_input.setText(card_data.get('name', ''))
        self.id_input.setText(card_data.get('id_number', ''))
        self.gender_input.setText(card_data.get('gender', ''))
        self.nation_input.setText(card_data.get('nation', ''))
        self.birthday_input.setText(card_data.get('birthday', ''))
        self.address_input.setText(card_data.get('address', ''))
        
        # 显示照片
        id_photo = card_data.get('id_photo')
        if id_photo is not None:
            self.display_photo(id_photo)
        
        self.save_btn.setEnabled(True)
        
        # 检查用户是否已在采集任务中
        self.check_and_handle_user()

    def check_and_handle_user(self):
        """检查用户是否已在采集任务中，并处理"""
        if not self.current_card_data or not self.current_collection_id:
            return
        
        try:
            db = DatabaseHelper()
            id_number = self.current_card_data['id_number']
            
            # 检查用户是否在当前采集任务中
            user = db.get_user_by_id_number(id_number, self.current_collection_id)
            
            if user:
                # 用户已在采集任务中
                QMessageBox.information(self, "提示", f"用户 {user.name} 已在采集列表中")
                # 发送当前读取的身份证照片，而不是数据库中的
                print(f"[DEBUG] 用户已存在，发送信号: user_id={user.id}, user_name={user.name}, 有照片={self.current_id_photo is not None}")
                self.user_selected.emit(user.id, user.name, self.current_id_photo, self.current_collection_id)
                db.close()
                return
            
            # 用户不在采集任务中
            # 检查是否启用了自动添加
            if self.auto_add_checkbox.isChecked():
                # 自动添加
                self.add_user_to_collection()
            else:
                # 弹窗询问
                reply = QMessageBox.question(
                    self, "确认",
                    f"用户 {self.current_card_data['name']} 不在采集列表中，是否添加到当前采集任务？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.add_user_to_collection()
            
            db.close()
        except Exception as e:
            print(f"[ERROR] 检查用户失败: {e}")

    def add_user_to_collection(self):
        """将用户添加到采集任务"""
        if not self.current_card_data or not self.current_collection_id:
            return
        
        try:
            from datetime import datetime
            
            # 验证身份证号
            validation_result = IDCardValidator.validate(self.current_card_data['id_number'])
            if not validation_result['valid']:
                QMessageBox.warning(self, "警告", f"身份证号验证失败: {validation_result['message']}")
                # 重新启用保存按钮
                self.save_btn.setEnabled(True)
                self.save_btn.setText("保存到数据库")
                return
            
            db = DatabaseHelper()
            
            # 保存身份证照片到内存（不保存到数据库）
            self.current_id_photo = self.current_card_data.get('id_photo')

            # 转换生日为date对象
            birthday = None
            if self.current_card_data.get('birthday'):
                try:
                    birthday_str = self.current_card_data.get('birthday')
                    if isinstance(birthday_str, str):
                        birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
                    else:
                        birthday = birthday_str
                except:
                    birthday = None

            # 添加用户到采集任务（不保存照片）
            user = db.add_user(
                name=self.current_card_data['name'],
                id_number=self.current_card_data['id_number'],
                gender=self.current_card_data.get('gender'),
                nation=self.current_card_data.get('nation'),
                birthday=birthday,
                address=self.current_card_data.get('address'),
                collection_id=self.current_collection_id
            )
            
            # 保存用户ID和名称（在关闭数据库前）
            user_id = user.id
            user_name = user.name
            
            # 创建待采集记录
            import getpass
            operator = getpass.getuser()
            record = db.add_record(
                user_id=user_id,
                operator=operator,
                status='pending',
                notes='用户信息已录入，等待采集照片',
                collection_id=self.current_collection_id
            )
            print(f"[INFO] 创建待采集记录: user_id={user_id}, record_id={record.id}, status=pending")

            db.close()
            
            # 发出信号，通知拍照采集界面更新用户信息
            print(f"[DEBUG] 发送信号: user_id={user_id}, user_name={user_name}, 有照片={self.current_id_photo is not None}")
            self.user_selected.emit(user_id, user_name, self.current_id_photo, self.current_collection_id)
            
            # 通知主窗口更新统计
            self.notify_data_changed()
            
            QMessageBox.information(self, "成功", f"用户 {user_name} 已添加到采集任务")
            self.clear_info()
        except Exception as e:
            # 重新启用保存按钮
            self.save_btn.setEnabled(True)
            self.save_btn.setText("保存到数据库")
            QMessageBox.critical(self, "错误", f"添加失败: {e}")
            import traceback
            traceback.print_exc()

    def on_error(self, error_msg):
        """错误回调"""
        QMessageBox.critical(self, "错误", f"读卡失败: {error_msg}")

    def display_photo(self, photo_data):
        """显示照片"""
        try:
            # 如果是 bytes 类型
            if isinstance(photo_data, bytes):
                from io import BytesIO
                pixmap = QPixmap()
                pixmap.loadFromData(photo_data)
            # 如果是 numpy 数组
            elif isinstance(photo_data, np.ndarray):
                rgb_image = cv2.cvtColor(photo_data, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = 3 * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
            else:
                # 如果是文件路径
                pixmap = QPixmap(photo_data)
            
            # 缩放到标签大小
            scaled_pixmap = pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            self.photo_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"显示照片失败: {e}")

    def save_to_database(self):
        """保存到数据库"""
        if not self.current_card_data:
            QMessageBox.warning(self, "警告", "没有读取到身份证信息")
            return
        
        if not self.current_collection_id:
            QMessageBox.warning(self, "警告", "请先选择采集任务")
            return

        # 先检查是否已存在相同身份证号
        try:
            db = DatabaseHelper()
            id_number = self.current_card_data['id_number']
            existing_user = db.get_user_by_id_number(id_number, self.current_collection_id)
            db.close()
            
            if existing_user:
                QMessageBox.warning(self, "警告", f"身份证号 {id_number} 已存在于当前采集任务中\n用户姓名: {existing_user.name}")
                return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"检查重复身份证号失败: {e}")
            return

        # 立即禁用按钮，防止重复点击
        self.save_btn.setEnabled(False)
        self.save_btn.setText("保存中...")
        
        try:
            self.add_user_to_collection()
        except Exception as e:
            # 如果出错，重新启用按钮
            self.save_btn.setEnabled(True)
            self.save_btn.setText("保存到数据库")
            raise e

    def clear_info(self):
        """清空信息"""
        self.name_input.clear()
        self.id_input.clear()
        self.gender_input.clear()
        self.nation_input.clear()
        self.birthday_input.clear()
        self.address_input.clear()
        self.photo_label.clear()
        self.current_card_data = None
        self.save_btn.setEnabled(False)
        self.save_btn.setText("保存到数据库")  # 重置按钮文本

    def get_test_cards(self):
        """获取测试卡片数据列表 - 包含照片"""
        photo_dir = "test_id_photos"
        
        # 读取照片文件
        photos = {}
        if os.path.exists(photo_dir):
            photo_files = sorted([f for f in os.listdir(photo_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
            for i, photo_file in enumerate(photo_files[:5]):  # 只取前 5 张
                photo_path = os.path.join(photo_dir, photo_file)
                try:
                    with open(photo_path, 'rb') as f:
                        photos[i] = f.read()
                except Exception as e:
                    print(f"[WARNING] 读取照片失败: {photo_file} - {e}")
        
        return [
            {
                'name': '张三',
                'id_number': '110101199001010015',
                'gender': '男',
                'nation': '汉',
                'birthday': '1990-01-01',
                'address': '北京市朝阳区',
                'id_photo_data': photos.get(0)
            },
            {
                'name': '李四',
                'id_number': '110101199001010023',
                'gender': '女',
                'nation': '汉',
                'birthday': '1990-01-01',
                'address': '北京市东城区',
                'id_photo_data': photos.get(1)
            },
            {
                'name': '王五',
                'id_number': '310101198503151232',
                'gender': '男',
                'nation': '汉',
                'birthday': '1985-03-15',
                'address': '上海市黄浦区',
                'id_photo_data': photos.get(2)
            },
            {
                'name': '赵六',
                'id_number': '440101199205204563',
                'gender': '女',
                'nation': '汉',
                'birthday': '1992-05-20',
                'address': '广州市越秀区',
                'id_photo_data': photos.get(3)
            },
            {
                'name': '孙七',
                'id_number': '500101198808087898',
                'gender': '男',
                'nation': '汉',
                'birthday': '1988-08-08',
                'address': '重庆市渝中区',
                'id_photo_data': photos.get(4)
            }
        ]
    
    def insert_test_card(self):
        """放置测试卡片 - 从 get_test_cards() 获取数据（包含照片）"""
        if not self.current_collection_id:
            QMessageBox.warning(self, "警告", "请先选择采集任务")
            return
        
        if not self.reader.test_mode:
            QMessageBox.warning(self, "警告", "测试模式未启用")
            return
        
        test_cards = self.get_test_cards()
        if self.test_card_index >= len(test_cards):
            self.test_card_index = 0
        
        card = test_cards[self.test_card_index]
        
        # 插入测试卡片，包含照片数据
        self.reader.insert_test_card(
            name=card['name'],
            id_number=card['id_number'],
            gender=card['gender'],
            nation=card['nation'],
            birthday=card['birthday'],
            address=card['address'],
            id_photo_data=card.get('id_photo_data')  # 传递照片数据
        )
        
        photo_info = ""
        if card.get('id_photo_data'):
            photo_info = f"\n照片: {len(card['id_photo_data'])} 字节"
        
        QMessageBox.information(
            self, "测试", 
            f"用户 {self.test_card_index + 1}/5\n"
            f"姓名: {card['name']}\n"
            f"ID: {card['id_number']}"
            f"{photo_info}"
        )
        
        self.test_card_index += 1
        if self.test_card_index >= len(test_cards):
            self.test_card_index = 0
    
    def remove_test_card(self):
        """拿走测试卡片"""
        if not self.reader.test_mode:
            QMessageBox.warning(self, "警告", "测试模式未启用")
            return
        
        self.reader.remove_test_card()
        self.clear_info()
        
        # 发出信号通知拍照采集界面清空用户选择
        self.user_cleared.emit()
        print("[INFO] 已拿走身份证，通知清空用户选择")
        
        QMessageBox.information(self, "测试", "已拿走身份证")
    
    def notify_data_changed(self):
        """通知主窗口数据已更改"""
        try:
            from PyQt5.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'update_status_bar'):
                    widget.update_status_bar()
                    print("[INFO] 已通知主窗口更新统计")
                    break
        except Exception as e:
            print(f"[WARNING] 通知主窗口失败: {e}")
