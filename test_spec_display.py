"""
测试规格显示
"""
import sys
from PyQt5.QtWidgets import QApplication
from views.process_view import ProcessView

def test_spec_display():
    """测试规格显示"""
    print("=" * 60)
    print("测试规格显示")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    try:
        view = ProcessView()
        
        print(f"\n规格复选框数量: {len(view.spec_checkboxes)}")
        print("\n规格列表:")
        
        for key, checkbox in view.spec_checkboxes.items():
            text = checkbox.text()
            tooltip = checkbox.toolTip()
            checked = "☑" if checkbox.isChecked() else "☐"
            print(f"  {checked} {text}")
            if tooltip:
                print(f"     提示: {tooltip}")
        
        # 检查是否有滚动区域
        has_scroll = False
        for child in view.findChildren(QApplication.instance().__class__.__bases__[0]):
            if "QScrollArea" in str(type(child)):
                has_scroll = True
                break
        
        print(f"\n是否有滚动区域: {'是' if has_scroll else '否'}")
        
        print("\n" + "=" * 60)
        if len(view.spec_checkboxes) == 10:
            print("✓ 规格折叠显示正确（10个不同尺寸）")
        else:
            print(f"✗ 规格数量不对，应该是10个，实际是{len(view.spec_checkboxes)}个")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_spec_display()
    sys.exit(0 if success else 1)
