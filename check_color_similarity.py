"""
检查背景颜色的相似度
"""
from config.config import BACKGROUND_COLORS
import math

def rgb_distance(rgb1, rgb2):
    """计算两个RGB颜色的欧氏距离"""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))

def rgb_to_hex(rgb):
    """RGB转十六进制"""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def analyze_colors():
    """分析颜色相似度"""
    print("=" * 80)
    print("背景颜色详细分析")
    print("=" * 80)
    
    colors = list(BACKGROUND_COLORS.items())
    
    print(f"\n当前颜色数: {len(colors)}\n")
    
    # 显示所有颜色
    print("所有颜色列表:")
    print("-" * 80)
    for name, rgb in colors:
        hex_color = rgb_to_hex(rgb)
        rgb_str = f"{rgb}"
        print(f"  {name:20s} RGB{rgb_str:25s} {hex_color}")
    
    # 检查相似颜色
    print("\n" + "=" * 80)
    print("颜色相似度分析（距离 < 30 视为相似）")
    print("=" * 80)
    
    similar_pairs = []
    
    for i, (name1, rgb1) in enumerate(colors):
        for j, (name2, rgb2) in enumerate(colors[i+1:], i+1):
            distance = rgb_distance(rgb1, rgb2)
            if distance < 30:  # 距离小于30认为相似
                similar_pairs.append((name1, rgb1, name2, rgb2, distance))
    
    if similar_pairs:
        print("\n⚠️  发现相似颜色:\n")
        for name1, rgb1, name2, rgb2, distance in sorted(similar_pairs, key=lambda x: x[4]):
            print(f"  {name1} RGB{rgb1}")
            print(f"  {name2} RGB{rgb2}")
            print(f"  → 距离: {distance:.2f}\n")
    else:
        print("\n✓ 没有发现相似颜色（距离 < 30）")
    
    # 按颜色类型分组
    print("\n" + "=" * 80)
    print("按颜色类型分组")
    print("=" * 80)
    
    # 白色系（R,G,B都>240）
    whites = [(name, rgb) for name, rgb in colors if all(c > 240 for c in rgb)]
    if whites:
        print(f"\n白色系 ({len(whites)}种):")
        for name, rgb in whites:
            print(f"  {name:20s} RGB{rgb}")
    
    # 蓝色系（B > R and B > G）
    blues = [(name, rgb) for name, rgb in colors if rgb[2] > rgb[0] and rgb[2] > rgb[1]]
    if blues:
        print(f"\n蓝色系 ({len(blues)}种):")
        for name, rgb in blues:
            print(f"  {name:20s} RGB{rgb}")
    
    # 灰色系（R≈G≈B，且在180-240之间）
    grays = [(name, rgb) for name, rgb in colors 
             if 180 <= min(rgb) and max(rgb) <= 240 
             and max(rgb) - min(rgb) < 20]
    if grays:
        print(f"\n灰色系 ({len(grays)}种):")
        for name, rgb in grays:
            print(f"  {name:20s} RGB{rgb}")
    
    # 红色系
    reds = [(name, rgb) for name, rgb in colors if rgb[0] > 200 and rgb[1] < 50 and rgb[2] < 50]
    if reds:
        print(f"\n红色系 ({len(reds)}种):")
        for name, rgb in reds:
            print(f"  {name:20s} RGB{rgb}")
    
    # 建议
    print("\n" + "=" * 80)
    print("优化建议")
    print("=" * 80)
    
    if len(whites) > 2:
        print(f"\n⚠️  白色系有 {len(whites)} 种，建议保留2-3种即可：")
        print("  - 纯白 (255,255,255) - 通用")
        print("  - 浅白 (248,248,248) - 日本等国标准")
        print("  - 极浅白 (250,250,250) - 可选")
    
    if len(blues) > 4:
        print(f"\n⚠️  蓝色系有 {len(blues)} 种，建议保留3-4种即可：")
        print("  - 标准蓝 - 中国常用")
        print("  - 美国护照蓝")
        print("  - 英国签证蓝")
        print("  - 泰国签证蓝（可选）")

if __name__ == '__main__':
    analyze_colors()
