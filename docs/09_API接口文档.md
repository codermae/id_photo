# 09 API接口文档

## 9.1 数据库操作接口

### 9.1.1 DatabaseHelper类

**位置**: `utils/database_helper.py`

**初始化**:
```python
from utils.database_helper import DatabaseHelper

db = DatabaseHelper()
```

### 9.1.2 采集任务操作

**创建采集任务**:
```python
collection = db.create_collection(
    name="2024年新生入学",
    organization="某某大学",
    description="2024级新生证件照采集",
    start_date=date(2024, 9, 1),
    end_date=date(2024, 9, 30)
)
# 返回: Collection对象
```

**获取采集任务**:
```python
# 根据ID获取
collection = db.get_collection_by_id(collection_id)

# 获取所有活跃任务
collections = db.get_active_collections()

# 获取所有任务
collections = db.get_all_collections(status='active')
```

**更新采集任务**:
```python
db.update_collection(
    collection_id=1,
    name="新名称",
    status="completed"
)
```

**删除采集任务**:
```python
db.delete_collection(collection_id)
# 注意: 会级联删除关联的用户、照片、记录
```

### 9.1.3 用户操作

**添加用户**:
```python
user = db.add_user(
    name="张三",
    id_number="110101199001011234",
    gender="男",
    nation="汉族",
    birthday=date(1990, 1, 1),
    address="北京市东城区",
    collection_id=1
)
# 返回: User对象
```

**查询用户**:
```python
# 根据ID查询
user = db.get_user_by_id(user_id)

# 根据身份证号查询
user = db.get_user_by_id_number("110101199001011234", collection_id=1)

# 获取所有用户
users = db.get_all_users(collection_id=1)

# 高级搜索
users = db.search_users(
    keyword="张三",
    collection_id=1,
    gender="男",
    age_range="18-30",
    nation="汉族"
)
```

**更新用户**:
```python
db.update_user(
    user_id=1,
    name="李四",
    address="新地址"
)
```

**删除用户**:
```python
db.delete_user(user_id)
# 注意: 会级联删除关联的照片和记录
```

### 9.1.4 照片操作

**添加照片**:
```python
photo = db.add_photo(
    user_id=1,
    photo_type="raw",  # raw/processed
    file_path="data/photos/user_1_raw.jpg",
    file_size=245678,
    photo_spec="一寸",
    background_color="white"
)
```

**查询照片**:
```python
# 根据ID查询
photo = db.get_photo_by_id(photo_id)

# 获取用户所有照片
photos = db.get_photos_by_user(user_id)
```

**更新照片**:
```python
db.update_photo(
    photo_id=1,
    photo_spec="二寸",
    background_color="blue"
)
```

**删除照片**:
```python
db.delete_photo(photo_id)
```

### 9.1.5 采集记录操作

**添加记录**:
```python
record = db.add_record(
    user_id=1,
    operator="操作员A",
    status="completed",  # pending/completed/failed
    notes="采集成功",
    collection_id=1
)
```

**查询记录**:
```python
# 根据ID查询
record = db.get_record_by_id(record_id)

# 获取用户所有记录
records = db.get_records_by_user(user_id)

# 获取指定日期的记录
records = db.get_records_by_date(date(2024, 9, 1), collection_id=1)
```

**更新记录**:
```python
db.update_record(
    record_id=1,
    status="completed",
    notes="重新采集成功"
)
```

### 9.1.6 统计操作

**采集统计**:
```python
stats = db.get_collection_stats(
    start_date=date(2024, 9, 1),
    end_date=date(2024, 9, 30),
    collection_id=1
)
# 返回: {
#     'total': 100,
#     'completed': 80,
#     'pending': 15,
#     'failed': 5,
#     'completion_rate': 80.0
# }
```

**用户统计**:
```python
user_count = db.get_user_count(collection_id=1)
photo_count = db.get_photo_count(collection_id=1)
```

**人口统计**:
```python
stats = db.get_demographic_stats(collection_id=1)
# 返回: {
#     'gender': {'男': 60, '女': 40},
#     'age': {'18-30': 50, '30-45': 30, ...},
#     'nation': {'汉族': 85, '回族': 10, ...},
#     'total_users': 100
# }
```

## 9.2 图像处理接口

### 9.2.1 AIProcessor类

**位置**: `controllers/ai_processor.py`

**初始化**:
```python
from controllers.ai_processor import AIProcessor

ai = AIProcessor()
```

**人脸检测**:
```python
face_bbox = ai.detect_face(image)
# 返回: {
#     'x': 0.2,
#     'y': 0.15,
#     'width': 0.6,
#     'height': 0.7,
#     'confidence': 0.95
# }
```

