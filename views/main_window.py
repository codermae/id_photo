"""
主窗口
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QStatusBar, QTabWidget)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from views.id_card_view import IDCardView
from views.camera_view import CameraView
from views.process_view import ProcessView
from views.data_view import DataView
from views.report_view import ReportView
from views.import_view import ImportView

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("证件照采集及处理系统 v1.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # 初始化采集任务系统
        self.init_collections()
        
        # 初始化UI
        self.init_ui()
        
        # 设置样式
        self.setStyleSheet(self.get_stylesheet())
    
    def init_collections(self):
        """初始化采集任务系统"""
        try:
            from utils.database_helper import DatabaseHelper
            db = DatabaseHelper()
            
            # 检查是否有采集任务
            collections = db.get_active_collections()
            if not collections:
                print("[INFO] 没有采集任务，创建默认采集任务...")
                default_collection = db.create_collection(
                    name="默认采集任务",
                    organization="默认机构",
                    description="系统默认采集任务"
                )
                print(f"[OK] 默认采集任务创建成功 (ID: {default_collection.id})")
            
            db.close()
        except Exception as e:
            print(f"[WARNING] 初始化采集任务失败: {e}")

    def init_ui(self):
        """初始化界面"""
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建顶部容器 - 包含Tab和按钮
        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ddd; }
            QTabBar::tab { 
                background-color: #f0f0f0; 
                padding: 8px 20px;
                border: 1px solid #ddd;
                margin-right: 2px;
            }
            QTabBar::tab:selected { 
                background-color: white;
                border-bottom: 2px solid #0078d4;
            }
        """)
        
        # 添加各个标签页
        self.id_card_view = IDCardView()
        self.camera_view = CameraView()
        self.process_view = ProcessView()
        self.import_view = ImportView()
        self.data_view = DataView()
        self.report_view = ReportView()
        
        # 连接身份证读取和拍照采集的信号
        self.id_card_view.user_selected.connect(self.camera_view.set_current_user)
        self.id_card_view.user_cleared.connect(self.camera_view.clear_current_user)
        
        # 连接数据导入的采集任务更新信号到其他页面
        self.import_view.collection_changed.connect(self.id_card_view.load_collections)
        self.import_view.collection_changed.connect(self.process_view.load_collections)
        
        # 连接标签页切换信号，实现自动刷新
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        self.tab_widget.addTab(self.id_card_view, "身份证读取")
        self.tab_widget.addTab(self.import_view, "数据导入")
        self.tab_widget.addTab(self.camera_view, "拍照采集")
        self.tab_widget.addTab(self.process_view, "图像处理")
        self.tab_widget.addTab(self.data_view, "数据管理")
        self.tab_widget.addTab(self.report_view, "统计报表")
        
        # 创建按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 0, 10, 0)  #容器内边距
        button_layout.setSpacing(8) #按钮间距
        
        # 备份恢复按钮
        backup_btn = QPushButton("备份恢复")
        backup_btn.clicked.connect(self.open_backup_dialog)
        button_layout.addWidget(backup_btn)
        
        # 帮助按钮
        help_btn = QPushButton("帮助")
        help_btn.clicked.connect(self.show_help_dialog)
        button_layout.addWidget(help_btn)
        
        # 关于按钮
        about_btn = QPushButton("关于")
        about_btn.clicked.connect(self.show_about)
        button_layout.addWidget(about_btn)
        
        # 将按钮容器添加到 Tab 栏右上角
        self.tab_widget.setCornerWidget(button_container, Qt.TopRightCorner)
        
        # 添加Tab栏到顶部布局
        top_layout.addWidget(self.tab_widget)
        
        main_layout.addWidget(top_container)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status()


    def update_status(self):
        """更新状态栏 - 与统计报表页面保持一致"""
        from utils.database_helper import DatabaseHelper
        
        try:
            db = DatabaseHelper()
            
            # 获取用户和照片总数
            users = db.get_all_users()
            total_users = len(users)
            total_photos = sum(len(db.get_photos_by_user(u.id)) for u in users)
            
            # 获取统计数据
            stats = db.get_collection_stats()
            
            # 计算无记录用户数
            no_record_count = 0
            for user in users:
                records = db.get_records_by_user(user.id)
                if not records:
                    no_record_count += 1
            
            db.close()
            
            # 状态栏显示（与统计报表页面一致，不加颜色）
            status_text = (f"用户总数: {total_users} | 照片总数: {total_photos} | "
                          f"已完成: {stats['completed']} | 待处理: {stats['processing']} | "
                          f"待采集: {stats['pending']} | 无记录: {no_record_count} | "
                          f"完成率: {stats['completion_rate']:.1f}%")
            self.status_bar.showMessage(status_text)
        except Exception as e:
            self.status_bar.showMessage(f"状态更新失败: {e}")
    
    def update_status_bar(self):
        """更新状态栏 - 别名方法，供其他视图调用"""
        self.update_status()
    
    def on_tab_changed(self, index):
        """标签页切换时的处理 - 自动刷新数据"""
        try:
            # 获取当前标签页的标题
            tab_title = self.tab_widget.tabText(index)
            
            # 数据管理标签页 - 自动刷新用户列表
            if tab_title == "数据管理":
                print("[INFO] 切换到数据管理，自动刷新用户列表")
                self.data_view.load_users()
            
            # 统计报表标签页 - 自动刷新统计数据
            elif tab_title == "统计报表":
                print("[INFO] 切换到统计报表，自动刷新统计数据")
                self.report_view.refresh_stats()
            
            # 任何标签页切换都更新状态栏（检查状态栏是否存在）
            if hasattr(self, 'status_bar'):
                self.update_status()
            
        except Exception as e:
            print(f"[WARNING] 标签页切换处理失败: {e}")

    def open_batch_processing(self):
        """打开批量处理窗口"""
        from views.batch_processing_dialog import BatchProcessingDialog
        
        dialog = BatchProcessingDialog(self)
        dialog.exec_()
    
    def open_backup_dialog(self):
        """打开备份恢复对话框"""
        from views.backup_dialog import BackupDialog
        
        dialog = BackupDialog(parent=self)
        dialog.exec_()
    
    def show_help_dialog(self):
        """显示帮助对话框"""
        from views.help_dialog import HelpDialog
        
        dialog = HelpDialog(parent=self)
        dialog.exec_()

    def show_help(self):
        """显示帮助"""
        from PyQt5.QtWidgets import QMessageBox
        
        help_text = """
        证件照采集及处理系统 - 使用指南

        1. 身份证读取
           - 连接身份证读卡器
           - 点击"开始读取"按钮
           - 将身份证放在读卡器上

        2. 拍照采集
           - 选择摄像头
           - 调整摄像头位置
           - 点击"拍照"按钮

        3. 图像处理
           - 选择要处理的照片
           - 调整裁切、背景、美颜等参数
           - 保存处理后的照片

        4. 数据管理
           - 查看所有用户信息
           - 搜索和编辑用户数据
           - 导出用户列表

        5. 统计报表
           - 查看采集统计
           - 生成各类报表
           - 导出Excel文件
        """
        
        QMessageBox.information(self, "帮助", help_text)

    def show_about(self):
        """显示关于"""
        from PyQt5.QtWidgets import QMessageBox
        
        about_text = """
        证件照采集及处理系统
        版本: v1.0
        
        一个完整的证件照采集、处理和管理系统
        支持身份证读取、摄像头拍照、AI图像处理等功能
        
        技术栈:
        - Python 3.8+
        - PyQt5
        - OpenCV
        - MediaPipe
        - SQLAlchemy
        
        开发者: 毕业设计项目
        """
        
        QMessageBox.information(self, "关于", about_text)

    def closeEvent(self, event):
        """关闭事件"""
        # 清理资源
        if hasattr(self, 'camera_view'):
            self.camera_view.cleanup()
        
        event.accept()

    def get_stylesheet(self):
        """获取样式表"""
        return """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QLabel {
            color: #333;
        }
        
        QLineEdit, QTextEdit, QComboBox {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 6px;
            background-color: white;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border: 2px solid #0078d4;
        }
        
        QTableWidget {
            border: 1px solid #ddd;
            gridline-color: #ddd;
        }
        
        QHeaderView::section {
            background-color: #f0f0f0;
            padding: 5px;
            border: 1px solid #ddd;
        }
        """
