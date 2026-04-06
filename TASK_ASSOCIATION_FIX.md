# 采集任务关联逻辑修复

## 问题描述

1. **用户识别问题**：用户不存在时，保存时只显示简单提示
2. **任务关联问题**：用户应该属于某个采集任务，但系统没有检查这个关联
3. **多规格批量生成**：没有检查采集任务，导致生成的照片无法正确关联

## 修复内容

### 1. 简化用户不存在提示 (process_view.py)

**修改前**：
```python
QMessageBox.warning(
    self, 
    "警告", 
    "无法识别用户信息\n\n请确保加载的图片文件名包含身份证号\n格式: {身份证号}_{时间戳}.jpg"
)
```

**修改后**：
```python
QMessageBox.warning(self, "警告", "用户不存在")
```

### 2. 加强用户-任务关联检查 (process_view.py)

在 `load_image()` 方法中添加检查：
- 加载图像时，验证用户是否属于选定的采集任务
- 如果用户不属于该任务，显示警告并清除 `current_user_id`
- 这样保存时会提示用户选择正确的任务

**关键代码**：
```python
if user:
    # 检查用户是否属于选定的采集任务
    if self.current_collection_id:
        collection = db.get_collection_by_id(self.current_collection_id)
        # 检查用户是否在该采集任务中
        user_in_collection = False
        if collection and hasattr(collection, 'users'):
            user_in_collection = user.id in [u.id for u in collection.users]
        
        if user_in_collection:
            self.current_user_id = user.id
        else:
            self.current_user_id = None
            QMessageBox.warning(
                self,
                "警告",
                f"用户 {user.name} 不属于选定的采集任务\n\n请选择正确的采集任务"
            )
```

### 3. 多规格批量生成共用任务选择 (unified_batch_dialog.py)

修改 `__init__()` 方法：
```python
# 从父窗口（ProcessView）获取采集任务信息
self.parent_view = parent
self.current_collection_id = parent.current_collection_id if parent else None
```

修改 `start_processing()` 方法：
```python
# 检查是否选择了采集任务
if not self.current_collection_id:
    QMessageBox.warning(self, "警告", "请先在图像处理界面选择采集任务")
    return
```

## 使用流程

### 正确的使用流程：

1. **选择采集任务**
   - 在图像处理界面的"任务"下拉框中选择一个采集任务
   - 该任务中应该包含你要处理的用户

2. **加载图像**
   - 选择图片文件（文件名应包含身份证号）
   - 系统会自动识别身份证号并检查用户是否在选定的任务中
   - 如果用户不在该任务中，会显示警告

3. **处理和保存**
   - 处理图像后点击保存
   - 照片会自动关联到选定的采集任务

4. **多规格批量生成**
   - 必须先在图像处理界面选择采集任务
   - 然后点击"多规格批量生成"按钮
   - 系统会使用相同的采集任务来生成照片

## 任务的作用

"任务"（采集任务）的作用：
- **组织用户**：将相关的用户组织在一个采集任务中
- **关联照片**：生成的照片会关联到该采集任务
- **生成报表**：可以按采集任务生成报表统计

## 数据库关系

```
采集任务 (Collection)
  ├─ 用户1 (User)
  │  └─ 照片1, 照片2, ...
  ├─ 用户2 (User)
  │  └─ 照片1, 照片2, ...
  └─ 用户3 (User)
     └─ 照片1, 照片2, ...
```

## 常见问题

**Q: 为什么保存时提示"用户不存在"？**
A: 可能的原因：
1. 图片文件名不包含身份证号
2. 身份证号在数据库中不存在
3. 用户存在但不属于选定的采集任务

**Q: 如何添加新用户到采集任务？**
A: 需要在系统的用户管理界面中添加用户，并将其分配到相应的采集任务。

**Q: 多规格批量生成需要单独选择任务吗？**
A: 不需要。多规格批量生成会使用图像处理界面中已选择的采集任务。
