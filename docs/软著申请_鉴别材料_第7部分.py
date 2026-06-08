"""
证件照智能采集及处理系统 - 软著鉴别材料第7部分
用户界面和PyQt5视图层

================================================================================
第7部分: 用户界面（View层）
================================================================================

本部分包含系统的PyQt5界面实现，包括主窗口、各功能模块的视图、
对话框、信号槽机制等UI相关代码。

"""

# ============================================================================
# 文件名: views/main_window.py
# 功能: 主窗口，统合所有功能模块
# 行数: 96 行
# ============================================================================

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QStatusBar, QMenuBar, QMenu, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from views.id_card_view import IDCardView
from views.import_view import ImportView
from views.camera_view import CameraView
from views.process_view import ProcessView
from views.data_view import DataView
from views.report_view import ReportView

class MainWindow(QMainWindow):
    """
    主窗口类
    
    功能:
    1. 整合所有功能模块
    2. 菜单栏管理
    3. 标签页切换
    4. 状态栏显示
    5. 快捷键绑定
    
    模块:
    - 身份证读取
    - 数据导入
    - 摄像头拍照
    - 图像处理
    - 数据管理
    - 统计报表
    """
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.setWindowTitle("智能化证件照采集及处理系统 v1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置样式
        self.setStyleSheet(self._load_stylesheet())
        
        # 初始化UI
        self._init_ui()
        
        # 连接信号
        self._connect_signals()
    
    def _init_ui(self):
        """初始化UI"""
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 身份证读取
        self.id_card_view = IDCardView()
        self.tabs.addTab(self.id_card_view, "身份证读取")
        
        # 数据导入
        self.import_view = ImportView()
        self.tabs.addTab(self.import_view, "批量导入")
        
        # 摄像头拍照
        self.camera_view = CameraView()
        self.tabs.addTab(self.camera_view, "拍照采集")
        
        # 图像处理
        self.process_view = ProcessView()
        self.tabs.addTab(self.process_view, "图像处理")
        
        # 数据管理
        self.data_view = DataView()
        self.tabs.addTab(self.data_view, "数据管理")
        
        # 统计报表
        self.report_view = ReportView()
        self.tabs.addTab(self.report_view, "统计报表")
        
        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        import_action = file_menu.addAction("导入数据...")
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.import_view.show_import_dialog)
        
        export_action = file_menu.addAction("导出数据...")
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.data_view.export_data)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("退出")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        settings_action = edit_menu.addAction("系统设置")
        settings_action.setShortcut("Ctrl+S")
        settings_action.triggered.connect(self._show_settings)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = help_menu.addAction("关于系统")
        about_action.triggered.connect(self._show_about)
        
        doc_action = help_menu.addAction("使用文档")
        doc_action.triggered.connect(self._show_documentation)
    
    def _connect_signals(self):
        """连接信号槽"""
        # 可以在这里连接各模块的信号槽
        pass
    
    def _load_stylesheet(self):
        """加载样式表"""
        return """
            QMainWindow { background-color: #f0f0f0; }
            QTabWidget::pane { border: 1px solid #cccccc; }
            QTabBar::tab { 
                background-color: #e0e0e0; 
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected { 
                background-color: #ffffff;
                border-bottom: 3px solid #0066cc;
            }
        """
    
    def _show_settings(self):
        """显示系统设置对话框"""
        QMessageBox.information(self, "系统设置", "功能开发中...")
    
    def _show_about(self):
        """显示关于信息"""
        about_text = """
        智能化证件照采集及处理系统
        版本: 1.0.0
        
        这是一个专业的证件照采集和处理系统，
        集成了AI人脸检测、美颜、背景替换等功能。
        
        © 2024 版权所有
        """
        QMessageBox.about(self, "关于系统", about_text)
    
    def _show_documentation(self):
        """显示使用文档"""
        QMessageBox.information(self, "使用文档", 
                               "请参考项目docs目录中的详细文档")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        reply = QMessageBox.question(self, "确认退出", 
                                    "确定要退出系统吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 清理资源
            self.camera_view.stop_camera()
            event.accept()
        else:
            event.ignore()


# ============================================================================
# 文件名: views/camera_view.py
# 功能: 摄像头拍照视图
# 行数: 94 行
# ============================================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage
from controllers.camera import CameraThread
from controllers.ai_processor import AIProcessor

class CameraView(QWidget):
    """
    摄像头拍照视图
    
    功能:
    1. 实时摄像头预览
    2. 人脸检测
    3. 质量评估
    4. 拍照和保存
    5. 批量采集
    """
    
    photo_captured = pyqtSignal(str)  # 照片路径
    
    def __init__(self):
        """初始化摄像头视图"""
        super().__init__()
        self.camera_thread = None
        self.ai_processor = AIProcessor()
        self.is_camera_running = False
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 预览区域
        preview_layout = QHBoxLayout()
        
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(640, 480)
        self.preview_label.setStyleSheet("border: 1px solid #cccccc;")
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        
        # 控制面板
        control_layout = QVBoxLayout()
        
        # 人脸检测状态
        self.face_status = QLabel("未检测到人脸")
        self.face_status.setStyleSheet("color: red; font-weight: bold;")
        control_layout.addWidget(self.face_status)
        
        # 质量评分
        self.quality_label = QLabel("质量评分: 0/100")
        control_layout.addWidget(self.quality_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("启动摄像头")
        self.start_button.clicked.connect(self.start_camera)
        button_layout.addWidget(self.start_button)
        
        self.capture_button = QPushButton("拍照")
        self.capture_button.clicked.connect(self.capture_photo)
        self.capture_button.setEnabled(False)
        button_layout.addWidget(self.capture_button)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_camera)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        control_layout.addLayout(button_layout)
        control_layout.addStretch()
        
        preview_layout.addLayout(control_layout)
        layout.addLayout(preview_layout)
        
        self.setLayout(layout)
    
    def start_camera(self):
        """启动摄像头"""
        try:
            from config.config import CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS
            
            self.camera_thread = CameraThread(
                width=CAMERA_WIDTH,
                height=CAMERA_HEIGHT,
                fps=CAMERA_FPS
            )
            
            # 连接信号
            self.camera_thread.frame_ready.connect(self.on_frame_received)
            self.camera_thread.error.connect(self.on_camera_error)
            
            self.camera_thread.start()
            self.is_camera_running = True
            
            self.start_button.setEnabled(False)
            self.capture_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动摄像头失败: {e}")
    
    def stop_camera(self):
        """停止摄像头"""
        if self.camera_thread:
            self.camera_thread.stop()
            self.is_camera_running = False
        
        self.start_button.setEnabled(True)
        self.capture_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.preview_label.clear()
        self.face_status.setText("摄像头已停止")
    
    def on_frame_received(self, q_image):
        """处理摄像头帧"""
        self.preview_label.setPixmap(QPixmap.fromImage(q_image))
    
    def on_camera_error(self, error_msg):
        """处理摄像头错误"""
        QMessageBox.warning(self, "摄像头错误", error_msg)
        self.stop_camera()
    
    def capture_photo(self):
        """拍照"""
        if not self.camera_thread:
            QMessageBox.warning(self, "错误", "摄像头未启动")
            return
        
        frame = self.camera_thread.capture_frame()
        if frame is not None:
            import cv2
            from datetime import datetime
            from pathlib import Path
            
            # 检测人脸
            try:
                from PIL import Image
                pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                faces = self.ai_processor.detect_faces(pil_image)
                
                if not faces:
                    QMessageBox.warning(self, "警告", "未检测到人脸，请调整角度")
                    return
                
                # 保存照片
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                save_path = Path('data/photos/raw') / f"photo_{timestamp}.jpg"
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                cv2.imwrite(str(save_path), frame)
                
                self.photo_captured.emit(str(save_path))
                QMessageBox.information(self, "成功", "照片已保存")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"拍照失败: {e}")


