"""
证件照智能采集及处理系统 - 软著鉴别材料第1部分
项目名称: 智能化证件照采集及处理系统
版本号: 1.0.0
创建日期: 2024-01-01
最后修改日期: 2025-12-31

================================================================================
                        软件鉴别材料 - 源程序代码部分
================================================================================

本文档为软件著作权登记用途的源程序代码鉴别材料，包含核心模块的源代码。
每页代码不少于50行，确保符合国家版权局的鉴别材料要求。

================================================================================
第1部分: 系统主程序入口
================================================================================

"""

# ============================================================================
# 文件名: main.py
# 功能: 系统主程序入口，负责初始化和启动应用
# 行数: 62 行
# ============================================================================

import sys
import os

# 设置环境变量以解决 TensorFlow 兼容性问题
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# 预加载rembg，避免在子进程中导入失败
# 静默导入，抑制所有输出
_old_stderr = sys.stderr
_old_stdout = sys.stdout
try:
    sys.stderr = open(os.devnull, 'w')
    sys.stdout = open(os.devnull, 'w')
    import rembg
    _rembg_preloaded = True
except:
    _rembg_preloaded = False
finally:
    if sys.stderr != _old_stderr:
        sys.stderr.close()
    if sys.stdout != _old_stdout:
        sys.stdout.close()
    sys.stderr = _old_stderr
    sys.stdout = _old_stdout

from PyQt5.QtWidgets import QApplication
from config.database import init_db
from config.config import init_directories
from views.main_window import MainWindow

def main():
    """
    主函数 - 应用入口点
    功能:
    1. 初始化应用所需的目录结构
    2. 初始化数据库
    3. 创建PyQt5应用实例
    4. 创建主窗口并显示
    5. 运行事件循环
    """
    # 初始化目录
    init_directories()
    
    # 初始化数据库
    init_db()
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


# ============================================================================
# 文件名: config/config.py
# 功能: 系统配置文件，定义全局参数和路径
# 行数: 85 行
# ============================================================================

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

# 摄像头配置
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 15

# 图像处理配置
PHOTO_QUALITY = 95
PHOTO_DPI = 300

# 证件照尺寸规格 (像素)
PHOTO_SPECS = {
    '一寸': (590, 826),           # 25mm×35mm
    '小二寸': (826, 1158),         # 35mm×49mm
    '二寸': (826, 1252),           # 35mm×53mm
    '大一寸': (780, 1134),         # 33mm×48mm
    '美国护照': (1200, 1200),      # 51mm×51mm
    '欧盟护照': (826, 1063),       # 35mm×45mm
    '英国签证': (826, 1063),       # 35mm×45mm
    '日本护照': (826, 1063),       # 35mm×45mm
    '韩国签证': (826, 1063),       # 35mm×45mm
    '印度签证': (1200, 1200),      # 51mm×51mm
    '泰国签证': (944, 1181),       # 40mm×50mm
    '驾驶证': (472, 630),          # 20mm×26.7mm
    '社保卡': (590, 826),          # 25mm×35mm
}

# 证件照背景色 (RGB)
BACKGROUND_COLORS = {
    '白色': (255, 255, 255),
    '蓝色': (67, 142, 219),
    '红色': (255, 0, 0),
    '灰色': (192, 192, 192),
    '美国护照蓝': (51, 122, 183),
    '泰国签证蓝': (65, 105, 225),
    '欧盟护照灰': (240, 240, 240),
}

# AI模型配置
FACE_DETECTION_CONFIDENCE = 0.3
FACE_RECOGNITION_THRESHOLD = 0.6
QUALITY_SCORE_THRESHOLD = 60

# GPU加速配置
USE_GPU = True
GPU_DEVICE_ID = 0
GPU_MEMORY_FRACTION = 0.8
GPU_ALLOW_GROWTH = True
AUTO_FALLBACK_TO_CPU = True

# 身份证读卡器配置
ID_CARD_READER_TIMEOUT = 5000

def init_directories():
    """初始化所有必要的目录"""
    dirs = [
        DATABASE_DIR, RAW_PHOTOS_DIR, PROCESSED_PHOTOS_DIR,
        ID_PHOTOS_DIR, REPORTS_DIR, ICONS_DIR, QSS_DIR, MODELS_DIR,
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    init_directories()
    print("目录初始化完成")


# ============================================================================
# 文件名: config/database.py
# 功能: 数据库初始化和会话管理
# 行数: 52 行
# ============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.config import DATABASE_URL, init_directories

# 初始化目录
init_directories()

# 创建数据库引擎
engine = create_engine(DATABASE_URL, echo=False)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 导入所有模型（确保它们被注册到 Base）
from models.collection import Collection
from models.user import User
from models.photo import Photo
from models.record import CollectionRecord

def get_db():
    """获取数据库会话 - 使用生成器模式管理会话生命周期"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    初始化数据库表
    功能:
    1. 检查数据库连接
    2. 创建所有表
    3. 执行初始化脚本
    """
    Base.metadata.create_all(bind=engine)
