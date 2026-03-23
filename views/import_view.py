"""
数据导入视图 - 支持手动和批量录入
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem, 
                             QGroupBox, QMessageBox, QFileDialog, QDateEdit, QComboBox, QDialog)
from PyQt5.QtCore import Qt, QDate
from utils.database_helper import DatabaseHelper
from utils.id_card_validator import IDCardValidator
from datetime import datetime
import csv

class CollectionSelectionDialog(QDialog):
    """采集任务选择对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择或创建采集任务")
        self.setGeometry(200, 200, 500, 300)
        self.selected_collection_id = None
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 选择现有采集任务
        select_group = QGroupBox("选择现有采集任务")
        select_layout = QVBoxLayout()
        
        select_layout.addWidget(QLabel("采集任务:"))
        self.collection_combo = QComboBox()
        self.load_collections()
        select_layout.addWidget(self.collection_combo)
        
        select_group.setLayout(select_layout)
        layout.addWidget(select_group)
        
        # 或创建新采集任务
        create_group = QGroupBox("或创建新采集任务")
        create_layout = QVBoxLayout()
        
        create_layout.addWidget(QLabel("任务名称:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如: 学校A-2026年3月")
        create_layout.addWidget(self.name_input)
        
        create_layout.addWidget(QLabel("机构名称:"))
        self.org_input = QLineEdit()
        self.org_input.setPlaceholderText("例如: 学校A")
        create_layout.addWidget(self.org_input)
        
        create_layout.addWidget(QLabel("任务描述 (可选):"))
        self.desc_input = QLineEdit()
        create_layout.addWidget(self.desc_input)
        
        create_group.setLayout(create_layout)
        layout.addWidget(create_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        select_btn = QPushButton("使用选中的任务")
        select_btn.clicked.connect(self.use_selected)
        button_layout.addWidget(select_btn)
        
        create_btn = QPushButton("创建新任务")
        create_btn.clicked.connect(self.create_new)
        button_layout.addWidget(create_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_collections(self):
        """加载采集任务列表"""
        try:
            db = DatabaseHelper()
            collections = db.get_active_collections()
            db.close()
            
            self.collection_combo.clear()
            if collections:
                for collection in collections:
                    self.collection_combo.addItem(
                        f"{collection.name} ({collection.organization})",
                        collection.id
                    )
            else:
                self.collection_combo.addItem("没有可用的采集任务", None)
        except Exception as e:
            print(f"[ERROR] 加载采集任务失败: {e}")
            self.collection_combo.addItem("加载失败", None)
    
    def use_selected(self):
        """使用选中的采集任务"""
        if self.collection_combo.count() == 0:
            QMessageBox.warning(self, "警告", "没有可用的采集任务")
            return
        
        collection_id = self.collection_combo.currentData()
        if collection_id is None:
            QMessageBox.warning(self, "警告", "请先创建采集任务")
            return
        
        self.selected_collection_id = collection_id
        self.accept()
    
    def create_new(self):
        """创建新采集任务"""
        name = self.name_input.text().strip()
        org = self.org_input.text().strip()
        desc = self.desc_input.text().strip()
        
        if not name or not org:
            QMessageBox.warning(self, "警告", "任务名称和机构名称不能为空")
            return
        
        try:
            db = DatabaseHelper()
            collection = db.create_collection(
                name=name,
                organization=org,
                description=desc if desc else None
            )
            collection_id = collection.id
            db.close()
            
            self.selected_collection_id = collection_id
            QMessageBox.information(self, "成功", f"采集任务 '{name}' 创建成功")
            self.accept()
        except Exception as e:
            print(f"[ERROR] 创建采集任务失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"创建采集任务失败: {e}")

class ImportView(QWidget):
    """数据导入视图"""

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
        
        select_collection_btn = QPushButton("选择/创建任务")
        select_collection_btn.clicked.connect(self.select_collection)
        collection_layout.addWidget(select_collection_btn)
        
        collection_layout.addStretch()
        
        collection_group.setLayout(collection_layout)
        main_layout.addWidget(collection_group)
        
        # 手动录入区域
        manual_group = QGroupBox("手动录入用户")
        manual_layout = QVBoxLayout()
        
        # 姓名
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("姓名:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        manual_layout.addLayout(name_layout)
        
        # 身份证号
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("身份证号:"))
        self.id_input = QLineEdit()
        self.id_input.textChanged.connect(self.on_id_changed)  # 监听身份证号变化
        id_layout.addWidget(self.id_input)
        manual_layout.addLayout(id_layout)
        
        # 性别
        gender_layout = QHBoxLayout()
        gender_layout.addWidget(QLabel("性别:"))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(['男', '女', '其他'])
        self.gender_combo.setEnabled(False)  # 设为禁用，自动从身份证号识别
        gender_layout.addWidget(self.gender_combo)
        manual_layout.addLayout(gender_layout)
        
        # 民族
        nation_layout = QHBoxLayout()
        nation_layout.addWidget(QLabel("民族:"))
        self.nation_input = QLineEdit()
        self.nation_input.setText("汉")
        nation_layout.addWidget(self.nation_input)
        manual_layout.addLayout(nation_layout)
        
        # 出生日期（自动从身份证号提取）
        birthday_layout = QHBoxLayout()
        birthday_layout.addWidget(QLabel("出生日期:"))
        self.birthday_input = QDateEdit()
        self.birthday_input.setDate(QDate(1990, 1, 1))
        self.birthday_input.setReadOnly(True)  # 设为只读，自动从身份证号提取
        birthday_layout.addWidget(self.birthday_input)
        manual_layout.addLayout(birthday_layout)
        
        # 地址
        address_layout = QHBoxLayout()
        address_layout.addWidget(QLabel("地址:"))
        self.address_input = QLineEdit()
        address_layout.addWidget(self.address_input)
        manual_layout.addLayout(address_layout)
        
        # 添加按钮
        add_btn = QPushButton("添加用户")
        add_btn.clicked.connect(self.add_user)
        manual_layout.addWidget(add_btn)
        
        manual_group.setLayout(manual_layout)
        main_layout.addWidget(manual_group)
        
        # 批量导入区域
        batch_group = QGroupBox("批量导入")
        batch_layout = QVBoxLayout()
        
        batch_btn_layout = QHBoxLayout()
        
        import_csv_btn = QPushButton("从CSV导入")
        import_csv_btn.clicked.connect(self.import_from_csv)
        batch_btn_layout.addWidget(import_csv_btn)
        
        import_excel_btn = QPushButton("从Excel导入")
        import_excel_btn.clicked.connect(self.import_from_excel)
        batch_btn_layout.addWidget(import_excel_btn)
        
        batch_layout.addLayout(batch_btn_layout)
        
        # 导入预览表格
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(6)
        self.preview_table.setHorizontalHeaderLabels(['姓名', '身份证号', '性别', '民族', '出生日期', '地址'])
        batch_layout.addWidget(self.preview_table)
        
        # 确认导入按钮
        confirm_btn = QPushButton("确认导入")
        confirm_btn.clicked.connect(self.confirm_import)
        batch_layout.addWidget(confirm_btn)
        
        batch_group.setLayout(batch_layout)
        main_layout.addWidget(batch_group)
        
        main_layout.addStretch()

    def select_collection(self):
        """选择或创建采集任务"""
        dialog = CollectionSelectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_collection_id = dialog.selected_collection_id
            self.db.set_current_collection(self.current_collection_id)
            
            # 更新显示
            collection = self.db.get_collection_by_id(self.current_collection_id)
            if collection:
                self.collection_label.setText(f"{collection.name} ({collection.organization})")
                self.collection_label.setStyleSheet("color: green; font-weight: bold;")
                print(f"[INFO] 已选择采集任务: {collection.name} (ID: {self.current_collection_id})")

    def on_id_changed(self, id_number):
        """身份证号变化时，自动提取出生日期和性别，并进行验证"""
        id_number = id_number.strip()
        
        # 重置输入框样式
        self.id_input.setStyleSheet("")
        
        # 验证身份证号格式
        validation_result = IDCardValidator.validate(id_number)
        
        if not validation_result['valid']:
            # 显示错误提示
            self.id_input.setStyleSheet("border: 2px solid red;")
            return
        
        # 格式正确，继续提取信息
        if len(id_number) >= 14:
            try:
                # 从身份证号提取出生日期
                # 身份证号格式: YYYYMMDD (第7-14位)
                year = int(id_number[6:10])
                month = int(id_number[10:12])
                day = int(id_number[12:14])
                
                # 设置出生日期
                self.birthday_input.setDate(QDate(year, month, day))
            except:
                # 如果提取失败，保持原值
                pass
        
        if len(id_number) >= 17:
            try:
                # 从身份证号提取性别
                # 身份证号格式: 倒数第二位 (第17位)
                # 奇数=男, 偶数=女
                gender_code = int(id_number[16])
                if gender_code % 2 == 1:
                    self.gender_combo.setCurrentIndex(0)  # 男
                else:
                    self.gender_combo.setCurrentIndex(1)  # 女
            except:
                # 如果提取失败，保持原值
                pass

    def add_user(self):
        """添加单个用户"""
        if not self.current_collection_id:
            QMessageBox.warning(self, "警告", "请先选择或创建采集任务")
            return
        
        name = self.name_input.text().strip()
        id_number = self.id_input.text().strip()
        gender = self.gender_combo.currentText()
        nation = self.nation_input.text().strip()
        birthday = self.birthday_input.date().toPyDate()
        address = self.address_input.text().strip()
        
        if not name or not id_number:
            QMessageBox.warning(self, "警告", "姓名和身份证号不能为空")
            return
        
        # 验证身份证号
        validation_result = IDCardValidator.validate(id_number)
        if not validation_result['valid']:
            QMessageBox.warning(self, "警告", f"身份证号验证失败: {validation_result['message']}")
            return
        
        try:
            # 检查是否已存在（在同一采集任务内）
            existing = self.db.get_user_by_id_number(id_number, self.current_collection_id)
            if existing:
                QMessageBox.warning(self, "警告", "该身份证号在当前采集任务中已存在")
                return
            
            # 添加用户
            self.db.add_user(
                name=name,
                id_number=id_number,
                gender=gender,
                nation=nation,
                birthday=birthday,
                address=address,
                collection_id=self.current_collection_id
            )
            
            QMessageBox.information(self, "成功", f"用户 {name} 已添加")
            
            # 通知主窗口更新统计
            self.notify_data_changed()
            
            # 清空输入框
            self.name_input.clear()
            self.id_input.clear()
            self.address_input.clear()
            self.gender_combo.setCurrentIndex(0)
            self.nation_input.setText("汉")
            self.birthday_input.setDate(QDate(1990, 1, 1))
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败: {e}")

    def import_from_csv(self):
        """从CSV导入"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", "", "CSV文件 (*.csv)"
        )
        
        if filepath:
            try:
                self.preview_table.setRowCount(0)
                self.import_data = []
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # 跳过表头
                    
                    for row in reader:
                        if len(row) >= 6:
                            self.preview_table.insertRow(self.preview_table.rowCount())
                            for col, value in enumerate(row[:6]):
                                self.preview_table.setItem(
                                    self.preview_table.rowCount() - 1, col,
                                    QTableWidgetItem(value)
                                )
                            self.import_data.append(row[:6])
                
                QMessageBox.information(self, "成功", f"已加载 {len(self.import_data)} 条记录")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {e}")

    def import_from_excel(self):
        """从Excel导入"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel文件 (*.xlsx *.xls)"
        )
        
        if filepath:
            try:
                import openpyxl
                
                self.preview_table.setRowCount(0)
                self.import_data = []
                
                wb = openpyxl.load_workbook(filepath)
                ws = wb.active
                
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if row[0]:  # 如果第一列不为空
                        self.preview_table.insertRow(self.preview_table.rowCount())
                        for col, value in enumerate(row[:6]):
                            self.preview_table.setItem(
                                self.preview_table.rowCount() - 1, col,
                                QTableWidgetItem(str(value) if value else "")
                            )
                        self.import_data.append(row[:6])
                
                QMessageBox.information(self, "成功", f"已加载 {len(self.import_data)} 条记录")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {e}")

    def confirm_import(self):
        """确认导入"""
        if not self.current_collection_id:
            QMessageBox.warning(self, "警告", "请先选择或创建采集任务")
            return
        
        if not hasattr(self, 'import_data') or not self.import_data:
            QMessageBox.warning(self, "警告", "没有要导入的数据")
            return
        
        try:
            success_count = 0
            fail_count = 0
            error_messages = []  # 记录错误信息
            
            for idx, row in enumerate(self.import_data, 1):
                try:
                    # 支持不同的列数
                    # 最少需要2列（姓名、身份证号）
                    # 最多6列（姓名、身份证号、性别、民族、出生日期、地址）
                    
                    if len(row) < 2:
                        error_messages.append(f"第{idx}行: 数据不足，至少需要姓名和身份证号")
                        fail_count += 1
                        continue
                    
                    # 提取基本信息
                    name = str(row[0]).strip() if row[0] else ""
                    id_number = str(row[1]).strip() if row[1] else ""
                    
                    # 提取可选信息（如果有的话）
                    gender = str(row[2]).strip() if len(row) > 2 and row[2] else None
                    nation = str(row[3]).strip() if len(row) > 3 and row[3] else ""
                    birthday_str = str(row[4]).strip() if len(row) > 4 and row[4] else None
                    address = str(row[5]).strip() if len(row) > 5 and row[5] else ""
                    
                    # 检查必填字段
                    if not name or not id_number:
                        error_messages.append(f"第{idx}行: 姓名或身份证号为空")
                        fail_count += 1
                        continue
                    
                    # 验证身份证号
                    validation_result = IDCardValidator.validate(id_number)
                    if not validation_result['valid']:
                        error_messages.append(f"第{idx}行: 身份证号无效 ({id_number}) - {validation_result['message']}")
                        fail_count += 1
                        continue
                    
                    # 从身份证号提取信息
                    id_info = validation_result['info']
                    
                    # 如果没有提供性别，从身份证号提取
                    if not gender:
                        gender = id_info['gender']
                    
                    # 如果没有提供出生日期，从身份证号提取
                    if not birthday_str:
                        birthday = id_info['birth_date']
                    else:
                        # 转换日期
                        birthday = None
                        try:
                            # 尝试多种日期格式
                            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%d-%m-%Y']:
                                try:
                                    birthday = datetime.strptime(birthday_str, fmt).date()
                                    break
                                except:
                                    continue
                        except Exception as e:
                            print(f"日期转换失败: {birthday_str}, 错误: {e}")
                            birthday = id_info['birth_date']
                    
                    # 检查是否已存在（在同一采集任务内）
                    if self.db.get_user_by_id_number(id_number, self.current_collection_id):
                        error_messages.append(f"第{idx}行: 身份证号已存在 ({id_number})")
                        fail_count += 1
                        continue
                    
                    # 添加用户
                    self.db.add_user(
                        name=name,
                        id_number=id_number,
                        gender=gender,
                        nation=nation,
                        birthday=birthday,
                        address=address,
                        collection_id=self.current_collection_id
                    )
                    success_count += 1
                    print(f"[OK] 第{idx}行导入成功: {name} ({id_number}) - 性别:{gender}, 出生日期:{birthday}")
                    
                except Exception as e:
                    error_messages.append(f"第{idx}行: 导入异常 - {str(e)}")
                    fail_count += 1
                    print(f"[ERROR] 第{idx}行导入失败: {str(e)}")
            
            # 显示详细的导入结果
            result_msg = f"成功导入: {success_count} 条\n失败: {fail_count} 条"
            
            if error_messages:
                result_msg += "\n\n失败原因:\n"
                result_msg += "\n".join(error_messages[:10])  # 只显示前10条错误
                if len(error_messages) > 10:
                    result_msg += f"\n... 还有 {len(error_messages) - 10} 条错误"
            
            QMessageBox.information(self, "导入完成", result_msg)
            
            # 通知主窗口更新统计
            self.notify_data_changed()
            
            self.preview_table.setRowCount(0)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {e}")

    def closeEvent(self, event):
        """关闭事件"""
        self.db.close()
        event.accept()
    
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

