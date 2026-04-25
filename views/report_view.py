# -*- coding: utf-8 -*-
"""统计报表视图"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from utils.database_helper import DatabaseHelper
import json


class DataWorker(QThread):
    """数据处理线程"""
    data_ready = pyqtSignal(dict)
    
    def __init__(self, db, cid, sd, ed):
        super().__init__()
        self.db = db
        self.cid = cid
        self.sd = sd
        self.ed = ed
    
    def run(self):
        """在后台线程处理数据"""
        from controllers.echarts_generator import EChartsGenerator
        
        # 获取用户数据
        users = self.db.get_all_users(self.cid)
        total_users = len(users)
        total_photos = sum(len(self.db.get_photos_by_user(u.id)) for u in users)
        
        # 使用数据库助手获取统计数据（与趋势图一致）
        stats_data = self.db.get_collection_stats(self.sd, self.ed, self.cid)
        
        # 计算无记录用户数（有用户信息但没有采集记录）
        no_record_count = 0
        for user in users:
            records = self.db.get_records_by_user(user.id)
            if not records:
                no_record_count += 1
        
        stats = {
            'total': total_users,
            'photos': total_photos,
            'completed': stats_data['completed'],
            'processing': stats_data['processing'],
            'pending': stats_data['pending'],
            'no_record': no_record_count,
            'rate': stats_data['completion_rate']
        }

        # 生成图表配置
        charts = {
            'status': EChartsGenerator.generate_collection_status_chart(stats),
            'region': EChartsGenerator.generate_region_comparison_chart(users),
            'age': EChartsGenerator.generate_age_distribution_chart(users),
            'trend': EChartsGenerator.generate_success_rate_trend_chart(
                self.sd, self.ed, self.db, self.cid
            ),
            'nation': EChartsGenerator.generate_nation_distribution_chart(users),
            'gender': EChartsGenerator.generate_gender_distribution_chart(users)
        }
        
        self.data_ready.emit({'stats': stats, 'charts': charts})


class ChartWidget(QGroupBox):
    """图表组件"""
    
    def __init__(self, title):
        super().__init__(title)
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                background-color: #FAFAFA;
                padding: 8px;
                margin: 3px;
                font-weight: bold;
                color: #333;
            }
        """)
        self.setMinimumSize(400, 320)
        self.setMaximumSize(400, 320)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 20, 5, 5)
        
        self.web = QWebEngineView()
        layout.addWidget(self.web)
    
    def set_option(self, opt):
        """设置图表配置"""
        html = f'''
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
        </head>
        <body style="margin:0;padding:0;overflow:hidden;">
            <div id="c" style="width:100%;height:295px"></div>
            <script>
                var c = echarts.init(document.getElementById('c'));
                c.setOption({json.dumps(opt)});
                window.addEventListener('resize', function() {{
                    c.resize();
                }});
            </script>
        </body>
        </html>
        '''
        self.web.setHtml(html)



