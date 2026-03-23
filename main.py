"""
证件照采集及处理系统 - 主程序入口
"""
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
    """主函数"""
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
