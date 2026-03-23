"""
初始化采集记录 - 为现有用户创建采集记录
"""
from utils.database_helper import DatabaseHelper
import getpass

def init_records_for_existing_users():
    """为所有现有用户初始化采集记录"""
    print("=" * 60)
    print("初始化采集记录")
    print("=" * 60)
    
    db = DatabaseHelper()
    
    # 获取所有用户
    users = db.get_all_users()
    print(f"\n找到 {len(users)} 个用户")
    
    if not users:
        print("没有用户，无需初始化")
        db.close()
        return
    
    operator = getpass.getuser()
    created_count = 0
    updated_count = 0
    
    for user in users:
        # 检查用户是否有照片
        photos = db.get_photos_by_user(user.id)
        has_photos = len(photos) > 0
        
        # 检查是否已有采集记录
        records = db.get_records_by_user(user.id)
        
        if not records:
            # 没有采集记录，创建新记录
            if has_photos:
                # 有照片，标记为已采集
                status = 'completed'
                notes = f'系统初始化：用户已有 {len(photos)} 张照片'
                print(f"✅ 用户 {user.name} (ID:{user.id}) - 有照片，创建已采集记录")
            else:
                # 没有照片，标记为待采集
                status = 'pending'
                notes = '系统初始化：等待采集照片'
                print(f"⏳ 用户 {user.name} (ID:{user.id}) - 无照片，创建待采集记录")
            
            record = db.add_record(
                user_id=user.id,
                operator=operator,
                status=status,
                notes=notes
            )
            created_count += 1
        else:
            # 已有采集记录，检查状态是否需要更新
            latest_record = records[-1]
            
            if has_photos and latest_record.status == 'pending':
                # 有照片但状态是待采集，更新为已采集
                latest_record.status = 'completed'
                latest_record.notes = f'系统更新：用户已有 {len(photos)} 张照片'
                db.db.commit()
                print(f"🔄 用户 {user.name} (ID:{user.id}) - 更新为已采集")
                updated_count += 1
            else:
                print(f"✓ 用户 {user.name} (ID:{user.id}) - 已有记录，状态: {latest_record.status}")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("初始化完成")
    print("=" * 60)
    print(f"创建新记录: {created_count}")
    print(f"更新记录: {updated_count}")
    print(f"总用户数: {len(users)}")
    
    # 显示统计
    print("\n" + "=" * 60)
    print("更新后的统计数据")
    print("=" * 60)
    
    db = DatabaseHelper()
    stats = db.get_collection_stats()
    
    print(f"\n📊 采集统计:")
    print(f"   总记录数: {stats['total']}")
    print(f"   已采集: {stats['completed']}")
    print(f"   待采集: {stats['pending']}")
    print(f"   失败: {stats['failed']}")
    print(f"   完成率: {stats['completion_rate']:.1f}%")
    
    user_count = db.get_user_count()
    photo_count = db.get_photo_count()
    
    print(f"\n👥 用户和照片:")
    print(f"   用户总数: {user_count}")
    print(f"   照片总数: {photo_count}")
    
    db.close()

if __name__ == '__main__':
    print("\n这个脚本会为所有现有用户创建采集记录")
    print("- 有照片的用户 → 标记为已采集")
    print("- 没照片的用户 → 标记为待采集\n")
    
    response = input("是否继续？(y/n): ")
    if response.lower() == 'y':
        init_records_for_existing_users()
    else:
        print("已取消")
