"""
金融市场事件采集器
采集: 重大市场事件、熔断、黑天鹅事件等
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
import requests

from collectors.base_collector import BaseCollector
from collectors.models import MacroEvent, EventCategory, COUNTRY_CODES


class MarketEventCollector(BaseCollector):
    """
    金融市场事件采集器
    
    事件类型:
    - 市场熔断
    - 黑天鹅事件
    - 重大金融机构事件
    - 信用评级变化
    - 大规模并购
    - IPO事件
    """
    
    # 市场事件关键词
    MARKET_EVENT_TYPES = {
        "circuit_breaker": {
            "keywords": ["circuit breaker", "熔断", "halt", "suspended"],
            "risk_bias": "Risk-Off"
        },
        "black_swan": {
            "keywords": ["crash", "plunge", "collapse", "暴跌", "崩盘", "危机"],
            "risk_bias": "Risk-Off"
        },
        "bankruptcy": {
            "keywords": ["bankruptcy", "default", "破产", "违约", "倒闭"],
            "risk_bias": "Risk-Off"
        },
        "rating": {
            "keywords": ["downgrade", "upgrade", "rating", "评级", "下调", "上调"],
            "risk_bias": "Neutral"
        },
        "merger": {
            "keywords": ["merger", "acquisition", "M&A", "并购", "收购"],
            "risk_bias": "Neutral"
        },
        "ipo": {
            "keywords": ["IPO", "public offering", "上市", "公开发行"],
            "risk_bias": "Neutral"
        }
    }
    
    # 重大市场事件历史记录
    HISTORICAL_EVENTS = [
        # 2020年熔断事件
        {
            "name": "美股熔断",
            "country": "US",
            "date": datetime(2020, 3, 9),
            "risk_bias": "Risk-Off",
            "description": "道指暴跌触发熔断"
        },
        {
            "name": "美股熔断",
            "country": "US",
            "date": datetime(2020, 3, 12),
            "risk_bias": "Risk-Off",
            "description": "道指暴跌触发熔断"
        },
        {
            "name": "美股熔断",
            "country": "US",
            "date": datetime(2020, 3, 16),
            "risk_bias": "Risk-Off",
            "description": "道指暴跌触发熔断"
        },
        {
            "name": "美股熔断",
            "country": "US",
            "date": datetime(2020, 3, 18),
            "risk_bias": "Risk-Off",
            "description": "道指暴跌触发熔断"
        },
        # 硅谷银行事件
        {
            "name": "硅谷银行倒闭",
            "country": "US",
            "date": datetime(2023, 3, 10),
            "risk_bias": "Risk-Off",
            "description": "硅谷银行被监管机构关闭"
        },
        # 瑞士信贷事件
        {
            "name": "瑞士信贷被收购",
            "country": "CH",
            "date": datetime(2023, 3, 19),
            "risk_bias": "Risk-Off",
            "description": "瑞银集团收购瑞士信贷"
        },
    ]
    
    def get_category(self) -> str:
        return EventCategory.MARKET_EVENT
    
    def collect(self, start_date: Optional[datetime] = None,
                end_date: Optional[datetime] = None) -> List[MacroEvent]:
        """
        采集市场事件
        """
        events = []
        
        # 从新闻采集实时市场事件
        events.extend(self._collect_from_news(start_date, end_date))
        
        # 从历史记录中获取
        events.extend(self._collect_historical(start_date, end_date))
        
        return events
    
    def _collect_from_news(self, start_date: datetime,
                           end_date: datetime) -> List[MacroEvent]:
        """从新闻源采集市场事件"""
        events = []
        
        # 使用Google News RSS
        rss_feeds = [
            "https://news.google.com/rss/search?q=market+crash+circuit+breaker+bankruptcy&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=股市暴跌+熔断+破产+违约&hl=zh-CN&gl=CN&ceid=CN:zh",
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for feed_url in rss_feeds:
            try:
                response = requests.get(feed_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    events.extend(self._parse_rss_feed(response.text, start_date, end_date))
            except Exception as e:
                self.logger.warning(f"RSS feed failed: {e}")
        
        return events
    
    def _parse_rss_feed(self, rss_content: str,
                        start_date: datetime,
                        end_date: datetime) -> List[MacroEvent]:
        """解析RSS feed"""
        events = []
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(rss_content)
            
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                pub_date_elem = item.find('pubDate')
                
                if title_elem is None:
                    continue
                
                title = title_elem.text
                
                # 分类事件
                event_type = self._classify_event(title)
                if not event_type:
                    continue
                
                # 解析日期
                pub_date = None
                if pub_date_elem is not None:
                    try:
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(pub_date_elem.text)
                    except:
                        continue
                
                if pub_date and not (start_date <= pub_date <= end_date):
                    continue
                
                country = self._infer_country(title)
                
                event = MacroEvent(
                    event_name=title,
                    country=country,
                    category=self.get_category(),
                    event_date=pub_date or datetime.now(),
                    risk_bias=self.MARKET_EVENT_TYPES[event_type]["risk_bias"],
                    source="Google News",
                    raw_data={"title": title, "event_type": event_type}
                )
                
                events.append(event)
                
        except Exception as e:
            self.logger.error(f"RSS parsing failed: {e}")
        
        return events
    
    def _classify_event(self, title: str) -> Optional[str]:
        """分类市场事件"""
        title_lower = title.lower()
        
        for event_type, config in self.MARKET_EVENT_TYPES.items():
            if any(kw in title_lower for kw in config["keywords"]):
                return event_type
        
        return None
    
    def _infer_country(self, title: str) -> str:
        """推断事件涉及国家"""
        title_lower = title.lower()
        
        # 市场名称映射
        markets = {
            "wall street": "US", "dow": "US", "nasdaq": "US", "s&p": "US", "美股": "US",
            "a股": "CN", "上证": "CN", "深证": "CN", "中国股市": "CN",
            "ftse": "UK", "英股": "UK",
            "nikkei": "JP", "日股": "JP",
            "dax": "DE", "德股": "DE",
            "hang seng": "HK", "恒生": "HK", "港股": "HK",
        }
        
        for market, country in markets.items():
            if market in title_lower:
                return country
        
        return "全球"
    
    def _collect_historical(self, start_date: datetime,
                           end_date: datetime) -> List[MacroEvent]:
        """从历史记录获取事件"""
        events = []
        
        for event_info in self.HISTORICAL_EVENTS:
            if start_date <= event_info["date"] <= end_date:
                event = MacroEvent(
                    event_name=event_info["name"],
                    country=event_info["country"],
                    category=self.get_category(),
                    event_date=event_info["date"],
                    risk_bias=event_info.get("risk_bias", "Risk-Off"),
                    core_view=event_info.get("description"),
                    source="Historical"
                )
                events.append(event)
        
        return events


if __name__ == "__main__":
    import json
    import os
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}
    
    collector = MarketEventCollector(config)
    
    result = collector.run(
        output_dir=os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'macro_events')
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
