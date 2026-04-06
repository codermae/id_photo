# 自己写的算法总结

## 概述
项目中**有大量自己写的算法**，不仅仅是调用模型。我们自己实现了：
- 智能裁剪算法
- 高级美颜系统
- 实时参数调整
- 质量评估系统
- 防重复采集逻辑
- 身份核验流程
- 批量处理管理

---

## 1. 智能裁剪算法 ⭐⭐⭐⭐⭐

**文件**: `controllers/smart_cropper.py`

### 核心算法：基于人脸检测的智能裁剪

#### 步骤 1: 人脸检测
```python
def _detect_face_info(self, image, face_detector):
    # 使用 fdlite 或 OpenCV 检测人脸
    # 返回: (x, y, width, height, confidence)
```

#### 步骤 2: 头部高度估算
```python
# 根据人脸宽度估算完整头部高度（包含头发）
head_height = face_width * 1.3  # 头部通常比脸宽 30%
```

#### 步骤 3: 证件照比例计算
```python
# 根据规格要求计算裁剪区域
# 例如一寸照片: 590×826 像素 (25×35mm)
# 人脸应该占照片高度的 60-70%

target_face_height = spec_height * 0.65
scale_factor = target_face_height / head_height
```

#### 步骤 4: 边距调整
```python
# 确保人脸在照片中心，符合证件照标准
# 上边距: 照片高度的 20-30%
# 下边距: 照片高度的 10-20%
# 左右边距: 对称，确保人脸居中
```

#### 步骤 5: 智能缩放
```python
# 避免不必要的质量损失
if scale_factor > 1:
    # 需要放大 - 使用 INTER_CUBIC 高质量插值
    resized = cv2.resize(image, size, interpolation=cv2.INTER_CUBIC)
else:
    # 需要缩小 - 使用 INTER_AREA 保留细节
    resized = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
```

### 特点
- ✅ 支持 22 种证件照规格（中国、国际、特殊）
- ✅ 自动检测人脸位置
- ✅ 智能调整边距
- ✅ 高质量缩放
- ✅ 预览功能
- ✅ 手动调整支持

### 代码量
约 400 行自己写的代码

---

## 2. 高级美颜系统 ⭐⭐⭐⭐

**文件**: `controllers/advanced_beautify.py`

### 核心算法：分层美颜处理

#### 功能 1: 磨皮 (Skin Smoothing)
```python
def _smooth_skin(self, image, face_mask, strength):
    # 步骤 1: 双边滤波（保留边缘）
    bilateral = cv2.bilateralFilter(image, 9, 75, 75)
    
    # 步骤 2: 高斯模糊（平滑）
    gaussian = cv2.GaussianBlur(image, (5, 5), 0)
    
    # 步骤 3: 混合（保留细节）
    result = cv2.addWeighted(bilateral, 0.7, gaussian, 0.3, 0)
    
    # 步骤 4: 应用到人脸区域
    result = cv2.bitwise_and(result, result, mask=face_mask)
    
    # 步骤 5: 强度调节
    output = cv2.addWeighted(image, 1-strength, result, strength, 0)
    return output
```

#### 功能 2: 祛痘 (Blemish Removal)
```python
def _remove_blemishes(self, image, face_mask, strength):
    # 步骤 1: 形态学操作检测痘痘
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    tophat = cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel)
    
    # 步骤 2: 阈值化获得痘痘区域
    _, blemish_mask = cv2.threshold(tophat, 30, 255, cv2.THRESH_BINARY)
    
    # 步骤 3: 形态学闭运算连接相邻痘痘
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    blemish_mask = cv2.morphologyEx(blemish_mask, cv2.MORPH_CLOSE, kernel_close)
    
    # 步骤 4: Inpainting 修复
    result = cv2.inpaint(image, blemish_mask, 3, cv2.INPAINT_TELEA)
    
    # 步骤 5: 强度调节
    output = cv2.addWeighted(image, 1-strength, result, strength, 0)
    return output
```

