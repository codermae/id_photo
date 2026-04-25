"""
测试数据生成脚本
生成两组测试用户数据（45人和38人），包含完整信息和模拟照片
"""
import os
import sys
import random
from datetime import datetime, timedelta, date
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import shutil

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config.database import SessionLocal, engine, Base
from models.user import User
from models.photo import Photo
from models.collection import Collection
from models.record import CollectionRecord
from config.config import RAW_PHOTOS_DIR, PROCESSED_PHOTOS_DIR

# 中国姓氏和名字库
SURNAMES = ['王', '李', '张', '刘', '陈', '杨', '黄', '赵', '周', '吴', 
            '徐', '孙', '马', '朱', '胡', '郭', '何', '林', '高', '罗',
            '郑', '梁', '谢', '宋', '唐', '许', '韩', '冯', '邓', '曹',
            '彭', '曾', '肖', '田', '董', '袁', '潘', '于', '蒋', '蔡',
            '余', '杜', '叶', '程', '苏', '魏', '吕', '丁', '任', '沈']

MALE_NAMES = ['伟', '强', '磊', '军', '勇', '涛', '明', '超', '杰', '鹏',
              '辉', '刚', '峰', '浩', '亮', '宇', '飞', '龙', '斌', '帆',
              '凯', '健', '波', '鑫', '博', '文', '俊', '豪', '宁', '昊']

FEMALE_NAMES = ['芳', '娜', '秀英', '敏', '静', '丽', '强', '洁', '莉', '桂英',
                '艳', '红', '玲', '梅', '琳', '燕', '霞', '雪', '月', '婷',
                '欣', '慧', '萍', '颖', '倩', '蕾', '薇', '菲', '瑶', '晶']

NATIONS = ['汉族', '回族', '满族', '蒙古族', '藏族', '维吾尔族', '苗族', '彝族', 
           '壮族', '布依族', '朝鲜族', '侗族', '瑶族', '白族', '土家族']

PROVINCES = ['北京市', '上海市', '天津市', '重庆市', '河北省', '山西省', '辽宁省',
             '吉林省', '黑龙江省', '江苏省', '浙江省', '安徽省', '福建省', '江西省',
             '山东省', '河南省', '湖北省', '湖南省', '广东省', '海南省', '四川省',
             '贵州省', '云南省', '陕西省', '甘肃省', '青海省', '台湾省']

CITIES = ['市辖区', '县', '市']
DISTRICTS = ['东城区', '西城区', '朝阳区', '海淀区', '丰台区', '石景山区']
STREETS = ['中山路', '人民路', '解放路', '建设路', '和平路', '光明路', '胜利路']

PHOTO_SPECS = ['一寸', '二寸', '小二寸']
BACKGROUND_COLORS = ['白色', '蓝色', '红色']
BG_COLOR_RGB = {
    '白色': (255, 255, 255),
    '蓝色': (67, 142, 219),
    '红色': (255, 0, 0)
}

def generate_id_number(birthday, gender, existing_ids):
    """生成身份证号码（18位）"""
    while True:
        # 地区码（前6位）- 使用北京市朝阳区
        area_code = '110105'
        
        # 出生日期（8位）
        birth_str = birthday.strftime('%Y%m%d')
        
        # 顺序码（3位）- 奇数为男，偶数为女
        if gender == '男':
            sequence = str(random.randint(0, 499) * 2 + 1).zfill(3)
        else:
            sequence = str(random.randint(0, 499) * 2).zfill(3)
        
        # 前17位
        id_17 = area_code + birth_str + sequence
        
        # 计算校验码
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        
        sum_val = sum(int(id_17[i]) * weights[i] for i in range(17))
        check_code = check_codes[sum_val % 11]
        
        id_number = id_17 + check_code
        
        # 确保不重复
        if id_number not in existing_ids:
            existing_ids.add(id_number)
            return id_number

def generate_name(gender):
    """生成随机姓名"""
    surname = random.choice(SURNAMES)
    if gender == '男':
        if random.random() < 0.3:  # 30%概率单字名
            name = surname + random.choice(MALE_NAMES)
        else:  # 70%概率双字名
            name = surname + random.choice(MALE_NAMES) + random.choice(MALE_NAMES)
    else:
        if random.random() < 0.3:
            name = surname + random.choice(FEMALE_NAMES)
        else:
            name = surname + random.choice(FEMALE_NAMES) + random.choice(FEMALE_NAMES)
    return name

