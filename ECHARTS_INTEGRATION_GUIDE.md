# ECharts 集成指南

## 一、概述

### 1.1 为什么选择 ECharts？

| 特性 | ECharts | Matplotlib | Plotly | PyQtGraph |
|------|---------|-----------|--------|-----------|
| 交互性 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 美观度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 功能丰富 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 易用性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 文件大小 | 中等 | 小 | 大 | 小 |

### 1.2 ECharts 优势
- 功能强大：支持 30+ 种图表类型
- 交互性好：缩放、拖拽、点击钻取等
- 美观现代：开箱即用的美观样式
- 性能优秀：支持大数据量渲染
- 文档完善：官方文档详细、示例丰富
- 开源免费：Apache 2.0 许可证

---

## 二、集成方案

### 2.1 技术架构

```
PyQt5 应用
    ↓
QWebEngineView（浏览器容器）
    ↓
HTML + JavaScript（ECharts）
    ↓
Python ↔ JavaScript 通信（QWebChannel）
```

### 2.2 依赖安装

```bash
# 添加到 requirements.txt
pyqtwebengine>=5.15.0

# 安装
pip install pyqtwebengine
```

### 2.3 文件结构

```
id_photo_system/
├── views/
│   ├── report_view.py          # 报表视图（修改）
│   └── chart_widget.py         # 新增：图表组件
├── resources/
│   └── charts/
│       ├── chart_template.html # 新增：图表模板
│       └── echarts.min.js      # 新增：ECharts 库（CDN 或本地）
└── utils/
    └── chart_helper.py         # 新增：图表辅助函数
```

---

## 三、核心实现

### 3.1 图表组件基类

```python
# views/chart_widget.py

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer
import json
import os

class ChartWidget(QWebEngineView):
    """ECharts 图表组件基类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_id = "chart_" + str(id(self))
        self.chart_option = {}
        self.init_chart()
    
    def init_chart(self):
        """初始化图表"""
        # 加载 HTML 模板
        html_path = os.path.join(
            os.path.dirname(__file__),
            '../resources/charts/chart_template.html'
        )
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 替换图表 ID
        html_content = html_content.replace('${CHART_ID}', self.chart_id)
        
        # 加载 HTML
        self.setHtml(html_content)
    
    def set_option(self, option):
        """设置图表选项"""
        self.chart_option = option
        self.update_chart()
    
    def update_chart(self):
        """更新图表"""
        # 将 Python 字典转换为 JSON
        option_json = json.dumps(self.chart_option, ensure_ascii=False)
        
        # 调用 JavaScript 更新图表
        js_code = f"""
        if (window.chart_{self.chart_id}) {{
            window.chart_{self.chart_id}.setOption({option_json});
        }}
        """
        
        self.page().runJavaScript(js_code)
    
    def resize_chart(self):
        """调整图表大小"""
        js_code = f"""
        if (window.chart_{self.chart_id}) {{
            window.chart_{self.chart_id}.resize();
        }}
        """
        self.page().runJavaScript(js_code)
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 延迟调整图表大小，避免频繁调用
        QTimer.singleShot(100, self.resize_chart)
```

### 3.2 HTML 模板

```html
<!-- resources/charts/chart_template.html -->

<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
        }
        body {
            width: 100%;
            height: 100%;
            background-color: white;
        }
        #${CHART_ID} {
            width: 100%;
            height: 100%;
        }
    </style>
</head>
<body>
    <div id="${CHART_ID}"></div>
    <script>
        // 初始化图表
        var chartDom = document.getElementById('${CHART_ID}');
        var chart_${CHART_ID} = echarts.init(chartDom);
        window.chart_${CHART_ID} = chart_${CHART_ID};
        
        // 设置默认选项
        var option = {
            title: {
                text: '加载中...'
            }
        };
        
        chart_${CHART_ID}.setOption(option);
        
        // 窗口大小改变时调整图表
        window.addEventListener('resize', function() {
            chart_${CHART_ID}.resize();
        });
    </script>
</body>
</html>
```

---

## 四、图表实现

### 4.1 完成率仪表盘

