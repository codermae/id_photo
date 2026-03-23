# 证件照采集系统 - 项目指南

## 项目概述
这是一个基于PyQt5的证件照采集和处理系统，支持身份证读取、摄像头拍照、人脸识别、图像处理和批量处理等功能。

## 快速开始

### 1. 环境要求
- Python 3.8+
- Windows 10/11
- 摄像头设备
- 身份证读卡器（可选）

### 2. 安装依赖
```bash
cd id_photo_system
pip install -r requirements.txt
```

### 3. 启动系统
```bash
python main.py
```

或者直接运行：
```bash
python START_NOW.py
```

## 主要功能

### 1. 身份证读取
- 支持身份证读卡器
- 自动提取姓名、身份证号、照片等信息
- 防止重复保存（检查身份证号）
- 保存后自动清空用户选择

### 2. 摄像头拍照
- 实时预览
- 人脸检测和质量评分
- 身份核验（与身份证照片对比）
- 相似度显示（持久化显示）
- 快速打开优化（640x480分辨率）

### 3. 图像处理
- **裁剪规格**: 一寸、二寸、小二寸、大一寸、五寸
- **背景替换**: 
  - 智能模式（AI模型，效果好）
  - 精细模式（AI+边缘优化，处理头发丝）
- **美颜功能**:
  - 磨皮（可调强度）
  - 祛痘（可调强度，保护眼睛/眉毛/嘴巴）
- **调整参数**:
  - 亮度调节
  - 对比度调节
- **手动裁剪**: 支持自定义裁剪框

### 4. 批量处理
- 批量导入图片
- 统一处理参数
- 进度显示
- 错误处理

### 5. 采集任务管理
- 创建采集任务
- 任务状态跟踪
- 统计信息

## 核心算法

### 背景替换
- **智能模式**: 使用rembg U2-Net模型，AI抠图
- **精细模式**: AI模型 + 多尺度边缘优化 + 头发丝处理

### 美颜处理
- **磨皮**: 双边滤波，保护眼睛/嘴巴/鼻孔
- **祛痘**: 
  - 形态学Top-Hat和Black-Hat检测
  - cv2.inpaint修复
  - 保护区域：眼睛30px、眉毛20x10、嘴巴30x15

### 人脸识别
- 使用OpenCV Haar级联分类器
- 支持人脸检测和质量评分
- 身份核验相似度计算

## 项目结构

```
id_photo_system/
├── main.py                 # 主程序入口
├── START_NOW.py           # 快速启动脚本
├── requirements.txt       # 依赖列表
├── config/               # 配置文件
├── controllers/          # 控制器（业务逻辑）
│   ├── ai_processor.py          # AI处理器
│   ├── advanced_beautify.py     # 高级美颜
│   ├── background_replacer.py   # 背景替换
│   ├── batch_processor.py       # 批量处理
│   ├── camera.py               # 摄像头控制
│   ├── id_card_reader.py       # 身份证读取
│   └── image_processor.py      # 图像处理
├── models/              # 数据模型
├── views/               # 视图（UI界面）
│   ├── main_window.py          # 主窗口
│   ├── id_card_view.py         # 身份证读取界面
│   ├── camera_view.py          # 摄像头界面
│   ├── process_view.py         # 图像处理界面
│   ├── crop_dialog.py          # 裁剪对话框
│   └── batch_processing_dialog.py  # 批量处理对话框
├── utils/               # 工具类
├── data/                # 数据存储
│   ├── database/       # 数据库文件
│   └── photos/         # 照片存储
└── resources/          # 资源文件
```

## 数据库结构

### users 表
- id: 主键
- name: 姓名
- id_number: 身份证号（唯一）
- gender: 性别
- birth_date: 出生日期
- address: 地址
- created_at: 创建时间

### photos 表
- id: 主键
- user_id: 用户ID（外键）
- photo_type: 照片类型（id_card/captured/processed）
- file_path: 文件路径
- file_size: 文件大小
- created_at: 创建时间

### collection_tasks 表
- id: 主键
- name: 任务名称
- organization: 组织单位
- start_date: 开始日期
- end_date: 结束日期
- status: 状态（active/completed/cancelled）
- created_at: 创建时间

### collection_records 表
- id: 主键
- user_id: 用户ID（外键）
- collection_id: 采集任务ID（外键）
- operator: 操作员
- status: 状态（pending/completed/failed）
- notes: 备注
- created_at: 创建时间

## 配置说明

### config/config.py
```python
# 摄像头配置
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# 人脸检测配置
FACE_DETECTION_MODEL = 'haarcascade_frontalface_alt2.xml'
MIN_FACE_SIZE = (100, 100)

# 图像处理配置
DEFAULT_PHOTO_SPEC = '一寸'
DEFAULT_BG_COLOR = '白色'
DEFAULT_BG_MODE = 'auto'

# 美颜配置
DEFAULT_SMOOTH_STRENGTH = 0.3
DEFAULT_BLEMISH_STRENGTH = 0.5
```

## 常见问题

### 1. 摄像头打不开
- 检查摄像头是否被其他程序占用
- 尝试修改CAMERA_INDEX（0, 1, 2...）
- 检查摄像头驱动是否正常

### 2. 身份证读卡器无法识别
- 检查读卡器驱动是否安装
- 确认读卡器型号是否支持
- 查看系统日志获取详细错误信息

### 3. 背景替换效果不好
- 使用"精细模式"处理头发丝
- 确保光线充足，背景简单
- 避免复杂背景和阴影

### 4. 祛痘没效果
- 提高祛痘强度（0.7-1.0）
- 确保人脸检测成功
- 检查图片质量和分辨率

### 5. 批量处理速度慢
- 使用"智能模式"而非"精细模式"
- 减少美颜选项
- 关闭不必要的参数调整

## 性能优化建议

1. **摄像头优化**
   - 使用640x480分辨率（已优化）
   - 启用快速模式
   - 减少预览帧率

2. **图像处理优化**
   - 批量处理时使用智能模式
   - 避免过高的美颜强度
   - 合理设置图片质量

3. **数据库优化**
   - 定期清理过期数据
   - 建立必要的索引
   - 使用事务批量操作

## 更新日志

### 最新版本
- ✓ 修复祛痘功能误删眼睛问题（扩大保护区域）
- ✓ 移除快速模式（质量差）
- ✓ 优化摄像头打开速度
- ✓ 修复身份核验相似度显示问题
- ✓ 添加采集任务ID支持
- ✓ 防止重复保存用户信息
- ✓ 身份证拿走后自动清空用户选择

## 技术支持

如有问题，请查看：
1. 系统日志（控制台输出）
2. 数据库日志
3. 错误提示信息

## 许可证
本项目仅供学习和研究使用。
