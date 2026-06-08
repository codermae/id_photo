"""
证件照智能采集及处理系统 - 软著鉴别材料第6部分
统计分析和可视化报表生成

================================================================================
第6部分: 数据统计和报表生成
================================================================================

本部分实现数据统计分析、报表生成和ECharts可视化等功能，
为用户提供直观的数据分析和决策支持。

"""

# ============================================================================
# 文件名: controllers/echarts_generator.py
# 功能: ECharts图表生成器，生成交互式可视化图表
# 行数: 89 行
# ============================================================================

import json
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from config.database import SessionLocal
from models.user import User
from models.photo import Photo

class EChartsGenerator:
    """
    ECharts图表生成器
    
    功能:
    1. 生成多种类型的图表
    2. 数据聚合和计算
    3. 生成ECharts配置JSON
    4. 支持时间范围过滤
    5. 支持多维度统计
    """
    
    def __init__(self):
        """初始化图表生成器"""
        self.db = SessionLocal()
        self.base_theme = {
            'color': ['#5470c6', '#91419f', '#ee6666', '#73c0de', '#3ba272'],
            'backgroundColor': '#ffffff'
        }
    
    def generate_daily_stats_chart(self, days=30):
        """
        生成日均采集统计图表
        
        返回: ECharts配置JSON字符串
        """
        dates = []
        counts = []
        
        for i in range(days - 1, -1, -1):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            dates.append(date_str)
            
            start = date.replace(hour=0, minute=0, second=0)
            end = date.replace(hour=23, minute=59, second=59)
            
            count = self.db.query(User).filter(
                User.created_at >= start,
                User.created_at <= end,
                User.is_deleted == False
            ).count()
            
            counts.append(count)
        
        config = {
            'title': {
                'text': '日均采集人数统计',
                'subtext': f'过去{days}天',
                'left': 'center'
            },
            'tooltip': {'trigger': 'axis'},
            'grid': {'left': '10%', 'right': '10%', 'top': '20%', 'bottom': '10%'},
            'xAxis': {
                'type': 'category',
                'data': dates,
                'axisLabel': {'interval': max(0, len(dates) // 7), 'rotate': 45}
            },
            'yAxis': {'type': 'value', 'name': '采集人数'},
            'series': [{
                'data': counts,
                'type': 'line',
                'smooth': True,
                'areaStyle': {'color': 'rgba(84, 112, 198, 0.3)'},
                'lineStyle': {'color': '#5470c6', 'width': 2}
            }],
            'color': self.base_theme['color']
        }
        
        return json.dumps(config, ensure_ascii=False)
    
    def generate_status_distribution_chart(self):
        """
        生成采集状态分布饼图
        
        返回: ECharts配置JSON字符串
        """
        statuses = ['completed', 'pending', 'failed']
        status_names = {'completed': '已采集', 'pending': '待采集', 'failed': '失败'}
        data = []
        
        for status in statuses:
            count = self.db.query(User).filter(
                User.status == status,
                User.is_deleted == False
            ).count()
            
            data.append({
                'name': status_names[status],
                'value': count
            })
        
        config = {
            'title': {
                'text': '采集状态分布',
                'subtext': '采集人数统计',
                'left': 'center'
            },
            'tooltip': {'trigger': 'item'},
            'legend': {'orient': 'vertical', 'left': 'left'},
            'series': [{
                'name': '采集状态',
                'type': 'pie',
                'radius': '50%',
                'data': data,
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 10,
                        'shadowOffsetX': 0,
                        'shadowColor': 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }],
            'color': self.base_theme['color']
        }
        
        return json.dumps(config, ensure_ascii=False)
    
    def generate_spec_distribution_chart(self):
        """
        生成证件照规格分布条形图
        
        返回: ECharts配置JSON字符串
        """
        specs = self.db.query(
            Photo.spec,
            func.count(Photo.id).label('count')
        ).filter(
            Photo.is_deleted == False
        ).group_by(Photo.spec).all()
        
        spec_names = [s[0] for s in specs]
        counts = [s[1] for s in specs]
        
        config = {
            'title': {
                'text': '证件照规格分布',
                'subtext': '规格使用统计',
                'left': 'center'
            },
            'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
            'grid': {'left': '10%', 'right': '10%', 'top': '20%', 'bottom': '15%'},
            'xAxis': {
                'type': 'category',
                'data': spec_names,
                'axisLabel': {'interval': 0, 'rotate': 45}
            },
            'yAxis': {'type': 'value', 'name': '使用数量'},
            'series': [{
                'data': counts,
                'type': 'bar',
                'itemStyle': {'color': '#5470c6'}
            }],
            'color': self.base_theme['color']
        }
        
        return json.dumps(config, ensure_ascii=False)
    
    def generate_quality_distribution_chart(self):
        """
        生成照片质量评分分布直方图
        
        返回: ECharts配置JSON字符串
        """
        # 按质量评分分桶
        ranges = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
        range_labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
        counts = []
        
        for min_score, max_score in ranges:
            count = self.db.query(Photo).filter(
                Photo.quality_score >= min_score,
                Photo.quality_score < max_score,
                Photo.is_deleted == False
            ).count()
            counts.append(count)
        
        config = {
            'title': {
                'text': '照片质量评分分布',
                'subtext': '质量评分统计',
                'left': 'center'
            },
            'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
            'grid': {'left': '10%', 'right': '10%', 'top': '20%', 'bottom': '15%'},
            'xAxis': {
                'type': 'category',
                'data': range_labels,
                'name': '评分范围'
            },
            'yAxis': {'type': 'value', 'name': '照片数量'},
            'series': [{
                'data': counts,
                'type': 'bar',
                'itemStyle': {'color': '#ee6666'}
            }],
            'color': self.base_theme['color']
        }
        
        return json.dumps(config, ensure_ascii=False)
    
    def generate_background_color_chart(self):
        """
        生成背景颜色使用分布
        
        返回: ECharts配置JSON字符串
        """
        bg_colors = self.db.query(
            Photo.background,
            func.count(Photo.id).label('count')
        ).filter(
            Photo.background != None,
            Photo.is_deleted == False
        ).group_by(Photo.background).all()
        
        data = []
        for bg_color, count in bg_colors:
            data.append({
                'name': bg_color or '未设定',
                'value': count
            })
        
        config = {
            'title': {
                'text': '背景颜色使用统计',
                'subtext': '各颜色使用频率',
                'left': 'center'
            },
            'tooltip': {'trigger': 'item'},
            'legend': {'orient': 'vertical', 'left': 'left'},
            'series': [{
                'name': '使用次数',
                'type': 'pie',
                'radius': '50%',
                'data': data,
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 10,
                        'shadowOffsetX': 0,
                        'shadowColor': 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }],
            'color': self.base_theme['color']
        }
        
        return json.dumps(config, ensure_ascii=False)
    
    def generate_monthly_comparison_chart(self, months=6):
        """
        生成月度对比分析图表
        
        返回: ECharts配置JSON字符串
        """
        month_labels = []
        monthly_counts = []
        
        for i in range(months - 1, -1, -1):
            date = datetime.now() - timedelta(days=30*i)
            month_str = date.strftime('%Y-%m')
            month_labels.append(month_str)
            
            start = date.replace(day=1, hour=0, minute=0, second=0)
            next_month = (start + timedelta(days=32)).replace(day=1)
            
            count = self.db.query(User).filter(
                User.created_at >= start,
                User.created_at < next_month,
                User.status == 'completed',
                User.is_deleted == False
            ).count()
            
            monthly_counts.append(count)
        
        config = {
            'title': {
                'text': '月度采集对比',
                'subtext': f'过去{months}个月',
                'left': 'center'
            },
            'tooltip': {'trigger': 'axis'},
            'grid': {'left': '10%', 'right': '10%', 'top': '20%', 'bottom': '10%'},
            'xAxis': {
                'type': 'category',
                'data': month_labels
            },
            'yAxis': {'type': 'value', 'name': '采集人数'},
            'series': [{
                'data': monthly_counts,
                'type': 'bar',
                'itemStyle': {'color': '#73c0de'}
            }],
            'color': self.base_theme['color']
        }
        
        return json.dumps(config, ensure_ascii=False)


# ============================================================================
# 文件名: controllers/statistics_analyzer.py
# 功能: 统计分析控制器，计算各类统计指标
# 行数: 82 行
# ============================================================================

from datetime import datetime, timedelta
from sqlalchemy import func
from config.database import SessionLocal
from models.user import User
from models.photo import Photo

class StatisticsAnalyzer:
    """
    统计分析器
    
    功能:
    1. 计算基本统计指标
    2. 生成趋势分析报告
    3. 效率评估
    4. 异常检测
    """
    
    def __init__(self):
        """初始化统计分析器"""
        self.db = SessionLocal()
    
    def get_overall_statistics(self):
        """获取总体统计"""
        total_users = self.db.query(User).filter(
            User.is_deleted == False
        ).count()
        
        completed_users = self.db.query(User).filter(
            User.status == 'completed',
            User.is_deleted == False
        ).count()
        
        total_photos = self.db.query(Photo).filter(
            Photo.is_deleted == False
        ).count()
        
        avg_quality = self.db.query(
            func.avg(Photo.quality_score)
        ).filter(
            Photo.is_deleted == False
        ).scalar() or 0.0
        
        return {
            'total_users': total_users,
            'completed_users': completed_users,
            'pending_users': total_users - completed_users,
            'completion_rate': (completed_users / total_users * 100) if total_users > 0 else 0,
            'total_photos': total_photos,
            'avg_quality_score': round(float(avg_quality), 2),
            'photos_per_user': round(total_photos / total_users, 2) if total_users > 0 else 0
        }
    
    def get_time_range_statistics(self, start_date, end_date):
        """获取时间范围内的统计"""
        users = self.db.query(User).filter(
            User.created_at >= start_date,
            User.created_at <= end_date,
            User.is_deleted == False
        ).count()
        
        photos = self.db.query(Photo).filter(
            Photo.created_at >= start_date,
            Photo.created_at <= end_date,
            Photo.is_deleted == False
        ).count()
        
        return {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'user_count': users,
            'photo_count': photos,
            'avg_photo_per_user': photos / users if users > 0 else 0
        }
    
    def get_top_specs(self, limit=5):
        """获取最常用的规格"""
        results = self.db.query(
            Photo.spec,
            func.count(Photo.id).label('count')
        ).filter(
            Photo.is_deleted == False
        ).group_by(Photo.spec).order_by(
            func.count(Photo.id).desc()
        ).limit(limit).all()
        
        return [{'spec': r[0], 'count': r[1]} for r in results]
    
    def get_top_background_colors(self, limit=5):
        """获取最常用的背景色"""
        results = self.db.query(
            Photo.background,
            func.count(Photo.id).label('count')
        ).filter(
            Photo.background != None,
            Photo.is_deleted == False
        ).group_by(Photo.background).order_by(
            func.count(Photo.id).desc()
        ).limit(limit).all()
        
        return [{'color': r[0], 'count': r[1]} for r in results]
    
    def get_quality_statistics(self):
        """获取质量相关统计"""
        stats = self.db.query(
            func.min(Photo.quality_score).label('min_score'),
            func.max(Photo.quality_score).label('max_score'),
            func.avg(Photo.quality_score).label('avg_score'),
            func.count(Photo.id).label('total_photos')
        ).filter(
            Photo.is_deleted == False
        ).first()
        
        # 高质量照片（评分 >= 70）
        high_quality_count = self.db.query(Photo).filter(
            Photo.quality_score >= 70,
            Photo.is_deleted == False
        ).count()
        
        return {
            'min_score': round(float(stats.min_score or 0), 2),
            'max_score': round(float(stats.max_score or 0), 2),
            'avg_score': round(float(stats.avg_score or 0), 2),
            'total_photos': stats.total_photos,
            'high_quality_count': high_quality_count,
            'high_quality_rate': (high_quality_count / stats.total_photos * 100) 
                                 if stats.total_photos > 0 else 0
        }
    
    def get_processing_performance(self):
        """获取处理性能统计"""
        from models.record import CollectionRecord
        
        records = self.db.query(CollectionRecord).filter(
            CollectionRecord.processing_time > 0,
            CollectionRecord.status == 'completed'
        ).all()
        
        if not records:
            return {
                'total_records': 0,
                'avg_processing_time': 0,
                'min_processing_time': 0,
                'max_processing_time': 0
            }
        
        times = [r.processing_time for r in records]
        
        return {
            'total_records': len(records),
            'avg_processing_time': round(sum(times) / len(times), 2),
            'min_processing_time': round(min(times), 2),
            'max_processing_time': round(max(times), 2),
            'throughput': round(len(records) / sum(times), 2) if sum(times) > 0 else 0
        }
    
    def export_report(self, file_path):
        """导出统计报告"""
        overall = self.get_overall_statistics()
        quality = self.get_quality_statistics()
        performance = self.get_processing_performance()
        top_specs = self.get_top_specs()
        top_colors = self.get_top_background_colors()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'overall': overall,
            'quality': quality,
            'performance': performance,
            'top_specs': top_specs,
            'top_colors': top_colors
        }
        
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return file_path
