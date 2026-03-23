"""
摄像头控制器
"""
import cv2
import threading
import numpy as np
from config.config import CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS

class CameraController:
    """摄像头控制器"""

    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.is_running = False
        self.frame = None
        self.thread = None
        self.callback = None

    def open(self, fast_mode=True):
        """打开摄像头
        
        Args:
            fast_mode: 是否使用快速模式（跳过参数设置，减少延迟）
        """
        try:
            print(f"[DEBUG] CameraController.open() - 开始打开摄像头 ID: {self.camera_id}")
            
            self.cap = cv2.VideoCapture(self.camera_id)
            print("[DEBUG] cv2.VideoCapture 创建完成")
            
            if fast_mode:
                print("[DEBUG] 使用快速模式 - 跳过参数设置以减少延迟")
                # 快速模式：跳过参数设置，使用摄像头默认设置
            else:
                # 标准模式：设置参数（会有延迟）
                width, height, fps = CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS
                print(f"[DEBUG] 使用标准模式: {width}x{height}, FPS: {fps}")
                
                print("[DEBUG] 开始设置摄像头参数...")
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                print("[DEBUG] 设置宽度完成")
                
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                print("[DEBUG] 设置高度完成")
                
                self.cap.set(cv2.CAP_PROP_FPS, fps)
                print("[DEBUG] 设置FPS完成")
                
                print("[DEBUG] 摄像头参数设置完成")
            
            print("[DEBUG] 检查摄像头是否打开...")
            if not self.cap.isOpened():
                print("[ERROR] 无法打开摄像头")
                return False
            
            print("[DEBUG] 摄像头状态检查完成")
            
            # 获取实际的摄像头参数
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            print(f"[INFO] 摄像头实际参数: {actual_width}x{actual_height}, FPS: {actual_fps}")
            
            # 尝试读取第一帧
            print("[DEBUG] 尝试读取第一帧...")
            ret, frame = self.cap.read()
            if ret:
                print(f"[DEBUG] 成功读取第一帧，尺寸: {frame.shape}")
            else:
                print("[WARNING] 读取第一帧失败")
            
            print(f"[INFO] 摄像头已打开 (ID: {self.camera_id})")
            return True
        except Exception as e:
            print(f"[ERROR] 打开摄像头失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def close(self):
        """关闭摄像头"""
        self.stop()
        if self.cap:
            self.cap.release()
            print("摄像头已关闭")

    def start(self, callback=None):
        """开始捕获"""
        print("[DEBUG] CameraController.start() - 开始启动摄像头捕获")
        
        if not self.cap or not self.cap.isOpened():
            print("[ERROR] 摄像头未打开")
            return False

        print("[DEBUG] 设置运行状态和回调函数")
        self.is_running = True
        self.callback = callback
        
        print("[DEBUG] 创建并启动捕获线程")
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
        print("[INFO] 摄像头捕获已启动")
        return True

    def stop(self):
        """停止捕获"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)

    def _capture_loop(self):
        """捕获循环"""
        print("[DEBUG] _capture_loop 开始运行")
        frame_count = 0
        
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame
                frame_count += 1
                
                # 每100帧输出一次调试信息
                if frame_count % 100 == 0:
                    print(f"[DEBUG] 已捕获 {frame_count} 帧")
                
                if self.callback:
                    self.callback(frame)
            else:
                print("[ERROR] 读取帧失败")
                break
        
        print("[DEBUG] _capture_loop 结束")

    def get_frame(self):
        """获取当前帧"""
        return self.frame

    def take_photo(self, filepath):
        """拍照"""
        if self.frame is None:
            print("没有可用的帧")
            return False

        try:
            cv2.imwrite(filepath, self.frame)
            print(f"照片已保存: {filepath}")
            return True
        except Exception as e:
            print(f"保存照片失败: {e}")
            return False

    def get_camera_info(self):
        """获取摄像头信息"""
        if not self.cap:
            return None

        info = {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.cap.get(cv2.CAP_PROP_FPS)),
            'brightness': self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            'contrast': self.cap.get(cv2.CAP_PROP_CONTRAST),
        }
        return info

    def set_brightness(self, value):
        """设置亮度"""
        if self.cap:
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)

    def set_contrast(self, value):
        """设置对比度"""
        if self.cap:
            self.cap.set(cv2.CAP_PROP_CONTRAST, value)

    @staticmethod
    def list_cameras():
        """列出可用的摄像头"""
        cameras = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append(i)
                cap.release()
        return cameras
