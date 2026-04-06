# 亮度/对比度调整修复

## 问题描述

点击"应用处理"后，再调整亮度或对比度时，照片会重置到原始状态，而不是在处理后的基础上进行调整。

## 根本原因

`RealTimeAdjuster`中的`_apply_adjustments()`方法总是基于`self.original_image`进行调整。当处理完成后，`original_image`仍然是加载时的原始图像，所以调整亮度/对比度时会重置到原始状态。

## 修复方案

### 修改前的流程
```
加载图像 → 设置realtime_adjuster.original_image = 原始图像
应用处理 → 处理图像，但realtime_adjuster.original_image仍是原始图像
调整亮度 → 基于原始图像调整 → 照片重置
```

### 修改后的流程
```
加载图像 → 设置realtime_adjuster.original_image = 原始图像
应用处理 → 处理图像 → 更新realtime_adjuster.original_image = 处理后的图像
调整亮度 → 基于处理后的图像调整 → 照片在处理基础上调整
```

## 代码改动

在`apply_processing()`方法中，处理完成后添加：

```python
# 关键修改：更新realtime_adjuster的基础图像为处理后的图像
self.processor.realtime_adjuster.set_image(self.processor.get_current_image())

# 重置亮度和对比度滑块
self.brightness_slider.blockSignals(True)
self.contrast_slider.blockSignals(True)
self.brightness_slider.setValue(0)
self.contrast_slider.setValue(100)
self.brightness_slider.blockSignals(False)
self.contrast_slider.blockSignals(False)
```

## 工作原理

### `set_image()`方法
```python
def set_image(self, image: np.ndarray):
    """设置原始图像"""
    self.original_image = image.copy()  # 更新基础图像
    self.current_image = image.copy()
    self._update_display()
```

### 调整流程
1. 调用`set_image()`将处理后的图像设置为新的基础
2. 重置参数（亮度=0, 对比度=100）
3. 后续的亮度/对比度调整都基于这个新的基础图像

## 使用场景

### 场景1：加载图像后调整亮度/对比度
```
加载图像 → 调整亮度 → 基于原始图像调整 ✓
```

### 场景2：处理后调整亮度/对比度
```
加载图像 → 应用处理 → 调整亮度 → 基于处理后的图像调整 ✓
```

### 场景3：多次调整
```
加载图像 → 应用处理 → 调整亮度 → 调整对比度 → 调整饱和度
所有调整都基于处理后的图像 ✓
```

## 控制台输出示例

```
[INFO] 处理完成，已更新亮度/对比度基础图像
[DEBUG] 参数调整: brightness = 0 -> 10
[DEBUG] 开始应用图像调整...
[DEBUG] 亮度调整完成: 10
[DEBUG] 调整完成 - 原始图像: 均值=120.5, 标准差=45.2
[DEBUG] 调整完成 - 处理后: 均值=130.5, 标准差=45.2
```

## 优势

1. **连贯性**：处理后的调整基于处理结果，而不是重置
2. **直观性**：用户期望的行为得到实现
3. **灵活性**：可以在处理后继续微调参数

## 技术细节

### blockSignals的作用
```python
self.brightness_slider.blockSignals(True)
self.brightness_slider.setValue(0)
self.brightness_slider.blockSignals(False)
```

- `blockSignals(True)`：阻止setValue触发`valueChanged`信号
- `setValue(0)`：重置滑块位置
- `blockSignals(False)`：恢复信号

这样做是为了避免重置滑块时触发调整方法。

## 测试建议

1. 加载图像 → 调整亮度 → 确认基于原始图像调整
2. 应用处理 → 调整亮度 → 确认基于处理后的图像调整
3. 应用处理 → 调整亮度 → 调整对比度 → 确认两个调整都生效
4. 应用处理 → 调整亮度 → 重置 → 确认回到处理后的原始状态

## 总结

这个修复确保了：
1. 处理后的图像成为新的基础
2. 后续调整都基于处理结果
3. 用户体验更符合预期