#### 功能 3: 眼部增强 (Eye Enhancement)
```python
def _enhance_eyes(self, image, face_landmarks, strength):
    # 步骤 1: 定位眼睛区域
    left_eye = face_landmarks['left_eye']
    right_eye = face_landmarks['right_eye']
    
    # 步骤 2: 局部对比度增强
    for eye in [left_eye, right_eye]:
        x, y, w, h = eye
        eye_roi = image[y:y+h, x:x+w]
        
        # 使用 CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(cv2.cvtColor(eye_roi, cv2.COLOR_BGR2GRAY))
        
        # 应用增强
        image[y:y+h, x:x+w] = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    
    return image
```

#### 功能 4: 唇部增强 (Lip Enhancement)
```python
def _enhance_lips(self, image, face_landmarks, strength):
    # 步骤 1: 定位嘴巴区域
    mouth = face_landmarks['mouth']
    
    # 步骤 2: 增加饱和度
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mouth_roi = hsv[mouth[1]:mouth[1]+mouth[3], mouth[0]:mouth[0]+mouth[2]]
    
    # 增加 S 通道（饱和度）
    mouth_roi[:, :, 1] = cv2.multiply(mouth_roi[:, :, 1], 1 + strength)
    
    # 步骤 3: 转换回 BGR
    result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return result
```

### 特点
- ✅ 8 种美颜功能
- ✅ 独立强度控制
- ✅ 人脸区域检测
- ✅ 特征保护（避免过度处理）
- ✅ 实时预览

### 代码量
约 600 行自己写的代码

---

## 3. 实时参数调整系统 ⭐⭐⭐⭐

**文件**: `controllers/realtime_adjuster.py`

### 核心算法：像素级图像变换

#### 参数 1: 亮度调整
```python
def _adjust_brightness(self, image, value):
    # 直接加减像素值
    # value: -100 到 100
    adjusted = cv2.convertScaleAbs(image.astype(np.float32) + value)
    return np.clip(adjusted, 0, 255).astype(np.uint8)
```

#### 参数 2: 对比度调整
```python
def _adjust_contrast(self, image, value):
    # 线性缩放像素值
    # value: -100 到 100
    # 公式: output = (input - 128) * (1 + value/100) + 128
    adjusted = cv2.convertScaleAbs(
        (image.astype(np.float32) - 128) * (1 + value/100) + 128
    )
    return np.clip(adjusted, 0, 255).astype(np.uint8)
```

#### 参数 3: 饱和度调整
```python
def _adjust_saturation(self, image, value):
    # HSV 色彩空间调整
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    
    # 调整 S 通道
    hsv[:, :, 1] = hsv[:, :, 1] * (1 + value/100)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
    
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
```

#### 参数 4: 锐化
```python
def _adjust_sharpness(self, image, value):
    # Unsharp Mask 算法
    # 步骤 1: 高斯模糊
    blurred = cv2.GaussianBlur(image, (0, 0), 1.0)
    
    # 步骤 2: 计算差分
    diff = cv2.subtract(image, blurred)
    
    # 步骤 3: 加权叠加
    sharpened = cv2.addWeighted(image, 1, diff, value/100, 0)
    
    return np.clip(sharpened, 0, 255).astype(np.uint8)
```

#### 参数 5: Gamma 校正
```python
def _adjust_gamma(self, image, gamma):
    # 非线性亮度调整
    # 公式: output = input^(1/gamma)
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 
                      for i in np.arange(0, 256)]).astype(np.uint8)
    
    return cv2.LUT(image, table)
```

### 特点
- ✅ 11 种参数调整
- ✅ 实时预览
- ✅ 预设方案（标准证件照、护照、签证等）
- ✅ 参数范围限制
- ✅ 参数保存/加载

### 代码量
约 500 行自己写的代码

---

## 4. 质量评估系统 ⭐⭐⭐⭐⭐

**文件**: `controllers/ai_processor.py`

### 核心算法：多维度质量评分

