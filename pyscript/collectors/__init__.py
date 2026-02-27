"""
宏观事件采集器模块

模块结构:
- models: 数据模型定义
- base_collector: 采集器基类
- economic_calendar: 经济日历事件采集器
- central_bank: 央行政策事件采集器
- geopolitical: 地缘政治事件采集器
- market_events: 金融市场事件采集器
- orchestrator: 采集编排器
"""

from collectors.models import MacroEvent, EventCategory, COUNTRY_CODES, COUNTRY_NAMES
from collectors.base_collector import BaseCollector
from collectors.economic_calendar import EconomicCalendarCollector
from collectors.central_bank import CentralBankCollector
from collectors.geopolitical import GeopoliticalCollector
from collectors.market_events import MarketEventCollector
from collectors.orchestrator import CollectorOrchestrator

__all__ = [
    # 数据模型
    "MacroEvent",
    "EventCategory",
    "COUNTRY_CODES",
    "COUNTRY_NAMES",
    # 采集器
    "BaseCollector",
    "EconomicCalendarCollector",
    "CentralBankCollector",
    "GeopoliticalCollector",
    "MarketEventCollector",
    # 编排器
    "CollectorOrchestrator",
]

__version__ = "1.0.0"