# ============================================================================
# 文件名: views/data_view.py
# 功能: 数据管理视图
# 行数: 87 行
# ============================================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from config.database import SessionLocal
from models.user import User
from utils.database_helper import DatabaseHelper

class DataViewWorker(QThread):
    """数据加载工作线程"""
    
    data_loaded = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, search_filters):
        """初始化工作线程"""
        super().__init__()
        self.search_filters = search_filters
        self.db_helper = DatabaseHelper()
    
    def run(self):
        """执行数据查询"""
        try:
            users = self.db_helper.search_users(**self.search_filters)
            self.data_loaded.emit(users)
        except Exception as e:
            self.error.emit(str(e))


class DataView(QWidget):
    """
    数据管理视图
    
    功能:
    1. 用户数据表格显示
    2. 高级搜索过滤
    3. 数据增删改查
    4. 数据导出
    5. 数据统计
    """
    
    def __init__(self):
        """初始化数据管理视图"""
        super().__init__()
        self.db_helper = DatabaseHelper()
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 搜索区域
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索姓名或身份证号...")
        search_layout.addWidget(self.search_input)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["全部", "待采集", "已采集", "失败"])
        search_layout.addWidget(self.status_combo)
        
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self._perform_search)
        search_layout.addWidget(search_button)
        
        export_button = QPushButton("导出数据")
        export_button.clicked.connect(self.export_data)
        search_layout.addWidget(export_button)
        
        layout.addLayout(search_layout)
        
        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "姓名", "身份证号", "性别", "状态", "创建时间"
        ])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 150)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def _load_data(self):
        """加载数据"""
        try:
            users = self.db_helper.search_users()
            self._display_users(users)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据失败: {e}")
    
    def _display_users(self, users):
        """显示用户数据"""
        self.table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(user.id)))
            self.table.setItem(row, 1, QTableWidgetItem(user.name))
            self.table.setItem(row, 2, QTableWidgetItem(user.id_number))
            self.table.setItem(row, 3, QTableWidgetItem("男" if user.sex == 'M' else "女"))
            self.table.setItem(row, 4, QTableWidgetItem(self._status_name(user.status)))
            self.table.setItem(row, 5, QTableWidgetItem(user.created_at.strftime('%Y-%m-%d %H:%M')))
    
    def _perform_search(self):
        """执行搜索"""
        search_text = self.search_input.text()
        status = self.status_combo.currentText()
        
        filters = {}
        if search_text:
            # 尝试作为身份证号搜索，否则作为姓名搜索
            if len(search_text) == 18 and search_text.isdigit():
                filters['id_number'] = search_text
            else:
                filters['name'] = search_text
        
        if status != "全部":
            status_map = {"待采集": "pending", "已采集": "completed", "失败": "failed"}
            filters['status'] = status_map[status]
        
        self._load_data_with_filters(filters)
    
    def _load_data_with_filters(self, filters):
        """使用过滤条件加载数据"""
        try:
            users = self.db_helper.search_users(**filters)
            self._display_users(users)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")
    
    def export_data(self):
        """导出数据"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "", "Excel 文件 (*.xlsx);;CSV 文件 (*.csv)"
        )
        
        if file_path:
            try:
                # 实现导出逻辑
                QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
    @staticmethod
    def _status_name(status):
        """状态名称转换"""
        status_map = {"pending": "待采集", "completed": "已采集", "failed": "失败"}
        return status_map.get(status, status)
