"""
测试四种状态的显示
"""
from config.database import SessionLocal
from models.user import User
from models.record import CollectionRecord
from models.photo import Photo
from collections import Counter

session = SessionLocal()

print("=" * 60)
print("四种状态测试")
print("=" * 60)

# 统计各状态数量
all_users = session.query(User).all()
print(f"\n总用户数: {len(all_users)}")

status_count = {
    'no_record': 0,
    'pending': 0,
    'processing': 0,
    'completed': 0
}

for user in all_users:
    records = session.query(CollectionRecord).filter(CollectionRecord.user_id == user.id).all()
    photos = session.query(Photo).filter(Photo.user_id == user.id).all()
    
    if not records:
        # 1. 无记录
        status_count['no_record'] += 1
        status = '无记录'
    else:
        latest_record = records[-1]
        raw_photos = [p for p in photos if p.photo_type == 'raw']
        processed_photos = [p for p in photos if p.photo_type == 'processed']
        
        if latest_record.status == 'completed':
            # 4. 已完成
            status_count['completed'] += 1
            status = '✅ 已完成'
        elif latest_record.status == 'pending':
            if len(raw_photos) > 0 and len(processed_photos) == 0:
                # 3. 待处理
                status_count['processing'] += 1
                status = '⏳ 待处理'
            else:
                # 2. 待采集
                status_count['pending'] += 1
                status = '⏸ 待采集'
        else:
            status = '未知'
    
    raw_photos = [p for p in photos if p.photo_type == 'raw']
    processed_photos = [p for p in photos if p.photo_type == 'processed']

print("\n状态分布:")
print(f"  1. 无记录: {status_count['no_record']} ({status_count['no_record']/len(all_users)*100:.1f}%)")
print(f"  2. 待采集: {status_count['pending']} ({status_count['pending']/len(all_users)*100:.1f}%)")
print(f"  3. 待处理: {status_count['processing']} ({status_count['processing']/len(all_users)*100:.1f}%)")
print(f"  4. 已采集: {status_count['completed']} ({status_count['completed']/len(all_users)*100:.1f}%)")

print("\n各状态示例（前3个）:")

# 无记录
print("\n1. 无记录（只有用户信息，没贴身份证）:")
no_record_users = []
for user in all_users:
    records = session.query(CollectionRecord).filter(CollectionRecord.user_id == user.id).all()
    if not records:
        no_record_users.append(user)
        if len(no_record_users) <= 3:
            print(f"   用户ID {user.id}: {user.name} ({user.gender}) - {user.id_number}")

# 待采集
print("\n2. 待采集（已贴身份证，但没拍照）:")
pending_count = 0
for user in all_users:
    records = session.query(CollectionRecord).filter(CollectionRecord.user_id == user.id).all()
    photos = session.query(Photo).filter(Photo.user_id == user.id).all()
    if records and records[-1].status == 'pending':
        raw_photos = [p for p in photos if p.photo_type == 'raw']
        if len(raw_photos) == 0:
            pending_count += 1
            if pending_count <= 3:
                print(f"   用户ID {user.id}: {user.name} - 记录: {records[-1].notes} - 照片数: {len(photos)}")

# 待处理
print("\n3. 待处理（已拍照，但没处理）:")
processing_count = 0
for user in all_users:
    records = session.query(CollectionRecord).filter(CollectionRecord.user_id == user.id).all()
    photos = session.query(Photo).filter(Photo.user_id == user.id).all()
    if records and records[-1].status == 'pending':
        raw_photos = [p for p in photos if p.photo_type == 'raw']
        processed_photos = [p for p in photos if p.photo_type == 'processed']
        if len(raw_photos) > 0 and len(processed_photos) == 0:
            processing_count += 1
            if processing_count <= 3:
                print(f"   用户ID {user.id}: {user.name} - 原始照片: {len(raw_photos)}, 处理后: {len(processed_photos)}")

# 已完成
print("\n4. 已完成（已拍照并处理）:")
completed_count = 0
for user in all_users:
    records = session.query(CollectionRecord).filter(CollectionRecord.user_id == user.id).all()
    photos = session.query(Photo).filter(Photo.user_id == user.id).all()
    if records and records[-1].status == 'completed':
        completed_count += 1
        if completed_count <= 3:
            raw = len([p for p in photos if p.photo_type == 'raw'])
            processed = len([p for p in photos if p.photo_type == 'processed'])
            print(f"   用户ID {user.id}: {user.name} - 原始照片: {raw}, 处理后: {processed}")

print("\n" + "=" * 60)

session.close()
