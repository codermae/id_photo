"""
身份证读卡器控制器
支持0501SAM模块
"""
import threading
from datetime import datetime
from utils.id_card_photo_generator import IDCardPhotoSimulator

class IDCardReader:
    """身份证读卡器控制器"""

    def __init__(self, test_mode=False):
        self.is_connected = False
        self.reader_thread = None
        self.callback = None
        self.stop_flag = False
        self.test_mode = test_mode  # 测试模式标志
        self.test_card_data = None  # 测试卡片数据
        self.test_card_inserted = False  # 测试卡片是否已插入
        self.photo_simulator = IDCardPhotoSimulator()  # 身份证照片生成器

    def connect(self):
        """连接读卡器"""
        try:
            # 这里应该调用硬件SDK初始化
            # 示例：使用ctypes调用DLL
            # import ctypes
            # self.dll = ctypes.CDLL('path/to/reader.dll')
            
            self.is_connected = True
            print("身份证读卡器已连接")
            return True
        except Exception as e:
            print(f"连接读卡器失败: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """断开连接"""
        self.stop_flag = True
        if self.reader_thread:
            self.reader_thread.join(timeout=2)
        self.is_connected = False
        print("身份证读卡器已断开")

    def start_reading(self, callback=None):
        """开始读取身份证"""
        if not self.is_connected:
            print("读卡器未连接")
            return False

        self.callback = callback
        self.stop_flag = False
        self.reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.reader_thread.start()
        return True

    def stop_reading(self):
        """停止读取"""
        self.stop_flag = True

    def _read_loop(self):
        """读取循环 - 连续读取模式"""
        last_card_id = None
        
        while not self.stop_flag:
            try:
                card_data = self._read_card()
                
                # 如果读取到新的身份证（与上一次不同）
                if card_data and card_data.get('id_number') != last_card_id:
                    last_card_id = card_data.get('id_number')
                    if self.callback:
                        self.callback(card_data)
                
                # 如果身份证被移除（读取失败），重置
                elif not card_data:
                    last_card_id = None
                    
            except Exception as e:
                print(f"读卡错误: {e}")
                last_card_id = None
            
            # 每100ms检查一次
            import time
            time.sleep(0.1)

    def _read_card(self):
        """读取卡片数据"""
        try:
            # 测试模式：返回测试卡片数据或None
            if self.test_mode:
                if self.test_card_inserted and self.test_card_data:
                    return self.test_card_data
                else:
                    return None
            
            # 这里应该调用硬件SDK读取数据
            # 示例数据结构
            card_data = {
                'name': '张三',
                'id_number': '110101199001011234',
                'gender': '男',
                'nation': '汉',
                'birthday': '1990-01-01',
                'address': '北京市朝阳区',
                'issue_authority': '北京市公安局',
                'valid_period': '2020-01-01 ~ 2030-01-01',
                'id_photo': None,  # 二进制照片数据
                'read_time': datetime.now().isoformat()
            }
            return card_data
        except Exception as e:
            print(f"读卡失败: {e}")
            return None

    def validate_id_number(self, id_number):
        """验证身份证号"""
        if not id_number or len(id_number) != 18:
            return False
        
        # 简单的校验码验证
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = '10X98765432'
        
        try:
            total = sum(int(id_number[i]) * weights[i] for i in range(17))
            check_code = check_codes[total % 11]
            return id_number[17] == check_code
        except:
            return False

    def parse_birthday(self, id_number):
        """从身份证号解析出生日期"""
        try:
            year = id_number[6:10]
            month = id_number[10:12]
            day = id_number[12:14]
            return f"{year}-{month}-{day}"
        except:
            return None

    def parse_gender(self, id_number):
        """从身份证号解析性别"""
        try:
            gender_code = int(id_number[16])
            return '男' if gender_code % 2 == 1 else '女'
        except:
            return None

    # ========== 测试模式方法 ==========
    
    def insert_test_card(self, name, id_number, gender='男', nation='汉', 
                        birthday='1990-01-01', address='测试地址', id_photo_data=None):
        """插入测试卡片"""
        if not self.test_mode:
            print("测试模式未启用")
            return False
        
        # 如果提供了照片数据，直接使用；否则生成模拟照片
        if id_photo_data:
            id_photo = id_photo_data
            print(f"[测试] 使用提供的身份证照片 ({len(id_photo_data)} 字节)")
        else:
            # 生成身份证照片
            user_data = {
                'name': name,
                'id_number': id_number,
                'gender': gender,
                'nation': nation,
                'birth_date': birthday,
                'address': address,
                'issue_authority': '测试公安局',
                'valid_period': '2020-01-01 ~ 2030-01-01'
            }
            
            # 生成模拟身份证照片
            id_photo = self.photo_simulator.generate_realistic_id_card(user_data)
            print(f"[测试] 已生成身份证照片")
        
        self.test_card_data = {
            'name': name,
            'id_number': id_number,
            'gender': gender,
            'nation': nation,
            'birthday': birthday,
            'address': address,
            'issue_authority': '测试公安局',
            'valid_period': '2020-01-01 ~ 2030-01-01',
            'id_photo': id_photo,  # 添加身份证照片
            'read_time': datetime.now().isoformat()
        }
        self.test_card_inserted = True
        print(f"[测试] 插入身份证: {name} ({id_number})")
        return True
    
    def remove_test_card(self):
        """移除测试卡片"""
        if not self.test_mode:
            print("测试模式未启用")
            return False
        
        if self.test_card_data:
            print(f"[测试] 移除身份证: {self.test_card_data.get('name')}")
        
        self.test_card_inserted = False
        self.test_card_data = None
        return True
    
    def get_test_card_status(self):
        """获取测试卡片状态"""
        if not self.test_mode:
            return None
        
        return {
            'inserted': self.test_card_inserted,
            'card_data': self.test_card_data
        }
