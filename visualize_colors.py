"""
可视化背景颜色对比
"""
from config.config import BACKGROUND_COLORS
import math

def rgb_distance(rgb1, rgb2):
    """计算两个RGB颜色的欧氏距离"""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))

def rgb_to_ansi(rgb):
    """RGB转ANSI终端颜色代码"""
    return f"\033[48;2;{rgb[0]};{rgb[1]};{rgb[2]}m"

def reset_ansi():
    """重置ANSI颜色"""
    return "\033[0m"

def visualize_colors():
    """可视化显示所有颜色"""
    print("=" * 80)
    print("背景颜色可视化对比")
    print("=" * 80)
    
    colors = list(BACKGROUND_COLORS.items())
    
    print(f"\n总颜色数: {len(colors)}\n")
    
    # 按类型分组显示
    groups = {
        '基础颜色': ['白色', '蓝色', '红色', '灰色'],
        '国际标准': [name for name in BACKGROUND_COLORS.keys() 
                    if name not in ['白色', '蓝色', '红色', '灰色']]
    }
    
    for group_name, color_names in groups.items():
        print(f"\n{group_name}:")
        print("-" * 80)
        
        for name in color_names:
            if name in BACKGROUND_COLORS:
                rgb = BACKGROUND_COLORS[name]
                
                # 创建颜色块（使用空格作为色块）
                color_block = rgb_to_ansi(rgb) + "    " + reset_ansi()
                
                # 计算与纯白的距离
                white_distance = rgb_distance(rgb, (255, 255, 255))
                
                # 判断文字颜色（深色背景用白字，浅色背景用黑字）
                brightness = sum(rgb) / 3
                text_color = "深色" if brightness < 128 else "浅色"
                
                print(f"  {color_block} {name:15s} RGB{str(rgb):20s} "
                      f"亮度:{brightness:5.1f} 与白色距离:{white_distance:5.1f}")
    
    # 显示相似度矩阵
    print("\n" + "=" * 80)
    print("颜色相似度矩阵（数字为RGB距离）")
    print("=" * 80)
    print("\n距离说明: <10=几乎相同, 10-30=相似, 30-50=接近, >50=明显不同\n")
    
    # 只显示相似的颜色对
    similar_threshold = 30
    similar_pairs = []
    
    for i, (name1, rgb1) in enumerate(colors):
        for j, (name2, rgb2) in enumerate(colors[i+1:], i+1):
            distance = rgb_distance(rgb1, rgb2)
            if distance < similar_threshold:
                similar_pairs.append((name1, name2, distance))
    
    if similar_pairs:
        for name1, name2, distance in sorted(similar_pairs, key=lambda x: x[2]):
            status = "⚠️ 几乎相同" if distance < 10 else "⚠️ 相似" if distance < 20 else "✓ 可接受"
            print(f"  {name1:15s} ↔ {name2:15s}  距离: {distance:5.1f}  {status}")
    else:
        print("  ✓ 所有颜色差异明显（距离 > 30）")
    
    # 优化建议
    print("\n" + "=" * 80)
    print("最终优化建议")
    print("=" * 80)
    
    # 检查是否还有可以合并的
    very_similar = [p for p in similar_pairs if p[2] < 15]
    
    if very_similar:
        print("\n⚠️  以下颜色非常相似，建议考虑合并：\n")
        for name1, name2, distance in very_similar:
            rgb1 = BACKGROUND_COLORS[name1]
            rgb2 = BACKGROUND_COLORS[name2]
            print(f"  {name1} RGB{rgb1}")
            print(f"  {name2} RGB{rgb2}")
            print(f"  → 距离: {distance:.2f}")
            print(f"  → 建议: 保留 '{name1}'，移除 '{name2}'\n")
    else:
        print("\n✓ 当前配置已经很好，所有颜色都有明显差异")
        print("✓ 建议保持现状，8种颜色覆盖了所有主要需求")
    
    # 统计信息
    print("\n" + "=" * 80)
    print("统计信息")
    print("=" * 80)
    
    from collections import defaultdict
    size_groups = defaultdict(list)
    from config.config import PHOTO_SPECS
    for spec_name, size in PHOTO_SPECS.items():
        size_groups[size].append(spec_name)
    
    unique_sizes = len(size_groups)
    total_colors = len(BACKGROUND_COLORS)
    
    print(f"\n规格: {unique_sizes} 种不同尺寸")
    print(f"颜色: {total_colors} 种")
    print(f"全选生成: {unique_sizes} × {total_colors} = {unique_sizes * total_colors} 张")
    print(f"\n相比原始配置 (22规格 × 17颜色 = 374张):")
    print(f"减少: {374 - unique_sizes * total_colors} 张 ({(374 - unique_sizes * total_colors) / 374 * 100:.1f}%)")

if __name__ == '__main__':
    visualize_colors()
