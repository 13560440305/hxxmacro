"""
宏观事件采集编排器
统一调度所有采集器，执行采集任务
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import os
import sys
import argparse

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import setup_logger
from collectors.base_collector import BaseCollector
from collectors.economic_calendar import EconomicCalendarCollector
from collectors.central_bank import CentralBankCollector
from collectors.geopolitical import GeopoliticalCollector
from collectors.market_events import MarketEventCollector
from collectors.models import MacroEvent


class CollectorOrchestrator:
    """
    采集器编排器
    
    功能:
    - 统一调度各类采集器
    - 汇总采集结果
    - 保存到文件
    - 可选: 直接写入数据库
    """
    
    def __init__(self, config: dict = None):
        """
        初始化编排器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.logger = setup_logger(
            "collector.orchestrator",
            self.config.get("logging", {})
        )
        
        # 初始化所有采集器
        self.collectors: Dict[str, BaseCollector] = {
            "economic_calendar": EconomicCalendarCollector(config),
            "central_bank": CentralBankCollector(config),
            "geopolitical": GeopoliticalCollector(config),
            "market_event": MarketEventCollector(config),
        }
        
        self.all_events: List[MacroEvent] = []
    
    def collect_all(self, start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        执行所有采集器的采集任务
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            categories: 指定要采集的类别列表，None表示全部
            
        Returns:
            采集结果汇总
        """
        # 默认时间范围
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=7)
        
        self.logger.info(f"Starting collection from {start_date} to {end_date}")
        
        results = {
            "start_time": datetime.now().isoformat(),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "collectors": {},
            "total_events": 0,
            "status": "running"
        }
        
        self.all_events = []
        
        # 执行各采集器
        for name, collector in self.collectors.items():
            # 跳过未指定的类别
            if categories and name not in categories:
                self.logger.info(f"Skipping collector: {name}")
                continue
            
            self.logger.info(f"Running collector: {name}")
            
            try:
                result = collector.run(
                    start_date=start_date,
                    end_date=end_date,
                    output_dir=None,  # 不单独保存
                    save_json=False,
                    save_markdown=False
                )
                
                results["collectors"][name] = {
                    "status": result.get("status"),
                    "valid": result.get("valid", 0),
                    "total": result.get("total", 0)
                }
                
                if result.get("status") == "success":
                    self.all_events.extend(result.get("events", []))
                    results["total_events"] += result.get("valid", 0)
                else:
                    results["collectors"][name]["error"] = result.get("error")
                    
            except Exception as e:
                self.logger.exception(f"Collector {name} failed: {e}")
                results["collectors"][name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        results["end_time"] = datetime.now().isoformat()
        results["status"] = "completed"
        
        self.logger.info(f"Collection completed: {results['total_events']} events")
        
        return results
    
    def save_all(self, output_dir: str,
                 save_json: bool = True,
                 save_markdown: bool = True,
                 save_by_category: bool = True) -> Dict[str, str]:
        """
        保存所有采集结果
        
        Args:
            output_dir: 输出目录
            save_json: 是否保存JSON
            save_markdown: 是否保存Markdown
            save_by_category: 是否按类别分别保存
            
        Returns:
            保存的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)
        saved_files = {}
        
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        
        # 保存汇总文件
        if save_json:
            # 按日期分组
            events_by_date = {}
            for event in self.all_events:
                date_key = event.event_date.strftime("%Y-%m-%d")
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append(event.to_dict())
            
            data = {
                "collected_at": datetime.now().isoformat(),
                "total_events": len(self.all_events),
                "events_by_date": events_by_date,
                "events": [e.to_dict() for e in self.all_events]
            }
            
            filepath = os.path.join(output_dir, f"macro_events_{date_str}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            saved_files["json"] = filepath
            self.logger.info(f"Saved JSON to {filepath}")
        
        if save_markdown:
            filepath = os.path.join(output_dir, f"macro_events_{date_str}.md")
            self._save_markdown(filepath)
            saved_files["markdown"] = filepath
            self.logger.info(f"Saved Markdown to {filepath}")
        
        # 按类别分别保存
        if save_by_category:
            events_by_category = {}
            for event in self.all_events:
                cat = event.category
                if cat not in events_by_category:
                    events_by_category[cat] = []
                events_by_category[cat].append(event)
            
            for cat, events in events_by_category.items():
                cat_dir = os.path.join(output_dir, cat)
                os.makedirs(cat_dir, exist_ok=True)
                
                # JSON
                if save_json:
                    cat_data = {
                        "category": cat,
                        "collected_at": datetime.now().isoformat(),
                        "count": len(events),
                        "events": [e.to_dict() for e in events]
                    }
                    cat_file = os.path.join(cat_dir, f"{cat}_{date_str}.json")
                    with open(cat_file, 'w', encoding='utf-8') as f:
                        json.dump(cat_data, f, ensure_ascii=False, indent=2)
                
                # Markdown
                if save_markdown:
                    cat_md = os.path.join(cat_dir, f"{cat}_{date_str}.md")
                    self._save_category_markdown(cat_md, cat, events)
        
        return saved_files
    
    def _save_markdown(self, filepath: str):
        """保存Markdown报告"""
        lines = [
            "# 宏观事件采集报告",
            "",
            f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"> 事件总数: {len(self.all_events)}",
            "",
            "---",
            ""
        ]
        
        # 按日期分组
        events_by_date = {}
        for event in self.all_events:
            date_key = event.event_date.strftime("%Y-%m-%d")
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append(event)
        
        # 按日期排序
        for date_key in sorted(events_by_date.keys()):
            events = events_by_date[date_key]
            lines.append(f"## {date_key}")
            lines.append("")
            
            for event in events:
                lines.append(f"### {event.event_name}")
                lines.append("")
                lines.append(f"- **国家**: {event.country}")
                lines.append(f"- **类别**: {event.category}")
                lines.append(f"- **时间**: {event.event_date.strftime('%H:%M')}")
                
                if event.actual is not None:
                    lines.append(f"- **实际值**: {event.actual}")
                if event.forecast is not None:
                    lines.append(f"- **预期值**: {event.forecast}")
                if event.previous is not None:
                    lines.append(f"- **前值**: {event.previous}")
                if event.surprise is not None:
                    lines.append(f"- **惊喜值**: {event.surprise}")
                if event.risk_bias:
                    lines.append(f"- **风险偏好**: {event.risk_bias}")
                if event.core_view:
                    lines.append(f"- **核心观点**: {event.core_view}")
                
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def _save_category_markdown(self, filepath: str, category: str, events: List[MacroEvent]):
        """保存类别Markdown报告"""
        category_names = {
            "economic_calendar": "经济日历",
            "central_bank": "央行政策",
            "geopolitical": "地缘政治",
            "market_event": "金融市场事件",
        }
        
        lines = [
            f"# {category_names.get(category, category)} 事件",
            "",
            f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"> 事件数量: {len(events)}",
            "",
            "---",
            ""
        ]
        
        for i, event in enumerate(events, 1):
            lines.append(f"## {i}. {event.event_name}")
            lines.append("")
            lines.append(f"- **国家**: {event.country}")
            lines.append(f"- **时间**: {event.event_date.strftime('%Y-%m-%d %H:%M')}")
            
            if event.actual is not None:
                lines.append(f"- **实际值**: {event.actual}")
            if event.forecast is not None:
                lines.append(f"- **预期值**: {event.forecast}")
            if event.previous is not None:
                lines.append(f"- **前值**: {event.previous}")
            if event.risk_bias:
                lines.append(f"- **风险偏好**: {event.risk_bias}")
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def get_events(self) -> List[MacroEvent]:
        """获取所有采集的事件"""
        return self.all_events
    
    def get_events_by_category(self, category: str) -> List[MacroEvent]:
        """获取指定类别的事件"""
        return [e for e in self.all_events if e.category == category]
    
    def get_events_by_country(self, country: str) -> List[MacroEvent]:
        """获取指定国家的事件"""
        return [e for e in self.all_events if e.country == country]
    
    def get_events_by_date(self, date: datetime) -> List[MacroEvent]:
        """获取指定日期的事件"""
        date_str = date.strftime("%Y-%m-%d")
        return [e for e in self.all_events if e.event_date.strftime("%Y-%m-%d") == date_str]


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="宏观事件采集器")
    parser.add_argument("--start-date", type=str, help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--categories", type=str, nargs="+", 
                        choices=["economic_calendar", "central_bank", "geopolitical", "market_event"],
                        help="指定采集的类别")
    parser.add_argument("--output-dir", type=str, 
                        default=os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'macro_events'),
                        help="输出目录")
    parser.add_argument("--no-json", action="store_true", help="不保存JSON")
    parser.add_argument("--no-md", action="store_true", help="不保存Markdown")
    parser.add_argument("--config", type=str, help="配置文件路径")
    
    args = parser.parse_args()
    
    # 加载配置
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        # 尝试默认配置路径
        default_config = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        if os.path.exists(default_config):
            with open(default_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
    
    # 解析日期
    start_date = None
    end_date = None
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    # 创建编排器并执行
    orchestrator = CollectorOrchestrator(config)
    
    # 采集
    results = orchestrator.collect_all(
        start_date=start_date,
        end_date=end_date,
        categories=args.categories
    )
    
    # 保存
    saved_files = orchestrator.save_all(
        output_dir=args.output_dir,
        save_json=not args.no_json,
        save_markdown=not args.no_md
    )
    
    # 输出结果
    output = {
        "collection_results": results,
        "saved_files": saved_files
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
