"""
语音播放助手 - 用于播放提示语音
"""
import pyttsx3
import threading
import logging
import re
import time

logger = logging.getLogger(__name__)


class VoiceHelper:
    """语音播放助手"""
    
    def __init__(self):
        """初始化"""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 120)  # 语速（降低到120，更清晰）
            self.engine.setProperty('volume', 0.9)  # 音量
            self.available = True
            self.last_speak_time = 0  # 上次播放时间
            self.min_interval = 1.5  # 最小间隔（秒），避免语音重叠
            logger.info("[✓] 语音引擎初始化成功")
        except Exception as e:
            logger.warning(f"[⚠] 语音引擎初始化失败: {e}")
            self.available = False
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本，移除图标和特殊符号
        
        Args:
            text: 原始文本
        
        Returns:
            清理后的文本
        """
        # 移除所有非中文、非英文、非数字的字符（除了空格和标点）
        # 保留中文、英文、数字、空格、中文标点
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？；：]', '', text)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def speak(self, text: str, async_mode: bool = True, force: bool = False):
        """
        播放语音
        
        Args:
            text: 要播放的文本
            async_mode: 是否异步播放（不阻塞主线程）
            force: 是否强制播放（忽略时间间隔限制）
        """
        if not self.available:
            return
        
        # 清理文本
        clean_text = self._clean_text(text)
        if not clean_text:
            return
        
        # 检查时间间隔，避免语音重叠
        current_time = time.time()
        if not force and (current_time - self.last_speak_time) < self.min_interval:
            return
        
        self.last_speak_time = current_time
        
        try:
            if async_mode:
                # 异步播放，不阻塞主线程
                thread = threading.Thread(target=self._speak_sync, args=(clean_text,))
                thread.daemon = True
                thread.start()
            else:
                # 同步播放
                self._speak_sync(clean_text)
        except Exception as e:
            logger.error(f"语音播放失败: {e}")
    
    def _speak_sync(self, text: str):
        """同步播放语音"""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"语音播放异常: {e}")
    
    def close(self):
        """关闭语音引擎"""
        try:
            if self.engine:
                self.engine.stop()
            self.available = False
        except Exception as e:
            logger.error(f"关闭语音引擎失败: {e}")


# 全局实例
_voice_helper = None


def get_voice_helper() -> VoiceHelper:
    """获取全局语音助手实例"""
    global _voice_helper
    if _voice_helper is None:
        _voice_helper = VoiceHelper()
    return _voice_helper
