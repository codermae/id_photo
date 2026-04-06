#!/usr/bin/env python3
"""
测试UI修复 - 最终版本
验证所有用户反馈的问题是否已修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from views.process_view import ProcessView
from config.config import PHOTO_SPECS, BACKGROUND_COLORS
from collections import defaultdict

def test_spec_display():
    """测试规格显示格式"""
    print("=== 测试规格显示格式 ===")
    
    # 模拟规格分组逻辑
    size_groups = defaultdict(list)
    for spec_name, size in PHOTO_SPECS.items():
        size_groups[size].append(spec_name)
    
    print(f"总规格数: {len(PHOTO_SPECS)}")
    print(f"不同尺寸数: {len(size_groups)}")
    
    for size, specs in size_groups.items():
        size_str = f"{size[0]}x{size[1]}px"
        
        if len(specs) == 1:
            display_name = f"{size_str} {specs[0]}"
            tooltip = f"尺寸: {size[0]}×{size[1]}px"
        else:
            display_name = f"{size_str} {specs[0]} 等{len(specs)}种"
            tooltip = f"相同尺寸 {size[0]}×{size[1]}px:\n" + "\n".join(specs)
        
        print(f"显示: {display_name}")
        print(f"提示: {tooltip}")
        print("---")

def test_background_colors():
    """测试背景色数量"""
    print("=== 测试背景色 ===")
    print(f"背景色数量: {len(BACKGROUND_COLORS)}")
    for name, rgb in BACKGROUND_COLORS.items():
        print(f"{name}: {rgb}")

def test_ui_initialization():
    """测试UI初始化"""
    print("=== 测试UI初始化 ===")
    
    app = QApplication(sys.argv)
    
    try:
        # 创建主窗口
        main_window = QMainWindow()
        main_window.setWindowTitle("UI修复测试")
        main_window.setGeometry(100, 100, 1200, 800)
        
        # 创建ProcessView
        print("正在创建 ProcessView...")
        try:
            process_view = ProcessView()
            print("✓ ProcessView 创建成功")
        except Exception as e:
            print(f"✗ ProcessView 创建失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        main_window.setCentralWidget(process_view)
        
        print("✓ ProcessView 初始化成功")
        
        # 检查关键组件
        print(f"ProcessView 属性列表: {[attr for attr in dir(process_view) if not attr.startswith('_')]}")
        print(f"是否有 spec_checkboxes: {hasattr(process_view, 'spec_checkboxes')}")
        if hasattr(process_view, 'spec_checkboxes'):
            print(f"spec_checkboxes 类型: {type(process_view.spec_checkboxes)}")
        
        assert hasattr(process_view, 'spec_checkboxes'), "spec_checkboxes 属性缺失"
        assert hasattr(process_view, 'bg_checkboxes'), "bg_checkboxes 属性缺失"
        assert hasattr(process_view, 'compare_btn'), "compare_btn 属性缺失"
        assert hasattr(process_view, 'manual_crop_btn'), "manual_crop_btn 属性缺失"
        
        print("✓ 所有关键组件存在")
        
        # 检查规格复选框数量
        spec_count = len(process_view.spec_checkboxes)
        print(f"✓ 规格复选框数量: {spec_count}")
        
        # 检查背景色复选框数量
        bg_count = len(process_view.bg_checkboxes)
        print(f"✓ 背景色复选框数量: {bg_count}")
        
        # 检查Alpha Matte文本
        alpha_text = process_view.alpha_matting_check.text()
        print(f"✓ Alpha Matte文本: {alpha_text}")
        assert "Alpha Matte边缘增强" in alpha_text, f"Alpha Matte文本不正确: {alpha_text}"
        
        print("✓ UI初始化测试通过")
        
        # 显示窗口（可选）
        # main_window.show()
        # app.exec_()
        
    except Exception as e:
        print(f"✗ UI初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """主测试函数"""
    print("开始UI修复验证测试...")
    print("=" * 50)
    
    # 测试规格显示
    test_spec_display()
    print()
    
    # 测试背景色
    test_background_colors()
    print()
    
    # 测试UI初始化
    success = test_ui_initialization()
    
    print("=" * 50)
    if success:
        print("✓ 所有测试通过！UI修复成功")
    else:
        print("✗ 测试失败，需要进一步修复")
    
    return success

if __name__ == '__main__':
    main()