```python
def create_gauge_chart(completion_rate):
    """创建完成率仪表盘"""
    return {
        'series': [
            {
                'type': 'gauge',
                'startAngle': 225,
                'endAngle': -45,
                'radius': '75%',
                'center': ['50%', '50%'],
                'progress': {
                    'itemStyle': {
                        'borderRadius': 10,
                        'borderWidth': 2
                    }
                },
                'axisLine': {
                    'lineStyle': {
                        'width': 30
                    }
                },
                'axisTick': {
                    'distance': -30,
                    'length': 8,
                    'lineStyle': {
                        'color': '#fff',
                        'width': 2
                    }
                },
                'splitLine': {
                    'distance': -30,
                    'length': 30,
                    'lineStyle': {
                        'color': '#fff',
                        'width': 4
                    }
                },
                'axisLabel': {
                    'color': 'auto',
                    'distance': 40,
                    'fontSize': 16
                },
                'detail': {
                    'valueAnimation': True,
                    'formatter': '{value}%',
                    'color': 'auto',
                    'fontSize': 20
                },
                'data': [
                    {
                        'value': completion_rate,
                        'name': '完成率'
                    }
                ]
            }
        ]
    }
```

### 4.2 采集趋势折线图

```python
def create_line_chart(dates, daily_counts):
    """创建采集趋势折线图"""
    return {
        'title': {
            'text': '采集趋势（过去30天）',
            'left': 'center'
        },
        'tooltip': {
            'trigger': 'axis'
        },
        'xAxis': {
            'type': 'category',
            'data': dates,
            'boundaryGap': False
        },
        'yAxis': {
            'type': 'value',
            'name': '采集数量'
        },
        'series': [
            {
                'data': daily_counts,
                'type': 'line',
                'smooth': True,
                'itemStyle': {
                    'color': '#0078D4'
                },
                'areaStyle': {
                    'color': 'rgba(0, 120, 212, 0.2)'
                }
            }
        ],
        'grid': {
            'left': '10%',
            'right': '10%',
            'bottom': '10%',
            'top': '15%',
            'containLabel': True
        }
    }
```

### 4.3 采集状态饼图

```python
def create_pie_chart(completed, pending, failed):
    """创建采集状态饼图"""
    total = completed + pending + failed
    
    return {
        'title': {
            'text': '采集状态分布',
            'left': 'center'
        },
        'tooltip': {
            'trigger': 'item',
            'formatter': '{b}: {c} ({d}%)'
        },
        'series': [
            {
                'type': 'pie',
                'radius': '50%',
                'center': ['50%', '50%'],
                'data': [
                    {
                        'value': completed,
                        'name': '已采集',
                        'itemStyle': {'color': '#50E3C2'}
                    },
                    {
                        'value': pending,
                        'name': '待采集',
                        'itemStyle': {'color': '#D0D0D0'}
                    },
                    {
                        'value': failed,
                        'name': '失败',
                        'itemStyle': {'color': '#E81123'}
                    }
                ],
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 10,
                        'shadowOffsetX': 0,
                        'shadowColor': 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }
        ]
    }
```

### 4.4 采集任务对比柱状图

```python
def create_bar_chart(task_names, completed_counts, total_counts):
    """创建采集任务对比柱状图"""
    completion_rates = [
        (c / t * 100) if t > 0 else 0
        for c, t in zip(completed_counts, total_counts)
    ]
    
    return {
        'title': {
            'text': '采集任务完成情况对比',
            'left': 'center'
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'shadow'
            }
        },
        'xAxis': {
            'type': 'category',
            'data': task_names
        },
        'yAxis': {
            'type': 'value',
            'name': '完成率 (%)'
        },
        'series': [
            {
                'data': completion_rates,
                'type': 'bar',
                'itemStyle': {
                    'color': '#0078D4'
                }
            }
        ],
        'grid': {
            'left': '10%',
            'right': '10%',
            'bottom': '15%',
            'top': '15%',
            'containLabel': True
        }
    }
```

---

## 五、集成到报表视图

### 5.1 修改 report_view.py

