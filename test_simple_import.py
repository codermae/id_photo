#!/usr/bin/env python3
"""
简单的导入测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 检查ProcessView类的定义
print("=== 检查ProcessView类定义 ===")

# 读取文件内容
with open('views/process_view.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查关键代码
if 'self.spec_checkboxes = {}' in content:
    print("✓ 找到 self.spec_checkboxes = {} 定义")
else:
    print("✗ 未找到 self.spec_checkboxes = {} 定义")

if 'def init_ui(self):' in content:
    print("✓ 找到 init_ui 方法定义")
else:
    print("✗ 未找到 init_ui 方法定义")

# 检查是否有语法错误
try:
    compile(content, 'views/process_view.py', 'exec')
    print("✓ 文件语法正确")
except SyntaxError as e:
    print(f"✗ 语法错误: {e}")
    print(f"   行号: {e.lineno}")
    print(f"   位置: {e.offset}")

# 尝试导入
try:
    from views.process_view import ProcessView
    print("✓ ProcessView 导入成功")
    
    # 检查类的方法
    if hasattr(ProcessView, 'init_ui'):
        print("✓ ProcessView 有 init_ui 方法")
    else:
        print("✗ ProcessView 没有 init_ui 方法")
        
except Exception as e:
    print(f"✗ ProcessView 导入失败: {e}")
    import traceback
    traceback.print_exc()