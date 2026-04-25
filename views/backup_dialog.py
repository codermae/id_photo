"""
数据备份和恢复对话框
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QMessageBox, QFileDialog, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QGroupBox, QCheckBox,
                             QSpinBox, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from utils.backup_manager import BackupManager
from datetime import datetime
import os

class BackupThread(QThread):
    """备份线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, backup_manager, backup_name=None, include_photos=True):
        super().__init__()
        self.backup_manager = backup_manager
        self.backup_name = backup_name
        self.include_photos = include_photos
    
    def run(self):
        try:
            self.progress.emit("正在创建备份...")
            backup_info = self.backup_manager.create_backup(
                self.backup_name, 
                self.include_photos
            )
            self.progress.emit(f"备份已创建: {backup_info['name']}")
            self.finished.emit(True, f"备份成功: {backup_info['name']}")
        except Exception as e:
            self.progress.emit(f"备份失败: {e}")
            self.finished.emit(False, f"备份失败: {e}")

class RestoreThread(QThread):
    """恢复线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, backup_manager, backup_name, restore_photos=True):
        super().__init__()
        self.backup_manager = backup_manager
        self.backup_name = backup_name
        self.restore_photos = restore_photos
    
    def run(self):
        try:
            self.progress.emit("正在恢复备份...")
            self.backup_manager.restore_backup(
                self.backup_name,
                self.restore_photos
            )
            self.progress.emit(f"备份已恢复: {self.backup_name}")
            self.finished.emit(True, f"恢复成功: {self.backup_name}")
        except Exception as e:
            self.progress.emit(f"恢复失败: {e}")
            self.finished.emit(False, f"恢复失败: {e}")

class BackupDialog(QDialog):
    """数据备份和恢复对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据备份和恢复")
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setGeometry(100, 100, 1200, 600)
        self.backup_manager = BackupManager()
        self.backup_thread = None
        self.restore_thread = None
        self.init_ui()
        self.refresh_backup_list()
        # 居中显示
        if parent:
            self.move(parent.frameGeometry().center() - self.rect().center())
    
    def init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        
        # 备份操作组
        backup_group = QGroupBox("创建备份")
        backup_layout = QVBoxLayout()
        
        # 备份选项
        options_layout = QHBoxLayout()
        
        options_layout.addWidget(QLabel("备份名称:"))
        self.backup_name_input = QComboBox()
        self.backup_name_input.setEditable(True)
        self.backup_name_input.setPlaceholderText("自动生成（留空）")
        options_layout.addWidget(self.backup_name_input)
        
        self.include_photos_checkbox = QCheckBox("包含照片文件")
        self.include_photos_checkbox.setChecked(True)
        options_layout.addWidget(self.include_photos_checkbox)
        
        backup_layout.addLayout(options_layout)
        
        # 备份按钮
        button_layout = QHBoxLayout()
        
        create_backup_btn = QPushButton("创建备份")
        create_backup_btn.clicked.connect(self.create_backup)
        button_layout.addWidget(create_backup_btn)
        
        button_layout.addStretch()
        
        backup_layout.addLayout(button_layout)
        
        backup_group.setLayout(backup_layout)
        main_layout.addWidget(backup_group)
        
        # 备份列表组
        list_group = QGroupBox("备份列表")
        list_layout = QVBoxLayout()
        
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(6)
        self.backup_table.setHorizontalHeaderLabels([
            "备份名称", "创建时间", "数据库大小", "照片大小", "状态", "操作"
        ])
        self.backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        list_layout.addWidget(self.backup_table)
        
        list_group.setLayout(list_layout)
        main_layout.addWidget(list_group)
        
        # 操作按钮组
        operation_group = QGroupBox("操作")
        operation_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_backup_list)
        operation_layout.addWidget(refresh_btn)
        
        verify_btn = QPushButton("验证备份")
        verify_btn.clicked.connect(self.verify_selected_backup)
        operation_layout.addWidget(verify_btn)
        
        export_btn = QPushButton("导出备份")
        export_btn.clicked.connect(self.export_backup)
        operation_layout.addWidget(export_btn)
        
        import_btn = QPushButton("导入备份")
        import_btn.clicked.connect(self.import_backup)
        operation_layout.addWidget(import_btn)
        
        operation_layout.addStretch()
        
        operation_group.setLayout(operation_layout)
        main_layout.addWidget(operation_group)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)
    
    def create_backup(self):
        """创建备份"""
        try:
            backup_name = self.backup_name_input.currentText().strip()
            if not backup_name:
                backup_name = None
            
            include_photos = self.include_photos_checkbox.isChecked()
            
            # 禁用按钮
            self.setEnabled(False)
            
            # 创建备份线程
            self.backup_thread = BackupThread(
                self.backup_manager,
                backup_name,
                include_photos
            )
            self.backup_thread.progress.connect(self.on_backup_progress)
            self.backup_thread.finished.connect(self.on_backup_finished)
            self.backup_thread.start()
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建备份失败: {e}")
            self.setEnabled(True)
    
    def on_backup_progress(self, message):
        """备份进度"""
        self.status_label.setText(message)
    
    def on_backup_finished(self, success, message):
        """备份完成"""
        self.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "成功", message)
            self.refresh_backup_list()
        else:
            QMessageBox.critical(self, "错误", message)
    
    def refresh_backup_list(self):
        """刷新备份列表"""
        try:
            self.backup_table.setRowCount(0)
            
            backups = self.backup_manager.list_backups()
            
            for row, backup in enumerate(backups):
                self.backup_table.insertRow(row)
                
                # 备份名称
                self.backup_table.setItem(row, 0, QTableWidgetItem(backup.get('name', '')))
                
                # 创建时间
                timestamp = backup.get('timestamp', '')
                if timestamp:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    time_str = '未知'
                self.backup_table.setItem(row, 1, QTableWidgetItem(time_str))
                
                # 数据库大小
                db_size = backup.get('db_size', 0)
                db_size_str = self._format_size(db_size)
                self.backup_table.setItem(row, 2, QTableWidgetItem(db_size_str))
                
                # 照片大小
                photos_size = backup.get('photos_size', 0)
                photos_size_str = self._format_size(photos_size)
                self.backup_table.setItem(row, 3, QTableWidgetItem(photos_size_str))
                
                # 状态
                status = backup.get('status', '未知')
                # 翻译状态
                status_map = {
                    'completed': '已完成',
                    'failed': '失败',
                    'pending': '进行中',
                    'unknown': '未知'
                }
                status_text = status_map.get(status, status)
                self.backup_table.setItem(row, 4, QTableWidgetItem(status_text))
                
                # 操作按钮
                button_widget = self._create_operation_buttons(backup.get('name', ''))
                self.backup_table.setCellWidget(row, 5, button_widget)
            
            self.status_label.setText(f"共有 {len(backups)} 个备份")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新备份列表失败: {e}")
    
    def _create_operation_buttons(self, backup_name):
        """创建操作按钮"""
        from PyQt5.QtWidgets import QWidget
        
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        restore_btn = QPushButton("恢复")
        restore_btn.setMaximumWidth(60)
        restore_btn.clicked.connect(lambda: self.restore_backup(backup_name))
        layout.addWidget(restore_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setMaximumWidth(60)
        delete_btn.clicked.connect(lambda: self.delete_backup(backup_name))
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def restore_backup(self, backup_name):
        """恢复备份"""
        try:
            reply = QMessageBox.question(
                self, "确认恢复",
                f"确定要恢复备份 '{backup_name}' 吗？\n\n"
                "这将覆盖当前的数据库和照片文件。",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 禁用界面
                self.setEnabled(False)
                
                # 创建恢复线程
                self.restore_thread = RestoreThread(
                    self.backup_manager,
                    backup_name,
                    True
                )
                self.restore_thread.progress.connect(self.on_restore_progress)
                self.restore_thread.finished.connect(self.on_restore_finished)
                self.restore_thread.start()
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"恢复备份失败: {e}")
    
    def on_restore_progress(self, message):
        """恢复进度"""
        self.status_label.setText(message)
    
    def on_restore_finished(self, success, message):
        """恢复完成"""
        self.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self, "成功", 
                f"{message}\n\n请重启应用以加载恢复的数据。"
            )
        else:
            QMessageBox.critical(self, "错误", message)
    
    def delete_backup(self, backup_name):
        """删除备份"""
        try:
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除备份 '{backup_name}' 吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.backup_manager.delete_backup(backup_name)
                QMessageBox.information(self, "成功", "备份已删除")
                self.refresh_backup_list()
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除备份失败: {e}")
    
    def verify_selected_backup(self):
        """验证选中的备份"""
        try:
            current_row = self.backup_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "提示", "请先选择一个备份")
                return
            
            backup_name = self.backup_table.item(current_row, 0).text()
            
            result = self.backup_manager.verify_backup(backup_name)
            
            if result['valid']:
                QMessageBox.information(self, "验证成功", result['message'])
            else:
                QMessageBox.warning(self, "验证失败", result['message'])
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"验证备份失败: {e}")
    
    def export_backup(self):
        """导出备份"""
        try:
            current_row = self.backup_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "提示", "请先选择一个备份")
                return
            
            backup_name = self.backup_table.item(current_row, 0).text()
            
            export_dir = QFileDialog.getExistingDirectory(
                self, "选择导出目录"
            )
            
            if export_dir:
                self.backup_manager.export_backup(backup_name, export_dir)
                QMessageBox.information(
                    self, "成功",
                    f"备份已导出到: {export_dir}"
                )
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出备份失败: {e}")
    
    def import_backup(self):
        """导入备份"""
        try:
            import_dir = QFileDialog.getExistingDirectory(
                self, "选择要导入的备份目录"
            )
            
            if import_dir:
                backup_info = self.backup_manager.import_backup(import_dir)
                QMessageBox.information(
                    self, "成功",
                    f"备份已导入: {backup_info['name']}"
                )
                self.refresh_backup_list()
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入备份失败: {e}")
    
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
