# API参考手册

## 概述

本文档提供系统所有主要API的详细参考，包括参数说明、返回值、使用示例和错误处理。

---

## 图像处理API

### ImageProcessor (图像处理控制器)

#### load_image(filepath)

加载图像文件

```python
def load_image(filepath: str) -> np.ndarray:
    """
    加载图像文件
    
    Args:
        filepath (str): 图像文件路径
        
    Returns:
        np.ndarray: 加载的图像数组
        
    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件格式不支持
        
    Example:
        >>> processor = ImageProcessor()
        >>> image = processor.load_image('photo.jpg')
        >>> print(image.shape)
        (1080, 1440, 3)
    """
```

#### crop_to_spec(spec)

按规格智能裁剪

```python
def crop_to_spec(spec: str = '一寸') -> Tuple[bool, Dict]:
    """
    按规格智能裁剪
    
    Args:
        spec (str): 证件照规格，可选值：
            - '一寸': 25×35mm
            - '二寸': 35×53mm
            - '小二寸': 35×49mm
            - '大一寸': 33×48mm
            - '五寸': 89×127mm
            
    Returns:
        Tuple[bool, Dict]: (成功标志, 裁剪信息)
        
    Example:
        >>> success, info = processor.crop_to_spec('一寸')
        >>> if success:
        ...     print(f"裁剪成功: {info}")
        ... else:
        ...     print(f"裁剪失败: {info['error']}")
    """
```

#### change_background(color_name)

更换背景色

```python
def change_background(color_name: str = '白色') -> bool:
    """
    更换背景色
    
    Args:
        color_name (str): 背景色名称，可选值：
            - '白色': RGB(255, 255, 255)
            - '蓝色': RGB(67, 142, 219)
            - '红色': RGB(255, 0, 0)
            - '浅蓝色': RGB(173, 216, 230)
            - '灰色': RGB(192, 192, 192)
            
    Returns:
        bool: 是否成功
        
    Example:
        >>> success = processor.change_background('蓝色')
        >>> if success:
        ...     print("背景替换成功")
    """
```

#### beautify(strength=1.0)

美颜处理

```python
def beautify(strength: float = 1.0) -> bool:
    """
    美颜处理
    
    Args:
        strength (float): 美颜强度，范围0.0-2.0
            - 0.0-0.5: 轻度美颜
            - 0.5-1.0: 标准美颜
            - 1.0-1.5: 中度美颜
            - 1.5-2.0: 强度美颜
            
    Returns:
        bool: 是否成功
        
    Example:
        >>> success = processor.beautify(strength=1.0)
    """
```

#### adjust_brightness(value)

调整亮度

```python
def adjust_brightness(value: int) -> bool:
    """
    调整亮度
    
    Args:
        value (int): 亮度调整值，范围-100到+100
            - 负值：降低亮度
            - 正值：提高亮度
            
    Returns:
        bool: 是否成功
        
    Example:
        >>> processor.adjust_brightness(10)  # 提高亮度
    """
```

#### undo()

撤销上一步操作

```python
def undo() -> bool:
    """
    撤销上一步操作
    
    Returns:
        bool: 是否成功
        
    Example:
        >>> processor.undo()
    """
```

#### save_processed_image(id_number, spec, bg_color)

保存处理后的图像

```python
def save_processed_image(id_number: str, spec: str, bg_color: str) -> Tuple[bool, str]:
    """
    保存处理后的图像
    
    Args:
        id_number (str): 身份证号
        spec (str): 证件照规格
        bg_color (str): 背景色
        
    Returns:
        Tuple[bool, str]: (成功标志, 文件路径)
        
    Example:
        >>> success, path = processor.save_processed_image(
        ...     '110101199001011234', '一寸', '白色'
        ... )
        >>> if success:
        ...     print(f"保存成功: {path}")
    """
```

---

## AI处理API

### AIProcessor (AI处理控制器)

#### detect_face(image)

检测人脸

```python
def detect_face(image: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    检测人脸
    
    Args:
        image (np.ndarray): 输入图像
        
    Returns:
        List[Tuple[int, int, int, int]]: 人脸位置列表 [(x, y, w, h), ...]
        
    Example:
        >>> faces = ai_processor.detect_face(image)
        >>> for x, y, w, h in faces:
        ...     print(f"人脸位置: ({x}, {y}, {w}, {h})")
    """
```

#### check_face_quality(image)

检查人脸质量