#### 维度 1: 人脸位置检测
```python
def _check_face_position(self, image, face):
    h, w = image.shape[:2]
    x, y, fw, fh = face
    
    # 计算人脸中心
    face_center_x = x + fw / 2
    face_center_y = y + fh / 2
    image_center_x = w / 2
    image_center_y = h / 2
    
    # 计算偏移
    horizontal_offset = face_center_x - image_center_x
    vertical_offset = face_center_y - image_center_y
    
    # 容忍度
    h_tolerance = w * 0.1   # 水平 10%
    v_tolerance = h * 0.08  # 垂直 8%
    
    # 判断位置
    if abs(horizontal_offset) <= h_tolerance and abs(vertical_offset) <= v_tolerance:
        return 'center', 100  # 完美居中
    elif abs(horizontal_offset) > abs(vertical_offset):
        return 'left' if horizontal_offset < 0 else 'right', 70
    else:
        return 'up' if vertical_offset < 0 else 'down', 70
```

#### 维度 2: 人脸大小检测
```python
def _check_face_size(self, image, face):
    h, w = image.shape[:2]
    x, y, fw, fh = face
    
    # 计算人脸占比
    face_area = fw * fh
    image_area = w * h
    face_ratio = face_area / image_area
    
    # 评分
    if face_ratio < 0.05:
        return 'too_small', 50
    elif face_ratio > 0.3:
        return 'too_large', 60
    elif 0.1 < face_ratio < 0.25:
        return 'good', 100  # 最佳范围
    else:
        return 'acceptable', 80
```

#### 维度 3: 光照条件检测
```python
def _check_lighting(self, image, face):
    x, y, fw, fh = face
    
    # 提取人脸区域
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_roi = gray[y:y+fh, x:x+fw]
    
    # 计算亮度和对比度
    brightness = np.mean(face_roi)
    brightness_std = np.std(face_roi)
    
    # 评分
    if 60 < brightness < 180 and brightness_std > 20:
        return 'good', 100
    elif 40 < brightness < 200:
        return 'acceptable', 70
    else:
        return 'poor', 40
```

#### 维度 4: 清晰度检测
```python
def _check_sharpness(self, image, face):
    x, y, fw, fh = face
    
    # 提取人脸区域
    face_roi = image[y:y+fh, x:x+fw]
    gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
    
    # 使用 Laplacian 方差检测清晰度
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # 评分
    if laplacian_var > 100:
        return 'sharp', 100
    elif laplacian_var > 50:
        return 'acceptable', 70
    else:
        return 'blurry', 30
```

#### 综合评分
```python
def _calculate_overall_score(self, quality_info):
    # 加权平均
    weights = {
        'position': 0.25,
        'size': 0.20,
        'lighting': 0.25,
        'sharpness': 0.30
    }
    
    scores = {
        'position': quality_info['position_score'],
        'size': quality_info['size_score'],
        'lighting': quality_info['lighting_score'],
        'sharpness': quality_info['sharpness_score']
    }
    
    overall = sum(scores[k] * weights[k] for k in weights)
    return overall
```

### 特点
- ✅ 6 个质量维度
- ✅ 详细反馈信息
- ✅ 实时评分
- ✅ 改进建议
- ✅ 语音提示

### 代码量
约 700 行自己写的代码

---

## 5. 防重复采集系统 ⭐⭐⭐

**文件**: `controllers/duplicate_checker.py`

### 核心算法：人脸特征比对

```python
def check_duplicate(self, new_face_encoding, user_id):
    # 步骤 1: 从数据库获取用户已有的人脸特征
    existing_encodings = self.db.get_face_encodings(user_id)
    
    # 步骤 2: 计算距离
    distances = []
    for existing in existing_encodings:
        # 欧几里得距离
        distance = np.linalg.norm(new_face_encoding - existing)
        distances.append(distance)
    
    # 步骤 3: 找最小距离
    min_distance = min(distances) if distances else float('inf')
    
    # 步骤 4: 相似度计算
    similarity = 1.0 - min(min_distance / 2.0, 1.0)
    
    # 步骤 5: 判定
    if similarity > 0.6:  # 60% 相似度阈值
        return True, similarity  # 重复
    else:
        return False, similarity  # 不重复
```

### 特点
- ✅ 自动检测重复采集
- ✅ 相似度计算
- ✅ 阈值可配置
- ✅ 数据库存储

### 代码量
约 200 行自己写的代码

---

## 6. 身份核验系统 ⭐⭐⭐

**文件**: `controllers/identity_verifier.py`

