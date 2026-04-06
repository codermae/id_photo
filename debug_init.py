"""
调试初始化问题
"""
import sys
sys.dont_write_bytecode = True

from PyQt5.QtWidgets import QApplication

def debug_init():
    """调试初始化"""
    print("开始调试初始化...")
    
    app = QApplication(sys.argv)
    
    try:
        print("1. 导入ProcessView...")
        from views.process_view import ProcessView
        
        print("2. 创建ProcessView实例...")
        view = ProcessView()
        
        print("3. 检查属性...")
        attrs = ['spec_checkboxes', 'bg_checkboxes', 'collection_combo', 'preview_label']
        for attr in attrs:
            if hasattr(view, attr):
                print(f"   ✓ {attr}: 存在")
            else:
                print(f"   ✗ {attr}: 缺失")
        
        print("4. 检查init_ui方法...")
        if hasattr(view, 'init_ui'):
            print("   ✓ init_ui方法存在")
        else:
            print("   ✗ init_ui方法缺失")
        
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    debug_init()