class ReportView(QWidget):
    """统计报表视图"""
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseHelper()
        self.cid = None
        self.worker = None
        self.charts = {}
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 筛选条件
        fg = QGroupBox("筛选条件")
        fl = QHBoxLayout()
        fl.setSpacing(8)
        
        fl.addWidget(QLabel("采集任务:"))
        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self.on_changed)
        self.combo.setMinimumWidth(250)
        fl.addWidget(self.combo)
        
        fl.addWidget(QLabel("开始日期:"))
        self.sd = QDateEdit()
        self.sd.setDate(QDate.currentDate().addDays(-30))
        self.sd.dateChanged.connect(self.refresh_stats)
        self.sd.setMaximumWidth(120)
        fl.addWidget(self.sd)
        
        fl.addWidget(QLabel("结束日期:"))
        self.ed = QDateEdit()
        self.ed.setDate(QDate.currentDate())
        self.ed.dateChanged.connect(self.refresh_stats)
        self.ed.setMaximumWidth(120)
        fl.addWidget(self.ed)
        
        fl.addStretch()
        fg.setLayout(fl)
        layout.addWidget(fg)
        
        # 统计信息
        sg = QGroupBox("统计信息")
        sl = QHBoxLayout()
        sl.setSpacing(15)
        
        self.l1 = QLabel("用户总数: 0")
        self.l1.setStyleSheet("font-weight: bold;")
        self.l2 = QLabel("照片总数: 0")
        self.l2.setStyleSheet("font-weight: bold;")
        self.l3 = QLabel("已完成: 0")
        self.l3.setStyleSheet("color: green; font-weight: bold;")
        self.l4 = QLabel("待处理: 0")
        self.l4.setStyleSheet("color: orange; font-weight: bold;")
        self.l5 = QLabel("待采集: 0")
        self.l5.setStyleSheet("color: #DAA520; font-weight: bold;")
        self.l6 = QLabel("无记录: 0")
        self.l6.setStyleSheet("color: gray; font-weight: bold;")
        self.l7 = QLabel("完成率: 0%")
        self.l7.setStyleSheet("font-weight: bold;")
        
        sl.addWidget(self.l1)
        sl.addWidget(self.l2)
        sl.addWidget(self.l3)
        sl.addWidget(self.l4)
        sl.addWidget(self.l5)
        sl.addWidget(self.l6)
        sl.addWidget(self.l7)
        sl.addStretch()
        
        btn = QPushButton("刷新统计")
        btn.clicked.connect(self.refresh_stats)
        btn.setMaximumWidth(100)
        sl.addWidget(btn)
        
        export_btn = QPushButton("导出报表")
        export_btn.clicked.connect(self.export_report)
        export_btn.setMaximumWidth(100)
        sl.addWidget(export_btn)
        
        sg.setLayout(sl)
        layout.addWidget(sg)

        
        # 图表
        cg = QGroupBox("统计图表")
        cl = QVBoxLayout()
        cl.setContentsMargins(5, 5, 5, 5)
        
        gw = QWidget()
        gl = QGridLayout(gw)
        gl.setSpacing(5)
        gl.setContentsMargins(0, 0, 0, 0)
        
        self.charts = {
            'status': ChartWidget("采集状态分布"),
            'region': ChartWidget("地区用户对比"),
            'age': ChartWidget("年龄段分布"),
            'trend': ChartWidget("采集进度趋势"),
            'nation': ChartWidget("民族分布"),
            'gender': ChartWidget("性别分布")
        }
        
        gl.addWidget(self.charts['status'], 0, 0)
        gl.addWidget(self.charts['region'], 0, 1)
        gl.addWidget(self.charts['age'], 0, 2)
        gl.addWidget(self.charts['trend'], 1, 0)
        gl.addWidget(self.charts['nation'], 1, 1)
        gl.addWidget(self.charts['gender'], 1, 2)
        
        cl.addWidget(gw)
        cg.setLayout(cl)
        layout.addWidget(cg, 1)
        
        self.load()
    
    def load(self):
        """加载采集任务列表"""
        cols = self.db.get_active_collections()
        self.combo.clear()
        self.combo.addItem("全部采集任务", None)
        for c in cols:
            self.combo.addItem(f"{c.name} ({c.organization})", c.id)
    
    def on_changed(self, i):
        """采集任务切换"""
        if i >= 0:
            self.cid = self.combo.currentData()
            self.db.set_current_collection(self.cid)
            self.refresh_stats()
    
    def showEvent(self, e):
        """显示事件"""
        super().showEvent(e)
        self.load()
        self.refresh_stats()
    
    def refresh_stats(self):
        """刷新统计数据"""
        if self.worker:
            try:
                if self.worker.isRunning():
                    self.worker.quit()
                    self.worker.wait()
            except:
                pass
        
        sd = self.sd.date().toPyDate()
        ed = self.ed.date().toPyDate()
        self.worker = DataWorker(self.db, self.cid, sd, ed)
        self.worker.data_ready.connect(self.update_ui)
        self.worker.start()
    
    def update_ui(self, data):
        """更新界面"""
        s = data['stats']
        self.l1.setText(f"用户总数: {s['total']}")
        self.l2.setText(f"照片总数: {s['photos']}")
        self.l3.setText(f"已完成: {s['completed']}")
        self.l4.setText(f"待处理: {s['processing']}")
        self.l5.setText(f"待采集: {s['pending']}")
        self.l6.setText(f"无记录: {s['no_record']}")
        self.l7.setText(f"完成率: {s['rate']:.1f}%")
        
        for k, opt in data['charts'].items():
            if k in self.charts:
                self.charts[k].set_option(opt)
    
    def closeEvent(self, e):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        self.db.close()
        e.accept()
    
    def export_report(self):
        """导出报表"""
        try:
            import pandas as pd
            from datetime import datetime, timedelta
            
            # 获取用户选择的日期和数据集
            sd = self.sd.date().toPyDate()
            ed = self.ed.date().toPyDate()
            cid = self.cid
            
            # 获取该数据集中的用户
            users = self.db.get_all_users(cid)
            
            # 统计各状态数量
            total_users = len(users)
            no_record = 0
            completed = 0
            processing = 0
            pending = 0
            total_photos = 0
            
            # 按地区、民族、性别、年龄统计
            region_stats = {}
            nation_stats = {}
            gender_stats = {}
            age_stats = {'0-18': 0, '18-25': 0, '26-35': 0, '36-45': 0, '46-55': 0, '56-65': 0, '65+': 0}
            
            # 用户详细列表
            user_details = []
            
            today = datetime.now().date()
            
            for u in users:
                recs = self.db.get_records_by_user(u.id)
                photos = self.db.get_photos_by_user(u.id)
                total_photos += len(photos)
                
                # 判断状态
                if not recs:
                    status_text = '无记录'
                    no_record += 1
                else:
                    latest_rec = recs[-1]
                    if latest_rec.status == 'completed':
                        status_text = '已完成'
                        completed += 1
                    elif latest_rec.status == 'processing':
                        status_text = '待处理'
                        processing += 1
                    elif latest_rec.status == 'pending':
                        status_text = '待采集'
                        pending += 1
                    else:
                        status_text = '未知'
                
                # 地区统计（从地址提取）
                if u.address:
                    if '省' in u.address:
                        region = u.address.split('省')[0] + '省'
                    elif '市' in u.address:
                        region = u.address.split('市')[0] + '市'
                    else:
                        region = u.address[:10] if len(u.address) > 10 else u.address
                else:
                    region = '未知'
                region_stats[region] = region_stats.get(region, 0) + 1
                
                # 民族统计
                nation = u.nation if u.nation else '未知'
                nation_stats[nation] = nation_stats.get(nation, 0) + 1
                
                # 性别统计
                gender = u.gender if u.gender else '未知'
                gender_stats[gender] = gender_stats.get(gender, 0) + 1
                
                # 年龄统计
                age = None
                if u.birthday:
                    age = (today - u.birthday).days // 365
                    if age < 18:
                        age_stats['0-18'] += 1
                    elif age <= 25:
                        age_stats['18-25'] += 1
                    elif age <= 35:
                        age_stats['26-35'] += 1
                    elif age <= 45:
                        age_stats['36-45'] += 1
                    elif age <= 55:
                        age_stats['46-55'] += 1
                    elif age <= 65:
                        age_stats['56-65'] += 1
                    else:
                        age_stats['65+'] += 1
                
                # 照片统计
                raw_photos = [p for p in photos if p.photo_type == 'raw']
                processed_photos = [p for p in photos if p.photo_type == 'processed']
                
                # 采集日期
                collection_date = recs[-1].collection_date if recs else None
                
                # 用户详细信息
                user_details.append({
                    '序号': len(user_details) + 1,
                    '姓名': u.name,
                    '身份证号': u.id_number,
                    '性别': gender,
                    '民族': nation,
                    '年龄': age if age else '未知',
                    '地区': region,
                    '采集状态': status_text,
                    '原始照片数': len(raw_photos),
                    '处理后照片数': len(processed_photos),
                    '采集日期': collection_date.strftime('%Y-%m-%d') if collection_date else '未采集'
                })
            
            # 计算完成率
            total_records = completed + processing + pending
            completion_rate = (completed / total_records * 100) if total_records > 0 else 0
            
            # 创建Excel工作簿
            filename = f"统计报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = QFileDialog.getSaveFileName(self, "导出报表", filename, "Excel文件 (*.xlsx)")[0]
            
            if filepath:
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    # Sheet 1：总体统计
                    summary_data = {
                        '统计项目': [
                            '采集任务',
                            '统计日期范围',
                            '报表生成时间',
                            '',
                            '用户总数',
                            '照片总数',
                            '',
                            '已完成',
                            '待处理',
                            '待采集',
                            '无记录',
                            '',
                            '采集记录总数',
                            '完成率',
                            '',
                            '男性人数',
                            '女性人数',
                            '性别比例'
                        ],
                        '统计数值': [
                            self.combo.currentText(),
                            f"{sd} 至 {ed}",
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            '',
                            total_users,
                            total_photos,
                            '',
                            completed,
                            processing,
                            pending,
                            no_record,
                            '',
                            total_records,
                            f'{completion_rate:.2f}%',
                            '',
                            gender_stats.get('男', 0),
                            gender_stats.get('女', 0),
                            f"{gender_stats.get('男', 0) / max(1, total_users) * 100:.1f}% : {gender_stats.get('女', 0) / max(1, total_users) * 100:.1f}%"
                        ]
                    }
                    df_summary = pd.DataFrame(summary_data)
                    df_summary.to_excel(writer, sheet_name='总体统计', index=False)
                    
                    # Sheet 2：用户详细列表
                    df_users = pd.DataFrame(user_details)
                    df_users.to_excel(writer, sheet_name='用户详细列表', index=False)
                    
                    # Sheet 3：状态分布统计
                    status_data = {
                        '采集状态': ['已完成', '待处理', '待采集', '无记录', '合计'],
                        '人数': [completed, processing, pending, no_record, total_users],
                        '占比(%)': [
                            f'{completed/max(1, total_users)*100:.2f}',
                            f'{processing/max(1, total_users)*100:.2f}',
                            f'{pending/max(1, total_users)*100:.2f}',
                            f'{no_record/max(1, total_users)*100:.2f}',
                            '100.00'
                        ]
                    }
                    df_status = pd.DataFrame(status_data)
                    df_status.to_excel(writer, sheet_name='状态分布', index=False)
                    
                    # Sheet 4：地区分布
                    region_data = sorted(region_stats.items(), key=lambda x: x[1], reverse=True)
                    df_region = pd.DataFrame(region_data, columns=['地区', '人数'])
                    df_region['占比(%)'] = df_region['人数'].apply(lambda x: f'{x/max(1, total_users)*100:.2f}')
                    df_region.to_excel(writer, sheet_name='地区分布', index=False)
                    
                    # Sheet 5：民族分布
                    nation_data = sorted(nation_stats.items(), key=lambda x: x[1], reverse=True)
                    df_nation = pd.DataFrame(nation_data, columns=['民族', '人数'])
                    df_nation['占比(%)'] = df_nation['人数'].apply(lambda x: f'{x/max(1, total_users)*100:.2f}')
                    df_nation.to_excel(writer, sheet_name='民族分布', index=False)
                    
                    # Sheet 6：性别分布
                    gender_data = sorted(gender_stats.items(), key=lambda x: x[1], reverse=True)
                    df_gender = pd.DataFrame(gender_data, columns=['性别', '人数'])
                    df_gender['占比(%)'] = df_gender['人数'].apply(lambda x: f'{x/max(1, total_users)*100:.2f}')
                    df_gender.to_excel(writer, sheet_name='性别分布', index=False)
                    
                    # Sheet 7：年龄分布
                    age_data = [(k, v) for k, v in age_stats.items() if v > 0]
                    if age_data:
                        df_age = pd.DataFrame(age_data, columns=['年龄段', '人数'])
                        df_age['占比(%)'] = df_age['人数'].apply(lambda x: f'{x/max(1, total_users)*100:.2f}')
                        df_age.to_excel(writer, sheet_name='年龄分布', index=False)
                    
                    # Sheet 8：每日采集统计
                    daily_stats = []
                    current_date = sd
                    while current_date <= ed:
                        records = self.db.get_records_by_date(current_date, cid)
                        if records:
                            day_completed = len([r for r in records if r.status == 'completed'])
                            day_processing = len([r for r in records if r.status == 'processing'])
                            day_pending = len([r for r in records if r.status == 'pending'])
                            day_total = len(records)
                            day_rate = (day_completed / day_total * 100) if day_total > 0 else 0
                            
                            daily_stats.append({
                                '日期': current_date.strftime('%Y-%m-%d'),
                                '采集记录数': day_total,
                                '已完成': day_completed,
                                '待处理': day_processing,
                                '待采集': day_pending,
                                '完成率(%)': f'{day_rate:.2f}'
                            })
                        current_date += timedelta(days=1)
                    
                    if daily_stats:
                        df_daily = pd.DataFrame(daily_stats)
                        df_daily.to_excel(writer, sheet_name='每日采集统计', index=False)
                
                QMessageBox.information(self, "成功", f"报表已导出到:\n{filepath}\n\n包含以下数据表：\n1. 总体统计\n2. 用户详细列表\n3. 状态分布\n4. 地区分布\n5. 民族分布\n6. 性别分布\n7. 年龄分布\n8. 每日采集统计")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
            import traceback
            traceback.print_exc()
