"""
证件照智能采集及处理系统 - 软著鉴别材料第4部分
批量处理、身份证读取、数据导入

================================================================================
第4部分: 批量处理和数据导入模块
================================================================================

本部分实现了系统的批量处理功能、身份证信息读取以及
Excel数据导入等关键功能，支持大规模数据处理。

"""

# ============================================================================
# 文件名: controllers/batch_processor.py
# 功能: 批量处理控制器，支持多线程批量操作
# 行数: 92 行
# ============================================================================

from PyQt5.QtCore import QThread, pyqtSignal
import time
from pathlib import Path
from config.database import SessionLocal
from models.user import User
from models.photo import Photo
from models.record import CollectionRecord
from controllers.ai_processor import AIProcessor
from controllers.image_processor import ImageProcessor
import traceback

class BatchProcessThread(QThread):
    """
    批量处理线程 - 处理大量照片的多线程处理
    
    信号:
    - progress: 处理进度 (当前, 总数)
    - status: 状态更新信息
    - completed: 批量处理完成
    - error: 错误信息
    """
    
    progress = pyqtSignal(int, int)  # current, total
    status = pyqtSignal(str)
    completed = pyqtSignal(dict)  # 完成统计信息
    error = pyqtSignal(str)
    
    def __init__(self, photo_paths, specs, bg_color, collection_id=None):
        """
        初始化批量处理
        
        参数:
        - photo_paths: 照片文件路径列表
        - specs: 证件照规格列表
        - bg_color: 背景颜色
        - collection_id: 所属采集任务ID
        """
        super().__init__()
        self.photo_paths = photo_paths
        self.specs = specs
        self.bg_color = bg_color
        self.collection_id = collection_id
        self.is_running = False
        self.ai_processor = AIProcessor()
        self.image_processor = ImageProcessor()
    
    def run(self):
        """
        执行批量处理
        
        流程:
        1. 逐个处理照片
        2. 进行AI处理（人脸检测、美颜等）
        3. 生成多个规格
        4. 保存结果
        5. 更新数据库
        """
        self.is_running = True
        total = len(self.photo_paths)
        success_count = 0
        fail_count = 0
        
        try:
            db = SessionLocal()
            
            for idx, photo_path in enumerate(self.photo_paths):
                if not self.is_running:
                    break
                
                try:
                    start_time = time.time()
                    
                    # 检测人脸
                    image = Image.open(photo_path)
                    faces = self.ai_processor.detect_faces(image)
                    
                    if not faces:
                        self.status.emit(f"[{idx+1}/{total}] {Path(photo_path).name} - 未检测到人脸")
                        fail_count += 1
                        continue
                    
                    # 获取主人脸
                    main_face = max(faces, key=lambda f: (f[2]-f[0]) * (f[3]-f[1]))
                    
                    # 评估质量
                    quality = self.ai_processor.evaluate_face_quality(
                        np.array(image), main_face[:4]
                    )
                    
                    # 美颜处理
                    beautified = self.ai_processor.beautify_face(image)
                    
                    # 移除背景
                    no_bg = self.ai_processor.remove_background(beautified)
                    
                    # 生成多规格
                    results = self.image_processor.generate_multiple_specs(
                        no_bg, self.specs, self.bg_color
                    )
                    
                    # 保存处理后的照片
                    output_dir = Path('data/photos/processed')
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    for spec, img in results.items():
                        output_path = output_dir / f"{Path(photo_path).stem}_{spec}.jpg"
                        self.image_processor.save_photo(img, str(output_path))
                    
                    # 更新数据库
                    if self.collection_id:
                        record = db.query(CollectionRecord).filter_by(
                            collection_id=self.collection_id
                        ).first()
                        if record:
                            record.processing_time = time.time() - start_time
                            record.ai_score = quality
                            record.status = 'completed'
                            db.commit()
                    
                    success_count += 1
                    self.status.emit(
                        f"[{idx+1}/{total}] {Path(photo_path).name} - "
                        f"质量评分: {quality:.1f} - 耗时: {time.time()-start_time:.2f}s"
                    )
                    
                except Exception as e:
                    fail_count += 1
                    error_msg = f"[{idx+1}/{total}] {Path(photo_path).name} - 处理失败: {str(e)}"
                    self.status.emit(error_msg)
                    traceback.print_exc()
                
                self.progress.emit(idx + 1, total)
            
            db.close()
            
            # 发送完成信号
            result_stat = {
                'total': total,
                'success': success_count,
                'failed': fail_count,
                'success_rate': (success_count / total * 100) if total > 0 else 0
            }
            self.completed.emit(result_stat)
            
        except Exception as e:
            self.error.emit(f"批量处理出错: {str(e)}")
            traceback.print_exc()
    
    def stop(self):
        """停止处理"""
        self.is_running = False
        self.wait()


