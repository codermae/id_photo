"""
测试新功能
"""
from config.config import PHOTO_SPECS, BACKGROUND_COLORS, PHOTO_SPEC_DETAILS

def test_new_specs():
    """测试新增的证件照规格"""
    print("=== 测试证件照规格 ===")
    print(f"总规格数: {len(PHOTO_SPECS)}")
    
    # 测试中国标准
    china_specs = ['一寸', '小二寸', '二寸', '大一寸']
    print(f"\n中国标准 ({len(china_specs)}种):")
    for spec in china_specs:
        if spec in PHOTO_SPECS:
            size = PHOTO_SPECS[spec]
            print(f"  ✓ {spec}: {size[0]}×{size[1]} 像素")
        else:
            print(f"  ✗ {spec}: 未找到")
    
    # 测试国际标准
    intl_specs = ['美国护照', '欧盟护照', '英国签证', '日本护照', '印度签证', '泰国签证']
    print(f"\n国际标准 ({len(intl_specs)}种):")
    for spec in intl_specs:
        if spec in PHOTO_SPECS:
            size = PHOTO_SPECS[spec]
            print(f"  ✓ {spec}: {size[0]}×{size[1]} 像素")
        else:
            print(f"  ✗ {spec}: 未找到")
    
    # 测试特殊规格
    special_specs = ['驾驶证', '社保卡', '学生证', '工作证']
    print(f"\n特殊规格 ({len(special_specs)}种):")
    for spec in special_specs:
        if spec in PHOTO_SPECS:
            size = PHOTO_SPECS[spec]
            print(f"  ✓ {spec}: {size[0]}×{size[1]} 像素")
        else:
            print(f"  ✗ {spec}: 未找到")

def test_new_colors():
    """测试新增的背景颜色"""
    print("\n=== 测试背景颜色 ===")
    print(f"总颜色数: {len(BACKGROUND_COLORS)}")
    
    # 测试基础颜色
    basic_colors = ['白色', '蓝色', '红色', '灰色']
    print(f"\n基础颜色 ({len(basic_colors)}种):")
    for color in basic_colors:
        if color in BACKGROUND_COLORS:
            rgb = BACKGROUND_COLORS[color]
            print(f"  ✓ {color}: RGB{rgb}")
        else:
            print(f"  ✗ {color}: 未找到")
    
    # 测试国际标准颜色
    intl_colors = ['美国护照蓝', '欧盟护照灰', '英国签证蓝', '日本护照白']
    print(f"\n国际标准颜色 ({len(intl_colors)}种):")
    for color in intl_colors:
        if color in BACKGROUND_COLORS:
            rgb = BACKGROUND_COLORS[color]
            print(f"  ✓ {color}: RGB{rgb}")
        else:
            print(f"  ✗ {color}: 未找到")

def test_spec_details():
    """测试规格详细信息"""
    print("\n=== 测试规格详细信息 ===")
    print(f"详细信息数: {len(PHOTO_SPEC_DETAILS)}")
    
    # 测试几个关键规格的详细信息
    test_specs = ['一寸', '美国护照', '欧盟护照', '泰国签证']
    for spec in test_specs:
        if spec in PHOTO_SPEC_DETAILS:
            details = PHOTO_SPEC_DETAILS[spec]
            print(f"\n{spec}:")
            print(f"  尺寸: {details['size_mm']}mm")
            print(f"  像素: {details['size_px']}px")
            print(f"  DPI: {details['dpi']}")
            print(f"  用途: {details['usage']}")
            print(f"  国家: {details['country']}")
        else:
            print(f"  ✗ {spec}: 详细信息未找到")

def test_imports():
    """测试新模块导入"""
    print("\n=== 测试模块导入 ===")
    
    try:
        from views.multi_spec_dialog import MultiSpecDialog
        print("  ✓ MultiSpecDialog 导入成功")
    except Exception as e:
        print(f"  ✗ MultiSpecDialog 导入失败: {e}")
    
    try:
        from controllers.hifi_pipeline import HiFiPipeline
        print("  ✓ HiFiPipeline 导入成功")
    except Exception as e:
        print(f"  ✗ HiFiPipeline 导入失败: {e}")

if __name__ == "__main__":
    print("新功能测试")
    print("=" * 50)
    
    test_new_specs()
    test_new_colors()
    test_spec_details()
    test_imports()
    
    print("\n" + "=" * 50)
    print("测试完成！")