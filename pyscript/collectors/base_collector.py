"""
宏观事件采集器基类
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import setup_logger
from collectors.models import MacroEvent


class BaseCollector(ABC):
    """
    采集器基类
    
    子类需要实现:
    - collect(): 采集逻辑
    - get_category(): 返回事件类别
    """
    
    def __init__(self, config: dict = None):
        """
        初始化采集器
        
        Args:
            config: 配置字典，包含数据库、AI、日志等配置
        """
        self.config = config or {}
        self.logger = setup_logger(
            f"collector.{self.__class__.__name__.lower()}",
            self.config.get("logging", {})
        )
        self.events: List[MacroEvent] = []
        
    @abstractmethod
    def collect(self, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None) -> List[MacroEvent]:
        """
        采集事件
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            MacroEvent列表
        """
        pass
    
    @abstractmethod
    def get_category(self) -> str:
        """
        返回采集器处理的事件类别
        """
        pass
    
    def validate_event(self, event: MacroEvent) -> tuple[bool, str]:
        """
        验证事件数据
        
        Args:
            event: 待验证的事件
            
        Returns:
            (是否有效, 错误信息)
        """
        return event.validate()
    
    def save_to_json(self, events: List[MacroEvent], 
                     output_dir: str,
                     filename: Optional[str] = None) -> str:
        """
        保存事件到JSON文件
        
        Args:
            events: 事件列表
            output_dir: 输出目录
            filename: 文件名（不含扩展名）
            
        Returns:
            保存的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if not filename:
            date_str = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{self.get_category()}_{date_str}"
        
        filepath = os.path.join(output_dir, f"{filename}.json")
        
        data = {
            "category": self.get_category(),
            "collected_at": datetime.now().isoformat(),
            "count": len(events),
            "events": [e.to_dict() for e in events]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved {len(events)} events to {filepath}")
        return filepath
    
    def save_to_markdown(self, events: List[MacroEvent],
                         output_dir: str,
                         filename: Optional[str] = None) -> str:
        """
        保存事件到Markdown文件
        
        Args:
            events: 事件列表
            output_dir: 输出目录
            filename: 文件名（不含扩展名）
            
        Returns:
            保存的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if not filename:
            date_str = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{self.get_category()}_{date_str}"
        
        filepath = os.path.join(output_dir, f"{filename}.md")
        
        lines = [
            f"# {self.get_category_name()} 事件采集",
            "",
            f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"> 事件数量: {len(events)}",
            "",
            "---",
            ""
        ]
        
        for i, event in enumerate(events, 1):
            lines.extend([
                f"## {i}. {event.event_name}",
                "",
                f"| 字段 | 值 |",
                f"|------|-----|",
                f"| 国家 | {event.country} |",
                f"| 类别 | {event.category} |",
                f"| 时间 | {event.event_date.strftime('%Y-%m-%d %H:%M') if event.event_date else 'N/A'} |",
            ])
            
            if event.actual is not None:
                lines.append(f"| 实际值 | {event.actual} |")
            if event.forecast is not None:
                lines.append(f"| 预期值 | {event.forecast} |")
            if event.previous is not None:
                lines.append(f"| 前值 | {event.previous} |")
            if event.surprise is not None:
                lines.append(f"| 惊喜值 | {event.surprise} |")
            if event.risk_bias:
                lines.append(f"| 风险偏好 | {event.risk_bias} |")
            if event.core_view:
                lines.extend(["", f"**核心观点**: {event.core_view}"])
            
            lines.extend(["", "---", ""])
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        self.logger.info(f"Saved {len(events)} events to {filepath}")
        return filepath
    
    def get_category_name(self) -> str:
        """获取类别的中文名称"""
        category_names = {
            "economic_calendar": "经济日历",
            "central_bank": "央行政策",
            "geopolitical": "地缘政治",
            "market_event": "金融市场事件",
            "natural_disaster": "自然灾害",
            "policy_change": "政策变化",
            "earnings": "财报事件",
            "trade_data": "贸易数据",
        }
        return category_names.get(self.get_category(), self.get_category())
    
    def calculate_surprise(self, actual: Optional[float], 
                          forecast: Optional[float],
                          previous: Optional[float]) -> Optional[float]:
        """
        计算惊喜值
        
        优先使用 forecast，否则使用 previous
        
        Args:
            actual: 实际值
            forecast: 预期值
            previous: 前值
            
        Returns:
            惊喜值 (actual - baseline)
        """
        if actual is None:
            return None
        if forecast is not None:
            return actual - forecast
        if previous is not None:
            return actual - previous
        return None
    
    def infer_risk_bias(self, event_name: str, 
                        surprise: Optional[float] = None,
                        actual: Optional[float] = None,
                        forecast: Optional[float] = None) -> Optional[str]:
        """
        推断风险偏好
        
        Args:
            event_name: 事件名称
            surprise: 惊喜值
            actual: 实际值
            forecast: 预期值
            
        Returns:
            'Risk-On', 'Risk-Off', 或 'Neutral'
        """
        # 简单的规则推断，子类可以覆盖
        if surprise is None:
            return None
        
        # 根据事件类型和惊喜值方向判断
        event_lower = event_name.lower()
        
        # 利率事件
        if any(k in event_lower for k in ['利率', 'rate', 'interest']):
            if surprise > 0:  # 利率高于预期
                return 'Risk-Off'  # 通常不利于风险资产
            elif surprise < 0:
                return 'Risk-On'
        
        # 就业数据
        if any(k in event_lower for k in ['就业', '非农', 'employment', 'nfp', 'payroll']):
            if surprise > 0:  # 就业好于预期
                return 'Risk-On'  # 经济好
            elif surprise < 0:
                return 'Risk-Off'
        
        # CPI/通胀
        if any(k in event_lower for k in ['cpi', '通胀', 'inflation', 'pce']):
            if surprise > 0:  # 通胀高于预期
                return 'Risk-Off'  # 可能加息
            elif surprise < 0:
                return 'Risk-On'
        
        # GDP
        if any(k in event_lower for k in ['gdp', '国内生产']):
            if surprise > 0:
                return 'Risk-On'
            elif surprise < 0:
                return 'Risk-Off'
        
        return 'Neutral'
    
    def run(self, start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            output_dir: Optional[str] = None,
            save_json: bool = True,
            save_markdown: bool = True) -> Dict[str, Any]:
        """
        执行采集任务
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            output_dir: 输出目录
            save_json: 是否保存JSON
            save_markdown: 是否保存Markdown
            
        Returns:
            执行结果
        """
        self.logger.info(f"Starting collection for {self.get_category()}")
        
        # 默认时间范围：今天到未来7天
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=7)
        
        # 执行采集
        try:
            events = self.collect(start_date, end_date)
            self.events = events
            
            # 验证事件
            valid_events = []
            for event in events:
                is_valid, msg = self.validate_event(event)
                if is_valid:
                    valid_events.append(event)
                else:
                    self.logger.warning(f"Invalid event: {msg}")
            
            self.logger.info(f"Collected {len(valid_events)} valid events out of {len(events)}")
            
            result = {
                "status": "success",
                "category": self.get_category(),
                "total": len(events),
                "valid": len(valid_events),
                "events": valid_events
            }
            
            # 保存文件
            if output_dir:
                if save_json:
                    json_path = self.save_to_json(valid_events, output_dir)
                    result["json_path"] = json_path
                if save_markdown:
                    md_path = self.save_to_markdown(valid_events, output_dir)
                    result["markdown_path"] = md_path
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Collection failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "category": self.get_category()
            }