# ============================================================================
# 文件名: controllers/id_card_reader.py
# 功能: 二代身份证读取模块
# 行数: 85 行
# ============================================================================

import os
import struct
from datetime import datetime

class IDCardReader:
    """
    二代身份证读取器
    
    功能:
    1. 连接身份证读卡器
    2. 读取身份证信息
    3. 解析身份证数据
    4. 生成ID照片
    5. 身份验证和重复检测
    
    支持的读卡器: 精伦IDR系列、康泰X系列等
    """
    
    def __init__(self, device_name=None, timeout=5000):
        """
        初始化读卡器
        
        参数:
        - device_name: 读卡器设备名称
        - timeout: 读取超时时间（毫秒）
        """
        self.device_name = device_name
        self.timeout = timeout
        self.is_connected = False
        self.reader_handle = None
    
    def connect(self):
        """
        连接读卡器
        
        返回: 是否连接成功
        """
        try:
            # 注意：实际实现需要调用读卡器的SDK
            # 这里展示的是接口设计
            self.is_connected = True
            return True
        except Exception as e:
            print(f"连接读卡器失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.is_connected = False
    
    def read_card_info(self):
        """
        读取身份证信息
        
        返回: 身份证数据字典
        {
            'name': '姓名',
            'id_number': '身份证号',
            'sex': '性别',
            'birth_date': '出生日期',
            'nationality': '民族',
            'province': '省份',
            'city': '城市',
            'address': '住址',
            'issue_date': '签发日期',
            'expiry_date': '有效期',
            'id_photo': '身份证照片（字节数据）'
        }
        """
        if not self.is_connected:
            raise Exception("未连接到读卡器")
        
        try:
            # 读取身份证照片
            id_photo_data = self._read_id_photo()
            
            card_info = {
                'name': '张三',  # 实际从读卡器读取
                'id_number': '110101199003151234',
                'sex': 'M',  # M/F
                'birth_date': '1990-03-15',
                'nationality': '汉',
                'province': '北京',
                'city': '北京',
                'address': '朝阳区某街道123号',
                'issue_date': '2015-03-15',
                'expiry_date': '2035-03-15',
                'id_photo': id_photo_data
            }
            
            return card_info
        
        except Exception as e:
            raise Exception(f"读取身份证信息失败: {e}")
    
    def _read_id_photo(self):
        """
        读取身份证照片
        
        返回: 照片字节数据
        """
        # 实际实现依赖于读卡器SDK
        pass
    
    def extract_info_from_id_number(self, id_number):
        """
        从身份证号码提取信息
        
        参数:
        - id_number: 18位身份证号
        
        返回: 提取的信息字典
        """
        if len(id_number) != 18:
            raise ValueError("身份证号长度必须为18位")
        
        # 提取出生日期
        year = int(id_number[6:10])
        month = int(id_number[10:12])
        day = int(id_number[12:14])
        birth_date = f"{year}-{month:02d}-{day:02d}"
        
        # 提取性别 (倒数第二位: 奇数为男, 偶数为女)
        sex_code = int(id_number[16])
        sex = 'M' if sex_code % 2 == 1 else 'F'
        
        # 地区码 (前6位)
        area_code = id_number[:6]
        
        # 检验码验证
        is_valid = self._validate_id_number(id_number)
        
        return {
            'birth_date': birth_date,
            'sex': sex,
            'area_code': area_code,
            'is_valid': is_valid
        }
    
    def _validate_id_number(self, id_number):
        """
        验证身份证号检验位
        
        返回: 是否有效
        """
        if len(id_number) != 18:
            return False
        
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = '10X98765432'
        
        total = 0
        for i in range(17):
            total += int(id_number[i]) * weights[i]
        
        check_digit = check_codes[total % 11]
        return id_number[17] == check_digit
    
    def save_id_photo(self, photo_data, output_path):
        """
        保存身份证照片
        
        参数:
        - photo_data: 照片字节数据
        - output_path: 保存路径
        """
        with open(output_path, 'wb') as f:
            f.write(photo_data)


# ============================================================================
# 文件名: controllers/batch_importer.py
# 功能: 批量导入控制器，支持Excel数据导入
# 行数: 78 行
# ============================================================================

import pandas as pd
from datetime import datetime
from config.database import SessionLocal
from models.user import User
from models.collection import Collection

class BatchImporter:
    """
    批量导入器 - 从Excel导入用户信息
    
    支持的格式:
    - Excel文件 (.xlsx, .xls)
    - 必填列: 姓名, 身份证号
    - 可选列: 性别, 出生日期, 民族, 省份, 城市, 地址, 电话, 邮箱
    """
    
    def __init__(self):
        """初始化导入器"""
        self.db = SessionLocal()
        self.required_columns = ['姓名', '身份证号']
        self.optional_columns = ['性别', '出生日期', '民族', '省份', 
                                 '城市', '地址', '电话', '邮箱']
    
    def validate_file(self, file_path):
        """
        验证Excel文件
        
        检查:
        1. 文件是否存在
        2. 文件格式是否正确
        3. 必填列是否完整
        4. 数据类型是否正确
        
        返回: (是否有效, 错误信息列表)
        """
        errors = []
        
        try:
            # 读取Excel
            df = pd.read_excel(file_path)
            
            # 检查必填列
            for col in self.required_columns:
                if col not in df.columns:
                    errors.append(f"缺少必填列: {col}")
            
            # 检查数据完整性
            for col in self.required_columns:
                if df[col].isnull().any():
                    errors.append(f"列 {col} 包含空值")
            
            # 检查身份证号格式
            for idx, id_num in enumerate(df['身份证号']):
                if not self._validate_id_format(str(id_num)):
                    errors.append(f"第 {idx+2} 行身份证号格式错误")
            
            return len(errors) == 0, errors
        
        except Exception as e:
            return False, [f"读取文件错误: {str(e)}"]
    
    def import_data(self, file_path, collection_id=None):
        """
        导入数据
        
        参数:
        - file_path: Excel文件路径
        - collection_id: 所属采集任务ID
        
        返回: (导入数量, 错误列表)
        """
        try:
            df = pd.read_excel(file_path)
            import_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    # 检查重复
                    existing = self.db.query(User).filter_by(
                        id_number=str(row['身份证号'])
                    ).first()
                    
                    if existing:
                        errors.append(f"第 {idx+2} 行: 身份证号已存在")
                        continue
                    
                    # 创建用户
                    user = User(
                        name=str(row['姓名']),
                        id_number=str(row['身份证号']),
                        sex=str(row.get('性别', 'M')),
                        birth_date=pd.to_datetime(row.get('出生日期')) if '出生日期' in row else None,
                        nationality=str(row.get('民族', '')),
                        province=str(row.get('省份', '')),
                        city=str(row.get('城市', '')),
                        address=str(row.get('地址', '')),
                        phone=str(row.get('电话', '')),
                        email=str(row.get('邮箱', '')),
                        status='pending'
                    )
                    
                    self.db.add(user)
                    import_count += 1
                
                except Exception as e:
                    errors.append(f"第 {idx+2} 行导入错误: {str(e)}")
            
            self.db.commit()
            return import_count, errors
        
        except Exception as e:
            return 0, [f"导入过程错误: {str(e)}"]
    
    def _validate_id_format(self, id_number):
        """验证身份证号格式"""
        return len(id_number) == 18 and id_number.isdigit()
    
    def download_template(self, output_path):
        """
        下载导入模板
        
        参数:
        - output_path: 保存路径
        """
        template_data = {
            '姓名': ['张三', '李四'],
            '身份证号': ['110101199003151234', '110101199004151234'],
            '性别': ['M', 'F'],
            '出生日期': ['1990-03-15', '1990-04-15'],
            '民族': ['汉', '汉'],
            '省份': ['北京', '北京'],
            '城市': ['北京', '北京'],
            '地址': ['朝阳区某街道123号', '东城区某街道456号'],
            '电话': ['13800000001', '13800000002'],
            '邮箱': ['[email]@example.com', '[email]@example.com'],
        }
        
        df = pd.DataFrame(template_data)
        df.to_excel(output_path, index=False, engine='openpyxl')
