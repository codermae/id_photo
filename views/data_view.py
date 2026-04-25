"""
数据管理视图
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem, 
                             QGroupBox, QMessageBox, QFileDialog, QComboBox, QSpinBox)
from PyQt5.QtCore import Qt
from utils.database_helper import DatabaseHelper
import pandas as pd

class DataView(QWidget):
    """数据管理视图"""

    def __init__(self):
        super().__init__()
        self.db = DatabaseHelper()
        self.current_collection_id = None
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        
        # 采集任务选择区域
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
        
        # 搜索和筛选区域
        search_group = QGroupBox("搜索和筛选")
        search_layout = QVBoxLayout()
        
        # 第一行：基本搜索
        basic_search_layout = QHBoxLayout()
        basic_search_layout.addWidget(QLabel("关键词:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入姓名或身份证号")
        basic_search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.apply_filters)
        basic_search_layout.addWidget(search_btn)
        
        search_layout.addLayout(basic_search_layout)
        
        # 第二行：高级筛选
        advanced_filter_layout = QHBoxLayout()
        
        advanced_filter_layout.addWidget(QLabel("性别:"))
        self.gender_filter = QComboBox()
        self.gender_filter.addItems(['全部', '男', '女'])
        advanced_filter_layout.addWidget(self.gender_filter)
        
        advanced_filter_layout.addWidget(QLabel("民族:"))
        self.nation_filter = QComboBox()
        self.nation_filter.addItems(['全部', '汉族', '回族', '满族', '蒙古族', '其他'])
        advanced_filter_layout.addWidget(self.nation_filter)
        
        # 年龄自定义范围
        advanced_filter_layout.addWidget(QLabel("年龄范围:"))
        self.age_min_spin = QSpinBox()
        self.age_min_spin.setMinimum(0)
        self.age_min_spin.setMaximum(150)
        self.age_min_spin.setValue(0)
        advanced_filter_layout.addWidget(self.age_min_spin)
        
        advanced_filter_layout.addWidget(QLabel("-"))
        self.age_max_spin = QSpinBox()
        self.age_max_spin.setMinimum(0)
        self.age_max_spin.setMaximum(150)
        self.age_max_spin.setValue(150)
        advanced_filter_layout.addWidget(self.age_max_spin)
        
        advanced_filter_layout.addWidget(QLabel("状态:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(['全部', '已采集', '待采集', '失败', '无记录'])
        advanced_filter_layout.addWidget(self.status_filter)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_data)
        advanced_filter_layout.addWidget(refresh_btn)
        
        advanced_filter_layout.addStretch()
        
        search_layout.addLayout(advanced_filter_layout)
        
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)
        
        # 用户表格
        table_group = QGroupBox("用户列表")
        table_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            'ID', '姓名', '身份证号', '性别', '民族', '出生日期', '地址', '采集状态', '原始照片', '处理照片', '操作'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # 整行选择
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)  # 支持多选（Ctrl/Shift）
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 50)
        self.table.setColumnWidth(4, 50)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(7, 100)
        self.table.setColumnWidth(8, 80)
        self.table.setColumnWidth(9, 80)
        self.table.setColumnWidth(10, 100)
        
        # 地址字段自动填充剩余宽度
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setColumnWidth(6, 390)  # 初始宽度
        
        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group)
        
        # 操作按钮
        button_group = QGroupBox("操作")
        button_layout = QHBoxLayout()
        
        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self.delete_user)
        button_layout.addWidget(delete_btn)
        
        export_btn = QPushButton("导出Excel")
        export_btn.clicked.connect(self.export_excel)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        button_group.setLayout(button_layout)
        main_layout.addWidget(button_group)
        
        # 加载用户数据
        self.load_collections()
        self.load_users()

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
            
            # 加载民族选项
            self.load_nation_options()
        except Exception as e:
            print(f"[WARNING] 加载采集任务失败: {e}")
    
    def load_nation_options(self):
        """从数据库加载民族选项"""
        try:
            # 获取所有用户的民族值
            all_users = self.db.get_all_users()
            nations = set()
            for user in all_users:
                if user.nation:
                    nations.add(user.nation)
            
            # 更新民族下拉框
            current_selection = self.nation_filter.currentText()
            self.nation_filter.blockSignals(True)
            self.nation_filter.clear()
            self.nation_filter.addItem('全部')
            
            # 添加数据库中存在的民族
            for nation in sorted(nations):
                self.nation_filter.addItem(nation)
            
            # 恢复之前的选择
            index = self.nation_filter.findText(current_selection)
            if index >= 0:
                self.nation_filter.setCurrentIndex(index)
            else:
                self.nation_filter.setCurrentIndex(0)
            
            self.nation_filter.blockSignals(False)
        except Exception as e:
            print(f"[WARNING] 加载民族选项失败: {e}")
    
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
            
            # 重新加载民族选项
            self.load_nation_options()
            
            # 刷新用户列表
            self.load_users()
    
    def showEvent(self, event):
        """标签页显示时的处理 - 重新加载采集任务列表"""
        super().showEvent(event)
        # 每次显示时都重新加载采集任务列表
        self.load_collections()

    def load_users(self):
        """加载用户数据"""
        try:
            from PyQt5.QtGui import QColor, QBrush
            
            users = self.db.get_all_users()
            self.table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                self.table.setItem(row, 0, QTableWidgetItem(str(user.id)))
                self.table.setItem(row, 1, QTableWidgetItem(user.name))
                self.table.setItem(row, 2, QTableWidgetItem(user.id_number))
                self.table.setItem(row, 3, QTableWidgetItem(user.gender or ''))
                self.table.setItem(row, 4, QTableWidgetItem(user.nation or ''))
                self.table.setItem(row, 5, QTableWidgetItem(str(user.birthday) if user.birthday else ''))
                self.table.setItem(row, 6, QTableWidgetItem(user.address or ''))
                
                # 获取采集状态
                records = self.db.get_records_by_user(user.id)
                photos = self.db.get_photos_by_user(user.id)
                
                if records:
                    latest_record = records[-1]
                    status = latest_record.status
                    
                    # 状态显示和颜色
                    if status == 'completed':
                        status_text = '已采集'
                        status_color = QColor(200, 255, 200)  # 浅绿色
                    elif status == 'pending':
                        status_text = '待采集'
                        status_color = QColor(255, 255, 200)  # 浅黄色
                    elif status == 'failed':
                        status_text = '失败'
                        status_color = QColor(255, 200, 200)  # 浅红色
                    else:
                        status_text = '未知'
                        status_color = QColor(220, 220, 220)  # 浅灰色
                else:
                    status_text = '无记录'
                    status_color = QColor(240, 240, 240)  # 灰色
                
                status_item = QTableWidgetItem(status_text)
                status_item.setBackground(QBrush(status_color))
                status_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 7, status_item)
                
                # 照片数量 - 分类统计
                raw_photos = [p for p in photos if p.photo_type == 'raw']
                processed_photos = [p for p in photos if p.photo_type == 'processed']
                
                raw_count_item = QTableWidgetItem(str(len(raw_photos)))
                raw_count_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 8, raw_count_item)
                
                processed_count_item = QTableWidgetItem(str(len(processed_photos)))
                processed_count_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 9, processed_count_item)
                
                # 操作按钮
                view_btn = QPushButton("查看")
                view_btn.clicked.connect(lambda checked, u=user: self.view_user(u))
                self.table.setCellWidget(row, 10, view_btn)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载用户失败: {e}")
            import traceback
            traceback.print_exc()

    def search_user(self):
        """搜索用户 - 支持姓名和身份证号"""
        from PyQt5.QtGui import QColor, QBrush
        
        keyword = self.search_input.text().strip()
        if not keyword:
            self.load_users()
            return

        try:
            users = self.db.get_all_users()
            
            # 搜索匹配的用户（姓名或身份证号包含关键词）
            matched_users = []
            for user in users:
                if (keyword.lower() in user.name.lower() or 
                    keyword in user.id_number):
                    matched_users.append(user)
            
            if matched_users:
                self.table.setRowCount(len(matched_users))
                
                for row, user in enumerate(matched_users):
                    self.table.setItem(row, 0, QTableWidgetItem(str(user.id)))
                    self.table.setItem(row, 1, QTableWidgetItem(user.name))
                    self.table.setItem(row, 2, QTableWidgetItem(user.id_number))
                    self.table.setItem(row, 3, QTableWidgetItem(user.gender or ''))
                    self.table.setItem(row, 4, QTableWidgetItem(user.nation or ''))
                    self.table.setItem(row, 5, QTableWidgetItem(str(user.birthday) if user.birthday else ''))
                    self.table.setItem(row, 6, QTableWidgetItem(user.address or ''))
                    
                    # 获取采集状态
                    records = self.db.get_records_by_user(user.id)
                    photos = self.db.get_photos_by_user(user.id)
                    
                    if records:
                        latest_record = records[-1]
                        status = latest_record.status
                        
                        if status == 'completed':
                            status_text = '已采集'
                            status_color = QColor(200, 255, 200)
                        elif status == 'pending':
                            status_text = '待采集'
                            status_color = QColor(255, 255, 200)
                        elif status == 'failed':
                            status_text = '失败'
                            status_color = QColor(255, 200, 200)
                        else:
                            status_text = '未知'
                            status_color = QColor(220, 220, 220)
                    else:
                        status_text = '无记录'
                        status_color = QColor(240, 240, 240)
                    
                    status_item = QTableWidgetItem(status_text)
                    status_item.setBackground(QBrush(status_color))
                    status_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 7, status_item)
                    
                    # 照片数量 - 分类统计
                    raw_photos = [p for p in photos if p.photo_type == 'raw']
                    processed_photos = [p for p in photos if p.photo_type == 'processed']
                    
                    raw_count_item = QTableWidgetItem(str(len(raw_photos)))
                    raw_count_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 8, raw_count_item)
                    
                    processed_count_item = QTableWidgetItem(str(len(processed_photos)))
                    processed_count_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 9, processed_count_item)
                    
                    view_btn = QPushButton("查看")
                    view_btn.clicked.connect(lambda checked, u=user: self.view_user(u))
                    self.table.setCellWidget(row, 10, view_btn)
                
                # 显示搜索结果数量
                QMessageBox.information(self, "搜索结果", f"找到 {len(matched_users)} 个匹配的用户")
            else:
                QMessageBox.information(self, "搜索结果", f"未找到包含 '{keyword}' 的用户")
                self.load_users()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")
            import traceback
            traceback.print_exc()

    def apply_filters(self):
        """应用高级筛选"""
        keyword = self.search_input.text().strip()
        gender = self.gender_filter.currentText()
        nation = self.nation_filter.currentText()
        age_min = self.age_min_spin.value()
        age_max = self.age_max_spin.value()
        status = self.status_filter.currentText()
        
        # 转换筛选值
        gender_val = None if gender == '全部' else gender
        nation_val = None if nation == '全部' else nation
        status_val = None if status == '全部' else status
        
        try:
            # 获取所有用户
            users = self.db.get_all_users()
            
            # 应用筛选条件
            filtered_users = []
            from datetime import datetime
            today = datetime.now().date()
            
            for user in users:
                # 关键词筛选
                if keyword and keyword.lower() not in user.name.lower() and keyword not in user.id_number:
                    continue
                
                # 性别筛选
                if gender_val and user.gender != gender_val:
                    continue
                
                # 民族筛选
                if nation_val and user.nation != nation_val:
                    continue
                
                # 年龄范围筛选
                if user.birthday:
                    age = (today - user.birthday).days // 365
                    if age < age_min or age > age_max:
                        continue
                
                # 采集状态筛选
                if status_val:
                    records = self.db.get_records_by_user(user.id)
                    
                    if status_val == '无记录':
                        if records:  # 有记录则不符合
                            continue
                    else:
                        if not records:  # 无记录则不符合
                            continue
                        
                        latest_record = records[-1]
                        status_map = {
                            '已采集': 'completed',
                            '待采集': 'pending',
                            '失败': 'failed'
                        }
                        
                        if latest_record.status != status_map.get(status_val):
                            continue
                
                filtered_users.append(user)
            
            if filtered_users:
                self.display_search_results(filtered_users)
            else:
                self.table.setRowCount(0)
                QMessageBox.information(self, "搜索结果", "未找到匹配的用户")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"筛选失败: {e}")

    def refresh_data(self):
        """刷新数据和重置筛选条件"""
        # 重置筛选条件
        self.search_input.clear()
        self.gender_filter.setCurrentIndex(0)
        self.nation_filter.setCurrentIndex(0)
        self.age_min_spin.setValue(0)
        self.age_max_spin.setValue(150)
        self.status_filter.setCurrentIndex(0)
        
        # 加载所有用户
        self.load_users()

    def display_search_results(self, users):
        """显示搜索结果"""
        from PyQt5.QtGui import QColor, QBrush
        
        if not users:
            self.table.setRowCount(0)
            return
        
        try:
            self.table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                self.table.setItem(row, 0, QTableWidgetItem(str(user.id)))
                self.table.setItem(row, 1, QTableWidgetItem(user.name))
                self.table.setItem(row, 2, QTableWidgetItem(user.id_number))
                self.table.setItem(row, 3, QTableWidgetItem(user.gender or ''))
                self.table.setItem(row, 4, QTableWidgetItem(user.nation or ''))
                self.table.setItem(row, 5, QTableWidgetItem(str(user.birthday) if user.birthday else ''))
                self.table.setItem(row, 6, QTableWidgetItem(user.address or ''))
                
                # 获取采集状态
                records = self.db.get_records_by_user(user.id)
                photos = self.db.get_photos_by_user(user.id)
                
                if records:
                    latest_record = records[-1]
                    status = latest_record.status
                    
                    if status == 'completed':
                        status_text = '✅ 已采集'
                        status_color = QColor(200, 255, 200)
                    elif status == 'pending':
                        status_text = '⏳ 待采集'
                        status_color = QColor(255, 255, 200)
                    elif status == 'failed':
                        status_text = '❌ 失败'
                        status_color = QColor(255, 200, 200)
                    else:
                        status_text = '❓ 未知'
                        status_color = QColor(220, 220, 220)
                else:
                    status_text = '⚠️ 无记录'
                    status_color = QColor(240, 240, 240)
                
                status_item = QTableWidgetItem(status_text)
                status_item.setBackground(QBrush(status_color))
                status_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 7, status_item)
                
                # 照片数量 - 分类统计
                raw_photos = [p for p in photos if p.photo_type == 'raw']
                processed_photos = [p for p in photos if p.photo_type == 'processed']
                
                raw_count_item = QTableWidgetItem(str(len(raw_photos)))
                raw_count_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 8, raw_count_item)
                
                processed_count_item = QTableWidgetItem(str(len(processed_photos)))
                processed_count_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 9, processed_count_item)
                
                # 操作按钮
                view_btn = QPushButton("查看")
                view_btn.clicked.connect(lambda checked, u=user: self.view_user(u))
                self.table.setCellWidget(row, 10, view_btn)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示搜索结果失败: {e}")

    def view_user(self, user):
        """查看用户详情"""
        photos = self.db.get_photos_by_user(user.id)
        records = self.db.get_records_by_user(user.id)
        
        # 照片分类统计
        raw_photos = [p for p in photos if p.photo_type == 'raw']
        processed_photos = [p for p in photos if p.photo_type == 'processed']
        
        # 采集状态信息
        status_info = ""
        if records:
            latest_record = records[-1]
            status_map = {
                'completed': '已采集',
                'pending': '待采集',
                'failed': '失败'
            }
            status_text = status_map.get(latest_record.status, '未知')
            status_info = f"""
        采集状态: {status_text}
        采集日期: {latest_record.collection_date}
        操作员: {latest_record.operator or '未知'}
        备注: {latest_record.notes or '无'}
        """
        else:
            status_info = "\n        采集状态: 无采集记录"
        
        info = f"""
        用户信息
        --------
        姓名: {user.name}
        身份证号: {user.id_number}
        性别: {user.gender}
        民族: {user.nation}
        出生日期: {user.birthday}
        地址: {user.address}
        {status_info}
        
        照片统计
        --------
        原始照片: {len(raw_photos)} 张
        处理照片: {len(processed_photos)} 张
        总计: {len(photos)} 张
        采集记录数: {len(records)}
        """
        
        QMessageBox.information(self, "用户详情", info)

    def delete_user(self):
        """删除用户 - 支持批量删除"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请选择要删除的用户")
            return
        
        # 获取所有选中的用户信息
        users_to_delete = []
        total_photos = 0
        total_records = 0
        
        for index in selected_rows:
            row = index.row()
            user_id = int(self.table.item(row, 0).text())
            user_name = self.table.item(row, 1).text()
            
            photos = self.db.get_photos_by_user(user_id)
            records = self.db.get_records_by_user(user_id)
            
            users_to_delete.append({
                'id': user_id,
                'name': user_name,
                'photos': photos,
                'records': records
            })
            
            total_photos += len(photos)
            total_records += len(records)
        
        # 详细的确认信息
        user_count = len(users_to_delete)
        user_names = ', '.join([u['name'] for u in users_to_delete[:3]])
        if user_count > 3:
            user_names += f' 等{user_count}人'
        
        confirm_msg = f"""确定要删除 {user_count} 个用户吗？

用户: {user_names}

删除操作将：
• 删除 {user_count} 个用户的基本信息
• 删除 {total_photos} 张照片记录
• 删除 {total_records} 条采集记录
• 删除该用户的照片文件

此操作不可恢复！"""
        
        reply = QMessageBox.question(
            self, "确认删除", confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import os
                
                total_deleted_files = 0
                total_failed_files = 0
                deleted_users = 0
                
                # 逐个删除用户
                for user_info in users_to_delete:
                    user_id = user_info['id']
                    user_name = user_info['name']
                    photos = user_info['photos']
                    
                    # 1. 删除照片文件
                    for photo in photos:
                        if photo.file_path and os.path.exists(photo.file_path):
                            try:
                                os.remove(photo.file_path)
                                total_deleted_files += 1
                                print(f"[INFO] 删除照片文件: {photo.file_path}")
                            except Exception as e:
                                total_failed_files += 1
                                print(f"[WARNING] 删除照片文件失败: {photo.file_path}, 错误: {e}")
                    
                    # 2. 删除数据库记录
                    try:
                        self.db.delete_user(user_id)
                        deleted_users += 1
                        print(f"[INFO] 删除用户: {user_name} (ID: {user_id})")
                    except Exception as e:
                        print(f"[ERROR] 删除用户失败: {user_name}, 错误: {e}")
                
                # 3. 显示删除结果
                result_msg = f"批量删除完成\n\n"
                result_msg += f"• 用户: 删除 {deleted_users}/{user_count} 个\n"
                result_msg += f"• 照片文件: 删除 {total_deleted_files} 个"
                if total_failed_files > 0:
                    result_msg += f", 失败 {total_failed_files} 个"
                result_msg += f"\n• 数据库记录: 已清除"
                
                QMessageBox.information(self, "删除完成", result_msg)
                
                # 4. 刷新列表
                self.load_users()
                
                # 5. 通知主窗口更新统计
                self.notify_data_changed()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
                import traceback
                traceback.print_exc()
    
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

    def export_excel(self):
        """导出Excel"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "Excel文件 (*.xlsx)"
        )
        
        if filepath:
            try:
                users = self.db.get_all_users(self.current_collection_id)
                data = []
                
                for user in users:
                    photos = self.db.get_photos_by_user(user.id)
                    records = self.db.get_records_by_user(user.id)
                    
                    # 照片分类统计
                    raw_photos = [p for p in photos if p.photo_type == 'raw']
                    processed_photos = [p for p in photos if p.photo_type == 'processed']
                    
                    # 获取采集状态
                    if records:
                        latest_record = records[-1]
                        status_map = {
                            'completed': '已采集',
                            'pending': '待采集',
                            'failed': '失败'
                        }
                        status = status_map.get(latest_record.status, '未知')
                        collection_date = latest_record.collection_date
                        operator = latest_record.operator or '未知'
                    else:
                        status = '无记录'
                        collection_date = None
                        operator = '未知'
                    
                    data.append({
                        'ID': user.id,
                        '姓名': user.name,
                        '身份证号': user.id_number,
                        '性别': user.gender,
                        '民族': user.nation,
                        '出生日期': user.birthday,
                        '地址': user.address,
                        '采集状态': status,
                        '采集日期': collection_date,
                        '操作员': operator,
                        '原始照片': len(raw_photos),
                        '处理照片': len(processed_photos),
                        '照片总数': len(photos),
                        '创建时间': user.created_at,
                    })
                
                df = pd.DataFrame(data)
                
                # 获取当前采集任务信息
                collection = self.db.get_collection_by_id(self.current_collection_id)
                sheet_name = collection.name if collection else '用户列表'
                
                df.to_excel(filepath, index=False, sheet_name=sheet_name[:31])  # Excel sheet名称最多31个字符
                
                QMessageBox.information(self, "成功", f"数据已导出\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
                import traceback
                traceback.print_exc()

    def filter_by_status(self, status_text):
        """按状态筛选用户"""
        try:
            from PyQt5.QtGui import QColor, QBrush
            
            users = self.db.get_all_users()
            
            # 筛选用户
            filtered_users = []
            for user in users:
                records = self.db.get_records_by_user(user.id)
                
                if status_text == '全部':
                    filtered_users.append(user)
                elif status_text == '已采集':
                    if records and records[-1].status == 'completed':
                        filtered_users.append(user)
                elif status_text == '待采集':
                    if records and records[-1].status == 'pending':
                        filtered_users.append(user)
                elif status_text == '失败':
                    if records and records[-1].status == 'failed':
                        filtered_users.append(user)
                elif status_text == '无记录':
                    if not records:
                        filtered_users.append(user)
            
            # 显示筛选结果
            self.table.setRowCount(len(filtered_users))
            
            for row, user in enumerate(filtered_users):
                self.table.setItem(row, 0, QTableWidgetItem(str(user.id)))
                self.table.setItem(row, 1, QTableWidgetItem(user.name))
                self.table.setItem(row, 2, QTableWidgetItem(user.id_number))
                self.table.setItem(row, 3, QTableWidgetItem(user.gender or ''))
                self.table.setItem(row, 4, QTableWidgetItem(user.nation or ''))
                self.table.setItem(row, 5, QTableWidgetItem(str(user.birthday) if user.birthday else ''))
                
                # 获取采集状态
                records = self.db.get_records_by_user(user.id)
                photos = self.db.get_photos_by_user(user.id)
                
                if records:
                    latest_record = records[-1]
                    status = latest_record.status
                    
                    if status == 'completed':
                        status_text = '已采集'
                        status_color = QColor(200, 255, 200)
                    elif status == 'pending':
                        status_text = '待采集'
                        status_color = QColor(255, 255, 200)
                    elif status == 'failed':
                        status_text = '失败'
                        status_color = QColor(255, 200, 200)
                    else:
                        status_text = '未知'
                        status_color = QColor(220, 220, 220)
                else:
                    status_text = '无记录'
                    status_color = QColor(240, 240, 240)
                
                status_item = QTableWidgetItem(status_text)
                status_item.setBackground(QBrush(status_color))
                status_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 6, status_item)
                
                # 照片数量 - 分类统计
                raw_photos = [p for p in photos if p.photo_type == 'raw']
                processed_photos = [p for p in photos if p.photo_type == 'processed']
                
                raw_count_item = QTableWidgetItem(str(len(raw_photos)))
                raw_count_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 7, raw_count_item)
                
                processed_count_item = QTableWidgetItem(str(len(processed_photos)))
                processed_count_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 8, processed_count_item)
                
                view_btn = QPushButton("查看")
                view_btn.clicked.connect(lambda checked, u=user: self.view_user(u))
                self.table.setCellWidget(row, 9, view_btn)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"筛选失败: {e}")
            import traceback
            traceback.print_exc()

    def closeEvent(self, event):
        """关闭事件"""
        self.db.close()
        event.accept()