**质量评分**:
```python
score = ai.calculate_quality_score(image, face_bbox)
# 返回: {
#     'total': 85.5,
#     'details': {
#         'sharpness': 90,
#         'lighting': 85,
#         'position': 80,
#         'size': 87
#     }
# }
```

### 9.2.2 ImageProcessor类

**位置**: `controllers/image_processor.py`

**美颜处理**:
```python
from controllers.image_processor import ImageProcessor

processor = ImageProcessor()
beautified = processor.beautify(image, strength=0.8)
```

**背景替换**:
```python
result = processor.replace_background(
    image,
    bg_color=(255, 255, 255),  # RGB
    bg_type='solid'  # solid/gradient/custom
)
```

**智能裁剪**:
```python
cropped = processor.smart_crop(
    image,
    face_bbox,
    spec='一寸'  # 规格名称
)
```

### 9.2.3 BatchProcessor类

**位置**: `controllers/batch_processor.py`

**批量处理**:
```python
from controllers.batch_processor import BatchProcessor

processor = BatchProcessor()
processor.progress_updated.connect(on_progress)  # 连接进度信号
processor.process_completed.connect(on_complete)  # 连接完成信号

processor.process_batch(
    users=user_list,
    specs=['一寸', '二寸'],
    bg_colors=['white', 'blue'],
    beautify_strength=0.8
)
```

## 9.3 统计分析接口

### 9.3.1 EChartsGenerator类

**位置**: `controllers/echarts_generator.py`

**生成图表配置**:
```python
from controllers.echarts_generator import EChartsGenerator

# 状态分布图
option = EChartsGenerator.generate_collection_status_chart(stats)

# 地区对比图
option = EChartsGenerator.generate_region_comparison_chart(users)

# 年龄分布图
option = EChartsGenerator.generate_age_distribution_chart(users)

# 趋势图
option = EChartsGenerator.generate_success_rate_trend_chart(
    start_date, end_date, db, collection_id
)

# 民族分布图
option = EChartsGenerator.generate_nation_distribution_chart(users)

# 性别分布图
option = EChartsGenerator.generate_gender_distribution_chart(users)
```

## 9.4 工具类接口

### 9.4.1 FileHelper类

**位置**: `utils/file_helper.py`

**文件操作**:
```python
from utils.file_helper import FileHelper

# 保存图片
FileHelper.save_image(image, filepath, quality=95)

# 读取图片
image = FileHelper.load_image(filepath)

# 删除文件
FileHelper.delete_file(filepath)

# 创建目录
FileHelper.ensure_dir(dirpath)
```

### 9.4.2 ImageHelper类

**位置**: `utils/image_helper.py`

**图像工具**:
```python
from utils.image_helper import ImageHelper

# 调整大小
resized = ImageHelper.resize(image, width, height)

# 旋转
rotated = ImageHelper.rotate(image, angle)

# 转换格式
converted = ImageHelper.convert_color(image, 'BGR', 'RGB')
```

## 9.5 扩展开发指南

### 9.5.1 添加新的照片规格

**步骤**:
1. 在`config/config.py`中添加规格定义
2. 更新UI中的规格选项
3. 测试裁剪功能

**示例**:
```python
PHOTO_SPECS = {
    '自定义规格': {
        'size': (400, 600),  # 像素
        'dpi': 300,
        'description': '自定义尺寸'
    }
}
```

### 9.5.2 添加新的背景效果

**步骤**:
1. 在`controllers/background_replacer.py`中实现新效果
2. 更新UI中的背景选项
3. 测试效果

**示例**:
```python
def apply_gradient_background(image, color1, color2):
    """渐变背景"""
    h, w = image.shape[:2]
    gradient = np.linspace(color1, color2, h)
    background = np.tile(gradient, (w, 1, 1))
    return blend_with_background(image, background)
```

### 9.5.3 添加新的统计图表

**步骤**:
1. 在`EChartsGenerator`中添加生成方法
2. 在`ReportView`中添加图表组件
3. 连接数据和显示

**示例**:
```python
@staticmethod
def generate_custom_chart(data):
    return {
        'tooltip': {'trigger': 'axis'},
        'xAxis': {'type': 'category', 'data': data['labels']},
        'yAxis': {'type': 'value'},
        'series': [{
            'type': 'bar',
            'data': data['values']
        }]
    }
```

---
**上一篇**: [部署运维指南](./08_部署运维指南.md)  
**下一篇**: [测试验证报告](./10_测试验证报告.md)
