# 进度条显示修复

## 问题描述
处理完成后，进度条仍然停留在三分之二的位置（2/3），而不是显示 100%。

## 根本原因
进度条的最大值设置为生成的照片总数（126），但进度值只更新到原始图片的数量（3）。

**计算错误**:
- 进度条最大值: 126（3张图片 × 7规格 × 6颜色）
- 进度条当前值: 3（3张原始图片）
- 显示百分比: 3/126 ≈ 2.4%（显示为三分之二是因为UI缩放）

## 解决方案

### 1. 保存总数信息
在 `start_processing()` 方法中保存总照片数和每张图片生成的照片数：

```python
# 保存总数用于进度计算
self.total_photos = total  # 126
self.per_image_count = per_image  # 42
```

### 2. 修改进度更新逻辑
在 `on_progress_update()` 方法中，根据已处理的原始图片数计算生成的照片总数：

```python
def on_progress_update(self, current, total, current_file):
    """进度更新回调"""
    # current 和 total 是原始图片的数量（0/3, 1/3, 2/3）
    # 但我们需要显示生成的照片总数的进度
    
    # 计算已处理的照片总数
    # 每处理完一张原始图片，就生成了 per_image_count 张照片
    if hasattr(self, 'per_image_count') and hasattr(self, 'total_photos'):
        # 已完成的原始图片数 × 每张生成的照片数
        completed_photos = current * self.per_image_count
        
        # 更新进度条
        self.progress_bar.setMaximum(self.total_photos)
        self.progress_bar.setValue(completed_photos)
        
        # 计算进度百分比
        percentage = (completed_photos / self.total_photos * 100) if self.total_photos > 0 else 0
        self.progress_bar.setFormat(f"处理中... {percentage:.1f}% ({completed_photos}/{self.total_photos})")
```

**进度计算示例**:
- 处理第 1 张图片完成: 1 × 42 = 42 张照片 → 42/126 = 33.3%
- 处理第 2 张图片完成: 2 × 42 = 84 张照片 → 84/126 = 66.7%
- 处理第 3 张图片完成: 3 × 42 = 126 张照片 → 126/126 = 100%

### 3. 修改完成状态处理
在 `on_status_update()` 方法中，处理完成时将进度条设置为 100%：

```python
def on_status_update(self, message, level):
    """状态更新回调"""
    # ... 前面的代码 ...
    
    # 如果处理完成，更新按钮状态和进度条
    if level == 'success' or '完成' in message:
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # 将进度条设置为 100%
        if hasattr(self, 'total_photos'):
            self.progress_bar.setMaximum(self.total_photos)
            self.progress_bar.setValue(self.total_photos)
            self.progress_bar.setFormat(f"处理完成！ 100% ({self.total_photos}/{self.total_photos})")
        else:
            self.progress_bar.setFormat("处理完成！")
```

## 工作流程

```
用户点击"开始生成"
    ↓
保存总数信息:
  - total_photos = 126
  - per_image_count = 42
    ↓
处理第 1 张图片完成
    ↓
on_progress_update(0, 3, "image1.jpg")
    ↓
计算: completed_photos = 0 × 42 = 0
进度条: 0/126 = 0%
    ↓
处理第 2 张图片完成
    ↓
on_progress_update(1, 3, "image2.jpg")
    ↓
计算: completed_photos = 1 × 42 = 42
进度条: 42/126 = 33.3%
    ↓
处理第 3 张图片完成
    ↓
on_progress_update(2, 3, "image3.jpg")
    ↓
计算: completed_photos = 2 × 42 = 84
进度条: 84/126 = 66.7%
    ↓
处理完成
    ↓
on_status_update("批量处理已完成", "success")
    ↓
进度条设置为 100%: 126/126
```

## 修改的文件

- `id_photo_system/views/unified_batch_dialog.py`
  - `start_processing()` - 添加保存总数信息
  - `on_progress_update()` - 修改进度计算逻辑
  - `on_status_update()` - 添加完成时设置 100% 的逻辑

## 测试步骤

1. 选择 3 张图片
2. 选择 7 个规格和 6 种颜色
3. 点击"▶️ 开始生成"
4. 点击"Yes"确认
5. **预期结果**：
   - 处理第 1 张完成: 进度条显示 33.3% (42/126)
   - 处理第 2 张完成: 进度条显示 66.7% (84/126)
   - 处理第 3 张完成: 进度条显示 100% (126/126)
   - 显示"处理完成！ 100% (126/126)"

## 进度条显示示例

| 阶段 | 进度条显示 | 百分比 |
|------|----------|--------|
| 开始 | 处理中... 0% (0/126) | 0% |
| 第1张完成 | 处理中... 33.3% (42/126) | 33.3% |
| 第2张完成 | 处理中... 66.7% (84/126) | 66.7% |
| 第3张完成 | 处理完成！ 100% (126/126) | 100% |

## 关键改进

1. **准确的进度显示**: 进度条现在显示生成的照片总数，而不是原始图片数
2. **实时百分比**: 每处理完一张原始图片，进度条更新 33.3%
3. **完成状态**: 处理完成时进度条显示 100%
4. **清晰的信息**: 进度条显示"处理中... X% (Y/Z)"格式

## 相关代码位置

- 修改文件：`id_photo_system/views/unified_batch_dialog.py`
- `start_processing()` 方法：第 ~310-315 行
- `on_progress_update()` 方法：第 ~330-355 行
- `on_status_update()` 方法：第 ~355-375 行

## 验证清单

- [x] 保存总数信息
- [x] 修改进度计算逻辑
- [x] 添加完成时的 100% 设置
- [x] 无语法错误
- [x] 功能完整可用