def generate_address():
    """生成随机地址"""
    province = random.choice(PROVINCES)
    city = random.choice(CITIES)
    district = random.choice(DISTRICTS)
    street = random.choice(STREETS)
    number = random.randint(1, 999)
    unit = random.randint(1, 6)
    room = random.randint(101, 2999)
    
    return f"{province}{city}{district}{street}{number}号{unit}单元{room}室"

def generate_birthday(min_age=18, max_age=65):
    """生成随机生日"""
    today = date.today()
    start_date = today - timedelta(days=max_age * 365)
    end_date = today - timedelta(days=min_age * 365)
    
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    
    return start_date + timedelta(days=random_days)

def create_mock_photo(file_path, bg_color_name, name, id_number):
    """创建模拟证件照"""
    # 创建一寸照片尺寸 (590x826)
    width, height = 590, 826
    bg_color = BG_COLOR_RGB[bg_color_name]
    
    # 创建图像
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # 绘制一个简单的人脸轮廓（椭圆）
    face_color = (255, 220, 177)  # 肤色
    face_width = int(width * 0.6)
    face_height = int(height * 0.7)
    face_x = (width - face_width) // 2
    face_y = int(height * 0.15)
    
    draw.ellipse([face_x, face_y, face_x + face_width, face_y + face_height], 
                 fill=face_color, outline=(200, 180, 150), width=3)
    
    # 绘制眼睛
    eye_y = face_y + int(face_height * 0.35)
    left_eye_x = face_x + int(face_width * 0.3)
    right_eye_x = face_x + int(face_width * 0.7)
    eye_size = 20
    
    draw.ellipse([left_eye_x - eye_size, eye_y - eye_size//2, 
                  left_eye_x + eye_size, eye_y + eye_size//2], 
                 fill=(50, 50, 50))
    draw.ellipse([right_eye_x - eye_size, eye_y - eye_size//2, 
                  right_eye_x + eye_size, eye_y + eye_size//2], 
                 fill=(50, 50, 50))
    
    # 绘制嘴巴
    mouth_y = face_y + int(face_height * 0.7)
    mouth_width = int(face_width * 0.4)
    mouth_x = (width - mouth_width) // 2
    
    draw.arc([mouth_x, mouth_y - 20, mouth_x + mouth_width, mouth_y + 20], 
             0, 180, fill=(150, 100, 100), width=3)
    
    # 添加文字信息（用于测试识别）
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("msyh.ttc", 24)  # 微软雅黑
    except:
        font = ImageFont.load_default()
    
    # 在底部添加姓名和身份证号（小字）
    text_y = height - 60
    draw.text((10, text_y), name, fill=(100, 100, 100), font=font)
    draw.text((10, text_y + 30), id_number[-6:], fill=(100, 100, 100), font=font)
    
    # 保存图片
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    img.save(file_path, 'JPEG', quality=95)
    
    return os.path.getsize(file_path)

def clear_existing_data(session):
    """清除现有数据"""
    print("正在清除现有数据...")
    
    # 删除采集记录
    session.query(CollectionRecord).delete()
    print("  - 已删除采集记录")
    
    # 删除照片记录
    session.query(Photo).delete()
    print("  - 已删除照片记录")
    
    # 删除用户
    session.query(User).delete()
    print("  - 已删除用户数据")
    
    # 删除采集任务
    session.query(Collection).delete()
    print("  - 已删除采集任务")
    
    session.commit()
    
    # 删除照片文件
    if RAW_PHOTOS_DIR.exists():
        shutil.rmtree(RAW_PHOTOS_DIR)
        print("  - 已删除原始照片文件")
    
    if PROCESSED_PHOTOS_DIR.exists():
        shutil.rmtree(PROCESSED_PHOTOS_DIR)
        print("  - 已删除处理后照片文件")
    
    # 重新创建目录
    RAW_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    
    print("数据清除完成！\n")

def generate_users(collection_id, count, existing_ids, start_index=1):
    """生成用户数据"""
    users_data = []
    
    for i in range(count):
        gender = random.choice(['男', '女'])
        birthday = generate_birthday()
        name = generate_name(gender)
        id_number = generate_id_number(birthday, gender, existing_ids)
        nation = random.choice(NATIONS)
        address = generate_address()
        
        users_data.append({
            'collection_id': collection_id,
            'name': name,
            'id_number': id_number,
            'gender': gender,
            'nation': nation,
            'birthday': birthday,
            'address': address
        })
    
    return users_data

def determine_record_status():
    """确定采集记录状态（三状态系统）
    
    状态说明：
    - None: 无记录（用户信息存在，但没有采集记录）
    - pending: 待采集（已读身份证，但没拍照）
    - processing: 待处理（已拍照，但没处理）
    - completed: 已完成（已拍照并处理）
    
    返回: (status, notes, has_raw_photo, has_processed_photo)
    """
    rand = random.random()
    if rand < 0.10:  # 10%无记录（只有用户信息，没贴身份证）
        return None, None, False, False
    elif rand < 0.25:  # 15%待采集（贴了身份证，但没拍照）
        return 'pending', random.choice([
            '用户信息已录入，等待采集照片',
            '等待拍照',
            '待采集',
            None
        ]), False, False
    elif rand < 0.40:  # 15%待处理（拍了照，但没处理）
        return 'processing', random.choice([
            '照片已采集',
            '待处理',
            '原始照片已保存',
            None
        ]), True, False  # 有原始照片
    else:  # 60%已完成（拍照并处理完成）
        return 'completed', random.choice([
            '处理后照片已保存',
            '采集完成',
            '已完成',
            None
        ]), True, True  # 有原始照片和处理后照片

def main():
    """主函数"""
    print("=" * 60)
    print("证件照采集系统 - 测试数据生成工具")
    print("=" * 60)
    print()
    
    # 创建数据库会话
    session = SessionLocal()
    
    try:
        # 1. 清除现有数据
        clear_existing_data(session)
        
        # 2. 创建两个采集任务
        print("正在创建采集任务...")
        
        collection1 = Collection(
            name="苏州科技大学-2026年春季",
            organization="苏州科技大学",
            description="2026年春季学期学生证件照采集",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            status='active'
        )
        session.add(collection1)
        
        collection2 = Collection(
            name="苏州科技大学-2026年秋季",
            organization="苏州科技大学",
            description="2026年秋季学期新生证件照采集",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            status='active'
        )
        session.add(collection2)
        
        session.commit()
        print(f"  - 创建采集任务1: {collection1.name} (ID: {collection1.id})")
        print(f"  - 创建采集任务2: {collection2.name} (ID: {collection2.id})")
        print()
        
        # 3. 生成用户数据
        print("正在生成用户数据...")
        existing_ids = set()
        
        # 第一组：45人
        users_group1 = generate_users(collection1.id, 45, existing_ids)
        print(f"  - 第一组生成 {len(users_group1)} 个用户")
        
        # 第二组：38人
        users_group2 = generate_users(collection2.id, 38, existing_ids)
        print(f"  - 第二组生成 {len(users_group2)} 个用户")
        print()
        
        # 4. 插入用户并生成照片
        print("正在创建用户和照片...")
        total_users = 0
        total_photos = 0
        status_stats = {'no_record': 0, 'pending': 0, 'processing': 0, 'completed': 0}
        
        for group_idx, users_data in enumerate([users_group1, users_group2], 1):
            print(f"\n处理第 {group_idx} 组用户...")
            
            for idx, user_data in enumerate(users_data, 1):
                # 创建用户
                user = User(**user_data)
                session.add(user)
                session.flush()  # 获取用户ID
                
                # 确定采集状态
                record_status, record_notes, has_raw_photo, has_processed_photo = determine_record_status()
                
                # 生成照片规格和背景色
                photo_spec = random.choice(PHOTO_SPECS)
                bg_color = random.choice(BACKGROUND_COLORS)
                
                # 根据状态决定是否生成照片和记录
                if record_status is None:
                    # 无记录：只有用户信息，没有采集记录
                    status_stats['no_record'] += 1
                    
                elif record_status == 'pending':
                    # pending状态：待采集（有记录，但没照片）
                    status_stats['pending'] += 1
                    
                    # 创建采集记录（pending状态）
                    record = CollectionRecord(
                        collection_id=user.collection_id,
                        user_id=user.id,
                        collection_date=date.today() - timedelta(days=random.randint(0, 30)),
                        operator=random.choice(['系统管理员', '操作员A', '操作员B', '操作员C']),
                        status='pending',
                        notes=record_notes
                    )
                    session.add(record)
                    
                elif record_status == 'processing':
                    # processing状态：待处理（有原始照片，但没有处理后照片）
                    status_stats['processing'] += 1
                    
                    # 生成原始照片
                    raw_filename = f"raw_{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                    raw_path = RAW_PHOTOS_DIR / raw_filename
                    raw_size = create_mock_photo(str(raw_path), bg_color, user.name, user.id_number)
                    
                    raw_photo = Photo(
                        user_id=user.id,
                        photo_type='raw',
                        file_path=str(raw_path),
                        file_size=raw_size,
                        photo_spec=photo_spec,
                        background_color=bg_color,
                        quality_score=random.randint(70, 90),
                        face_similarity=None
                    )
                    session.add(raw_photo)
                    total_photos += 1
                    
                    # 创建采集记录（processing状态）
                    record = CollectionRecord(
                        collection_id=user.collection_id,
                        user_id=user.id,
                        collection_date=date.today() - timedelta(days=random.randint(0, 30)),
                        operator=random.choice(['系统管理员', '操作员A', '操作员B', '操作员C']),
                        status='processing',
                        notes=record_notes
                    )
                    session.add(record)
                    
                elif record_status == 'completed':
                    # completed状态：已完成（有原始照片和处理后照片）
                    status_stats['completed'] += 1
                    
                    # 生成原始照片
                    raw_filename = f"raw_{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                    raw_path = RAW_PHOTOS_DIR / raw_filename
                    raw_size = create_mock_photo(str(raw_path), bg_color, user.name, user.id_number)
                    
                    raw_photo = Photo(
                        user_id=user.id,
                        photo_type='raw',
                        file_path=str(raw_path),
                        file_size=raw_size,
                        photo_spec=photo_spec,
                        background_color=bg_color,
                        quality_score=random.randint(75, 95),
                        face_similarity=None
                    )
                    session.add(raw_photo)
                    
                    # 生成处理后照片
                    processed_filename = f"processed_{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                    processed_path = PROCESSED_PHOTOS_DIR / processed_filename
                    processed_size = create_mock_photo(str(processed_path), bg_color, user.name, user.id_number)
                    
                    processed_photo = Photo(
                        user_id=user.id,
                        photo_type='processed',
                        file_path=str(processed_path),
                        file_size=processed_size,
                        photo_spec=photo_spec,
                        background_color=bg_color,
                        quality_score=random.randint(85, 100),
                        face_similarity=random.randint(85, 98)
                    )
                    session.add(processed_photo)
                    total_photos += 2
                    
                    # 创建采集记录（completed状态）
                    record = CollectionRecord(
                        collection_id=user.collection_id,
                        user_id=user.id,
                        collection_date=date.today() - timedelta(days=random.randint(0, 30)),
                        operator=random.choice(['系统管理员', '操作员A', '操作员B', '操作员C']),
                        status='completed',
                        notes=record_notes
                    )
                    session.add(record)
                
                total_users += 1
                
                if idx % 10 == 0:
                    print(f"  已处理 {idx}/{len(users_data)} 个用户...")
        
        # 提交所有数据
        session.commit()
        
        print()
        print("=" * 60)
        print("测试数据生成完成！")
        print("=" * 60)
        print(f"采集任务数: 2")
        print(f"用户总数: {total_users}")
        print(f"  - 第一组: 45 人")
        print(f"  - 第二组: 38 人")
        print(f"照片总数: {total_photos}")
        total_records = status_stats['pending'] + status_stats['processing'] + status_stats['completed']
        print(f"采集记录数: {total_records}")
        print()
        print(f"显示状态统计:")
        print(f"  - 无记录: {status_stats['no_record']} ({status_stats['no_record']/total_users*100:.1f}%) - 只有用户信息，未贴身份证")
        print(f"  - 待采集: {status_stats['pending']} ({status_stats['pending']/total_users*100:.1f}%) - 已贴身份证，未拍照")
        print(f"  - 待处理: {status_stats['processing']} ({status_stats['processing']/total_users*100:.1f}%) - 已拍照，未处理")
        print(f"  - 已完成: {status_stats['completed']} ({status_stats['completed']/total_users*100:.1f}%) - 已拍照并处理")
        print()
        print(f"数据库状态统计:")
        print(f"  - pending记录: {status_stats['pending']} (待采集)")
        print(f"  - processing记录: {status_stats['processing']} (待处理)")
        print(f"  - completed记录: {status_stats['completed']} (已完成)")
        print()
        print(f"状态说明:")
        print(f"  1. 无记录: 用户信息存在，但没有采集记录（没贴身份证）")
        print(f"  2. 待采集: 有pending记录，已读身份证但没拍照")
        print(f"  3. 待处理: 有processing记录，已拍照但没处理")
        print(f"  4. 已完成: 有completed记录，已拍照并处理")
        print()
        print(f"照片文件位置:")
        print(f"  - 原始照片: {RAW_PHOTOS_DIR}")
        print(f"  - 处理后照片: {PROCESSED_PHOTOS_DIR}")
        print("=" * 60)
        
    except Exception as e:
        session.rollback()
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    main()
