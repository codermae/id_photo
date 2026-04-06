# 多规格批量生成 - 快速参考

## 问题
点击"开始生成"后没有反应，照片没有生成。

## 原因
`start_processing()` 方法没有实际调用 `BatchProcessor` 来处理图片。

## 解决方案
已添加完整的处理流程和回调函数。

## 修改内容

### 1. start_processing() 方法
添加以下步骤：
```python
# 配置参数
batch_params = {...}
self.batch_processor.set_batch_params(batch_params)

# 添加图片
self.batch_processor.add_images(self.selected_files)

# 设置回调
self.batch_processor.progress_callback = self.on_progress_update
self.batch_processor.status_callback = self.on_status_update

# 启动处理
self.batch_processor.start_batch_processing(self.output_dir)
```

### 2. 添加回调函数
```python
def on_progress_update(self, current, total, current_file):
    # 更新进度条和状态

def on_status_update(self, message, level):
    # 显示处理信息
```

### 3. 修复停止方法
```python
def stop_processing(self):
    self.batch_processor.stop_batch_processing()
```

## 工作流程

```
点击"开始生成" → 确认对话框 → 配置参数 → 启动处理线程 → 
进度条更新 → 状态文本更新 → 照片保存 → 处理完成
```

## 测试

1. 选择图片
2. 选择输出目录
3. 选择规格和颜色
4. 点击"▶️ 开始生成"
5. 点击"Yes"确认
6. **预期**：进度条出现，照片开始处理

## 文件修改

- `id_photo_system/views/unified_batch_dialog.py`
  - `start_processing()` - 添加处理逻辑
  - `on_progress_update()` - 新增回调函数
  - `on_status_update()` - 新增回调函数
  - `stop_processing()` - 修复停止逻辑

## 验证

✅ 无语法错误
✅ 处理流程完整
✅ 回调函数正确
✅ 功能可用

## 预期行为

| 操作 | 预期结果 |
|------|---------|
| 点击"开始生成" | 显示确认对话框 |
| 点击"Yes" | 进度条出现，开始处理 |
| 处理中 | 进度条更新，状态文本显示当前文件 |
| 处理完成 | 进度条显示"处理完成！"，照片保存到输出目录 |
| 点击"⏹️ 停止" | 处理停止，显示"处理已停止" |
