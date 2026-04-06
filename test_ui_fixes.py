"""
测试UI修复
"""
import sys
from PyQt5.QtWidgets import QApplication
from views.process_view import ProcessView

def test_ui_fixes():
    """测试UI修复"""
    print("=" * 60)
    print("测试UI修复")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    try:
        view = ProcessView()
        
        # 测试1: 检查规格数量（应该是22个，不是10个）
        print(f"\n1. 规格数量: {len(view.spec_checkboxes)}")
        if len(view.spec_checkboxes) == 22:
            print("   ✓ 规格已展开显示所有22个")
        else:
            print(f"   ✗ 规格数量不对，应该是22个")
        
        # 测试2: 检查Alpha Matte文本
        alpha_text = view.alpha_matting_check.text()
        print(f"\n2. Alpha Matte文本: '{alpha_text}'")
        if "边缘增强" in alpha_text:
            print("   ✓ Alpha Matte文本已更新")
        else:
            print("   ✗ Alpha Matte文本未更新")
        
        # 测试3: 检查操作按钮布局
        print(f"\n3. 操作按钮:")
        if hasattr(view, 'manual_crop_btn'):
            print("   ✓ 裁剪按钮存在")
        else:
            print("   ✗ 裁剪按钮缺失")
        
        if hasattr(view, 'save_btn'):
            print("   ✓ 保存按钮存在")
        else:
            print("   ✗ 保存按钮缺失")
        
        # 测试4: 检查对比按钮文本
        compare_text = view.compare_btn.text()
        print(f"\n4. 对比按钮文本: '{compare_text}'")
        if compare_text == "📷 对比":
            print("   ✓ 对比按钮文本正确")
        else:
            print("   ✗ 对比按钮文本不对")
        
        # 测试5: 检查模式下拉框
        mode_items = [view.bg_mode_combo.itemText(i) for i in range(view.bg_mode_combo.count())]
        print(f"\n5. 模式选项: {mode_items}")
        if '精细' in mode_items and '高保真' in mode_items:
            print("   ✓ 模式选项正确")
        else:
            print("   ✗ 模式选项不对")
        
        print("\n" + "=" * 60)
        print("✓ UI修复测试完成")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_ui_fixes()
    sys.exit(0 if success else 1)
