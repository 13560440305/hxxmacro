# hxxmacro

macro notion

## 目录结构
- `links/` – 分类数据源链接文件
- `scripts/` – 可复用的抓取脚本

## 数据源分类（links/）
1. **ai_tech_sources.txt** – AI与科技新闻/数据源
2. **finance_sources.txt** – 股票、指数、宏观财经数据源
3. **investment_gold_forex.txt** – 投资理财、黄金、贵金属、外汇数据源
4. **government_economic_data.txt** – 国家经济贸易数据（中/国际）

## 脚本（scripts/）
1. **tech_news_scraper.py** – 抓取科技新闻（RSS/API示例）
2. **finance_data_scraper.py** – 抓取财经数据（股票、汇率、黄金示例）

## 使用说明
- 所有数据源均为公开或需API密钥（标注）。
- 脚本为示例框架，实际使用时需根据目标网站结构调整解析逻辑。
- 可自由组合脚本，实现自动化数据流水线。

## 后续扩展
- 添加配置文件（API密钥管理）。
- 增加错误处理与重试机制。
- 封装为模块化函数库。

更新日期：2026-02-14
