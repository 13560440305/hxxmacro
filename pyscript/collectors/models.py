"""
宏观事件数据模型
对应数据库表: macro_events
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import uuid
import json


@dataclass
class MacroEvent:
    """
    宏观事件数据模型
    
    字段说明:
    - event_name: 事件名称 (必填)
    - country: 事件所在国家 (必填)
    - category: 事件类别 (必填)
    - event_date: 事件发生时间 (必填)
    - actual: 实际值
    - forecast: 预期值
    - previous: 前值
    - surprise: 惊喜值/意外值 (actual - forecast 或 actual - previous)
    - impact_valid: 影响是否有效 (默认False)
    - risk_bias: 风险偏好 ('Risk-On', 'Risk-Off', 'Neutral')
    - core_view: 核心观点 (可由AI生成)
    """
    event_name: str
    country: str
    category: str
    event_date: datetime
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    surprise: Optional[float] = None
    impact_valid: bool = False
    risk_bias: Optional[str] = None  # 'Risk-On', 'Risk-Off', 'Neutral'
    core_view: Optional[str] = None
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 额外字段（不存数据库，用于采集时记录）
    source: Optional[str] = None
    raw_data: Optional[dict] = None
    
    def __post_init__(self):
        """初始化后自动计算surprise"""
        if self.surprise is None and self.actual is not None:
            if self.forecast is not None:
                self.surprise = self.actual - self.forecast
            elif self.previous is not None:
                self.surprise = self.actual - self.previous
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime序列化
        data['event_date'] = self.event_date.isoformat() if self.event_date else None
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        return data
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def to_db_dict(self) -> dict:
        """转换为数据库格式（去除非数据库字段）"""
        data = self.to_dict()
        # 移除非数据库字段
        for key in ['source', 'raw_data']:
            data.pop(key, None)
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MacroEvent':
        """从字典创建实例"""
        # 处理datetime字段
        if isinstance(data.get('event_date'), str):
            data['event_date'] = datetime.fromisoformat(data['event_date'])
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)
    
    def validate(self) -> tuple[bool, str]:
        """验证数据完整性"""
        if not self.event_name:
            return False, "event_name is required"
        if not self.country:
            return False, "country is required"
        if not self.category:
            return False, "category is required"
        if not self.event_date:
            return False, "event_date is required"
        if self.risk_bias and self.risk_bias not in ('Risk-On', 'Risk-Off', 'Neutral'):
            return False, f"risk_bias must be one of: Risk-On, Risk-Off, Neutral, got {self.risk_bias}"
        return True, "OK"


# 事件类别枚举
class EventCategory:
    """事件类别"""
    ECONOMIC_CALENDAR = "economic_calendar"      # 经济日历事件
    CENTRAL_BANK = "central_bank"                # 央行政策
    GEOPOLITICAL = "geopolitical"                # 地缘政治
    MARKET_EVENT = "market_event"                # 金融市场事件
    NATURAL_DISASTER = "natural_disaster"        # 自然灾害
    POLICY_CHANGE = "policy_change"              # 政策变化
    EARNINGS = "earnings"                        # 财报事件
    TRADE_DATA = "trade_data"                    # 贸易数据


# 国家代码映射
COUNTRY_CODES = {
    "US": "美国",
    "CN": "中国",
    "EU": "欧盟",
    "UK": "英国",
    "JP": "日本",
    "DE": "德国",
    "FR": "法国",
    "IT": "意大利",
    "ES": "西班牙",
    "CA": "加拿大",
    "AU": "澳大利亚",
    "NZ": "新西兰",
    "CH": "瑞士",
    "SE": "瑞典",
    "NO": "挪威",
    "KR": "韩国",
    "IN": "印度",
    "BR": "巴西",
    "RU": "俄罗斯",
    "MX": "墨西哥",
    "ZA": "南非",
    "SG": "新加坡",
    "HK": "香港",
    "TW": "台湾",
}

# 反向映射
COUNTRY_NAMES = {v: k for k, v in COUNTRY_CODES.items()}
