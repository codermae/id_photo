from config.database import SessionLocal
from models.record import CollectionRecord
from models.user import User
from models.photo import Photo
from collections import Counter

session = SessionLocal()

print('采集记录状态分布:')
records = session.query(CollectionRecord).all()
status_count = Counter([r.status for r in records])
for k, v in status_count.items():
    print(f'  {k}: {v}')

print('\n用户统计:')
total_users = session.query(User).count()
users_with_records = session.query(User).join(CollectionRecord).distinct().count()
users_without_records = total_users - users_with_records
print(f'  总用户数: {total_users}')
print(f'  有采集记录: {users_with_records}')
print(f'  无记录: {users_without_records}')

print('\n照片统计:')
raw_photos = session.query(Photo).filter(Photo.photo_type == 'raw').count()
processed_photos = session.query(Photo).filter(Photo.photo_type == 'processed').count()
print(f'  原始照片: {raw_photos}')
print(f'  处理后照片: {processed_photos}')

print('\n各状态示例:')
print('\n1. 无记录用户（只有用户信息）:')
users_no_record = session.query(User).outerjoin(CollectionRecord).filter(CollectionRecord.id == None).limit(3).all()
for u in users_no_record:
    print(f'  用户ID {u.id}: {u.name} - 无采集记录')

print('\n2. 待采集（有记录，无照片）:')
pending_records = [r for r in records if r.status == 'pending'][:3]
for r in pending_records:
    photos = session.query(Photo).filter(Photo.user_id == r.user_id).count()
    print(f'  用户ID {r.user_id}: {r.notes} - 照片数: {photos}')

print('\n3. 待处理（有原始照片，无处理后照片）:')
processing_records = [r for r in records if r.status == 'processing'][:3]
for r in processing_records:
    raw = session.query(Photo).filter(Photo.user_id == r.user_id, Photo.photo_type == 'raw').count()
    processed = session.query(Photo).filter(Photo.user_id == r.user_id, Photo.photo_type == 'processed').count()
    print(f'  用户ID {r.user_id}: {r.notes} - 原始照片: {raw}, 处理后: {processed}')

print('\n4. 已采集（有原始和处理后照片）:')
completed_records = [r for r in records if r.status == 'completed'][:3]
for r in completed_records:
    raw = session.query(Photo).filter(Photo.user_id == r.user_id, Photo.photo_type == 'raw').count()
    processed = session.query(Photo).filter(Photo.user_id == r.user_id, Photo.photo_type == 'processed').count()
    print(f'  用户ID {r.user_id}: {r.notes} - 原始照片: {raw}, 处理后: {processed}')

session.close()