```python
# 在 report_view.py 中添加

from views.chart_widget import ChartWidget
from utils.chart_helper import (
    create_gauge_chart,
    create_line_chart,
    create_pie_chart,
    create_bar_chart
)

class ReportView(QWidget):
    def init_ui(self):
        # ... 现有代码 ...
        
        # 替换统计信息部分为图表
        stats_group = QGroupBox("采集统计")
        stats_layout = QVBoxLayout()
        
        # 创建图表容器
        charts_layout = QHBoxLayout()
        
        # 完成率仪表盘
        self.gauge_chart = ChartWidget()
        charts_layout.addWidget(self.gauge_chart)
        
        # 采集状态饼图
        self.pie_chart = ChartWidget()
        charts_layout.addWidget(self.pie_chart)
        
        stats_layout.addLayout(charts_layout)
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        # 采集趋势折线图
        trend_group = QGroupBox("采集趋势")
        trend_layout = QVBoxLayout()
        
        self.line_chart = ChartWidget()
        self.line_chart.setMinimumHeight(300)
        trend_layout.addWidget(self.line_chart)
        
        trend_group.setLayout(trend_layout)
        main_layout.addWidget(trend_group)
        
        # 采集任务对比柱状图
        comparison_group = QGroupBox("任务对比")
        comparison_layout = QVBoxLayout()
        
        self.bar_chart = ChartWidget()
        self.bar_chart.setMinimumHeight(300)
        comparison_layout.addWidget(self.bar_chart)
        
        comparison_group.setLayout(comparison_layout)
        main_layout.addWidget(comparison_group)
    
    def refresh_stats(self):
        """刷新统计和图表"""
        # ... 现有代码 ...
        
        # 更新图表
        completion_rate = stats['completion_rate']
        self.gauge_chart.set_option(create_gauge_chart(completion_rate))
        
        self.pie_chart.set_option(create_pie_chart(
            stats['completed'],
            stats['pending'],
            stats['failed']
        ))
        
        # 获取过去30天的数据
        dates, daily_counts = self.get_daily_stats(30)
        self.line_chart.set_option(create_line_chart(dates, daily_counts))
        
        # 获取所有采集任务的数据
        task_names, completed_counts, total_counts = self.get_task_stats()
        self.bar_chart.set_option(create_bar_chart(
            task_names,
            completed_counts,
            total_counts
        ))
    
    def get_daily_stats(self, days):
        """获取过去 N 天的每日采集数据"""
        from datetime import datetime, timedelta
        
        dates = []
        daily_counts = []
        
        for i in range(days, 0, -1):
            date = datetime.now() - timedelta(days=i)
            dates.append(date.strftime('%m-%d'))
            
            # 从数据库获取该日期的采集数量
            count = self.db.get_daily_collection_count(
                date.date(),
                self.current_collection_id
            )
            daily_counts.append(count)
        
        return dates, daily_counts
    
    def get_task_stats(self):
        """获取所有采集任务的统计数据"""
        collections = self.db.get_active_collections()
        
        task_names = []
        completed_counts = []
        total_counts = []
        
        for collection in collections:
            task_names.append(collection.name)
            
            stats = self.db.get_collection_stats(
                None, None, collection.id
            )
            completed_counts.append(stats['completed'])
            total_counts.append(stats['total'])
        
        return task_names, completed_counts, total_counts
```

---

## 六、数据库扩展

### 6.1 新增查询方法

```python
# 在 database_helper.py 中添加

def get_daily_collection_count(self, date, collection_id=None):
    """获取指定日期的采集数量"""
    from datetime import datetime
    
    query = self.db.query(CollectionRecord).filter(
        CollectionRecord.created_at >= datetime.combine(date, datetime.min.time()),
        CollectionRecord.created_at < datetime.combine(date, datetime.max.time()),
        CollectionRecord.status == 'completed'
    )
    
    if collection_id:
        query = query.filter(CollectionRecord.collection_id == collection_id)
    
    return query.count()

def get_collection_stats(self, start_date, end_date, collection_id=None):
    """获取采集统计数据"""
    query = self.db.query(CollectionRecord)
    
    if start_date:
        query = query.filter(CollectionRecord.created_at >= start_date)
    
    if end_date:
        from datetime import datetime
        query = query.filter(
            CollectionRecord.created_at < datetime.combine(end_date, datetime.max.time())
        )
    
    if collection_id:
        query = query.filter(CollectionRecord.collection_id == collection_id)
    
    records = query.all()
    
    completed = len([r for r in records if r.status == 'completed'])
    pending = len([r for r in records if r.status == 'pending'])
    failed = len([r for r in records if r.status == 'failed'])
    total = len(records)
    
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    return {
        'completed': completed,
        'pending': pending,
        'failed': failed,
        'total': total,
        'completion_rate': completion_rate
    }
```

