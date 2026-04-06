# 进度条显示 - 快速参考

## 问题
处理完成后，进度条仍停留在三分之二位置，而不是 100%。

## 原因
进度条最大值设置为生成的照片总数（126），但进度值只更新到原始图片数（3）。

## 解决方案

### 1. 保存总数信息
```python
self.total_photos = total  # 126
self.per_image_count = per_image  # 42
```

### 2. 修改进度计算
```python
def on_progress_update(self, current, total, current_file):
    # 计算已处理的照片总数
    completed_photos = current * self.per_image_count
    
    # 更新进度条
    self.progress_bar.setValue(completed_photos)
    percentage = (completed_photos / self.total_photos * 100)
    self.progress_bar.setFormat(f"处理中... {percentage:.1f}% ({completed_photos}/{self.total_photos})")
```

### 3. 完成时设置 100%
```python
def on_status_update(self, message, level):
    if level == 'success' or '完成' in message:
        self.progress_bar.setValue(self.total_photos)
        self.progress_bar.setFormat(f"处理完成！ 100% ({self.total_photos}/{self.total_photos})")
```

## 进度计算示例

3张图片 × 7规格 × 6颜色 = 126张照片

| 原始图片 | 已生成照片 | 进度 |
|---------|----------|------|
| 0/3 | 0/126 | 0% |
| 1/3 | 42/126 | 33.3% |
| 2/3 | 84/126 | 66.7% |
| 3/3 | 126/126 | 100% |

## 文件修改

- `id_photo_system/views/unified_batch_dialog.py`
  - `start_processing()` - 保存总数
  - `on_progress_update()` - 修改计算
  - `on_status_update()` - 设置 100%

## 验证

✅ 无语法错误
✅ 进度计算正确
✅ 完成时显示 100%
✅ 功能可用

## 预期行为

| 阶段 | 进度条 |
|------|--------|
| 开始 | 0% (0/126) |
| 第1张完成 | 33.3% (42/126) |
| 第2张完成 | 66.7% (84/126) |
| 完成 | 100% (126/126) ✓ |
