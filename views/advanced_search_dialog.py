"""
高级搜索和筛选对话框
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QComboBox, QPushButton, QCheckBox, QSpinBox, QMessageBox,
                             QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from utils.database_helper import DatabaseHelper
import json
import os
from datetime import datetime

class AdvancedSearchDialog(QDialog):
    """高级搜索和筛选对话框"""
    
    search_completed = pyqtSignal(list)  # 搜索完成信号，返回搜索结果
    
    def __init__(self, collection_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高级搜索和筛选")
        # 删除右上角的问号
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setGeometry(100, 100, 900, 700)
        self.db = DatabaseHelper()
        self.collection_id = collection_id
        self.search_results = []
        self.saved_filters_file = os.path.join(
            os.path.dirname(__file__), 
            '../data/saved_filters.json'
        )
        self.init_ui()
        self.load_saved_filters()
    
    def init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        
        # 搜索条件组
        search_group = QGroupBox("搜索条件")
        search_layout = QVBoxLayout()
        
        # 第一行：关键词搜索
        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(QLabel("关键词（姓名/身份证号）:"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入姓名或身份证号")
        keyword_layout.addWidget(self.keyword_input)
        search_layout.addLayout(keyword_layout)
        
        # 第二行：性别、民族、年龄
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("性别:"))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["全部", "男", "女", "其他"])
        filter_layout.addWidget(self.gender_combo)
        
        filter_layout.addWidget(QLabel("民族:"))
        self.nation_combo = QComboBox()
        self.nation_combo.addItems(["全部", "汉族", "回族", "满族", "蒙古族", "其他"])
        filter_layout.addWidget(self.nation_combo)
        
        filter_layout.addWidget(QLabel("年龄:"))
        self.age_combo = QComboBox()
        self.age_combo.addItems(["全部", "0-18岁", "18-30岁", "30-45岁", "45-60岁", "60岁以上"])
        filter_layout.addWidget(self.age_combo)
        
        search_layout.addLayout(filter_layout)
        
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        search_btn = QPushButton("🔍 搜索")
        search_btn.clicked.connect(self.perform_search)
        button_layout.addWidget(search_btn)
        
        clear_btn = QPushButton("🔄 清空")
        clear_btn.clicked.connect(self.clear_filters)
        button_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("💾 保存筛选条件")
        save_btn.clicked.connect(self.save_filter)
        button_layout.addWidget(save_btn)
        
        load_btn = QPushButton("📂 加载筛选条件")
        load_btn.clicked.connect(self.load_filter)
        button_layout.addWidget(load_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
        # 搜索结果表格
        result_group = QGroupBox("搜索结果")
        result_layout = QVBoxLayout()
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(7)
        self.result_table.setHorizontalHeaderLabels([
            "ID", "姓名", "身份证号", "性别", "民族", "出生日期", "地址"
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        result_layout.addWidget(self.result_table)
        
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)
    
    def perform_search(self):
        """执行搜索"""
        try:
            # 获取搜索条件
            keyword = self.keyword_input.text().strip()
            gender = self.gender_combo.currentText()
            nation = self.nation_combo.currentText()
            age_range = self.age_combo.currentText()
            
            # 转换为数据库查询格式
            gender = None if gender == "全部" else gender
            nation = None if nation == "全部" else nation
            age_range_key = None
            if age_range != "全部":
                age_range_key = age_range.replace("岁", "").replace("以上", "+")
            
            # 执行搜索
            self.search_results = self.db.search_users(
                keyword=keyword if keyword else None,
                collection_id=self.collection_id,
                gender=gender,
                age_range=age_range_key,
                nation=nation
            )
            
            # 显示结果
            self.display_results()
            
            # 更新状态
            self.status_label.setText(f"找到 {len(self.search_results)} 条结果")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")
    
    def display_results(self):
        """显示搜索结果"""
        self.result_table.setRowCount(0)
        
        for row, user in enumerate(self.search_results):
            self.result_table.insertRow(row)
            
            # ID
            self.result_table.setItem(row, 0, QTableWidgetItem(str(user.id)))
            
            # 姓名
            self.result_table.setItem(row, 1, QTableWidgetItem(user.name))
            
            # 身份证号
            self.result_table.setItem(row, 2, QTableWidgetItem(user.id_number))
            
            # 性别
            self.result_table.setItem(row, 3, QTableWidgetItem(user.gender or "未知"))
            
            # 民族
            self.result_table.setItem(row, 4, QTableWidgetItem(user.nation or "未知"))
            
            # 出生日期
            birthday = user.birthday.strftime('%Y-%m-%d') if user.birthday else "未知"
            self.result_table.setItem(row, 5, QTableWidgetItem(birthday))
            
            # 地址
            self.result_table.setItem(row, 6, QTableWidgetItem(user.address or ""))
    
    def clear_filters(self):
        """清空筛选条件"""
        self.keyword_input.clear()
        self.gender_combo.setCurrentIndex(0)
        self.nation_combo.setCurrentIndex(0)
        self.age_combo.setCurrentIndex(0)
        self.result_table.setRowCount(0)
        self.status_label.setText("就绪")
    
    def save_filter(self):
        """保存筛选条件"""
        try:
            # 获取当前筛选条件
            filter_data = {
                'keyword': self.keyword_input.text(),
                'gender': self.gender_combo.currentText(),
                'nation': self.nation_combo.currentText(),
                'age_range': self.age_combo.currentText(),
                'timestamp': datetime.now().isoformat()
            }
            
            # 加载现有筛选条件
            filters = {}
            if os.path.exists(self.saved_filters_file):
                with open(self.saved_filters_file, 'r', encoding='utf-8') as f:
                    filters = json.load(f)
            
            # 生成筛选条件名称
            filter_name = f"筛选_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            filters[filter_name] = filter_data
            
            # 保存到文件
            os.makedirs(os.path.dirname(self.saved_filters_file), exist_ok=True)
            with open(self.saved_filters_file, 'w', encoding='utf-8') as f:
                json.dump(filters, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "成功", f"筛选条件已保存为: {filter_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def load_filter(self):
        """加载筛选条件"""
        try:
            if not os.path.exists(self.saved_filters_file):
                QMessageBox.warning(self, "提示", "没有保存的筛选条件")
                return
            
            with open(self.saved_filters_file, 'r', encoding='utf-8') as f:
                filters = json.load(f)
            
            if not filters:
                QMessageBox.warning(self, "提示", "没有保存的筛选条件")
                return
            
            # 显示筛选条件列表
            filter_names = list(filters.keys())
            
            # 创建选择对话框
            from PyQt5.QtWidgets import QInputDialog
            filter_name, ok = QInputDialog.getItem(
                self, "加载筛选条件", "选择筛选条件:",
                filter_names, 0, False
            )
            
            if ok and filter_name:
                filter_data = filters[filter_name]
                
                # 应用筛选条件
                self.keyword_input.setText(filter_data.get('keyword', ''))
                
                gender_index = self.gender_combo.findText(filter_data.get('gender', '全部'))
                if gender_index >= 0:
                    self.gender_combo.setCurrentIndex(gender_index)
                
                nation_index = self.nation_combo.findText(filter_data.get('nation', '全部'))
                if nation_index >= 0:
                    self.nation_combo.setCurrentIndex(nation_index)
                
                age_index = self.age_combo.findText(filter_data.get('age_range', '全部'))
                if age_index >= 0:
                    self.age_combo.setCurrentIndex(age_index)
                
                QMessageBox.information(self, "成功", f"已加载筛选条件: {filter_name}")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {e}")
    
    def load_saved_filters(self):
        """在初始化时加载保存的筛选条件"""
        # 这个方法在初始化时调用，确保保存的筛选条件文件存在
        if not os.path.exists(self.saved_filters_file):
            os.makedirs(os.path.dirname(self.saved_filters_file), exist_ok=True)
    
    def get_results(self):
        """获取搜索结果"""
        return self.search_results
    
    def closeEvent(self, event):
        """关闭事件"""
        self.db.close()
        event.accept()
