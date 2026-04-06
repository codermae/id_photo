"""
可拖拽裁剪对话框
允许用户手动调整裁剪框位置和大小
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QWidget)
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap, QImage
import cv2
import numpy as np
from config.config import PHOTO_SPECS

class CropDialog(QDialog):
    """可拖拽裁剪对话框"""
    
    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.original_image = image.copy()
        self.display_image = None
        self.scale_factor = 1.0
        
        # 裁剪框（在显示图像上的坐标）
        self.crop_rect = None
        
        # 拖拽状态
        self.dragging = False
        self.resizing = False
        self.resize_corner = None
        self.drag_start_pos = None
        self.drag_start_rect = None
        
        # 证件照规格：使用全量配置，避免裁剪规格列表不全
        # PHOTO_SPECS 的 value 为像素尺寸（如 590x826）
        self.specs = dict(PHOTO_SPECS)
        
        self.current_spec = '一寸'
        
        self.init_ui()
        self.load_image()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('手动裁剪 - 拖拽调整裁剪框')
        self.setMinimumSize(800, 600)
        
        # 主布局
        layout = QVBoxLayout()
        
        # 顶部控制栏
        control_layout = QHBoxLayout()
        
        # 规格选择
        control_layout.addWidget(QLabel('证件照规格:'))
        self.spec_combo = QComboBox()
        self.spec_combo.addItems(list(self.specs.keys()))
        self.spec_combo.currentTextChanged.connect(self.on_spec_changed)
        control_layout.addWidget(self.spec_combo)
        
        control_layout.addStretch()
        
        # 说明文字
        help_label = QLabel('💡 拖拽裁剪框移动位置，拖拽四角调整大小')
        help_label.setStyleSheet('color: #666; font-size: 12px;')
        control_layout.addWidget(help_label)
        
        layout.addLayout(control_layout)
        
        # 图像显示区域
        self.image_label = CropImageLabel(self)
        layout.addWidget(self.image_label)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_btn = QPushButton('重置')
        self.reset_btn.clicked.connect(self.reset_crop)
        button_layout.addWidget(self.reset_btn)
        
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton('确定裁剪')
        self.ok_btn.setStyleSheet('background-color: #4CAF50; color: white; padding: 8px 20px;')
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_image(self):
        """加载图像并初始化裁剪框"""
        h, w = self.original_image.shape[:2]
        
        # 计算缩放比例以适应窗口
        max_width = 750
        max_height = 500
        
        scale_w = max_width / w
        scale_h = max_height / h
        self.scale_factor = min(scale_w, scale_h, 1.0)  # 不放大，只缩小
        
        # 缩放图像用于显示
        display_w = int(w * self.scale_factor)
        display_h = int(h * self.scale_factor)
        self.display_image = cv2.resize(self.original_image, (display_w, display_h))
        
        # 初始化裁剪框（居中）
        self.init_crop_rect()
        
        # 更新显示
        self.update_display()
    
    def init_crop_rect(self):
        """初始化裁剪框"""
        spec_w, spec_h = self.specs[self.current_spec]
        ratio = spec_w / spec_h
        
        display_h, display_w = self.display_image.shape[:2]
        
        # 计算裁剪框大小（占显示图像的70%）
        crop_h = int(display_h * 0.7)
        crop_w = int(crop_h * ratio)
        
        # 如果太宽，以宽度为准
        if crop_w > display_w * 0.9:
            crop_w = int(display_w * 0.7)
            crop_h = int(crop_w / ratio)
        
        # 居中
        x = (display_w - crop_w) // 2
        y = (display_h - crop_h) // 2
        
        self.crop_rect = QRect(x, y, crop_w, crop_h)
    
    def on_spec_changed(self, spec):
        """规格改变时重新计算裁剪框"""
        self.current_spec = spec
        self.init_crop_rect()
        self.update_display()
    
    def reset_crop(self):
        """重置裁剪框"""
        self.init_crop_rect()
        self.update_display()
    
    def update_display(self):
        """更新显示"""
        if self.display_image is None:
            return
        
        # 转换为QPixmap
        h, w, ch = self.display_image.shape
        bytes_per_line = ch * w
        q_image = QImage(self.display_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image.rgbSwapped())
        
        self.image_label.set_image(pixmap, self.crop_rect)
    
    def get_cropped_image(self):
        """获取裁剪后的图像"""
        if self.crop_rect is None:
            return None
        
        # 将显示坐标转换为原始图像坐标
        x = int(self.crop_rect.x() / self.scale_factor)
        y = int(self.crop_rect.y() / self.scale_factor)
        w = int(self.crop_rect.width() / self.scale_factor)
        h = int(self.crop_rect.height() / self.scale_factor)
        
        # 确保不超出边界
        orig_h, orig_w = self.original_image.shape[:2]
        x = max(0, min(x, orig_w - 1))
        y = max(0, min(y, orig_h - 1))
        w = min(w, orig_w - x)
        h = min(h, orig_h - y)
        
        # 裁剪
        cropped = self.original_image[y:y+h, x:x+w]
        
        # 调整到目标尺寸
        target_w, target_h = self.specs[self.current_spec]
        final = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        
        return final


class CropImageLabel(QLabel):
    """可交互的图像标签"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_dialog = parent
        self.pixmap = None
        self.crop_rect = None
        self.setMouseTracking(True)
        
        # 拖拽状态
        self.dragging = False
        self.resizing = False
        self.resize_corner = None
        self.last_pos = None
        
        # 角点大小
        self.corner_size = 10
    
    def set_image(self, pixmap, crop_rect):
        """设置图像和裁剪框"""
        self.pixmap = pixmap
        self.crop_rect = crop_rect
        self.setPixmap(pixmap)
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        
        # 1. 先绘制完整的图像
        if self.pixmap:
            painter.drawPixmap(0, 0, self.pixmap)
        
        if self.crop_rect is None:
            painter.end()
            return
        
        # 2. 只在裁剪框外绘制半透明遮罩
        # 创建一个遮罩区域（整个图像减去裁剪框）
        from PyQt5.QtGui import QRegion
        full_region = QRegion(self.rect())
        crop_region = QRegion(self.crop_rect)
        mask_region = full_region.subtracted(crop_region)
        
        # 设置裁剪区域为遮罩区域
        painter.setClipRegion(mask_region)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 60))  # 只在裁剪框外绘制遮罩
        
        # 重置裁剪区域
        painter.setClipping(False)
        
        # 3. 绘制裁剪框边框
        pen = QPen(QColor(0, 255, 0), 2)
        painter.setPen(pen)
        painter.drawRect(self.crop_rect)
        
        # 4. 绘制九宫格辅助线
        pen = QPen(QColor(255, 255, 255, 200), 1)
        painter.setPen(pen)
        
        # 垂直线
        third_w = self.crop_rect.width() // 3
        painter.drawLine(
            self.crop_rect.x() + third_w, self.crop_rect.y(),
            self.crop_rect.x() + third_w, self.crop_rect.y() + self.crop_rect.height()
        )
        painter.drawLine(
            self.crop_rect.x() + third_w * 2, self.crop_rect.y(),
            self.crop_rect.x() + third_w * 2, self.crop_rect.y() + self.crop_rect.height()
        )
        
        # 水平线
        third_h = self.crop_rect.height() // 3
        painter.drawLine(
            self.crop_rect.x(), self.crop_rect.y() + third_h,
            self.crop_rect.x() + self.crop_rect.width(), self.crop_rect.y() + third_h
        )
        painter.drawLine(
            self.crop_rect.x(), self.crop_rect.y() + third_h * 2,
            self.crop_rect.x() + self.crop_rect.width(), self.crop_rect.y() + third_h * 2
        )
        
        # 绘制四个角点
        corner_rects = self.get_corner_rects()
        painter.setBrush(QColor(0, 255, 0))
        for rect in corner_rects:
            painter.drawRect(rect)
        
        # 显示尺寸信息
        spec_w, spec_h = self.parent_dialog.specs[self.parent_dialog.current_spec]
        info_text = f'{self.parent_dialog.current_spec} ({spec_w}x{spec_h}px)'
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            self.crop_rect.x() + 5,
            self.crop_rect.y() - 5,
            info_text
        )
        
        # 结束绘制
        painter.end()
    
    def get_corner_rects(self):
        """获取四个角点的矩形"""
        s = self.corner_size
        corners = []
        
        # 左上
        corners.append(QRect(
            self.crop_rect.x() - s//2,
            self.crop_rect.y() - s//2,
            s, s
        ))
        
        # 右上
        corners.append(QRect(
            self.crop_rect.x() + self.crop_rect.width() - s//2,
            self.crop_rect.y() - s//2,
            s, s
        ))
        
        # 左下
        corners.append(QRect(
            self.crop_rect.x() - s//2,
            self.crop_rect.y() + self.crop_rect.height() - s//2,
            s, s
        ))
        
        # 右下
        corners.append(QRect(
            self.crop_rect.x() + self.crop_rect.width() - s//2,
            self.crop_rect.y() + self.crop_rect.height() - s//2,
            s, s
        ))
        
        return corners
    
    def get_corner_at_pos(self, pos):
        """获取鼠标位置对应的角点"""
        corners = self.get_corner_rects()
        for i, rect in enumerate(corners):
            if rect.contains(pos):
                return i
        return None
    
    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() != Qt.LeftButton or self.crop_rect is None:
            return
        
        pos = event.pos()
        
        # 检查是否点击角点
        corner = self.get_corner_at_pos(pos)
        if corner is not None:
            self.resizing = True
            self.resize_corner = corner
            self.last_pos = pos
            self.setCursor(Qt.SizeFDiagCursor)
            return
        
        # 检查是否点击裁剪框内部
        if self.crop_rect.contains(pos):
            self.dragging = True
            self.last_pos = pos
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        """鼠标移动"""
        pos = event.pos()
        
        if self.resizing and self.last_pos:
            # 调整大小
            delta = pos - self.last_pos
            self.resize_crop_rect(delta)
            self.last_pos = pos
            self.update()
            
        elif self.dragging and self.last_pos:
            # 移动裁剪框
            delta = pos - self.last_pos
            self.crop_rect.translate(delta)
            
            # 限制在图像范围内
            if self.crop_rect.x() < 0:
                self.crop_rect.moveLeft(0)
            if self.crop_rect.y() < 0:
                self.crop_rect.moveTop(0)
            if self.crop_rect.right() > self.width():
                self.crop_rect.moveRight(self.width())
            if self.crop_rect.bottom() > self.height():
                self.crop_rect.moveBottom(self.height())
            
            self.last_pos = pos
            self.update()
            
        else:
            # 更新鼠标样式
            corner = self.get_corner_at_pos(pos)
            if corner is not None:
                self.setCursor(Qt.SizeFDiagCursor)
            elif self.crop_rect and self.crop_rect.contains(pos):
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        self.dragging = False
        self.resizing = False
        self.resize_corner = None
        self.setCursor(Qt.ArrowCursor)
    
    def resize_crop_rect(self, delta):
        """调整裁剪框大小（保持宽高比）"""
        if self.resize_corner is None:
            return
        
        spec_w, spec_h = self.parent_dialog.specs[self.parent_dialog.current_spec]
        ratio = spec_w / spec_h
        
        # 根据角点调整
        if self.resize_corner == 0:  # 左上
            new_width = self.crop_rect.width() - delta.x()
            new_height = int(new_width / ratio)
            
            if new_width > 50 and new_height > 50:
                self.crop_rect.setLeft(self.crop_rect.right() - new_width)
                self.crop_rect.setTop(self.crop_rect.bottom() - new_height)
                
        elif self.resize_corner == 1:  # 右上
            new_width = self.crop_rect.width() + delta.x()
            new_height = int(new_width / ratio)
            
            if new_width > 50 and new_height > 50:
                self.crop_rect.setWidth(new_width)
                self.crop_rect.setTop(self.crop_rect.bottom() - new_height)
                
        elif self.resize_corner == 2:  # 左下
            new_width = self.crop_rect.width() - delta.x()
            new_height = int(new_width / ratio)
            
            if new_width > 50 and new_height > 50:
                self.crop_rect.setLeft(self.crop_rect.right() - new_width)
                self.crop_rect.setHeight(new_height)
                
        elif self.resize_corner == 3:  # 右下
            new_width = self.crop_rect.width() + delta.x()
            new_height = int(new_width / ratio)
            
            if new_width > 50 and new_height > 50:
                self.crop_rect.setWidth(new_width)
                self.crop_rect.setHeight(new_height)
        
        # 限制在图像范围内
        if self.crop_rect.left() < 0:
            self.crop_rect.moveLeft(0)
        if self.crop_rect.top() < 0:
            self.crop_rect.moveTop(0)
        if self.crop_rect.right() > self.width():
            self.crop_rect.moveRight(self.width())
        if self.crop_rect.bottom() > self.height():
            self.crop_rect.moveBottom(self.height())
