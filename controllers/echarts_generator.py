"""
ECharts 图表生成器 - 生成 ECharts 配置
"""
import json
from datetime import datetime, timedelta
from models.record import CollectionRecord


class EChartsGenerator:
    """ECharts 图表生成器"""
    
    @staticmethod
    def generate_collection_status_chart(stats):
        """生成采集状态分布环形图"""
        data = []
        
        if stats.get('completed', 0) > 0:
            data.append({'value': stats['completed'], 'name': '已完成', 'itemStyle': {'color': '#5CB87A'}})
        
        if stats.get('processing', 0) > 0:
            data.append({'value': stats['processing'], 'name': '待处理', 'itemStyle': {'color': '#FAC858'}})
        
        if stats.get('pending', 0) > 0:
            data.append({'value': stats['pending'], 'name': '待采集', 'itemStyle': {'color': '#E6A23C'}})
        
        if stats.get('no_record', 0) > 0:
            data.append({'value': stats['no_record'], 'name': '无记录', 'itemStyle': {'color': '#909399'}})
        
        return {
            'tooltip': {'trigger': 'item', 'formatter': '{b}: {c} ({d}%)'},
            'legend': {'orient': 'vertical', 'left': 'left', 'top': 'center'},
            'series': [{
                'type': 'pie',
                'radius': ['40%', '70%'],
                'center': ['50%', '50%'],
                'data': data,
                'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowOffsetX': 0, 'shadowColor': 'rgba(0, 0, 0, 0.5)'}},
                'label': {'show': False}
            }]
        }
    
    @staticmethod
    def generate_region_comparison_chart(filtered_users):
        """生成地区用户对比柱状图"""
        # 身份证前6位行政区划代码映射（常见省份/直辖市）
        id_region_map = {
            '11': '北京市', '12': '天津市', '13': '河北省', '14': '山西省', '15': '内蒙古自治区',
            '21': '辽宁省', '22': '吉林省', '23': '黑龙江省',
            '31': '上海市', '32': '江苏省', '33': '浙江省', '34': '安徽省', '35': '福建省', '36': '江西省', '37': '山东省',
            '41': '河南省', '42': '湖北省', '43': '湖南省', '44': '广东省', '45': '广西壮族自治区', '46': '海南省',
            '50': '重庆市', '51': '四川省', '52': '贵州省', '53': '云南省', '54': '西藏自治区',
            '61': '陕西省', '62': '甘肃省', '63': '青海省', '64': '宁夏回族自治区', '65': '新疆维吾尔自治区',
            '71': '台湾省', '81': '香港特别行政区', '82': '澳门特别行政区'
        }
        
        region_stats = {}
        for user in filtered_users:
            region = None
            
            # 如果地址不为空，直接使用地址
            if user.address:
                if '省' in user.address:
                    region = user.address.split('省')[0] + '省'
                elif '市' in user.address:
                    region = user.address.split('市')[0] + '市'
                else:
                    # 地址格式不标准，取前10个字符
                    region = user.address[:10] if len(user.address) > 10 else user.address
            else:
                # 地址为空，尝试从身份证号推断
                if user.id_number and len(user.id_number) >= 6:
                    province_code = user.id_number[:2]
                    region = id_region_map.get(province_code, None)
                    if region:
                        print(f"[DEBUG] 从身份证推断地区: 用户={user.name}, 身份证={user.id_number}, 推断地区={region}")
                    else:
                        region = '未知'
                        print(f"[DEBUG] 身份证代码无法识别: 用户={user.name}, 身份证={user.id_number}, 前2位={province_code}")
                else:
                    region = '未知'
                    print(f"[DEBUG] 地址和身份证都无效: 用户={user.name}, 身份证={user.id_number}")
            
            region_stats[region] = region_stats.get(region, 0) + 1
        
        sorted_regions = sorted(region_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        regions = [r[0] for r in sorted_regions]
        values = [r[1] for r in sorted_regions]
        
        return {
            'tooltip': {'trigger': 'axis'},
            'xAxis': {'type': 'category', 'data': regions},
            'yAxis': {'type': 'value'},
            'series': [{
                'type': 'bar',
                'data': values,
                'itemStyle': {'color': '#5470C6'}
            }]
        }
    
    @staticmethod
    def generate_age_distribution_chart(filtered_users):
        """生成年龄段分布图"""
        age_groups = {
            '18-25': 0,
            '26-35': 0,
            '36-45': 0,
            '46-55': 0,
            '56-65': 0,
            '65+': 0
        }
        
        today = datetime.now().date()
        for user in filtered_users:
            if user.birthday:
                age = (today - user.birthday).days // 365
                if age < 18:
                    continue
                elif age <= 25:
                    age_groups['18-25'] += 1
                elif age <= 35:
                    age_groups['26-35'] += 1
                elif age <= 45:
                    age_groups['36-45'] += 1
                elif age <= 55:
                    age_groups['46-55'] += 1
                elif age <= 65:
                    age_groups['56-65'] += 1
                else:
                    age_groups['65+'] += 1
        
        age_labels = list(age_groups.keys())
        age_values = list(age_groups.values())
        
        return {
            'tooltip': {'trigger': 'axis'},
            'xAxis': {'type': 'category', 'data': age_labels},
            'yAxis': {'type': 'value'},
            'series': [{
                'type': 'bar',
                'data': age_values,
                'itemStyle': {'color': '#91CC75'}
            }]
        }
    
    @staticmethod
    def generate_success_rate_trend_chart(start_date, end_date, db, collection_id):
        """生成完成率趋势折线图（三率对比）
        
        显示三条趋势线：
        1. 完成率 = 截止到当天累计已完成数 / 用户总数 × 100%
        2. 处理率 = 截止到当天累计(已完成+待处理)数 / 用户总数 × 100%
        3. 采集率 = 截止到当天累计(已完成+待处理+待采集)数 / 用户总数 × 100%
        
        关系：采集率 ≥ 处理率 ≥ 完成率
        """
        from datetime import timedelta
        from models.record import CollectionRecord
        
        dates = []
        completion_rates = []  # 完成率
        processing_rates = []  # 处理率
        collection_rates = []  # 采集率
        
        # 获取用户总数（包含无记录用户）
        total_users = db.get_user_count(collection_id)
        
        if total_users == 0:
            # 如果没有用户，返回空数据
            return {
                'title': {'text': '采集进度趋势', 'left': 'center'},
                'tooltip': {'trigger': 'axis'},
                'legend': {'data': ['完成率', '处理率', '采集率'], 'top': '30px'},
                'xAxis': {'type': 'category', 'data': []},
                'yAxis': {'type': 'value', 'min': 0, 'max': 100},
                'series': []
            }
        
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%m-%d'))
            
            try:
                # 构建基础查询：截止到当前日期的所有记录
                base_query = db.db.query(CollectionRecord).filter(
                    CollectionRecord.collection_date <= current_date
                )
                
                # 如果指定了采集任务，只查询该任务的数据
                if collection_id:
                    base_query = base_query.filter(CollectionRecord.collection_id == collection_id)
                elif db.current_collection_id:
                    base_query = base_query.filter(CollectionRecord.collection_id == db.current_collection_id)
                
                # 获取所有记录
                all_records = base_query.all()
                
                # 统计各状态的记录数
                cumulative_completed = len([r for r in all_records if r.status == 'completed'])
                cumulative_processed = len([r for r in all_records if r.status in ['completed', 'processing']])
                cumulative_collected = len([r for r in all_records if r.status in ['completed', 'processing', 'pending']])
                
                # 计算百分比
                completion_rate = (cumulative_completed / total_users * 100)
                processing_rate = (cumulative_processed / total_users * 100)
                collection_rate = (cumulative_collected / total_users * 100)
                
            except Exception as e:
                print(f"[ERROR] 计算完成率失败 ({current_date}): {e}")
                completion_rate = 0
                processing_rate = 0
                collection_rate = 0
            
            completion_rates.append(round(completion_rate, 2))
            processing_rates.append(round(processing_rate, 2))
            collection_rates.append(round(collection_rate, 2))
            current_date = current_date + timedelta(days=1)
        
        return {
            'title': {'text': '采集进度趋势',  'left': 'center'},
            'tooltip': {
                'trigger': 'axis',
                'formatter': '{b}<br/>{a0}: {c0}%<br/>{a1}: {c1}%<br/>{a2}: {c2}%'
            },
            'legend': {
                'data': ['完成率', '处理率', '采集率'],
                'top': '30px'
            },
            'dataZoom': [
                {
                    'type': 'inside',
                    'start': 0,
                    'end': 100,
                    'zoomOnMouseWheel': True,
                    'moveOnMouseMove': False,
                    'moveOnMouseWheel': False
                }
            ],
            'xAxis': {'type': 'category', 'data': dates, 'boundaryGap': False},
            'yAxis': {
                'type': 'value', 
                'min': 0, 
                'max': 100,
                'axisLabel': {'formatter': '{value}%'}
            },
            'series': [
                {
                    'name': '完成率',
                    'type': 'line',
                    'data': completion_rates,
                    'smooth': True,
                    'itemStyle': {'color': '#5CB87A'},
                    'lineStyle': {'width': 2},
                    'areaStyle': {'color': 'rgba(92, 184, 122, 0.1)'}
                },
                {
                    'name': '处理率',
                    'type': 'line',
                    'data': processing_rates,
                    'smooth': True,
                    'itemStyle': {'color': '#FAC858'},
                    'lineStyle': {'width': 2},
                    'areaStyle': {'color': 'rgba(250, 200, 88, 0.1)'}
                },
                {
                    'name': '采集率',
                    'type': 'line',
                    'data': collection_rates,
                    'smooth': True,
                    'itemStyle': {'color': '#5470C6'},
                    'lineStyle': {'width': 2},
                    'areaStyle': {'color': 'rgba(84, 112, 198, 0.1)'}
                }
            ]
        }
    
    @staticmethod
    def generate_nation_distribution_chart(filtered_users):
        """生成民族分布横向柱状图"""
        nation_stats = {}
        for user in filtered_users:
            nation = user.nation if user.nation else '未知'
            nation_stats[nation] = nation_stats.get(nation, 0) + 1
        
        # 按数量排序，取前10
        sorted_nations = sorted(nation_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        nations = [n[0] for n in sorted_nations]
        values = [n[1] for n in sorted_nations]
        
        return {
            'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
            'grid': {'left': '15%', 'right': '10%', 'top': '10%', 'bottom': '10%'},
            'xAxis': {'type': 'value'},
            'yAxis': {'type': 'category', 'data': nations, 'axisLabel': {'interval': 0}},
            'series': [{
                'type': 'bar',
                'data': values,
                'itemStyle': {'color': '#91CC75'},
                'label': {'show': True, 'position': 'right', 'formatter': '{c}人'}
            }]
        }
    
    @staticmethod
    def generate_gender_distribution_chart(filtered_users):
        """生成性别分布仪表盘"""
        gender_stats = {'男': 0, '女': 0, '未知': 0}
        for user in filtered_users:
            gender = user.gender if user.gender in ['男', '女'] else '未知'
            gender_stats[gender] += 1
        
        total = sum(gender_stats.values())
        male_ratio = (gender_stats['男'] / total * 100) if total > 0 else 0
        female_ratio = 100 - male_ratio
        
        return {
            'tooltip': {'formatter': '男性占比: {c}%'},
            'series': [{
                'type': 'gauge',
                'startAngle': 180,
                'endAngle': 0,
                'center': ['50%', '65%'],
                'radius': '90%',
                'min': 0,
                'max': 100,
                'splitNumber': 10,
                'axisLine': {
                    'lineStyle': {
                        'width': 20,
                        'color': [[0.5, '#5470C6'], [1, '#EE6666']]
                    }
                },
                'pointer': {'itemStyle': {'color': 'auto'}},
                'axisTick': {'distance': -20, 'length': 5, 'lineStyle': {'color': '#fff', 'width': 1}},
                'splitLine': {'distance': -25, 'length': 15, 'lineStyle': {'color': '#fff', 'width': 2}},
                'axisLabel': {'distance': -35, 'color': 'auto', 'fontSize': 10, 'formatter': '{value}%'},
                'detail': {
                    'valueAnimation': True,
                    'formatter': f'男性 {male_ratio:.1f}%    女性 {female_ratio:.1f}%',
                    'color': '#333',
                    'fontSize': 14,
                    'offsetCenter': [0, '30%']
                },
                'data': [{'value': round(male_ratio, 1), 'name': '性别比例'}],
                'title': {'show': False}
            }]
        }
