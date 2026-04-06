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

# 证件照尺寸规格 (像素) - 使用 600 DPI 保证高质量
# 注：打印时可以缩小到 300 DPI，但处理时保持高分辨率避免模糊
PHOTO_SPECS = {
    # 中国标准
    '一寸': (590, 826),      # 25mm×35mm，中国身份证、学生证等
    '小二寸': (826, 1158),   # 35mm×49mm，中国护照、港澳通行证
    '二寸': (826, 1252),     # 35mm×53mm，中国签证、毕业证等
    '大一寸': (780, 1134),   # 33mm×48mm，中国港澳通行证等
    
    # 国际标准
    '美国护照': (1200, 1200),     # 51mm×51mm，美国护照标准
    '欧盟护照': (826, 1063),      # 35mm×45mm，欧盟护照标准
    '英国签证': (826, 1063),      # 35mm×45mm，英国签证标准
    '日本护照': (826, 1063),      # 35mm×45mm，日本护照标准
    '韩国签证': (826, 1063),      # 35mm×45mm，韩国签证标准
    '印度签证': (1200, 1200),     # 51mm×51mm，印度签证标准
    '泰国签证': (944, 1181),      # 40mm×50mm，泰国签证标准
    '新加坡护照': (826, 1063),    # 35mm×45mm，新加坡护照标准
    '马来西亚签证': (826, 1063),  # 35mm×45mm，马来西亚签证标准
    '澳洲签证': (826, 1063),      # 35mm×45mm，澳洲签证标准
    '加拿大签证': (826, 1063),    # 35mm×45mm，加拿大签证标准
    
    # 特殊规格
    '驾驶证': (472, 630),         # 20mm×26.7mm，中国驾驶证
    '社保卡': (590, 826),         # 25mm×35mm，中国社保卡
    '学生证': (590, 826),         # 25mm×35mm，中国学生证
    '工作证': (590, 826),         # 25mm×35mm，中国工作证
    '会员卡': (590, 826),         # 25mm×35mm，各类会员卡
    
    # 大尺寸
    '五寸': (2100, 3000),        # 89mm×127mm，五寸照片
    '六寸': (2400, 3600),        # 102mm×152mm，六寸照片
}

# 证件照背景色要求 (RGB) - 精简到7种核心颜色
BACKGROUND_COLORS = {
    # 基础颜色 (4种)
    '白色': (255, 255, 255),           # 纯白 - 通用标准（中国、日本、印度、澳洲、新加坡等）
    '蓝色': (67, 142, 219),            # 标准蓝 - 中国常用
    '红色': (255, 0, 0),               # 标准红
    '灰色': (192, 192, 192),           # 标准灰
    
    # 国际标准背景色 (3种 - 保留差异明显的)
    '美国护照蓝': (51, 122, 183),      # 美国护照标准蓝（深蓝）
    '泰国签证蓝': (65, 105, 225),      # 泰国签证标准蓝（皇家蓝）
    '欧盟护照灰': (240, 240, 240),     # 欧盟护照标准灰白（浅灰白）
}

# 证件照详细规格信息
PHOTO_SPEC_DETAILS = {
    '一寸': {
        'size_mm': (25, 35),
        'size_px': (590, 826),
        'dpi': 600,
        'background': ['白色', '蓝色', '红色'],
        'usage': '身份证、学生证、工作证等',
        'country': '中国',
        'notes': '最常用的证件照规格'
    },
    '小二寸': {
        'size_mm': (35, 49),
        'size_px': (826, 1158),
        'dpi': 600,
        'background': ['白色', '蓝色'],
        'usage': '护照、港澳通行证等',
        'country': '中国',
        'notes': '护照专用规格'
    },
    '美国护照': {
        'size_mm': (51, 51),
        'size_px': (1200, 1200),
        'dpi': 600,
        'background': ['白色', '美国护照蓝'],
        'usage': '美国护照申请',
        'country': '美国',
        'notes': '正方形规格，头部占70-80%'
    },
    '欧盟护照': {
        'size_mm': (35, 45),
        'size_px': (826, 1063),
        'dpi': 600,
        'background': ['白色', '欧盟护照灰'],
        'usage': '欧盟各国护照申请',
        'country': '欧盟',
        'notes': '符合ICAO国际标准'
    },
    '英国签证': {
        'size_mm': (35, 45),
        'size_px': (826, 1063),
        'dpi': 600,
        'background': ['白色', '英国签证蓝'],
        'usage': '英国签证申请',
        'country': '英国',
        'notes': '头部占70-80%，不能戴眼镜'
    },
    '日本护照': {
        'size_mm': (35, 45),
        'size_px': (826, 1063),
        'dpi': 600,
        'background': ['白色', '日本护照白'],
        'usage': '日本护照、签证申请',
        'country': '日本',
        'notes': '6个月内拍摄，正面免冠'
    },
    '印度签证': {
        'size_mm': (51, 51),
        'size_px': (1200, 1200),
        'dpi': 600,
        'background': ['白色', '印度签证白'],
        'usage': '印度签证申请',
        'country': '印度',
        'notes': '正方形规格，白色背景'
    },
    '泰国签证': {
        'size_mm': (40, 50),
        'size_px': (944, 1181),
        'dpi': 600,
        'background': ['白色', '泰国签证蓝'],
        'usage': '泰国签证申请',
        'country': '泰国',
        'notes': '6个月内拍摄'
    }
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