---

## 七、高级功能

### 7.1 图表交互

```python
# 支持点击事件
def on_chart_click(self, params):
    """图表点击事件处理"""
    chart_type = params.get('componentType')
    
    if chart_type == 'series':
        # 处理数据点击
        series_name = params.get('seriesName')
        data_value = params.get('value')
        print(f"点击了 {series_name}: {data_value}")
```

### 7.2 图表导出

```python
def export_chart_as_image(self, chart_widget, filename):
    """将图表导出为图片"""
    js_code = f"""
    var url = window.chart_{chart_widget.chart_id}.getDataURL({{
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff'
    }});
    
    // 创建下载链接
    var link = document.createElement('a');
    link.href = url;
    link.download = '{filename}';
    link.click();
    """
    
    chart_widget.page().runJavaScript(js_code)
```

### 7.3 主题切换

```python
def set_chart_theme(self, chart_widget, theme='light'):
    """设置图表主题"""
    themes = {
        'light': 'light',
        'dark': 'dark',
        'vintage': 'vintage',
        'westeros': 'westeros',
        'essos': 'essos',
        'wonderland': 'wonderland',
        'walden': 'walden',
        'chalk': 'chalk',
        'infographic': 'infographic',
        'macarons': 'macarons',
        'roma': 'roma',
        'sakura': 'sakura',
        'gl': 'gl',
        'bee-inspired': 'bee-inspired',
        'dark-bold': 'dark-bold',
        'dark-fresh': 'dark-fresh',
        'dark-fresh-cut': 'dark-fresh-cut',
        'dark-mushroom': 'dark-mushroom',
        'flat': 'flat',
        'fresh-cut': 'fresh-cut',
        'grey': 'grey',
        'halloween': 'halloween',
        'heatmap': 'heatmap',
        'light-fresh-cut': 'light-fresh-cut',
        'mint': 'mint',
        'purple-passion': 'purple-passion',
        'romantic': 'romantic',
        'shine': 'shine',
        'tech-blue': 'tech-blue'
    }
    
    if theme in themes:
        js_code = f"""
        echarts.registerTheme('{theme}', {{}});
        window.chart_{chart_widget.chart_id}.dispose();
        window.chart_{chart_widget.chart_id} = echarts.init(
            document.getElementById('{chart_widget.chart_id}'),
            '{theme}'
        );
        """
        chart_widget.page().runJavaScript(js_code)
```

---

## 八、性能优化

### 8.1 大数据量处理

```python
# 使用采样减少数据点
def sample_data(data, max_points=1000):
    """对数据进行采样"""
    if len(data) <= max_points:
        return data
    
    step = len(data) // max_points
    return data[::step]
```

### 8.2 延迟加载

```python
# 只在标签页显示时加载图表
def showEvent(self, event):
    super().showEvent(event)
    if not self.charts_loaded:
        self.refresh_stats()
        self.charts_loaded = True
```

---

## 九、故障排除

### 9.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 图表不显示 | HTML 加载失败 | 检查文件路径 |
| 图表显示空白 | 数据为空 | 检查数据源 |
| 图表卡顿 | 数据量过大 | 使用采样 |
| 交互不响应 | JavaScript 错误 | 检查浏览器控制台 |

### 9.2 调试技巧

```python
# 启用开发者工具
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineCore import QWebEngineSettings

view = QWebEngineView()
view.settings().setAttribute(
    QWebEngineSettings.WebAttribute.DeveloperExtrasEnabled,
    True
)
```

---

## 十、参考资源

### 10.1 官方文档
- ECharts 官网：https://echarts.apache.org/
- ECharts 示例：https://echarts.apache.org/examples/
- PyQt5 WebEngine：https://doc.qt.io/qt-5/qtwebengine-index.html

### 10.2 相关教程
- ECharts 快速开始：https://echarts.apache.org/handbook/zh/get-started/
- PyQt5 WebEngine 集成：https://www.riverbankcomputing.com/static/Docs/PyQt5/

### 10.3 示例代码
- 官方示例：https://github.com/apache/echarts/tree/master/examples
- PyQt5 示例：https://github.com/PyQt5/PyQt5
