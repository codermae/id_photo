"""
证件照规格分析工具
"""
from config.config import PHOTO_SPECS, PHOTO_SPEC_DETAILS
from collections import defaultdict

def analyze_specs():
    """分析证件照规格"""
    print("📊 证件照规格分析报告")
    print("=" * 60)
    
    # 按尺寸分组
    size_groups = defaultdict(list)
    for spec, size in PHOTO_SPECS.items():
        size_groups[size].append(spec)
    
    print(f"📋 总规格数: {len(PHOTO_SPECS)}")
    print(f"🎯 实际不同尺寸数: {len(size_groups)}")
    print(f"💾 去重后可减少: {len(PHOTO_SPECS) - len(size_groups)} 种重复")
    print()
    
    print("📐 尺寸分组详情:")
    print("-" * 60)
    
    duplicate_count = 0
    for size, specs in sorted(size_groups.items()):
        width, height = size
        mm_width = round(width * 25.4 / 600, 1)  # 转换为毫米
        mm_height = round(height * 25.4 / 600, 1)
        
        if len(specs) > 1:
            duplicate_count += len(specs) - 1
            print(f"🔄 {width}×{height}px ({mm_width}×{mm_height}mm)")
            print(f"   重复规格 ({len(specs)}种): {', '.join(specs)}")
            print(f"   💡 建议: 选择 '{specs[0]}' 作为代表")
        else:
            print(f"✅ {width}×{height}px ({mm_width}×{mm_height}mm)")
            print(f"   唯一规格: {specs[0]}")
        print()
    
    print("📈 优化建议:")
    print("-" * 60)
    print(f"• 原始规格数: {len(PHOTO_SPECS)}")
    print(f"• 优化后规格数: {len(size_groups)}")
    print(f"• 减少重复: {duplicate_count} 种")
    print(f"• 节省比例: {duplicate_count/len(PHOTO_SPECS)*100:.1f}%")
    print()
    
    print("🎯 推荐选择:")
    print("-" * 60)
    
    # 中国常用
    china_common = []
    for size, specs in size_groups.items():
        if any(spec in ['一寸', '小二寸', '二寸', '大一寸'] for spec in specs):
            china_common.append(specs[0])
    print(f"🇨🇳 中国常用 ({len(china_common)}种): {', '.join(china_common)}")
    
    # 国际标准
    intl_common = []
    for size, specs in size_groups.items():
        if any('护照' in spec or '签证' in spec for spec in specs):
            intl_common.append(specs[0])
    print(f"🌍 国际标准 ({len(intl_common)}种): {', '.join(intl_common)}")
    
    # 特殊用途
    special = []
    for size, specs in size_groups.items():
        if any(spec in ['驾驶证', '五寸', '六寸'] for spec in specs):
            special.append(specs[0])
    print(f"🎨 特殊用途 ({len(special)}种): {', '.join(special)}")
    
    print()
    print("💡 使用建议:")
    print("-" * 60)
    print("1. 多规格生成时，系统已自动去重相同尺寸")
    print("2. 选择 '一寸等5种' 只会生成一张 590×826px 的照片")
    print("3. 如需特定规格名称，可在生成后重命名文件")
    print("4. 建议按实际用途选择，避免生成过多文件")

def calculate_generation_count():
    """计算生成数量"""
    print("\n🧮 生成数量计算器")
    print("=" * 60)
    
    from config.config import BACKGROUND_COLORS
    
    unique_sizes = len(set(PHOTO_SPECS.values()))
    total_colors = len(BACKGROUND_COLORS)
    
    scenarios = [
        ("全选规格 + 全选颜色", len(PHOTO_SPECS), total_colors),
        ("智能去重 + 全选颜色", unique_sizes, total_colors),
        ("常用规格 + 基础颜色", 4, 4),
        ("国际规格 + 标准颜色", 3, 6),
    ]
    
    for name, specs, colors in scenarios:
        total = specs * colors
        print(f"📊 {name}")
        print(f"   规格: {specs} × 颜色: {colors} = 总计: {total} 张")
        print()

if __name__ == "__main__":
    analyze_specs()
    calculate_generation_count()