```python
def check_face_quality(image: np.ndarray) -> Dict:
    """
    检查人脸质量
    
    Args:
        image (np.ndarray): 输入图像
        
    Returns:
        Dict: 质量信息
        {
            'score': 85,              # 质量评分 (0-100)
            'level': '良好',          # 评分等级
            'face_detected': True,    # 是否检测到人脸
            'frontal': True,          # 是否正视
            'eyes_open': True,        # 眼睛是否睁开
            'mouth_natural': True,    # 嘴巴是否自然
            'no_glasses': True,       # 是否佩戴眼镜
            'lighting_good': True,    # 光照是否良好
            'face_size_ok': True      # 人脸大小是否合适
        }
        
    Example:
        >>> quality = ai_processor.check_face_quality(image)
        >>> print(f"质量评分: {quality['score']}")
    """
```

#### extract_face_encoding(image)

提取人脸特征

```python
def extract_face_encoding(image: np.ndarray) -> np.ndarray:
    """
    提取人脸特征向量
    
    Args:
        image (np.ndarray): 输入图像
        
    Returns:
        np.ndarray: 128维特征向量
        
    Example:
        >>> encoding = ai_processor.extract_face_encoding(image)
        >>> print(encoding.shape)
        (128,)
    """
```

#### compare_face_encodings(encoding1, encoding2)

比对人脸特征

```python
def compare_face_encodings(
    encoding1: np.ndarray, 
    encoding2: np.ndarray
) -> float:
    """
    比对两个人脸特征
    
    Args:
        encoding1 (np.ndarray): 第一个特征向量
        encoding2 (np.ndarray): 第二个特征向量
        
    Returns:
        float: 相似度 (0-100%)
        
    Example:
        >>> similarity = ai_processor.compare_face_encodings(enc1, enc2)
        >>> if similarity > 80:
        ...     print("识别成功")
    """
```

---

## 数据库API

### DatabaseHelper (数据库操作助手)

#### add_user(name, id_number, ...)

添加用户

```python
def add_user(
    name: str,
    id_number: str,
    gender: str = None,
    nation: str = None,
    birthday: date = None,
    address: str = None
) -> User:
    """
    添加用户
    
    Args:
        name (str): 姓名
        id_number (str): 身份证号
        gender (str): 性别
        nation (str): 民族
        birthday (date): 出生日期
        address (str): 地址
        
    Returns:
        User: 用户对象
        
    Raises:
        IntegrityError: 身份证号已存在
        
    Example:
        >>> user = db_helper.add_user(
        ...     name='张三',
        ...     id_number='110101199001011234',
        ...     gender='男'
        ... )
        >>> print(user.id)
    """
```

#### get_user_by_id_number(id_number)

按身份证号查询用户

```python
def get_user_by_id_number(id_number: str) -> User:
    """
    按身份证号查询用户
    
    Args:
        id_number (str): 身份证号
        
    Returns:
        User: 用户对象，不存在返回None
        
    Example:
        >>> user = db_helper.get_user_by_id_number('110101199001011234')
        >>> if user:
        ...     print(user.name)
    """
```

#### add_photo(user_id, photo_type, file_path, ...)

添加照片记录

```python
def add_photo(
    user_id: int,
    photo_type: str,
    file_path: str,
    file_size: int = None,
    photo_spec: str = None,
    background_color: str = None,
    quality_score: int = None
) -> Photo:
    """
    添加照片记录
    
    Args:
        user_id (int): 用户ID
        photo_type (str): 照片类型 ('raw' 或 'processed')
        file_path (str): 文件路径
        file_size (int): 文件大小
        photo_spec (str): 证件照规格
        background_color (str): 背景色
        quality_score (int): 质量评分
        
    Returns:
        Photo: 照片对象
        
    Example:
        >>> photo = db_helper.add_photo(
        ...     user_id=1,
        ...     photo_type='processed',
        ...     file_path='/data/photos/user_1.jpg',
        ...     quality_score=95
        ... )
    """
```

#### get_collection_stats(start_date, end_date)

获取采集统计

```python
def get_collection_stats(
    start_date: date,
    end_date: date
) -> Dict:
    """
    获取采集统计
    
    Args:
        start_date (date): 开始日期
        end_date (date): 结束日期
        
    Returns:
        Dict: 统计信息
        {
            'total_users': 100,
            'total_photos': 150,
            'total_records': 120,
            'completed_records': 100,
            'pending_records': 15,
            'failed_records': 5,
            'completion_rate': 83.3,
            'average_quality_score': 92.5
        }
        
    Example:
        >>> stats = db_helper.get_collection_stats(
        ...     date(2026, 3, 1),
        ...     date(2026, 3, 31)
        ... )
        >>> print(f"完成率: {stats['completion_rate']}%")
    """
```

