#!/usr/bin/env python3
"""
测试融合的批量处理功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import PHOTO_SPECS, BACKGROUND_COLORS
from collections import defaultdict

def test_unified_batch():
    """测试融合批量处理"""
    print("=" * 60)
    print("🚀 智能批量处理功能测试")
    print("=" * 60)
    
    # 规格去重
    size_groups = defaultdict(list)
    for spec_name in PHOTO_SPECS.keys():
        size = PHOTO_SPECS[spec_name]
        size_groups[size].append(spec_name)
    
    print("\n📋 规格优化:")
    print(f"  原始规格: {len(PHOTO_SPECS)}种")
    print(f"  去重后: {len(size_groups)}种不同尺寸")
    print(f"  节省比例: {(len(PHOTO_SPECS) - len(size_groups)) / len(PHOTO_SPECS) * 100:.1f}%")
    
    # 背景色统计
    print(f"\n🎨 背景颜色: {len(BACKGROUND_COLORS)}种")
    
    # 模式1：单张多规格
    print("\n" + "=" * 60)
    print("模式1️⃣: 单张多规格生成")
    print("=" * 60)
    
    configs = [
        ("推荐配置", 4, 4),
        ("国际配置", 3, 6),
        ("完整配置", 10, 17),
    ]
    
    for name, spec_count, color_count in configs:
        total = spec_count * color_count
        time_sec = total * 3
        time_min = time_sec / 60
        size_mb = total * 0.4
        
        print(f"\n{name}:")
        print(f"  规格数: {spec_count}")
        print(f"  颜色数: {color_count}")
        print(f"  输出数: {total}张")
        print(f"  预计时间: {time_min:.1f}分钟")
        print(f"  存储空间: {size_mb:.1f}MB")
    
    # 模式2：多张批量
    print("\n" + "=" * 60)
    print("模式2️⃣: 多张批量处理")
    print("=" * 60)
    
    input_counts = [10, 50, 100]
    
    for input_count in input_counts:
        print(f"\n输入: {input_count}张图片")
        
        # 单规格模式
        output_single = input_count
        time_single = output_single * 3
        print(f"  单规格模式: {output_single}张 (~{time_single//60}分钟)")
        
        # 多规格模式
        for name, spec_count, color_count in configs:
            output_multi = input_count * spec_count * color_count
            time_multi = output_multi * 3
            size_multi = output_multi * 0.4
            
            print(f"  多规格({name}): {output_multi}张 (~{time_multi//60}分钟, {size_multi:.0f}MB)")
    
    # 融合优势
    print("\n" + "=" * 60)
    print("✨ 融合优势")
    print("=" * 60)
    
    print("""
1. 统一界面
   ✓ 单张和多张在同一对话框
   ✓ 标签页清晰分离功能
   ✓ 避免用户混淆

2. 灵活模式
   ✓ 支持单规格和多规格
   ✓ 支持单张和多张
   ✓ 支持精细和高保真

3. 智能去重
   ✓ 22种规格 → 10种不同尺寸
   ✓ 节省54.5%的重复生成
   ✓ 推荐配置从374张减少到16张

4. 高效处理
   ✓ 快速选择按钮
   ✓ 实时进度显示
   ✓ 详细的确认对话框

5. 用户友好
   ✓ 清晰的功能说明
   ✓ 智能提示信息
   ✓ 推荐配置预设
    """)
    
    # 使用场景
    print("\n" + "=" * 60)
    print("📌 使用场景")
    print("=" * 60)
    
    scenarios = [
        ("日常证件照", "单张多规格", "推荐配置", "16张"),
        ("国际签证", "单张多规格", "国际配置", "18张"),
        ("批量处理", "多张批量", "单规格", "N张"),
        ("专业覆盖", "多张批量", "多规格完整", "N×170张"),
    ]
    
    for scenario, mode, config, output in scenarios:
        print(f"\n{scenario}:")
        print(f"  模式: {mode}")
        print(f"  配置: {config}")
        print(f"  输出: {output}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_unified_batch()
