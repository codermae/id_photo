"""
测试新的显示格式
"""
from config.config import PHOTO_SPECS, BACKGROUND_COLORS
from collections import defaultdict

def test_spec_format():
    """测试规格显示格式"""
    print("=" * 60)
    print("规格显示格式测试")
    print("=" * 60)
    
    size_groups = defaultdict(list)
    for spec_name, size in PHOTO_SPECS.items():
        size_groups[size].append(spec_name)
    
    print(f"\n总规格数: {len(PHOTO_SPECS)}")
    print(f"不同尺寸数: {len(size_groups)}")
    print(f"\n新格式显示:\n")
    
    for size, specs in sorted(size_groups.items()):
        size_str = f"{size[0]}x{size[1]}px"
        
        if len(specs) == 1:
            display_name = f"{size_str} {specs[0]}"
            print(f"  ✓ {display_name}")
        else:
            display_name = f"{size_str} {specs[0]} 等{len(specs)}种"
            print(f"  ✓ {display_name}")
            print(f"    包含: {', '.join(specs)}")

def test_color_merge():
    """测试颜色合并"""
    print("\n" + "=" * 60)
    print("背景颜色合并测试")
    print("=" * 60)
    
    print(f"\n合并后颜色数: {len(BACKGROUND_COLORS)}")
    print(f"\n颜色列表:\n")
    
    # 按类别显示
    basic_colors = ['白色', '蓝色', '红色', '灰色']
    intl_colors = [c for c in BACKGROUND_COLORS.keys() if c not in basic_colors]
    
    print("基础颜色:")
    for color in basic_colors:
        if color in BACKGROUND_COLORS:
            rgb = BACKGROUND_COLORS[color]
            print(f"  ✓ {color}: RGB{rgb}")
    
    print("\n国际标准颜色:")
    for color in intl_colors:
        rgb = BACKGROUND_COLORS[color]
        print(f"  ✓ {color}: RGB{rgb}")
    
    # 检查是否有重复的RGB值
    print("\n" + "=" * 60)
    print("重复RGB值检查")
    print("=" * 60)
    
    rgb_to_names = defaultdict(list)
    for name, rgb in BACKGROUND_COLORS.items():
        rgb_to_names[rgb].append(name)
    
    has_duplicates = False
    for rgb, names in rgb_to_names.items():
        if len(names) > 1:
            has_duplicates = True
            print(f"  ⚠ RGB{rgb} 被多个颜色使用: {', '.join(names)}")
    
    if not has_duplicates:
        print("  ✓ 没有重复的RGB值")

def test_generation_count():
    """测试生成数量"""
    print("\n" + "=" * 60)
    print("生成数量对比")
    print("=" * 60)
    
    size_groups = defaultdict(list)
    for spec_name, size in PHOTO_SPECS.items():
        size_groups[size].append(spec_name)
    
    unique_sizes = len(size_groups)
    total_colors = len(BACKGROUND_COLORS)
    
    print(f"\n优化前: {len(PHOTO_SPECS)} 规格 × 17 颜色 = {len(PHOTO_SPECS) * 17} 张")
    print(f"优化后: {unique_sizes} 规格 × {total_colors} 颜色 = {unique_sizes * total_colors} 张")
    
    reduction = len(PHOTO_SPECS) * 17 - unique_sizes * total_colors
    reduction_pct = reduction / (len(PHOTO_SPECS) * 17) * 100
    
    print(f"\n减少: {reduction} 张 ({reduction_pct:.1f}%)")

if __name__ == '__main__':
    test_spec_format()
    test_color_merge()
    test_generation_count()
    
    print("\n" + "=" * 60)
    print("✓ 所有测试完成")
    print("=" * 60)
