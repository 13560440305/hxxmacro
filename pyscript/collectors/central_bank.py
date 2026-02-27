"""
央行政策事件采集器
采集: 利率决议、货币政策声明、央行讲话、量化宽松等
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
import requests
from bs4 import BeautifulSoup
import re

from collectors.base_collector import BaseCollector
from collectors.models import MacroEvent, EventCategory, COUNTRY_CODES


class CentralBankCollector(BaseCollector):
    """
    央行政策事件采集器
    
    覆盖央行:
    - 美联储 (Fed)
    - 欧洲央行 (ECB)
    - 日本央行 (BOJ)
    - 英国央行 (BOE)
    - 中国人民银行 (PBOC)
    - 瑞士央行 (SNB)
    - 加拿大央行 (BOC)
    - 澳大利亚央行 (RBA)
    - 新西兰央行 (RBNZ)
    """
    
    # 央行配置
    CENTRAL_BANKS = {
        "Fed": {
            "name": "美联储",
            "country": "US",
            "rate_name": "Federal Funds Rate",
            "meeting_cycle": 6,  # 每年8次，约每6周
            "keywords": ["FOMC", "Federal Reserve", "Fed", "美联储", "联邦基金利率"]
        },
        "ECB": {
            "name": "欧洲央行",
            "country": "EU",
            "rate_name": "Main Refinancing Rate",
            "meeting_cycle": 6,
            "keywords": ["ECB", "European Central Bank", "欧洲央行", "欧元区利率"]
        },
        "BOJ": {
            "name": "日本央行",
            "country": "JP",
            "rate_name": "Policy Rate",
            "meeting_cycle": 6,
            "keywords": ["BOJ", "Bank of Japan", "日本央行", "日银"]
        },
        "BOE": {
            "name": "英国央行",
            "country": "UK",
            "rate_name": "Bank Rate",
            "meeting_cycle": 6,
            "keywords": ["BOE", "Bank of England", "英国央行", "英银"]
        },
        "PBOC": {
            "name": "中国人民银行",
            "country": "CN",
            "rate_name": "Loan Prime Rate (LPR)",
            "meeting_cycle": 30,  # 每月20日
            "keywords": ["PBOC", "People's Bank", "中国央行", "人民银行", "LPR", "MLF"]
        },
        "SNB": {
            "name": "瑞士央行",
            "country": "CH",
            "rate_name": "Policy Rate",
            "meeting_cycle": 90,
            "keywords": ["SNB", "Swiss National Bank", "瑞士央行"]
        },
        "BOC": {
            "name": "加拿大央行",
            "country": "CA",
            "rate_name": "Overnight Rate",
            "meeting_cycle": 45,
            "keywords": ["BOC", "Bank of Canada", "加拿大央行"]
        },
        "RBA": {
            "name": "澳大利亚央行",
            "country": "AU",
            "rate_name": "Cash Rate",
            "meeting_cycle": 30,
            "keywords": ["RBA", "Reserve Bank of Australia", "澳洲联储", "澳联储"]
        },
        "RBNZ": {
            "name": "新西兰央行",
            "country": "NZ",
            "rate_name": "Official Cash Rate",
            "meeting_cycle": 45,
            "keywords": ["RBNZ", "Reserve Bank of New Zealand", "新西兰央行", "纽联储"]
        }
    }
    
    def get_category(self) -> str:
        return EventCategory.CENTRAL_BANK
    
    def collect(self, start_date: Optional[datetime] = None,
                end_date: Optional[datetime] = None) -> List[MacroEvent]:
        """
        采集央行政策事件
        """
        events = []
        
        # 采集利率决议
        events.extend(self._collect_rate_decisions(start_date, end_date))
        
        # 采集央行讲话
        events.extend(self._collect_speeches(start_date, end_date))
        
        # 采集货币政策纪要
        events.extend(self._collect_minutes(start_date, end_date))
        
        return events
    
    def _collect_rate_decisions(self, start_date: datetime,
                                 end_date: datetime) -> List[MacroEvent]:
        """采集利率决议事件"""
        events = []
        
        # 从ForexFactory获取利率决议
        try:
            events.extend(self._collect_from_forexfactory(start_date, end_date, "rate"))
        except Exception as e:
            self.logger.warning(f"Rate decision collection failed: {e}")
        
        # 补充中国央行数据
        try:
            events.extend(self._collect_pboc_rates(start_date, end_date))
        except Exception as e:
            self.logger.warning(f"PBOC rate collection failed: {e}")
        
        return events
    
    def _collect_speeches(self, start_date: datetime,
                          end_date: datetime) -> List[MacroEvent]:
        """采集央行官员讲话"""
        events = []
        
        # 重要央行官员讲话
        key_speakers = [
            {"name": "Jerome Powell", "role": "Fed Chair", "country": "US"},
            {"name": "Christine Lagarde", "role": "ECB President", "country": "EU"},
            {"name": "Kazuo Ueda", "role": "BOJ Governor", "country": "JP"},
            {"name": "Andrew Bailey", "role": "BOE Governor", "country": "UK"},
            {"name": "Pan Gongsheng", "role": "PBOC Governor", "country": "CN"},
        ]
        
        # 这里可以通过爬取财经日历获取讲话时间
        # 目前返回空列表，等待具体实现
        return events
    
    def _collect_minutes(self, start_date: datetime,
                         end_date: datetime) -> List[MacroEvent]:
        """采集货币政策会议纪要"""
        events = []
        
        # 各央行会议纪要发布时间
        # FOMC纪要通常在会议后3周发布
        # ECB纪要通常在会议后1周发布
        
        # 目前返回空列表，等待具体实现
        return events
    
    def _collect_from_forexfactory(self, start_date: datetime,
                                    end_date: datetime,
                                    event_type: str) -> List[MacroEvent]:
        """从ForexFactory采集央行事件"""
        events = []
        
        base_url = "https://www.forexfactory.com/calendar"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(base_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            rows = soup.select('tr.calendar__row')
            
            for row in rows:
                event = self._parse_rate_row(row)
                if event and start_date <= event.event_date <= end_date:
                    events.append(event)
                    
        except Exception as e:
            self.logger.error(f"ForexFactory request failed: {e}")
            raise
        
        return events
    
    def _parse_rate_row(self, row) -> Optional[MacroEvent]:
        """解析利率决议行"""
        try:
            name_elem = row.select_one('.calendar__event-title')
            if not name_elem:
                return None
            
            event_name = name_elem.text.strip()
            
            # 检查是否是央行利率事件
            matched_bank = None
            for bank_code, bank_info in self.CENTRAL_BANKS.items():
                if any(kw.lower() in event_name.lower() for kw in bank_info['keywords']):
                    matched_bank = bank_info
                    break
            
            if not matched_bank:
                return None
            
            # 提取时间
            time_elem = row.select_one('.calendar__time')
            if not time_elem:
                return None
            event_date = self._parse_time(time_elem.text.strip())
            
            # 提取数值
            actual = self._parse_rate(row.select_one('.calendar__actual'))
            forecast = self._parse_rate(row.select_one('.calendar__forecast'))
            previous = self._parse_rate(row.select_one('.calendar__previous'))
            
            event = MacroEvent(
                event_name=f"{matched_bank['name']}利率决议",
                country=matched_bank['country'],
                category=self.get_category(),
                event_date=event_date,
                actual=actual,
                forecast=forecast,
                previous=previous,
                source="ForexFactory"
            )
            
            # 利率决议的风险偏好判断
            event.risk_bias = self._infer_rate_bias(event)
            
            return event
            
        except Exception as e:
            self.logger.debug(f"Failed to parse rate row: {e}")
            return None
    
    def _collect_pboc_rates(self, start_date: datetime,
                            end_date: datetime) -> List[MacroEvent]:
        """
        采集中国央行利率数据
        
        LPR发布日: 每月20日（遇节假日顺延）
        MLF操作: 不定期
        """
        events = []
        
        # 计算时间范围内的LPR发布日期
        current = start_date
        while current <= end_date:
            # 每月20日
            lpr_date = current.replace(day=20)
            if start_date <= lpr_date <= end_date:
                # 跳过周末
                if lpr_date.weekday() < 5:
                    event = MacroEvent(
                        event_name="中国LPR利率",
                        country="CN",
                        category=self.get_category(),
                        event_date=lpr_date.replace(hour=9, minute=30),
                        source="Scheduled"
                    )
                    events.append(event)
            
            current += timedelta(days=1)
        
        return events
    
    def _parse_rate(self, elem) -> Optional[float]:
        """解析利率值"""
        if not elem:
            return None
        
        text = elem.text.strip()
        if not text or text == '-':
            return None
        
        try:
            # 利率通常是百分比形式，如 5.25%
            clean = text.replace('%', '').strip()
            return float(clean)
        except ValueError:
            return None
    
    def _parse_time(self, time_str: str) -> datetime:
        """解析时间"""
        today = datetime.now()
        
        try:
            if 'Today' in time_str:
                time_part = time_str.replace('Today', '').strip()
                if ':' in time_part:
                    hour, minute = map(int, time_part.split(':'))
                    return today.replace(hour=hour, minute=minute, second=0)
            elif ':' in time_str:
                # 尝试解析日期时间
                parts = time_str.split()
                if len(parts) >= 2:
                    dt = datetime.strptime(f"{today.year} {time_str}", '%Y %b %d %H:%M')
                    return dt
        except:
            pass
        
        return today
    
    def _infer_rate_bias(self, event: MacroEvent) -> str:
        """
        推断利率决议的风险偏好
        
        加息超预期 -> Risk-Off (紧缩)
        降息超预期 -> Risk-On (宽松)
        符合预期 -> Neutral
        """
        if event.surprise is None:
            return 'Neutral'
        
        if event.surprise > 0:
            # 加息超预期
            return 'Risk-Off'
        elif event.surprise < 0:
            # 降息超预期或加息不及预期
            return 'Risk-On'
        
        return 'Neutral'


if __name__ == "__main__":
    import json
    import os
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}
    
    collector = CentralBankCollector(config)
    
    result = collector.run(
        output_dir=os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'macro_events')
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
