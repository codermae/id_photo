"""
系统配置文件
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据目录
DATA_DIR = BASE_DIR / 'data'
DATABASE_DIR = DATA_DIR / 'database'
PHOTOS_DIR = DATA_DIR / 'photos'
RAW_PHOTOS_DIR = PHOTOS_DIR / 'raw'
PROCESSED_PHOTOS_DIR = PHOTOS_DIR / 'processed'
ID_PHOTOS_DIR = PHOTOS_DIR / 'id_photos'
EXPORTS_DIR = DATA_DIR / 'exports'
REPORTS_DIR = EXPORTS_DIR / 'reports'

# 资源目录
RESOURCES_DIR = BASE_DIR / 'resources'
ICONS_DIR = RESOURCES_DIR / 'icons'
QSS_DIR = RESOURCES_DIR / 'qss'
MODELS_DIR = RESOURCES_DIR / 'models'

# 数据库配置
DATABASE_URL = f'sqlite:///{DATABASE_DIR / "id_photo.db"}'

# 摄像头配置 - 优化以减少打开延迟
CAMERA_WIDTH = 640   # 从1280降低到640，减少延迟
CAMERA_HEIGHT = 480  # 从720降低到480，减少延迟
CAMERA_FPS = 15      # 从30降低到15，减少延迟

# 图像处理配置
PHOTO_QUALITY = 95
PHOTO_DPI = 300

# 证件照尺寸规格 (像素)
PHOTO_SPECS = {
    '一寸': (295, 413),
    '小二寸': (413, 579),
    '二寸': (413, 626),
    '大一寸': (390, 567),
}

# 证件照背景色 (RGB)
BACKGROUND_COLORS = {
    '白色': (255, 255, 255),
    '蓝色': (67, 142, 219),
    '红色': (255, 0, 0),
    '灰色': (192, 192, 192),
}

# AI模型配置
FACE_DETECTION_CONFIDENCE = 0.3  # 从 0.5 降低到 0.3
FACE_RECOGNITION_THRESHOLD = 0.6
QUALITY_SCORE_THRESHOLD = 60  # 从 70 降低到 60

# 身份证读卡器配置
ID_CARD_READER_TIMEOUT = 5000  # 毫秒

# 创建必要的目录
def init_directories():
    """初始化所有必要的目录"""
    dirs = [
        DATABASE_DIR,
        RAW_PHOTOS_DIR,
        PROCESSED_PHOTOS_DIR,
        ID_PHOTOS_DIR,
        REPORTS_DIR,
        ICONS_DIR,
        QSS_DIR,
        MODELS_DIR,
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    init_directories()
    print("目录初始化完成")
