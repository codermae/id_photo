"""
测试布局优化
"""
import sys
from PyQt5.QtWidgets import QApplication
from views.process_view import ProcessView

def test_layout():
    """测试ProcessView布局"""
    print("=" * 60)
    print("测试布局优化")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    try:
        # 创建ProcessView实例
        view = ProcessView()
        
        # 检查关键控件是否存在
        checks = [
            ('collection_combo', '采集任务下拉框'),
            ('preview_label', '预览标签'),
            ('spec_checkboxes', '规格复选框'),
            ('bg_checkboxes', '背景色复选框'),
            ('bg_mode_combo', '模式下拉框'),
            ('alpha_matting_check', 'Alpha Matte复选框'),
            ('skin_smooth_check', '磨皮复选框'),
            ('remove_blemishes_check', '祛痘复选框'),
            ('brightness_slider', '亮度滑块'),
            ('contrast_slider', '对比度滑块'),
            ('process_btn', '应用处理按钮'),
            ('reset_btn', '重置按钮'),
            ('save_btn', '保存按钮'),
            ('compare_btn', '对比按钮'),
            ('manual_crop_btn', '手动裁剪按钮'),
        ]
        
        print("\n检查控件:")
        all_ok = True
        for attr, name in checks:
            if hasattr(view, attr):
                print(f"  ✓ {name}")
            else:
                print(f"  ✗ {name} - 缺失!")
                all_ok = False
        
        # 检查规格和颜色数量
        print(f"\n规格数量: {len(view.spec_checkboxes)}")
        print(f"颜色数量: {len(view.bg_checkboxes)}")
        
        # 检查预览区域尺寸
        preview_size = view.preview_label.minimumSize()
        print(f"\n预览区域最小尺寸: {preview_size.width()}x{preview_size.height()}")
        
        if all_ok:
            print("\n" + "=" * 60)
            print("✓ 所有控件检查通过")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("✗ 部分控件缺失")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_layout()
    sys.exit(0 if success else 1)
