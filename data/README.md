# 数据目录结构说明

## 目录分类

### 1. ai_tech/ - AI/科技新闻数据
- **来源**: Hacker News API、GitHub Trending等
- **格式**: JSON、Markdown、文本
- **更新频率**: 每2小时（建议）
- **示例文件**:
  - `tech_news.json` - 原始JSON数据
  - `ai_news_latest.md` - 最新AI新闻简报
  - `tech_news_latest.md` - 技术新闻详细版

### 2. finance_a_stock/ - A股市场数据
- **来源**: 东方财富API、新浪财经等
- **内容**: A股指数、个股数据、市场行情
- **示例文件**:
  - `a_stock_test_report_*.json` - A股API测试报告
  - `finance_data_*.json` - 财经数据抓取结果

### 3. finance_global/ - 全球财经数据
- **来源**: Yahoo Finance、Alpha Vantage等（待完善）
- **内容**: 美股、外汇、黄金、加密货币
- **状态**: 需API密钥（Alpha Vantage、Twelve Data）

### 4. gov_economy/ - 政府经济数据
- **来源**: 国家统计局、世界银行、IMF等
- **内容**: GDP、CPI、PPI、PMI等宏观经济指标
- **示例文件**:
  - `gov_stats_*.json` - 统计局数据
  - `worldbank_*.json` - 世界银行数据

### 5. temp/ - 临时文件
- 测试输出
- 中间处理文件
- 缓存数据

## 数据更新时间

| 类别 | 建议频率 | 上次更新 | 状态 |
|------|----------|----------|------|
| AI科技新闻 | 每2小时 | 2026-02-14 15:57 | ✅ 就绪 |
| A股市场数据 | 每天开盘期间 | 2026-02-14 17:04 | ✅ 就绪 |
| 政府经济数据 | 每月/季发布后 | 2026-02-14 17:17 | ✅ 就绪 |
| 全球财经数据 | 每4小时 | 待完善 | 🔧 需API密钥 |

## 脚本位置
所有抓取脚本位于：`/home/work/hxxworkspace/scripts/`

## 自动化
使用 `automation_orchestrator.py` 统一调度各类抓取任务。

## 使用说明
1. 查看最新数据：浏览对应类别目录
2. 手动运行抓取：执行对应脚本
3. 自动化部署：配置cron任务

---
*最后更新: 2026-02-14*