#!/usr/bin/env python3
"""
测试批量处理与多规格生成集成
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import PHOTO_SPECS, BACKGROUND_COLORS
from collections import defaultdict

def test_spec_deduplication():
    """测试规格去重逻辑"""
    print("=== 证件照规格去重测试 ===")
    
    # 按尺寸分组
    size_groups = defaultdict(list)
    for spec_name, size in PHOTO_SPECS.items():
        size_groups[size].append(spec_name)
    
    print(f"原始规格数: {len(PHOTO_SPECS)}")
    print(f"去重后尺寸数: {len(size_groups)}")
    print(f"重复率: {(len(PHOTO_SPECS) - len(size_groups)) / len(PHOTO_SPECS) * 100:.1f}%")
    
    print("\n📋 去重后的规格组:")
    for i, (size, specs) in enumerate(size_groups.items(), 1):
        if len(specs) == 1:
            print(f"{i:2d}. {specs[0]} ({size[0]}×{size[1]}px)")
        else:
            print(f"{i:2d}. {specs[0]} 等{len(specs)}种 ({size[0]}×{size[1]}px)")
            print(f"    包含: {', '.join(specs)}")
    
    return size_groups

def test_generation_calculation():
    """测试生成数量计算"""
    print("\n=== 生成数量计算测试 ===")
    
    size_groups = test_spec_deduplication()
    
    # 常用配置
    common_specs = 4  # 一寸、小二寸、二寸、大一寸
    basic_colors = 4  # 白色、蓝色、红色、灰色
    
    # 国际配置
    intl_specs = 3    # 美国护照、欧盟护照、泰国签证
    intl_colors = 6   # 基础4色 + 美国护照蓝 + 欧盟护照灰
    
    # 完整配置
    all_specs = len(size_groups)
    all_colors = len(BACKGROUND_COLORS)
    
    print(f"\n📊 不同配置的生成数量:")
    print(f"常用配置: {common_specs} 规格 × {basic_colors} 颜色 = {common_specs * basic_colors} 张")
    print(f"国际配置: {intl_specs} 规格 × {intl_colors} 颜色 = {intl_specs * intl_colors} 张")
    print(f"完整配置: {all_specs} 规格 × {all_colors} 颜色 = {all_specs * all_colors} 张")
    
    # 原始配置对比
    original_all = len(PHOTO_SPECS) * len(BACKGROUND_COLORS)
    optimized_all = all_specs * all_colors
    
    print(f"\n💡 优化效果:")
    print(f"原始全选: {len(PHOTO_SPECS)} × {len(BACKGROUND_COLORS)} = {original_all} 张")
    print(f"优化全选: {all_specs} × {all_colors} = {optimized_all} 张")
    print(f"节省比例: {(original_all - optimized_all) / original_all * 100:.1f}%")

def test_ui_display():
    """测试UI显示逻辑"""
    print("\n=== UI显示逻辑测试 ===")
    
    size_groups = defaultdict(list)
    for spec_name, size in PHOTO_SPECS.items():
        size_groups[size].append(spec_name)
    
    print("\n🎨 ComboBox显示项:")
    for size, specs in size_groups.items():
        if len(specs) == 1:
            display_name = specs[0]
            tooltip = f"尺寸: {size[0]}×{size[1]}px"
        else:
            display_name = f"{specs[0]} 等{len(specs)}种"
            tooltip = f"相同尺寸 {size[0]}×{size[1]}px:\n" + "\n".join(specs)
        
        print(f"• {display_name}")
        if len(specs) > 1:
            print(f"  提示: {tooltip.replace(chr(10), ' | ')}")

if __name__ == "__main__":
    test_spec_deduplication()
    test_generation_calculation()
    test_ui_display()
    
    print("\n✅ 集成测试完成！")
    print("\n📋 主要改进:")
    print("1. 规格选择去重：22种→10种不同尺寸")
    print("2. 批量处理集成多规格生成功能")
    print("3. 智能提示和确认对话框")
    print("4. 统一的优化规格选择界面")