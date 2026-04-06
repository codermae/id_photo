# 采集任务下拉框自动刷新修复

## 问题描述
在数据导入页面创建新的采集任务后，身份证读取页面和图像处理页面的采集任务下拉框没有自动更新，仍然显示旧的任务列表。

## 根本原因
- 数据导入页面创建新任务后，只通知了主窗口更新统计信息
- 但没有通知其他页面（身份证读取、图像处理）刷新采集任务列表
- 其他页面的下拉框只在初始化时加载一次，之后不会自动更新

## 解决方案

### 1. 在 ImportView 中添加信号
**文件**: `id_photo_system/views/import_view.py`

```python
from PyQt5.QtCore import Qt, QDate, pyqtSignal  # ← 添加 pyqtSignal

class ImportView(QWidget):
    """数据导入视图"""
    
    # 定义信号：当采集任务被创建或更新时发出
    collection_changed = pyqtSignal()  # ← 新增
```

### 2. 在创建新任务后发出信号
**文件**: `id_photo_system/views/import_view.py` 的 `select_collection()` 方法

```python
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
            
            # 发出信号，通知其他页面刷新采集任务列表
            self.collection_changed.emit()  # ← 新增
            print("[INFO] 已发出采集任务更新信号")  # ← 新增
```

### 3. 在主窗口连接信号
**文件**: `id_photo_system/views/main_window.py` 的 `init_ui()` 方法

```python
# 连接数据导入的采集任务更新信号到其他页面
self.import_view.collection_changed.connect(self.id_card_view.load_collections)  # ← 新增
self.import_view.collection_changed.connect(self.process_view.load_collections)  # ← 新增
```

## 工作流程

```
用户在数据导入页面创建新采集任务
    ↓
CollectionSelectionDialog.create_new() 创建任务
    ↓
ImportView.select_collection() 被调用
    ↓
发出 collection_changed 信号
    ↓
主窗口接收信号
    ↓
调用 IDCardView.load_collections() 刷新身份证读取页面
调用 ProcessView.load_collections() 刷新图像处理页面
    ↓
两个页面的下拉框自动更新，显示新创建的采集任务
```

## 测试步骤

1. 启动应用程序
2. 进入"数据导入"页面
3. 点击"选择/创建任务"按钮
4. 在对话框中填写新任务信息
5. 点击"创建新任务"按钮
6. 查看控制台输出：应该看到 `[INFO] 已发出采集任务更新信号`
7. 切换到"身份证读取"页面
8. 查看采集任务下拉框：应该显示新创建的任务
9. 切换到"图像处理"页面
10. 查看采集任务下拉框：应该显示新创建的任务

## 控制台输出示例

```
[INFO] 已选择采集任务: 新任务 (ID: 5)
[INFO] 已发出采集任务更新信号
[DEBUG] 采集任务切换: index=0, collection_id=5
[DEBUG] 采集任务切换: index=0, collection_id=5
```

## 修改的文件

1. `id_photo_system/views/import_view.py`
   - 添加 `pyqtSignal` 导入
   - 添加 `collection_changed` 信号
   - 在 `select_collection()` 方法中发出信号

2. `id_photo_system/views/main_window.py`
   - 添加信号连接到 `id_card_view.load_collections`
   - 添加信号连接到 `process_view.load_collections`

## 优势

1. **自动刷新**: 创建新任务后，其他页面自动更新
2. **实时同步**: 所有页面的下拉框保持同步
3. **用户体验**: 用户无需手动刷新或切换页面
4. **可扩展**: 如果将来添加新页面，只需添加一行信号连接

## 相关代码位置

- 信号定义: `id_photo_system/views/import_view.py` 第 ~180 行
- 信号发出: `id_photo_system/views/import_view.py` 的 `select_collection()` 方法
- 信号连接: `id_photo_system/views/main_window.py` 第 ~95-96 行
- 刷新方法: 
  - `id_photo_system/views/id_card_view.py` 的 `load_collections()` 方法
  - `id_photo_system/views/process_view.py` 的 `load_collections()` 方法

## 后续改进

如果需要进一步改进，可以考虑：

1. **添加更多信号**
   - 用户被添加时刷新用户列表
   - 用户被删除时刷新用户列表

2. **添加更多连接**
   - 连接到其他需要刷新的页面（如数据管理、统计报表）

3. **集中管理信号**
   - 创建一个信号管理器类，统一管理所有跨页面信号

## 验证清单

- [x] 添加 `pyqtSignal` 导入
- [x] 定义 `collection_changed` 信号
- [x] 在创建新任务后发出信号
- [x] 在主窗口连接信号到其他页面
- [x] 测试信号是否正确发出
- [x] 测试其他页面是否正确刷新
- [x] 验证没有语法错误
