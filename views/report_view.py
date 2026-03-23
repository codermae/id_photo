"""
统计报表视图
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QGroupBox, QMessageBox, QFileDialog, QDateEdit, QComboBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from utils.database_helper import DatabaseHelper
import pandas as pd
from datetime import datetime, timedelta

class ReportView(QWidget):
    """统计报表视图"""

    def __init__(self):
        super().__init__()
        self.db = DatabaseHelper()
        self.current_collection_id = None
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        
        # 采集任务选择
        collection_group = QGroupBox("采集任务")
        collection_layout = QHBoxLayout()
        
        collection_layout.addWidget(QLabel("当前任务:"))
        self.collection_label = QLabel("未选择")
        self.collection_label.setStyleSheet("color: red; font-weight: bold;")
        collection_layout.addWidget(self.collection_label)
        
        self.collection_combo = QComboBox()
        self.collection_combo.currentIndexChanged.connect(self.on_collection_changed)
        collection_layout.addWidget(self.collection_combo)
        
        collection_layout.addStretch()
        
        collection_group.setLayout(collection_layout)
        main_layout.addWidget(collection_group)
        
        # 日期范围选择
        date_group = QGroupBox("日期范围")
        date_layout = QHBoxLayout()
        
        date_layout.addWidget(QLabel("开始日期:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("结束日期:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date)
        
        date_group.setLayout(date_layout)
        main_layout.addWidget(date_group)
        
        # 统计信息
        stats_group = QGroupBox("采集统计")
        stats_layout = QVBoxLayout()
        
        # 总体统计
        overall_layout = QHBoxLayout()
        
        self.total_users_label = QLabel("用户总数: 0")
        self.total_users_label.setFont(self.get_label_font())
        overall_layout.addWidget(self.total_users_label)
        
        self.total_photos_label = QLabel("照片总数: 0")
        self.total_photos_label.setFont(self.get_label_font())
        overall_layout.addWidget(self.total_photos_label)
        
        stats_layout.addLayout(overall_layout)
        
        # 采集统计
        collection_stats_layout = QHBoxLayout()
        
        self.completed_label = QLabel("已采集: 0")
        self.completed_label.setFont(self.get_label_font())
        self.completed_label.setStyleSheet("color: green;")
        collection_stats_layout.addWidget(self.completed_label)
        
        self.pending_label = QLabel("待采集: 0")
        self.pending_label.setFont(self.get_label_font())
        self.pending_label.setStyleSheet("color: orange;")
        collection_stats_layout.addWidget(self.pending_label)
        
        self.failed_label = QLabel("失败: 0")
        self.failed_label.setFont(self.get_label_font())
        self.failed_label.setStyleSheet("color: red;")
        collection_stats_layout.addWidget(self.failed_label)
        
        self.completion_rate_label = QLabel("完成率: 0%")
        self.completion_rate_label.setFont(self.get_label_font())
        collection_stats_layout.addWidget(self.completion_rate_label)
        
        stats_layout.addLayout(collection_stats_layout)
        
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        # 详细统计
        detail_group = QGroupBox("详细统计")
        detail_layout = QVBoxLayout()
        
        self.detail_label = QLabel()
        self.detail_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_label)
        
        detail_group.setLayout(detail_layout)
        main_layout.addWidget(detail_group)
        
        # 操作按钮
        button_group = QGroupBox("操作")
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新统计")
        refresh_btn.clicked.connect(self.refresh_stats)
        button_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("导出报表")
        export_btn.clicked.connect(self.export_report)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        button_group.setLayout(button_layout)
        main_layout.addWidget(button_group)
        
        main_layout.addStretch()
        
        # 加载采集任务
        self.load_collections()

    def load_collections(self):
        """加载采集任务列表"""
        try:
            collections = self.db.get_active_collections()
            self.collection_combo.clear()
            
            # 添加"全部"选项
            self.collection_combo.addItem("全部采集任务", None)
            
            for collection in collections:
                self.collection_combo.addItem(
                    f"{collection.name} ({collection.organization})",
                    collection.id
                )
            
            # 默认选择"全部"
            self.collection_combo.setCurrentIndex(0)
        except Exception as e:
            print(f"[WARNING] 加载采集任务失败: {e}")
    
    def on_collection_changed(self, index):
        """采集任务切换时的处理"""
        if index >= 0:
            self.current_collection_id = self.collection_combo.currentData()
            
            # 更新显示
            if self.current_collection_id is None:
                self.collection_label.setText("全部采集任务")
                self.collection_label.setStyleSheet("color: blue; font-weight: bold;")
                self.db.set_current_collection(None)
                print("[INFO] 已切换到全部采集任务")
            else:
                self.db.set_current_collection(self.current_collection_id)
                collection = self.db.get_collection_by_id(self.current_collection_id)
                if collection:
                    self.collection_label.setText(f"{collection.name} ({collection.organization})")
                    self.collection_label.setStyleSheet("color: green; font-weight: bold;")
                    print(f"[INFO] 已切换采集任务: {collection.name} (ID: {self.current_collection_id})")
            
            # 刷新统计
            self.refresh_stats()
    
    def showEvent(self, event):
        """标签页显示时的处理 - 重新加载采集任务列表"""
        super().showEvent(event)
        # 每次显示时都重新加载采集任务列表
        self.load_collections()

    def get_label_font(self):
        """获取标签字体"""
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        return font

    def refresh_stats(self):
        """刷新统计"""
        try:
            # 获取日期范围
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            # 总体统计
            total_users = self.db.get_user_count(self.current_collection_id)
            total_photos = self.db.get_photo_count(self.current_collection_id)
            
            self.total_users_label.setText(f"用户总数: {total_users}")
            self.total_photos_label.setText(f"照片总数: {total_photos}")
            
            # 采集统计
            stats = self.db.get_collection_stats(start_date, end_date, self.current_collection_id)
            
            self.completed_label.setText(f"已采集: {stats['completed']}")
            self.pending_label.setText(f"待采集: {stats['pending']}")
            self.failed_label.setText(f"失败: {stats['failed']}")
            self.completion_rate_label.setText(f"完成率: {stats['completion_rate']:.1f}%")
            
            # 详细信息
            detail_text = f"""
            统计周期: {start_date} 至 {end_date}
            
            采集总数: {stats['total']}
            已完成: {stats['completed']}
            待采集: {stats['pending']}
            失败: {stats['failed']}
            完成率: {stats['completion_rate']:.1f}%
            
            平均每天采集: {stats['total'] / max(1, (end_date - start_date).days + 1):.1f}人
            """
            
            self.detail_label.setText(detail_text)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"统计失败: {e}")

    def export_report(self):
        """导出报表"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存报表", "", "Excel文件 (*.xlsx)"
        )
        
        if filepath:
            try:
                start_date = self.start_date.date().toPyDate()
                end_date = self.end_date.date().toPyDate()
                
                # 创建Excel工作簿
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    # 统计汇总
                    stats = self.db.get_collection_stats(start_date, end_date, self.current_collection_id)
                    summary_data = {
                        '指标': ['用户总数', '照片总数', '已采集', '待采集', '失败', '完成率'],
                        '数值': [
                            self.db.get_user_count(self.current_collection_id),
                            self.db.get_photo_count(self.current_collection_id),
                            stats['completed'],
                            stats['pending'],
                            stats['failed'],
                            f"{stats['completion_rate']:.1f}%"
                        ]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='统计汇总', index=False)
                    
                    # 用户列表
                    users = self.db.get_all_users(self.current_collection_id)
                    user_data = []
                    for user in users:
                        photos = self.db.get_photos_by_user(user.id)
                        records = self.db.get_records_by_user(user.id)
                        user_data.append({
                            'ID': user.id,
                            '姓名': user.name,
                            '身份证号': user.id_number,
                            '性别': user.gender,
                            '民族': user.nation,
                            '出生日期': user.birthday,
                            '地址': user.address,
                            '照片数': len(photos),
                            '采集状态': records[-1].status if records else '未采集',
                        })
                    user_df = pd.DataFrame(user_data)
                    user_df.to_excel(writer, sheet_name='用户列表', index=False)
                
                QMessageBox.information(self, "成功", f"报表已导出\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def closeEvent(self, event):
        """关闭事件"""
        self.db.close()
        event.accept()
