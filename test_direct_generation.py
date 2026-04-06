"""
测试直接生成功能
"""
import sys
from PyQt5.QtWidgets import QApplication

def test_imports():
    """测试所有必要的导入"""
    print("测试导入...")
    
    try:
        from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                     QLabel, QComboBox, QSlider, QGroupBox, QMessageBox, 
                                     QFileDialog, QSpinBox, QCheckBox, QGridLayout, QDialog, 
                                     QInputDialog, QScrollArea, QProgressDialog)
        print("✓ PyQt5 导入成功")
    except ImportError as e:
        print(f"✗ PyQt5 导入失败: {e}")
        return False
    
    try:
        from config.config import PHOTO_SPECS, BACKGROUND_COLORS
        print(f"✓ 配置导入成功: {len(PHOTO_SPECS)} 规格, {len(BACKGROUND_COLORS)} 颜色")
    except ImportError as e:
        print(f"✗ 配置导入失败: {e}")
        return False
    
    return True

def test_spec_grouping():
    """测试规格分组逻辑"""
    print("\n测试规格分组...")
    
    from config.config import PHOTO_SPECS
    from collections import defaultdict
    
    size_groups = defaultdict(list)
    for spec_name, size in PHOTO_SPECS.items():
        size_groups[size].append(spec_name)
    
    print(f"总规格数: {len(PHOTO_SPECS)}")
    print(f"不同尺寸数: {len(size_groups)}")
    
    for size, specs in size_groups.items():
        if len(specs) > 1:
            print(f"  {size}: {specs}")
    
    return True

def test_multi_spec_logic():
    """测试多规格生成逻辑"""
    print("\n测试多规格生成逻辑...")
    
    # 模拟用户选择
    test_cases = [
        (["一寸"], ["蓝色"], "单规格单颜色"),
        (["一寸", "二寸"], ["蓝色"], "多规格单颜色"),
        (["一寸"], ["蓝色", "白色"], "单规格多颜色"),
        (["一寸", "二寸"], ["蓝色", "白色"], "多规格多颜色"),
    ]
    
    for specs, colors, desc in test_cases:
        total = len(specs) * len(colors)
        should_batch = len(specs) > 1 or len(colors) > 1
        
        print(f"  {desc}:")
        print(f"    规格: {specs}")
        print(f"    颜色: {colors}")
        print(f"    总数: {total}")
        print(f"    批量生成: {'是' if should_batch else '否'}")
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("直接生成功能测试")
    print("=" * 60)
    
    success = True
    
    # 测试导入
    if not test_imports():
        success = False
    
    # 测试规格分组
    if not test_spec_grouping():
        success = False
    
    # 测试多规格逻辑
    if not test_multi_spec_logic():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✓ 所有测试通过")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
