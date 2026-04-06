"""
详细调试初始化问题
"""
import sys
sys.dont_write_bytecode = True

from PyQt5.QtWidgets import QApplication

# 修改ProcessView的init_ui方法，添加调试信息
def debug_init_ui():
    """调试init_ui方法"""
    print("开始详细调试...")
    
    app = QApplication(sys.argv)
    
    try:
        # 导入并修改ProcessView
        from views.process_view import ProcessView
        
        # 保存原始的init_ui方法
        original_init_ui = ProcessView.init_ui
        
        def debug_init_ui_wrapper(self):
            """带调试信息的init_ui包装器"""
            print("  开始执行init_ui...")
            
            try:
                # 手动执行init_ui的关键部分
                from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QComboBox, 
                                           QPushButton, QWidget, QGroupBox, QCheckBox, 
                                           QGridLayout, QScrollArea)
                from PyQt5.QtCore import Qt
                from config.config import PHOTO_SPECS, BACKGROUND_COLORS
                from collections import defaultdict
                
                print("  1. 创建主布局...")
                main_layout = QHBoxLayout(self)
                left_layout = QVBoxLayout()
                
                print("  2. 创建顶部控制...")
                top_control_layout = QHBoxLayout()
                top_control_layout.addWidget(QLabel("任务:"))
                self.collection_combo = QComboBox()
                top_control_layout.addWidget(self.collection_combo)
                
                load_btn = QPushButton("📁 选择图像")
                top_control_layout.addWidget(load_btn)
                
                self.compare_btn = QPushButton("📷 对比")
                top_control_layout.addWidget(self.compare_btn)
                
                top_control_layout.addStretch()
                left_layout.addLayout(top_control_layout)
                
                print("  3. 创建预览区域...")
                self.preview_container = QWidget()
                self.preview_container_layout = QHBoxLayout(self.preview_container)
                
                self.preview_label = QLabel()
                self.preview_label.setMinimumSize(350, 400)
                self.preview_container_layout.addWidget(self.preview_label)
                
                self.original_preview_label = QLabel()
                self.original_preview_label.setMinimumSize(350, 400)
                self.original_preview_label.setVisible(False)
                self.preview_container_layout.addWidget(self.original_preview_label)
                
                left_layout.addWidget(self.preview_container)
                
                print("  4. 创建质量评分...")
                quality_layout = QHBoxLayout()
                quality_layout.addWidget(QLabel("质量:"))
                self.quality_label = QLabel("未加载")
                quality_layout.addWidget(self.quality_label)
                quality_layout.addStretch()
                left_layout.addLayout(quality_layout)
                
                print("  5. 创建右侧滚动区域...")
                right_scroll = QScrollArea()
                right_scroll.setWidgetResizable(True)
                right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                
                right_widget = QWidget()
                right_layout = QVBoxLayout(right_widget)
                right_layout.setSpacing(8)
                
                print("  6. 创建规格选择...")
                spec_group = QGroupBox("规格")
                spec_layout = QVBoxLayout()
                spec_layout.setSpacing(4)
                
                # 快速选择按钮
                quick_btn_layout = QHBoxLayout()
                select_all_spec_btn = QPushButton("全选")
                quick_btn_layout.addWidget(select_all_spec_btn)
                quick_btn_layout.addStretch()
                spec_layout.addLayout(quick_btn_layout)
                
                print("  7. 创建规格复选框...")
                spec_widget = QWidget()
                spec_grid = QGridLayout(spec_widget)
                spec_grid.setSpacing(2)
                
                self.spec_checkboxes = {}
                print(f"     初始化spec_checkboxes: {type(self.spec_checkboxes)}")
                
                size_groups = defaultdict(list)
                for spec_name, size in PHOTO_SPECS.items():
                    size_groups[size].append(spec_name)
                
                print(f"     size_groups数量: {len(size_groups)}")
                
                row, col = 0, 0
                for size, specs in size_groups.items():
                    size_str = f"{size[0]}x{size[1]}px"
                    
                    if len(specs) == 1:
                        display_name = f"{size_str} {specs[0]}"
                        tooltip = f"尺寸: {size[0]}×{size[1]}px"
                    else:
                        display_name = f"{size_str} {specs[0]} 等{len(specs)}种"
                        tooltip = f"相同尺寸 {size[0]}×{size[1]}px:\\n" + "\\n".join(specs)
                    
                    checkbox = QCheckBox(display_name)
                    checkbox.setToolTip(tooltip)
                    checkbox.spec_name = specs[0]
                    
                    if "一寸" in display_name:
                        checkbox.setChecked(True)
                    
                    size_key = f"{size[0]}x{size[1]}"
                    self.spec_checkboxes[size_key] = checkbox
                    spec_grid.addWidget(checkbox, row, col)
                    
                    col += 1
                    if col >= 3:
                        col = 0
                        row += 1
                
                print(f"     创建了{len(self.spec_checkboxes)}个规格复选框")
                
                spec_layout.addWidget(spec_widget)
                spec_group.setLayout(spec_layout)
                right_layout.addWidget(spec_group)
                
                print("  8. 创建背景色选择...")
                bg_group = QGroupBox("背景色")
                bg_layout = QVBoxLayout()
                
                self.bg_checkboxes = {}
                for color_name in BACKGROUND_COLORS.keys():
                    checkbox = QCheckBox(color_name)
                    if color_name == '蓝色':
                        checkbox.setChecked(True)
                    self.bg_checkboxes[color_name] = checkbox
                
                bg_layout.addWidget(QLabel("颜色选择"))
                bg_group.setLayout(bg_layout)
                right_layout.addWidget(bg_group)
                
                print("  9. 完成布局...")
                right_scroll.setWidget(right_widget)
                main_layout.addLayout(left_layout, 1)
                main_layout.addWidget(right_scroll, 1)
                
                print("  init_ui执行完成!")
                
            except Exception as e:
                print(f"  init_ui执行出错: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # 替换init_ui方法
        ProcessView.init_ui = debug_init_ui_wrapper
        
        print("创建ProcessView实例...")
        view = ProcessView()
        
        print("检查结果:")
        print(f"  spec_checkboxes: {'存在' if hasattr(view, 'spec_checkboxes') else '缺失'}")
        if hasattr(view, 'spec_checkboxes'):
            print(f"  规格数量: {len(view.spec_checkboxes)}")
        
        return True
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    debug_init_ui()