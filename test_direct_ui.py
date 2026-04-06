#!/usr/bin/env python3
"""
直接测试UI修复 - 不依赖导入
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt

def test_direct_creation():
    """直接创建ProcessView测试"""
    print("=== 直接创建ProcessView测试 ===")
    
    app = QApplication(sys.argv)
    
    try:
        # 直接执行ProcessView的代码而不是导入
        with open('views/process_view.py', 'r', encoding='utf-8') as f:
            code = f.read()
        exec(code, globals())
        
        # 现在ProcessView应该在全局命名空间中
        if 'ProcessView' in globals():
            print("✓ ProcessView 类定义成功")
            
            # 创建实例
            process_view = ProcessView()
            print("✓ ProcessView 实例创建成功")
            
            # 检查属性
            if hasattr(process_view, 'spec_checkboxes'):
                print(f"✓ spec_checkboxes 存在: {type(process_view.spec_checkboxes)}")
                print(f"  数量: {len(process_view.spec_checkboxes)}")
            else:
                print("✗ spec_checkboxes 不存在")
                
            if hasattr(process_view, 'bg_checkboxes'):
                print(f"✓ bg_checkboxes 存在: {type(process_view.bg_checkboxes)}")
                print(f"  数量: {len(process_view.bg_checkboxes)}")
            else:
                print("✗ bg_checkboxes 不存在")
                
        else:
            print("✗ ProcessView 类定义失败")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_direct_creation()