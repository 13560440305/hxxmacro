"""
经济日历事件采集器
采集: 非农、CPI、GDP、PMI、零售销售、工业生产等经济指标
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
import re
import requests
from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector
from collectors.models import MacroEvent, EventCategory, COUNTRY_CODES


class EconomicCalendarCollector(BaseCollector):
    """
    经济日历事件采集器
    
    数据源:
    - ForexFactory (forexfactory.com)
    - Investing.com
    - TradingEconomics
    - 东方财富网
    """
    
    # 重要经济指标配置
    INDICATORS = {
        # 美国指标
        "Non Farm Payrolls": {
            "keywords": ["非农", "NFP", "Non Farm", "Employment Change"],
            "country": "US",
            "importance": 3,
            "unit": "K"
        },
        "Unemployment Rate": {
            "keywords": ["失业率", "Unemployment Rate"],
            "country": "US",
            "importance": 3,
            "unit": "%"
        },
        "CPI": {
            "keywords": ["CPI", "消费者物价", "Consumer Price"],
            "country": "US",
            "importance": 3,
            "unit": "%"
        },
        "Core CPI": {
            "keywords": ["核心CPI", "Core CPI", "Core Consumer Price"],
            "country": "US",
            "importance": 3,
            "unit": "%"
        },
        "PCE": {
            "keywords": ["PCE", "个人消费支出"],
            "country": "US",
            "importance": 3,
            "unit": "%"
        },
        "GDP": {
            "keywords": ["GDP", "国内生产总值", "Gross Domestic"],
            "country": "US",
            "importance": 3,
            "unit": "%"
        },
        "PMI": {
            "keywords": ["PMI", "采购经理"],
            "country": "US",
            "importance": 2,
            "unit": ""
        },
        "ISM Manufacturing": {
            "keywords": ["ISM制造业", "ISM Manufacturing"],
            "country": "US",
            "importance": 2,
            "unit": ""
        },
        "ISM Services": {
            "keywords": ["ISM服务业", "ISM Services", "ISM Non-Manufacturing"],
            "country": "US",
            "importance": 2,
            "unit": ""
        },
        "Retail Sales": {
            "keywords": ["零售销售", "Retail Sales"],
            "country": "US",
            "importance": 2,
            "unit": "%"
        },
        "Industrial Production": {
            "keywords": ["工业生产", "Industrial Production"],
            "country": "US",
            "importance": 2,
            "unit": "%"
        },
        "Durable Goods": {
            "keywords": ["耐用品订单", "Durable Goods"],
            "country": "US",
            "importance": 2,
            "unit": "%"
        },
        "Initial Jobless Claims": {
            "keywords": ["初请失业金", "Jobless Claims", "Unemployment Claims"],
            "country": "US",
            "importance": 2,
            "unit": "K"
        },
        "ADP Employment": {
            "keywords": ["ADP就业", "ADP Employment"],
            "country": "US",
            "importance": 2,
            "unit": "K"
        },
        # 中国指标
        "China GDP": {
            "keywords": ["中国GDP", "China GDP"],
            "country": "CN",
            "importance": 3,
            "unit": "%"
        },
        "China CPI": {
            "keywords": ["中国CPI", "China CPI", "中国消费者物价"],
            "country": "CN",
            "importance": 2,
            "unit": "%"
        },
        "China PMI": {
            "keywords": ["中国PMI", "China PMI", "官方PMI"],
            "country": "CN",
            "importance": 2,
            "unit": ""
        },
        "China Trade Balance": {
            "keywords": ["中国贸易帐", "China Trade Balance"],
            "country": "CN",
            "importance": 2,
            "unit": "B"
        },
        # 欧盟指标
        "Eurozone CPI": {
            "keywords": ["欧元区CPI", "Eurozone CPI", "Euro Area CPI"],
            "country": "EU",
            "importance": 3,
            "unit": "%"
        },
        "Eurozone GDP": {
            "keywords": ["欧元区GDP", "Eurozone GDP"],
            "country": "EU",
            "importance": 3,
            "unit": "%"
        },
        "German ZEW": {
            "keywords": ["德国ZEW", "German ZEW"],
            "country": "DE",
            "importance": 2,
            "unit": ""
        },
        "German IFO": {
            "keywords": ["德国IFO", "German IFO"],
            "country": "DE",
            "importance": 2,
            "unit": ""
        },
        # 日本指标
        "Japan CPI": {
            "keywords": ["日本CPI", "Japan CPI", "Tokyo CPI"],
            "country": "JP",
            "importance": 2,
            "unit": "%"
        },
        "Japan GDP": {
            "keywords": ["日本GDP", "Japan GDP"],
            "country": "JP",
            "importance": 2,
            "unit": "%"
        },
        # 英国指标
        "UK CPI": {
            "keywords": ["英国CPI", "UK CPI", "British CPI"],
            "country": "UK",
            "importance": 2,
            "unit": "%"
        },
        "UK GDP": {
            "keywords": ["英国GDP", "UK GDP"],
            "country": "UK",
            "importance": 2,
            "unit": "%"
        },
    }
    
    def get_category(self) -> str:
        return EventCategory.ECONOMIC_CALENDAR
    
    def collect(self, start_date: Optional[datetime] = None,
                end_date: Optional[datetime] = None) -> List[MacroEvent]:
        """
        采集经济日历事件
        
        优先级:
        1. ForexFactory (英文数据，最准确)
        2. 东方财富 (中文数据)
        """
        events = []
        
        # 尝试多个数据源
        try:
            events.extend(self._collect_from_forexfactory(start_date, end_date))
        except Exception as e:
            self.logger.warning(f"ForexFactory collection failed: {e}")
        
        # 如果英文源失败，尝试中文源
        if not events:
            try:
                events.extend(self._collect_from_eastmoney(start_date, end_date))
            except Exception as e:
                self.logger.warning(f"Eastmoney collection failed: {e}")
        
        # 去重
        events = self._deduplicate_events(events)
        
        return events
    
    def _collect_from_forexfactory(self, start_date: datetime,
                                    end_date: datetime) -> List[MacroEvent]:
        """
        从ForexFactory采集数据
        """
        events = []
        
        # ForexFactory日期格式
        base_url = "https://www.forexfactory.com/calendar"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(base_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 解析表格行
            rows = soup.select('tr.calendar__row')
            
            for row in rows:
                event = self._parse_forexfactory_row(row)
                if event and start_date <= event.event_date <= end_date:
                    events.append(event)
                    
        except requests.RequestException as e:
            self.logger.error(f"Request to ForexFactory failed: {e}")
            raise
        
        return events
    
    def _parse_forexfactory_row(self, row) -> Optional[MacroEvent]:
        """解析ForexFactory表格行"""
        try:
            # 提取时间
            time_elem = row.select_one('.calendar__time')
            if not time_elem:
                return None
            time_str = time_elem.text.strip()
            
            # 提取事件名称
            name_elem = row.select_one('.calendar__event-title')
            if not name_elem:
                return None
            event_name = name_elem.text.strip()
            
            # 提取国家
            country_elem = row.select_one('.calendar__flag')
            country = "US"  # 默认美国
            if country_elem:
                flag_class = country_elem.get('class', [])
                for cls in flag_class:
                    if cls.startswith('flag-'):
                        country = cls.replace('flag-', '').upper()
                        break
            
            # 提取数值
            actual_elem = row.select_one('.calendar__actual')
            forecast_elem = row.select_one('.calendar__forecast')
            previous_elem = row.select_one('.calendar__previous')
            
            actual = self._parse_number(actual_elem.text if actual_elem else None)
            forecast = self._parse_number(forecast_elem.text if forecast_elem else None)
            previous = self._parse_number(previous_elem.text if previous_elem else None)
            
            # 重要性
            impact_elem = row.select_one('.calendar__impact')
            importance = 1
            if impact_elem:
                impact_class = impact_elem.get('class', [])
                if 'high' in impact_class:
                    importance = 3
                elif 'medium' in impact_class:
                    importance = 2
            
            # 只采集高重要性事件
            if importance < 2:
                return None
            
            # 创建事件
            event_date = self._parse_event_date(time_str)
            
            event = MacroEvent(
                event_name=event_name,
                country=COUNTRY_CODES.get(country, country),
                category=self.get_category(),
                event_date=event_date,
                actual=actual,
                forecast=forecast,
                previous=previous,
                source="ForexFactory"
            )
            
            # 推断风险偏好
            event.risk_bias = self.infer_risk_bias(event_name, event.surprise, actual, forecast)
            
            return event
            
        except Exception as e:
            self.logger.debug(f"Failed to parse row: {e}")
            return None
    
    def _collect_from_eastmoney(self, start_date: datetime,
                                 end_date: datetime) -> List[MacroEvent]:
        """
        从东方财富采集数据
        """
        events = []
        
        # 东方财富经济日历API
        # 注意: 这个URL可能需要调整
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        
        params = {
            "sortColumns": "REPORT_DATE",
            "sortTypes": "-1",
            "pageSize": 100,
            "pageNumber": 1,
            "reportName": "RPT_ECONOMIC_CALENDAR",
            "columns": "ALL",
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://data.eastmoney.com/'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('result') and data['result'].get('data'):
                for item in data['result']['data']:
                    event = self._parse_eastmoney_item(item)
                    if event and start_date <= event.event_date <= end_date:
                        events.append(event)
                        
        except Exception as e:
            self.logger.error(f"Eastmoney collection failed: {e}")
            raise
        
        return events
    
    def _parse_eastmoney_item(self, item: dict) -> Optional[MacroEvent]:
        """解析东方财富数据项"""
        try:
            event_name = item.get('INDICATOR_NAME', '')
            if not event_name:
                return None
            
            # 解析日期
            date_str = item.get('REPORT_DATE', '')
            if not date_str:
                return None
            event_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            
            country = item.get('COUNTRY', 'US')
            
            event = MacroEvent(
                event_name=event_name,
                country=COUNTRY_CODES.get(country, country),
                category=self.get_category(),
                event_date=event_date,
                actual=item.get('ACTUAL'),
                forecast=item.get('FORECAST'),
                previous=item.get('PREVIOUS'),
                source="Eastmoney"
            )
            
            event.risk_bias = self.infer_risk_bias(
                event_name, event.surprise, event.actual, event.forecast
            )
            
            return event
            
        except Exception as e:
            self.logger.debug(f"Failed to parse eastmoney item: {e}")
            return None
    
    def _parse_number(self, value: Optional[str]) -> Optional[float]:
        """解析数值字符串"""
        if not value or value in ['-', '', 'N/A', 'Tentative']:
            return None
        
        try:
            # 移除百分号、逗号等
            clean = value.replace('%', '').replace(',', '').replace('K', '').replace('M', '').strip()
            if not clean:
                return None
            
            num = float(clean)
            
            # 处理单位
            if 'K' in value:
                num *= 1000
            elif 'M' in value:
                num *= 1000000
            elif '%' in value:
                num = num  # 保持百分比形式
            
            return num
            
        except (ValueError, TypeError):
            return None
    
    def _parse_event_date(self, time_str: str) -> datetime:
        """解析事件时间"""
        # ForexFactory时间格式可能是 "Today 08:30", "Mar 15 08:30" 等
        today = datetime.now()
        
        try:
            if 'Today' in time_str:
                time_part = time_str.replace('Today', '').strip()
                hour, minute = map(int, time_part.split(':'))
                return today.replace(hour=hour, minute=minute, second=0, microsecond=0)
            elif 'Tomorrow' in time_str:
                time_part = time_str.replace('Tomorrow', '').strip()
                hour, minute = map(int, time_part.split(':'))
                tomorrow = today + timedelta(days=1)
                return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            else:
                # 尝试解析 "Mar 15 08:30" 格式
                dt = datetime.strptime(f"{today.year} {time_str}", '%Y %b %d %H:%M')
                return dt
        except:
            # 默认返回今天
            return today
    
    def _deduplicate_events(self, events: List[MacroEvent]) -> List[MacroEvent]:
        """去重"""
        seen = set()
        unique_events = []
        
        for event in events:
            # 使用事件名+国家+日期作为唯一标识
            key = (event.event_name, event.country, event.event_date.strftime('%Y-%m-%d'))
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        return unique_events


# 用于直接运行的入口
if __name__ == "__main__":
    import json
    
    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}
    
    collector = EconomicCalendarCollector(config)
    
    # 执行采集
    result = collector.run(
        output_dir=os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'macro_events')
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
