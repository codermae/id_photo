# 高保真商业头像处理架构 (HiFi Pipeline)

## 架构概述

新一代高保真商业头像处理架构，实现专业商业摄影级别的证件照处理效果。

### 核心目标
- ✅ 身份完美保留（包括痣和特征）
- ✅ 头发丝清晰锐利
- ✅ 皮肤干净自然
- ✅ 背景融合自然

## 技术架构

### 1. 人脸检测与身份特征提取（身份锁定层）

**核心模型**: InsightFace (buffalo_l)

**功能**:
- 高精度人脸检测（RetinaFace）
- 68+ 面部地标点定位
- 512 维身份特征向量提取（ArcFace）
- 年龄、性别等属性识别

**作用**:
- 为后续处理提供精确的人脸位置
- 提取身份特征向量，用于 CodeFormer 身份锁定
- 确保处理后"变美但没变样"

**降级方案**: OpenCV Haar Cascade

### 2. 语义分割与保真美颜（可选，当前禁用）

**核心技术**: 轻量级 U-Net + 局部处理

**功能**:
- 皮肤区域精确分割
- 保真祛痘/美白（仅处理瑕疵）
- 完美保留五官、皱纹、痣等身份信息

**当前状态**: 禁用，保持原始皮肤质感

### 3. 头发丝级抠图（细节提取层）⭐ 核心升级

**核心模型**: MODNet (当前使用 rembg 替代)

**功能**:
- Alpha 通道人像抠图
- 完美还原发丝细节
- 保留边缘自然的半透明质感

**优势**:
- 无需后处理即可达到商业级效果
- 支持复杂发型和细节
- 边缘自然过渡

**当前实现**: rembg (isnet-general-use / u2net)
- `alpha_matting=False`: 禁用额外边缘处理，保持原始质感
- `post_process_mask=False`: 禁用后处理，避免质量损失
- 保持原始分辨率，不做上采样

**未来升级**: 集成真正的 MODNet 模型

### 4. 背景合成（融合层）

**核心技术**: Alpha 通道混合

**功能**:
- 使用 Alpha 遮罩进行完美背景合成
- 保持边缘半透明质感
- 自然融合，无明显边界

**实现**:
```python
result = foreground * alpha + background * (1 - alpha)
```

### 5. 保真细节增强（质感提升层）⭐ 核心升级

**核心模型**: CodeFormer (待集成)

**功能**:
- 整体细节重构
- 身份细节锁定与增强（使用 InsightFace embedding）
- 头发纹理锐化
- 眼睛神态增强
- 保留痣等身份标记

**优势**:
- 商业摄影级质感
- 身份完美保留
- 细节清晰锐利

**当前状态**: 待集成

## 处理流程

```
输入图像
    ↓
[Step 1] InsightFace 人脸检测与特征提取
    ├─ 检测人脸位置
    ├─ 提取面部关键点
    └─ 提取身份特征向量 (512维)
    ↓
[Step 2] 跳过美颜处理（保持原始质感）
    ↓
[Step 3] MODNet/rembg 头发丝级抠图
    ├─ 生成 Alpha 通道
    ├─ 保留发丝细节
    └─ 边缘自然过渡
    ↓
[Step 4] Alpha 通道背景合成
    ├─ 创建目标背景
    └─ Alpha 混合
    ↓
[Step 5] CodeFormer 保真增强（可选）
    ├─ 使用身份特征锁定
    ├─ 增强细节质感
    └─ 保留身份标记
    ↓
输出图像
```

## 性能优化

### 当前优化
1. **禁用上采样**: 保持原始分辨率，避免质量损失
2. **禁用 alpha_matting**: 避免额外边缘处理导致的质量下降
3. **禁用后处理**: 保持 rembg 原始输出质量
4. **延迟初始化**: 模型按需加载

### 未来优化
1. **GPU 加速**: 使用 CUDA 加速 InsightFace 和 MODNet
2. **模型量化**: INT8 量化提升 CPU 推理速度
3. **批量处理**: 多线程/多进程并发处理
4. **模型缓存**: 避免重复加载模型

## 模块状态

| 模块 | 状态 | 说明 |
|------|------|------|
| InsightFace | ✅ 已集成 | buffalo_l 模型，CPU 推理 |
| MODNet | ⚠️ 使用 rembg 替代 | 待集成真正的 MODNet |
| CodeFormer | ❌ 待集成 | 可选功能，用于细节增强 |

## 使用示例

```python
from controllers.hifi_pipeline import HiFiPipeline
import cv2

# 初始化管线
pipeline = HiFiPipeline()
pipeline.initialize()

# 加载图像
image = cv2.imread('input.jpg')

# 处理图像
result, info = pipeline.process(
    image,
    bg_color=(255, 255, 255),  # 白色背景
    use_codeformer=False        # 暂不使用 CodeFormer
)

# 保存结果
cv2.imwrite('output.jpg', result)

# 查看处理信息
print("处理步骤:", info['steps'])
print("人脸信息:", info['face_info'])
```

## 依赖项

```
insightface>=0.7.3       # 人脸检测与特征提取
rembg>=2.0.0             # 背景移除（MODNet 替代）
onnxruntime>=1.23.0      # ONNX 推理引擎
opencv-python>=4.5.0     # 图像处理
numpy>=1.26.0            # 数值计算
Pillow>=9.0.0            # 图像 I/O
```

## 未来路线图

### 短期（1-2周）
- [ ] 优化 rembg 参数，提升抠图质量
- [ ] 添加质量检测（眼睛开合、正视检测）
- [ ] 性能基准测试

### 中期（1-2月）
- [ ] 集成真正的 MODNet 模型
- [ ] 集成 CodeFormer 细节增强
- [ ] GPU 加速支持
- [ ] 批量处理优化

### 长期（3-6月）
- [ ] 模型量化（INT8）
- [ ] 自定义模型训练
- [ ] 云端部署方案
- [ ] API 服务化

## 技术支持

如有问题或建议，请联系开发团队。
