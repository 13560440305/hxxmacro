# Notion 同步模块

**当前仅保留 cross_market_reactions 同步**：不单独全表同步 macro_events，避免重复。  
对每条 `sync_status='pending'` 的反应记录，用其 `event_id` 查询 macro_events（**仅 process_status='done'**），在 Notion 中创建/更新对应事件，再写入反应并标记 `sync_status='done'`。

同步相关日志统一写入 **logs/sync** 子目录（在 config.json 的 `logging.sync_dir` 可配置，默认 `"sync"`），便于与其它业务日志区分。

## 配置 (config.json)

在项目根目录的 `config.json` 中增加 `notion` 段：

- **api_token**: Notion Integration Token（在 https://www.notion.so/my-integrations 创建 Integration 后获得，不是账号密码）
- **databases.macro_events**: Notion 中「Macro_Events」数据库的 ID
- **databases.cross_market_reactions**: Notion 中「Cross_Market_Reactions」数据库的 ID
- **property_names**（可选）：若 Notion 里“存数据库主键”的列名不是 `DB_Id`，可配置为与 Notion 完全一致的列名，例如：
  - `"property_names": { "macro_events_db_id": "ID" }`（Macro_Events 中主键列叫 "ID" 时）

数据库 ID 获取方式：在 Notion 中打开对应数据库，浏览器地址栏中 `?v=` 前的 32 位字符串即为 database_id（有时带 `-`，需完整复制）。

## Notion 数据库属性（与代码映射）

### Macro_Events

字段列表：`Event, Date, Country, Category, Actual, Forecast, Previous, Surprise, Direction, AI_Summary, Raw_Note, Linked_Reactions, Expected_Impact, DB_Id`

同步时会写入：**DB_Id**（主键）、**Event**（Title）、**Date**、**Country**、**Category**、**Actual**、**Forecast**、**Previous**、**Surprise**、**Direction**（来自 risk_bias）、**AI_Summary**、**Raw_Note**（来自 core_view）。Linked_Reactions、Expected_Impact 无数据不写。

### Cross_Market_Reactions

字段列表：`Record, AI_Interpretation, Asset, Asset_Class, Date, Driver_Event, Historical_Similarity, Market_Tone, Move, Volatility, Direction, Magnitude, Reaction_Window, Reaction_Note`

同步时会写入：**Record**（Title，用 Asset 或 id）、**Driver_Event**（event_id）、**Asset**、**Direction**、**Magnitude**、**Reaction_Note**（reason）。其余列无数据不写。

## 运行方式

在 `pyscript` 目录下执行总控脚本（当前仅注册 cross_market_reactions 同步）：

```bash
cd pyscript
python sync_notion.py
```

单独执行 cross_market_reactions 同步：

```bash
cd pyscript
python -m sync.sync_cross_market_reactions
```

## 新增同步任务

1. 在 `sync` 目录下新建 `sync_<表名>.py`，实现 `run(db_config, notion_config, log_config=None)` 函数。
2. 在 `sync_notion.py` 中：`from sync.sync_<表名> import run as sync_<表名>`，并把 `("<表名>", sync_<表名>)` 加入 `SYNC_TASKS` 列表。
