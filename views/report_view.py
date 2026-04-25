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
        total = len(users)
        photos = sum(len(self.db.get_photos_by_user(u.id)) for u in users)
        
        # 统计采集状态
        c = p = f = 0
        for u in users:
            recs = [r for r in self.db.get_records_by_user(u.id) 
                   if self.sd <= r.collection_date <= self.ed]
            if recs:
                s = recs[-1].status
                if s == 'completed':
                    c += 1
                elif s == 'pending':
                    p += 1
                elif s == 'failed':
                    f += 1
        
        rate = (c / max(1, c+p+f)) * 100 if c+p+f > 0 else 0
        stats = {
            'total': total,
            'photos': photos,
            'completed': c,
            'pending': p,
            'failed': f,
            'rate': rate
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
        self.l3 = QLabel("已采集: 0")
        self.l3.setStyleSheet("color: green; font-weight: bold;")
        self.l4 = QLabel("待采集: 0")
        self.l4.setStyleSheet("color: orange; font-weight: bold;")
        self.l5 = QLabel("失败: 0")
        self.l5.setStyleSheet("color: red; font-weight: bold;")
        self.l6 = QLabel("完成率: 0%")
        self.l6.setStyleSheet("font-weight: bold;")
        
        sl.addWidget(self.l1)
        sl.addWidget(self.l2)
        sl.addWidget(self.l3)
        sl.addWidget(self.l4)
        sl.addWidget(self.l5)
        sl.addWidget(self.l6)
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
            'trend': ChartWidget("成功率趋势"),
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
        self.l3.setText(f"已采集: {s['completed']}")
        self.l4.setText(f"待采集: {s['pending']}")
        self.l5.setText(f"失败: {s['failed']}")
        self.l6.setText(f"完成率: {s['rate']:.1f}%")
        
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
            from datetime import datetime
            
            # 获取用户选择的日期和数据集
            sd = self.sd.date().toPyDate()
            ed = self.ed.date().toPyDate()
            cid = self.cid
            
            # 获取该数据集中的用户
            users = self.db.get_all_users(cid)
            
            total = 0
            photos = 0
            c = p = f = 0
            
            # 按日期范围统计
            for u in users:
                recs = [r for r in self.db.get_records_by_user(u.id) 
                       if sd <= r.collection_date <= ed]
                if recs:
                    total += 1
                    photos += len(self.db.get_photos_by_user(u.id))
                    s = recs[-1].status
                    if s == 'completed':
                        c += 1
                    elif s == 'pending':
                        p += 1
                    elif s == 'failed':
                        f += 1
            
            rate = (c / max(1, c+p+f)) * 100 if c+p+f > 0 else 0
            
            # 按地区统计（仅统计日期范围内的用户）
            region_stats = {}
            nation_stats = {}
            gender_stats = {}
            
            for u in users:
                recs = [r for r in self.db.get_records_by_user(u.id) 
                       if sd <= r.collection_date <= ed]
                if recs:
                    region = getattr(u, 'region', '未知')
                    region_stats[region] = region_stats.get(region, 0) + 1
                    
                    nation = getattr(u, 'nation', '未知')
                    nation_stats[nation] = nation_stats.get(nation, 0) + 1
                    
                    gender = getattr(u, 'gender', '未知')
                    gender_stats[gender] = gender_stats.get(gender, 0) + 1
            
            # 创建Excel工作簿
            filename = f"统计报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = QFileDialog.getSaveFileName(self, "导出报表", filename, "Excel文件 (*.xlsx)")[0]
            
            if filepath:
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    # 第一个sheet：总体统计
                    summary_data = {
                        '指标': ['数据集', '日期范围', '用户总数', '照片总数', '已采集', '待采集', '失败', '完成率(%)'],
                        '数值': [
                            self.combo.currentText(),
                            f"{sd} 至 {ed}",
                            total, 
                            photos, 
                            c, 
                            p, 
                            f, 
                            f'{rate:.2f}'
                        ]
                    }
                    df_summary = pd.DataFrame(summary_data)
                    df_summary.to_excel(writer, sheet_name='总体统计', index=False)
                    
                    # 第二个sheet：地区分布
                    df_region = pd.DataFrame(list(region_stats.items()), columns=['地区', '人数'])
                    df_region.to_excel(writer, sheet_name='地区分布', index=False)
                    
                    # 第三个sheet：民族分布
                    df_nation = pd.DataFrame(list(nation_stats.items()), columns=['民族', '人数'])
                    df_nation.to_excel(writer, sheet_name='民族分布', index=False)
                    
                    # 第四个sheet：性别分布
                    df_gender = pd.DataFrame(list(gender_stats.items()), columns=['性别', '人数'])
                    df_gender.to_excel(writer, sheet_name='性别分布', index=False)
                
                QMessageBox.information(self, "成功", f"报表已导出到:\n{filepath}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
