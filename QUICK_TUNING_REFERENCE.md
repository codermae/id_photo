# 快速参数调整参考卡

## 文件位置
`id_photo_system/controllers/background_replacer.py`

---

## 关键参数位置

### 位置 1: Alpha Matting 参数（第 210-213 行）
```python
output = self.rembg.remove(
    pil_image, 
    session=self.rembg_session,
    alpha_matting=True,
    alpha_matting_foreground_threshold=235,      # ← 前景阈值
    alpha_matting_background_threshold=5,        # ← 背景阈值
    alpha_matting_erode_size=15                  # ← 腐蚀大小
)
```

### 位置 2: 头发处理参数（第 275-276 行）
```python
hair_shrink = 1  # ← 头发收缩像素数
kernel_hair = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))  # ← 核大小
```

### 位置 3: 身体处理参数（第 352 行）
```python
expand_pixels = 0  # ← 边缘调整（负数=收缩，正数=扩展）
```

### 位置 4: 边缘平滑参数（第 554-555 行）
```python
final_mask = cv2.GaussianBlur(final_mask, (3, 3), 0)  # ← 高斯模糊
_, final_mask = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)  # ← 二值化
```

---

## 快速诊断和修复

### 症状 1: 背景有白边
```
修改方案 A（推荐）:
  alpha_matting_foreground_threshold: 235 → 220
  
修改方案 B:
  alpha_matting_erode_size: 15 → 20
  
修改方案 C:
  expand_pixels: 0 → -3
```

### 症状 2: 头发被切掉
```
修改方案 A（推荐）:
  alpha_matting_foreground_threshold: 235 → 245
  
修改方案 B:
  alpha_matting_erode_size: 15 → 10
  
修改方案 C:
  hair_shrink: 1 → 0
```

### 症状 3: 背景有黑边
```
修改方案 A（推荐）:
  alpha_matting_foreground_threshold: 235 → 245
  
修改方案 B:
  expand_pixels: 0 → 3
  
修改方案 C:
  alpha_matting_erode_size: 15 → 10
```

### 症状 4: 头发不清晰（毛躁）
```
修改方案 A（推荐）:
  GaussianBlur: (3, 3) → (5, 5)
  
修改方案 B:
  alpha_matting_erode_size: 15 → 20
  
修改方案 C:
  hair_shrink: 1 → 2
```

### 症状 5: 衣服边缘模糊
```
修改方案 A（推荐）:
  GaussianBlur: (3, 3) → (1, 1)
  
修改方案 B:
  threshold: 127 → 150
  
修改方案 C:
  alpha_matting_background_threshold: 5 → 10
```

---

## 参数范围速查表

| 参数 | 范围 | 默认 | 增大效果 | 减小效果 |
|------|------|------|---------|---------|
| foreground_threshold | 200-255 | 235 | 保留更多细节 | 更严格裁剪 |
| background_threshold | 1-20 | 5 | 边缘更干净 | 保留更多细节 |
| erode_size | 5-30 | 15 | 边缘更平滑 | 保留更多细节 |
| hair_shrink | 0-3 | 1 | 解决白边 | 保留头发 |
| expand_pixels | -5 to 5 | 0 | 扩展边缘 | 收缩边缘 |
| GaussianBlur | (1,1)-(7,7) | (3,3) | 更平滑 | 更锐利 |
| threshold | 100-180 | 127 | 更严格 | 更宽松 |

---

## 三步快速调整法

### 第 1 步：确定问题
- 白边？→ 方案 A
- 头发丢失？→ 方案 B
- 黑边？→ 方案 C
- 不清晰？→ 方案 D

### 第 2 步：修改参数
编辑对应位置的参数值

### 第 3 步：测试
重新运行程序，处理同一张照片，对比效果

---

## 推荐参数组合

### 保守（保留细节）
```
foreground_threshold=240
background_threshold=3
erode_size=12
hair_shrink=0
expand_pixels=0
GaussianBlur=(3,3)
threshold=127
```

### 平衡（推荐）
```
foreground_threshold=235
background_threshold=5
erode_size=15
hair_shrink=1
expand_pixels=0
GaussianBlur=(3,3)
threshold=127
```

### 激进（优先清晰）
```
foreground_threshold=230
background_threshold=8
erode_size=18
hair_shrink=2
expand_pixels=-2
GaussianBlur=(5,5)
threshold=150
```

---

## 调整技巧

1. **一次只改一个参数**，这样能清楚看到效果
2. **小幅度调整**，通常改 5-10 个单位就能看到明显变化
3. **保存原始参数**，如果效果变差可以快速恢复
4. **使用同一张测试照片**，这样对比效果更准确
5. **查看控制台输出**，了解处理过程

---

## 常见参数调整组合

### 对于浅肤色 + 长发
```
foreground_threshold=240
background_threshold=3
erode_size=12
hair_shrink=0
expand_pixels=0
```

### 对于深肤色 + 短发
```
foreground_threshold=225
background_threshold=8
erode_size=18
hair_shrink=2
expand_pixels=-2
```

### 对于卷发
```
foreground_threshold=225
background_threshold=5
erode_size=22
hair_shrink=1
expand_pixels=0
```

---

## 调试命令

### 保存中间结果（用于调试）
在 `_rembg_segment` 方法中添加：
```python
cv2.imwrite('debug_mask.png', mask)
```

### 查看处理信息
查看控制台输出：
```
[INFO] rembg分割完成（使用原始输出），mask覆盖率: XX.X%
```

---

## 何时需要更高级的调整

如果调整这些参数后效果仍不理想，可能需要：

1. **更换 rembg 模型**
   - 当前: `u2net`
   - 可选: `isnet-general-use`

2. **集成 CodeFormer**
   - 用于人脸细节增强

3. **集成 GFPGAN**
   - 用于人脸质量提升

4. **自定义训练**
   - 针对特定场景微调模型

但通常 95% 的情况下，调整这些参数就能解决问题。

---

## 参数调整检查清单

- [ ] 确认问题类型
- [ ] 选择对应的修改方案
- [ ] 编辑参数
- [ ] 重新运行程序
- [ ] 对比效果
- [ ] 效果改善？继续微调
- [ ] 效果变差？恢复参数，尝试其他方案
- [ ] 找到最佳参数？记录下来

---

## 快速参考

**最常改的 3 个参数**:
1. `alpha_matting_foreground_threshold` - 解决 90% 的问题
2. `expand_pixels` - 解决边缘问题
3. `GaussianBlur` - 调整清晰度

**最常改的值**:
- 白边: `foreground_threshold: 235→220`
- 头发丢失: `foreground_threshold: 235→245`
- 黑边: `expand_pixels: 0→3`
- 不清晰: `GaussianBlur: (3,3)→(5,5)`