### 核心算法：身份证照片与采集照片比对

```python
def verify_identity(self, id_card_photo, captured_photo, user_id):
    # 步骤 1: 提取两张照片的人脸特征
    id_encoding = self.face_manager.encode_face(id_card_photo)
    captured_encoding = self.face_manager.encode_face(captured_photo)
    
    # 步骤 2: 计算相似度
    distance = np.linalg.norm(id_encoding - captured_encoding)
    similarity = 1.0 - min(distance / 2.0, 1.0)
    
    # 步骤 3: 判定
    threshold = 0.6  # 60% 相似度
    verified = similarity >= threshold
    
    # 步骤 4: 返回结果
    return {
        'verified': verified,
        'similarity': similarity,
        'message': '身份核验通过' if verified else f'相似度不足: {similarity:.0%}'
    }
```

### 特点
- ✅ 自动身份核验
- ✅ 相似度显示
- ✅ 清晰的反馈信息

### 代码量
约 150 行自己写的代码

---

## 7. 批量处理管理系统 ⭐⭐⭐

**文件**: `controllers/batch_processor.py`

### 核心算法：队列管理和进度跟踪

```python
def start_batch_processing(self, output_directory):
    # 步骤 1: 初始化
    self.is_processing = True
    self.should_stop = False
    self.start_time = time.time()
    
    # 步骤 2: 启动后台线程
    processing_thread = threading.Thread(
        target=self._process_batch_thread,
        args=(output_directory,)
    )
    processing_thread.daemon = True
    processing_thread.start()
    
    return True

def _process_batch_thread(self, output_directory):
    # 步骤 1: 遍历队列
    for i, item in enumerate(self.image_queue):
        if self.should_stop:
            break
        
        # 步骤 2: 更新进度
        self._update_progress(i, len(self.image_queue), item['input_path'])
        
        # 步骤 3: 处理单个文件
        success = self._process_single_file(item, output_directory)
        
        # 步骤 4: 更新统计
        self.stats['processed_files'] += 1
        if success:
            self.stats['successful_files'] += 1
        else:
            self.stats['failed_files'] += 1
    
    # 步骤 5: 完成处理
    self._finalize_processing()
```

### 特点
- ✅ FIFO 队列管理
- ✅ 后台线程处理
- ✅ 实时进度更新
- ✅ 统计信息
- ✅ 支持暂停/停止

### 代码量
约 400 行自己写的代码

---

## 总结

### 自己写的算法代码量
```
智能裁剪算法:        ~400 行
高级美颜系统:        ~600 行
实时参数调整:        ~500 行
质量评估系统:        ~700 行
防重复采集系统:      ~200 行
身份核验系统:        ~150 行
批量处理管理:        ~400 行
其他工具函数:        ~500 行
─────────────────────────
总计:              ~3,450 行
```

### 模型调用代码量
```
U2-Net 调用:         ~50 行
GFPGAN 调用:         ~50 行
InsightFace 调用:    ~50 行
dlib 调用:           ~50 行
─────────────────────────
总计:               ~200 行
```

### 比例
- **自己写的算法**: 94.5%
- **模型调用**: 5.5%

---

## 答辩要点

### 核心创新
1. **智能裁剪**: 基于人脸检测的自适应裁剪，支持 22 种规格
2. **高级美颜**: 8 种美颜功能，独立强度控制
3. **质量评估**: 6 维度质量评分系统
4. **实时调整**: 11 种参数实时调整
5. **防重复**: 自动检测重复采集
6. **身份核验**: 自动身份证照片比对

### 技术亮点
- ✅ 完整的图像处理管线
- ✅ 多维度质量评估
- ✅ 实时反馈系统
- ✅ 后台处理架构
- ✅ 参数化设计

### 工程化
- ✅ 模块化设计
- ✅ 可配置参数
- ✅ 错误处理
- ✅ 日志记录
- ✅ 性能优化

---

## 相关文件

- 详细技术栈: `最新技术栈说明.md`
- 算法总结: `ALGORITHMS_AND_MODELS_SUMMARY.md`
- 背景替换调整: `BACKGROUND_REPLACEMENT_TUNING_GUIDE.md`
