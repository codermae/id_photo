"""
数据库操作助手
"""
from config.database import SessionLocal
from models.user import User
from models.photo import Photo
from models.record import CollectionRecord
from models.collection import Collection
from datetime import datetime, date

class DatabaseHelper:
    """数据库操作助手类"""

    def __init__(self):
        self.db = SessionLocal()
        self.current_collection_id = None  # 当前选中的采集任务ID

    def close(self):
        """关闭数据库连接"""
        self.db.close()

    # ========== 采集任务操作 ==========
    def create_collection(self, name, organization, description=None, start_date=None, end_date=None):
        """创建采集任务"""
        try:
            collection = Collection(
                name=name,
                organization=organization,
                description=description,
                start_date=start_date or date.today(),
                end_date=end_date,
                status='active'
            )
            self.db.add(collection)
            self.db.commit()
            return collection
        except Exception as e:
            self.db.rollback()
            raise e

    def get_collection_by_id(self, collection_id):
        """根据ID获取采集任务"""
        return self.db.query(Collection).filter(Collection.id == collection_id).first()

    def get_all_collections(self, status=None):
        """获取所有采集任务"""
        query = self.db.query(Collection)
        if status:
            query = query.filter(Collection.status == status)
        return query.order_by(Collection.created_at.desc()).all()

    def get_active_collections(self):
        """获取所有活跃的采集任务"""
        return self.get_all_collections(status='active')

    def update_collection(self, collection_id, **kwargs):
        """更新采集任务"""
        try:
            collection = self.get_collection_by_id(collection_id)
            if collection:
                for key, value in kwargs.items():
                    if hasattr(collection, key):
                        setattr(collection, key, value)
                collection.updated_at = datetime.now()
                self.db.commit()
            return collection
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_collection(self, collection_id):
        """删除采集任务（及其所有关联数据）"""
        try:
            collection = self.get_collection_by_id(collection_id)
            if collection:
                self.db.delete(collection)
                self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def set_current_collection(self, collection_id):
        """设置当前采集任务"""
        self.current_collection_id = collection_id

    def get_current_collection(self):
        """获取当前采集任务"""
        if self.current_collection_id:
            return self.get_collection_by_id(self.current_collection_id)
        return None

    # ========== 用户操作 ==========
    def add_user(self, name, id_number, gender=None, nation=None, birthday=None, address=None, collection_id=None):
        """添加用户"""
        try:
            # 如果没有指定采集任务，使用当前采集任务
            if collection_id is None:
                collection_id = self.current_collection_id
            
            if collection_id is None:
                raise ValueError("必须指定采集任务ID")
            
            user = User(
                collection_id=collection_id,
                name=name,
                id_number=id_number,
                gender=gender,
                nation=nation,
                birthday=birthday,
                address=address
            )
            self.db.add(user)
            self.db.commit()
            return user
        except Exception as e:
            self.db.rollback()
            raise e

    def get_user_by_id(self, user_id):
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_id_number(self, id_number, collection_id=None):
        """根据身份证号获取用户"""
        query = self.db.query(User).filter(User.id_number == id_number)
        
        # 如果指定了采集任务，只在该任务内查询
        if collection_id:
            query = query.filter(User.collection_id == collection_id)
        elif self.current_collection_id:
            query = query.filter(User.collection_id == self.current_collection_id)
        
        return query.first()

    def get_all_users(self, collection_id=None):
        """获取所有用户"""
        query = self.db.query(User)
        
        # 如果指定了采集任务，只获取该任务的用户
        if collection_id:
            query = query.filter(User.collection_id == collection_id)
        elif self.current_collection_id:
            query = query.filter(User.collection_id == self.current_collection_id)
        
        return query.all()

    def update_user(self, user_id, **kwargs):
        """更新用户信息"""
        try:
            user = self.get_user_by_id(user_id)
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                user.updated_at = datetime.now()
                self.db.commit()
            return user
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_user(self, user_id):
        """删除用户"""
        try:
            user = self.get_user_by_id(user_id)
            if user:
                self.db.delete(user)
                self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    # ========== 照片操作 ==========
    def add_photo(self, user_id, photo_type, file_path, file_size=None, photo_spec=None, background_color=None):
        """添加照片记录"""
        try:
            photo = Photo(
                user_id=user_id,
                photo_type=photo_type,
                file_path=file_path,
                file_size=file_size,
                photo_spec=photo_spec,
                background_color=background_color
            )
            self.db.add(photo)
            self.db.commit()
            return photo
        except Exception as e:
            self.db.rollback()
            raise e

    def get_photo_by_id(self, photo_id):
        """根据ID获取照片"""
        return self.db.query(Photo).filter(Photo.id == photo_id).first()

    def get_photos_by_user(self, user_id):
        """获取用户的所有照片"""
        return self.db.query(Photo).filter(Photo.user_id == user_id).all()

    def update_photo(self, photo_id, **kwargs):
        """更新照片信息"""
        try:
            photo = self.get_photo_by_id(photo_id)
            if photo:
                for key, value in kwargs.items():
                    if hasattr(photo, key):
                        setattr(photo, key, value)
                self.db.commit()
            return photo
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_photo(self, photo_id):
        """删除照片记录"""
        try:
            photo = self.get_photo_by_id(photo_id)
            if photo:
                self.db.delete(photo)
                self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    # ========== 采集记录操作 ==========
    def add_record(self, user_id, operator=None, status='pending', notes=None, collection_id=None):
        """添加采集记录"""
        try:
            # 如果没有指定采集任务，使用当前采集任务
            if collection_id is None:
                collection_id = self.current_collection_id
            
            # collection_id 可以为 None（手动选择用户时）
            record = CollectionRecord(
                collection_id=collection_id,
                user_id=user_id,
                operator=operator,
                status=status,
                notes=notes,
                collection_date=date.today()
            )
            self.db.add(record)
            self.db.commit()
            return record
        except Exception as e:
            self.db.rollback()
            raise e

    def get_record_by_id(self, record_id):
        """根据ID获取记录"""
        return self.db.query(CollectionRecord).filter(CollectionRecord.id == record_id).first()

    def get_records_by_user(self, user_id):
        """获取用户的所有采集记录"""
        return self.db.query(CollectionRecord).filter(CollectionRecord.user_id == user_id).all()

    def get_records_by_date(self, date, collection_id=None):
        """获取指定日期的采集记录"""
        query = self.db.query(CollectionRecord).filter(CollectionRecord.collection_date == date)
        
        if collection_id:
            query = query.filter(CollectionRecord.collection_id == collection_id)
        elif self.current_collection_id:
            query = query.filter(CollectionRecord.collection_id == self.current_collection_id)
        
        return query.all()

    def update_record(self, record_id, **kwargs):
        """更新采集记录"""
        try:
            record = self.get_record_by_id(record_id)
            if record:
                for key, value in kwargs.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                self.db.commit()
            return record
        except Exception as e:
            self.db.rollback()
            raise e

    # ========== 统计操作 ==========
    def get_collection_stats(self, start_date=None, end_date=None, collection_id=None):
        """获取采集统计"""
        query = self.db.query(CollectionRecord)
        
        # 如果指定了采集任务，只统计该任务的数据
        if collection_id:
            query = query.filter(CollectionRecord.collection_id == collection_id)
        elif self.current_collection_id:
            query = query.filter(CollectionRecord.collection_id == self.current_collection_id)
        
        if start_date:
            query = query.filter(CollectionRecord.collection_date >= start_date)
        if end_date:
            query = query.filter(CollectionRecord.collection_date <= end_date)
        
        records = query.all()
        total = len(records)
        completed = len([r for r in records if r.status == 'completed'])
        pending = len([r for r in records if r.status == 'pending'])
        failed = len([r for r in records if r.status == 'failed'])

        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'failed': failed,
            'completion_rate': (completed / total * 100) if total > 0 else 0
        }

    def get_user_count(self, collection_id=None):
        """获取用户总数"""
        query = self.db.query(User)
        
        if collection_id:
            query = query.filter(User.collection_id == collection_id)
        elif self.current_collection_id:
            query = query.filter(User.collection_id == self.current_collection_id)
        
        return query.count()

    def get_photo_count(self, collection_id=None):
        """获取照片总数"""
        query = self.db.query(Photo).join(User)
        
        if collection_id:
            query = query.filter(User.collection_id == collection_id)
        elif self.current_collection_id:
            query = query.filter(User.collection_id == self.current_collection_id)
        
        return query.count()

    def get_demographic_stats(self, collection_id=None):
        """获取人口统计数据（年龄、性别、民族等）"""
        from datetime import datetime
        
        query = self.db.query(User)
        
        if collection_id:
            query = query.filter(User.collection_id == collection_id)
        elif self.current_collection_id:
            query = query.filter(User.collection_id == self.current_collection_id)
        
        users = query.all()
        
        # 性别统计
        gender_stats = {}
        age_stats = {'0-18': 0, '18-30': 0, '30-45': 0, '45-60': 0, '60+': 0}
        nation_stats = {}
        
        today = datetime.now().date()
        
        for user in users:
            # 性别统计
            gender = user.gender or '未知'
            gender_stats[gender] = gender_stats.get(gender, 0) + 1
            
            # 年龄统计
            if user.birthday:
                age = (today - user.birthday).days // 365
                if age < 18:
                    age_stats['0-18'] += 1
                elif age < 30:
                    age_stats['18-30'] += 1
                elif age < 45:
                    age_stats['30-45'] += 1
                elif age < 60:
                    age_stats['45-60'] += 1
                else:
                    age_stats['60+'] += 1
            
            # 民族统计
            nation = user.nation or '未知'
            nation_stats[nation] = nation_stats.get(nation, 0) + 1
        
        return {
            'gender': gender_stats,
            'age': age_stats,
            'nation': nation_stats,
            'total_users': len(users)
        }

    def get_daily_collection_count(self, date, collection_id=None):
        """获取指定日期的采集数量"""
        query = self.db.query(CollectionRecord).filter(
            CollectionRecord.collection_date == date,
            CollectionRecord.status == 'completed'
        )
        
        if collection_id:
            query = query.filter(CollectionRecord.collection_id == collection_id)
        elif self.current_collection_id:
            query = query.filter(CollectionRecord.collection_id == self.current_collection_id)
        
        return query.count()

    def search_users(self, keyword, collection_id=None, gender=None, age_range=None, nation=None):
        """高级搜索用户"""
        from datetime import datetime
        
        query = self.db.query(User)
        
        if collection_id:
            query = query.filter(User.collection_id == collection_id)
        elif self.current_collection_id:
            query = query.filter(User.collection_id == self.current_collection_id)
        
        # 关键词搜索（姓名或身份证号）
        if keyword:
            query = query.filter(
                (User.name.like(f'%{keyword}%')) | 
                (User.id_number.like(f'%{keyword}%'))
            )
        
        # 性别筛选
        if gender:
            query = query.filter(User.gender == gender)
        
        # 民族筛选
        if nation:
            query = query.filter(User.nation == nation)
        
        # 年龄范围筛选
        if age_range:
            today = datetime.now().date()
            if age_range == '0-18':
                min_age, max_age = 0, 18
            elif age_range == '18-30':
                min_age, max_age = 18, 30
            elif age_range == '30-45':
                min_age, max_age = 30, 45
            elif age_range == '45-60':
                min_age, max_age = 45, 60
            elif age_range == '60+':
                min_age, max_age = 60, 150
            else:
                min_age, max_age = 0, 150
            
            # 计算出生日期范围
            from datetime import timedelta
            max_birthday = today - timedelta(days=min_age*365)
            min_birthday = today - timedelta(days=max_age*365)
            
            query = query.filter(
                (User.birthday >= min_birthday) & 
                (User.birthday <= max_birthday)
            )
        
        return query.all()
