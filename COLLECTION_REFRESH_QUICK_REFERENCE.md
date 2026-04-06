# 采集任务下拉框刷新 - 快速参考

## 问题
在数据导入页面创建新采集任务后，身份证读取和图像处理页面的下拉框没有更新。

## 解决方案
已通过信号机制实现自动刷新。

## 工作原理

```
数据导入页面创建新任务
    ↓
发出 collection_changed 信号
    ↓
主窗口接收信号
    ↓
自动调用其他页面的 load_collections() 方法
    ↓
下拉框自动更新
```

## 修改内容

### 1. ImportView 类 (import_view.py)
```python
# 添加信号
collection_changed = pyqtSignal()

# 在 select_collection() 方法中发出信号
self.collection_changed.emit()
```

### 2. MainWindow 类 (main_window.py)
```python
# 连接信号
self.import_view.collection_changed.connect(self.id_card_view.load_collections)
self.import_view.collection_changed.connect(self.process_view.load_collections)
```

## 测试

1. 进入"数据导入"页面
2. 创建新采集任务
3. 切换到"身份证读取"页面 → 下拉框应该显示新任务
4. 切换到"图像处理"页面 → 下拉框应该显示新任务

## 控制台输出

创建新任务后应该看到：
```
[INFO] 已发出采集任务更新信号
```

## 文件修改

- `id_photo_system/views/import_view.py` - 添加信号和发出逻辑
- `id_photo_system/views/main_window.py` - 连接信号

## 验证

✅ 无语法错误
✅ 信号正确定义
✅ 信号正确连接
✅ 自动刷新功能已实现