#### export_users_to_excel(output_path, ...)

导出用户数据到Excel

```python
def export_users_to_excel(
    output_path: str,
    include_photos: bool = True,
    include_records: bool = True
) -> bool:
    """
    导出用户数据到Excel
    
    Args:
        output_path (str): 输出文件路径
        include_photos (bool): 是否包含照片信息
        include_records (bool): 是否包含采集记录
        
    Returns:
        bool: 是否成功
        
    Example:
        >>> db_helper.export_users_to_excel('users.xlsx')
    """
```

---

## 批量处理API

### BatchProcessor (批量处理器)

#### add_images(image_paths)

添加图片到处理队列

```python
def add_images(image_paths: List[str]) -> int:
    """
    添加图片到处理队列
    
    Args:
        image_paths (List[str]): 图片路径列表
        
    Returns:
        int: 成功添加的图片数量
        
    Example:
        >>> paths = ['photo1.jpg', 'photo2.jpg']
        >>> count = batch_processor.add_images(paths)
        >>> print(f"添加了 {count} 张图片")
    """
```

#### start_batch_processing(output_directory)

开始批量处理

```python
def start_batch_processing(output_directory: str) -> bool:
    """
    开始批量处理
    
    Args:
        output_directory (str): 输出目录
        
    Returns:
        bool: 是否成功启动
        
    Example:
        >>> batch_processor.start_batch_processing('./output')
    """
```

#### get_processing_status() -> Dict

获取处理状态

```python
def get_processing_status() -> Dict:
    """
    获取处理状态
    
    Returns:
        Dict: 处理状态
        {
            'total_files': 100,
            'processed_files': 50,
            'successful_files': 48,
            'failed_files': 2,
            'progress': 50.0,
            'is_processing': True
        }
        
    Example:
        >>> status = batch_processor.get_processing_status()
        >>> print(f"进度: {status['progress']}%")
    """
```

---

## 错误处理

### 异常类型

```python
# 参数错误
ValueError: 参数值不合法

# 文件错误
FileNotFoundError: 文件不存在
IOError: 文件读写错误

# 数据库错误
IntegrityError: 数据完整性错误
OperationalError: 数据库操作错误

# 业务逻辑错误
RuntimeError: 运行时错误
```

### 错误处理示例

```python
try:
    processor.crop_to_spec('一寸')
except ValueError as e:
    print(f"参数错误: {e}")
except Exception as e:
    print(f"处理错误: {e}")
    logger.error(f"处理错误: {e}", exc_info=True)
```

---

## 使用示例

### 完整工作流

```python
from controllers.image_processor import ImageProcessor
from controllers.ai_processor import AIProcessor
from utils.database_helper import DatabaseHelper
from datetime import date

# 初始化
ai_processor = AIProcessor()
image_processor = ImageProcessor(ai_processor=ai_processor)
db_helper = DatabaseHelper()

# 1. 添加用户
user = db_helper.add_user(
    name='张三',
    id_number='110101199001011234',
    gender='男'
)

# 2. 加载图像
image_processor.load_image('photo.jpg')

# 3. 检查质量
quality = ai_processor.check_face_quality(image_processor.current_image)
print(f"质量评分: {quality['score']}")

# 4. 处理图像
image_processor.crop_to_spec('一寸')
image_processor.change_background('白色')
image_processor.beautify(strength=1.0)

# 5. 保存结果
success, path = image_processor.save_processed_image(
    user.id_number, '一寸', '白色'
)

# 6. 记录照片
if success:
    photo = db_helper.add_photo(
        user_id=user.id,
        photo_type='processed',
        file_path=path,
        photo_spec='一寸',
        background_color='白色',
        quality_score=quality['score']
    )

# 7. 记录采集
record = db_helper.add_collection_record(
    user_id=user.id,
    collection_date=date.today(),
    operator='操作员',
    status='completed'
)

# 8. 获取统计
stats = db_helper.get_collection_stats(
    date(2026, 3, 1),
    date(2026, 3, 31)
)
print(f"完成率: {stats['completion_rate']}%")

# 关闭连接
db_helper.close()
```

---

**模块版本**: v2.0  
**最后更新**: 2026-03-23  
**维护者**: 开发团队
