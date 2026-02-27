"""
地缘政治事件采集器
采集: 战争冲突、制裁、选举、贸易谈判、国际会议等
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
import requests
import re

from collectors.base_collector import BaseCollector
from collectors.models import MacroEvent, EventCategory, COUNTRY_CODES


class GeopoliticalCollector(BaseCollector):
    """
    地缘政治事件采集器
    
    事件类型:
    - 军事冲突
    - 国际制裁
    - 重要选举
    - 贸易谈判
    - 国际会议
    - 条约协定
    """
    
    # 地缘政治事件关键词
    GEOPOLITICAL_KEYWORDS = {
        "conflict": {
            "keywords": ["war", "conflict", "military", "invasion", "attack", "战争", "冲突", "军事"],
            "risk_bias": "Risk-Off"
        },
        "sanctions": {
            "keywords": ["sanction", "embargo", "ban", "制裁", "禁运", "禁止"],
            "risk_bias": "Risk-Off"
        },
        "election": {
            "keywords": ["election", "vote", "referendum", "选举", "投票", "公投"],
            "risk_bias": "Neutral"  # 取决于结果
        },
        "trade": {
            "keywords": ["trade deal", "tariff", "negotiation", "贸易协定", "关税", "谈判"],
            "risk_bias": "Neutral"
        },
        "summit": {
            "keywords": ["summit", "meeting", "conference", "峰会", "会议"],
            "risk_bias": "Neutral"
        },
        "treaty": {
            "keywords": ["treaty", "agreement", "accord", "协定", "条约"],
            "risk_bias": "Risk-On"  # 通常利好
        }
    }
    
    # 重要国家/地区代码
    REGIONS = {
        "US": "美国",
        "CN": "中国",
        "RU": "俄罗斯",
        "EU": "欧盟",
        "UK": "英国",
        "JP": "日本",
        "KR": "韩国",
        "KP": "朝鲜",
        "IR": "伊朗",
        "IL": "以色列",
        "TW": "台湾",
        "HK": "香港",
        "IN": "印度",
        "BR": "巴西",
        "UA": "乌克兰",
        "SY": "叙利亚",
        "AF": "阿富汗",
        "VE": "委内瑞拉",
    }
    
    def get_category(self) -> str:
        return EventCategory.GEOPOLITICAL
    
    def collect(self, start_date: Optional[datetime] = None,
                end_date: Optional[datetime] = None) -> List[MacroEvent]:
        """
        采集地缘政治事件
        
        数据源:
        1. 新闻API
        2. 预定义的重大事件日历
        """
        events = []
        
        # 采集新闻中的地缘政治事件
        events.extend(self._collect_from_news(start_date, end_date))
        
        # 采集预定义事件（选举、会议等）
        events.extend(self._collect_scheduled_events(start_date, end_date))
        
        return events
    
    def _collect_from_news(self, start_date: datetime,
                           end_date: datetime) -> List[MacroEvent]:
        """
        从新闻源采集地缘政治事件
        
        可用数据源:
        - NewsAPI (需要API Key)
        - GNews
        - Google News RSS
        """
        events = []
        
        # 使用Google News RSS作为免费数据源
        try:
            events.extend(self._collect_from_google_news(start_date, end_date))
        except Exception as e:
            self.logger.warning(f"Google News collection failed: {e}")
        
        return events
    
    def _collect_from_google_news(self, start_date: datetime,
                                   end_date: datetime) -> List[MacroEvent]:
        """从Google News RSS采集"""
        events = []
        
        # Google News RSS feeds for geopolitical topics
        rss_feeds = [
            "https://news.google.com/rss/search?q=geopolitics+war+conflict+sanctions&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=贸易战+地缘政治+制裁&hl=zh-CN&gl=CN&ceid=CN:zh",
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for feed_url in rss_feeds:
            try:
                response = requests.get(feed_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    # 解析RSS
                    events.extend(self._parse_rss_feed(response.text, start_date, end_date))
            except Exception as e:
                self.logger.warning(f"RSS feed {feed_url} failed: {e}")
        
        return events
    
    def _parse_rss_feed(self, rss_content: str,
                        start_date: datetime,
                        end_date: datetime) -> List[MacroEvent]:
        """解析RSS feed内容"""
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
                
                # 检查是否是地缘政治事件
                event_type = self._classify_event(title)
                if not event_type:
                    continue
                
                # 解析日期
                pub_date = None
                if pub_date_elem is not None:
                    try:
                        # RSS日期格式: Wed, 26 Feb 2026 10:30:00 GMT
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(pub_date_elem.text)
                    except:
                        continue
                
                if pub_date and not (start_date <= pub_date <= end_date):
                    continue
                
                # 推断涉及国家
                country = self._infer_country(title)
                
                event = MacroEvent(
                    event_name=title,
                    country=country,
                    category=self.get_category(),
                    event_date=pub_date or datetime.now(),
                    risk_bias=self.GEOPOLITICAL_KEYWORDS[event_type]["risk_bias"],
                    source="Google News",
                    raw_data={"title": title, "pub_date": str(pub_date)}
                )
                
                events.append(event)
                
        except Exception as e:
            self.logger.error(f"RSS parsing failed: {e}")
        
        return events
    
    def _classify_event(self, title: str) -> Optional[str]:
        """分类事件类型"""
        title_lower = title.lower()
        
        for event_type, config in self.GEOPOLITICAL_KEYWORDS.items():
            if any(kw in title_lower for kw in config["keywords"]):
                return event_type
        
        return None
    
    def _infer_country(self, title: str) -> str:
        """从标题推断涉及的国家"""
        title_lower = title.lower()
        
        # 检查国家名称
        for code, name in self.REGIONS.items():
            if name in title or code.lower() in title_lower:
                return name
        
        # 英文国家名
        country_names = {
            "america": "美国", "united states": "美国", "u.s.": "美国",
            "china": "中国", "chinese": "中国",
            "russia": "俄罗斯", "russian": "俄罗斯",
            "europe": "欧盟", "european": "欧盟",
            "japan": "日本", "japanese": "日本",
            "korea": "韩国", "korean": "韩国",
            "iran": "伊朗",
            "israel": "以色列",
            "taiwan": "台湾",
            "ukraine": "乌克兰",
            "uk": "英国", "britain": "英国",
        }
        
        for eng_name, cn_name in country_names.items():
            if eng_name in title_lower:
                return cn_name
        
        return "全球"
    
    def _collect_scheduled_events(self, start_date: datetime,
                                  end_date: datetime) -> List[MacroEvent]:
        """
        采集预定义的重大事件
        
        如: 重要选举、国际会议、条约签署等
        """
        events = []
        
        # 2026年预定义事件
        scheduled_events = [
            # 美国中期选举
            {
                "name": "美国中期选举",
                "country": "US",
                "date": datetime(2026, 11, 3),
                "risk_bias": "Neutral"
            },
            # G7峰会
            {
                "name": "G7峰会",
                "country": "全球",
                "date": datetime(2026, 6, 15),  # 示例日期
                "risk_bias": "Neutral"
            },
            # G20峰会
            {
                "name": "G20峰会",
                "country": "全球",
                "date": datetime(2026, 11, 15),  # 示例日期
                "risk_bias": "Neutral"
            },
            # APEC峰会
            {
                "name": "APEC峰会",
                "country": "全球",
                "date": datetime(2026, 11, 20),  # 示例日期
                "risk_bias": "Neutral"
            },
        ]
        
        for event_info in scheduled_events:
            if start_date <= event_info["date"] <= end_date:
                event = MacroEvent(
                    event_name=event_info["name"],
                    country=event_info["country"],
                    category=self.get_category(),
                    event_date=event_info["date"],
                    risk_bias=event_info.get("risk_bias", "Neutral"),
                    source="Scheduled"
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
    
    collector = GeopoliticalCollector(config)
    
    result = collector.run(
        output_dir=os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'macro_events')
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
