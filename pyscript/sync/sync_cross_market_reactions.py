"""
将 cross_market_reactions 表中 sync_status='pending' 的数据同步到 Notion。
对每条 pending 记录：按 event_id 查询 macro_events（仅 process_status='done'），
在 Notion 中创建/更新对应事件，再写入反应并标记 sync_status='done'。不单独全表同步 macro_events，避免重复。
"""
import os
import json
import logging
from decimal import Decimal

import psycopg2
from notion_client import Client

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "..", "config.json")

logger = logging.getLogger("sync_cross_market_reactions")


def _notion_props_from_macro_row(row, db_id_prop="DB_Id"):
    """将 macro_events 一行转为 Notion Macro_Events 的 properties。db_id_prop 为 Notion 中用于存主键的属性名。"""
    (
        id_,
        event,
        country,
        category,
        event_date,
        actual,
        forecast,
        previous,
        surprise,
        impact_valid,
        risk_bias,
        core_view,
        created_at,
        updated_at,
        process_status,
        ai_summary,
    ) = row

    def num(v):
        if v is None:
            return None
        if isinstance(v, Decimal):
            return float(v)
        return v

    def text(v):
        if v is None:
            return ""
        return str(v).strip()

    # 与 Notion Macro_Events 字段一致；Country、Category 在 Notion 中为 Select
    props = {
        db_id_prop: {"rich_text": [{"text": {"content": str(id_)}}]},
        "Event": {"title": [{"text": {"content": text(event) or "(无)"}}]},
        "Country": {"select": {"name": text(country) or "—"}},
        "Category": {"select": {"name": text(category) or "—"}},
    }
    if event_date:
        props["Date"] = {
            "date": {"start": event_date.isoformat() if hasattr(event_date, "isoformat") else str(event_date)}
        }
    if actual is not None:
        props["Actual"] = {"number": num(actual)}
    if forecast is not None:
        props["Forecast"] = {"number": num(forecast)}
    if previous is not None:
        props["Previous"] = {"number": num(previous)}
    if surprise is not None:
        props["Surprise"] = {"number": num(surprise)}
    if risk_bias:
        props["Direction"] = {"select": {"name": text(risk_bias)}}
    if core_view:
        props["Raw_Note"] = {"rich_text": [{"text": {"content": text(core_view)[:2000]}}]}
    if ai_summary:
        props["AI_Summary"] = {"rich_text": [{"text": {"content": text(ai_summary)[:2000]}}]}
    return props


def _get_data_source_id(client, database_id):
    """从 database_id 解析出 data_source_id（Notion API 2025-09-03 起查询需用 data_sources）。"""
    try:
        db = client.databases.retrieve(database_id)
    except Exception as e:
        err_msg = str(e).lower()
        if "404" in err_msg or "not find database" in err_msg or "not found" in err_msg:
            raise ValueError(
                f"无法访问数据库 {database_id}（404）。请确认：\n"
                "1. 在 Notion 中打开该数据库页面，点击右上角「···」→「添加连接」/「Connections」→ 选择你的 Integration；\n"
                "2. 配置中的 database_id 与浏览器地址栏中「?」前的那段 ID 一致。"
            ) from e
        raise
    data_sources = db.get("data_sources") or []
    if not data_sources:
        raise ValueError(f"数据库 {database_id} 未返回 data_sources，请确认 Notion Integration 与 API 版本")
    return data_sources[0]["id"]


def _ensure_macro_event_in_notion(client, macro_events_data_source_id, macro_row, db_id_prop="DB_Id"):
    """确保一条 macro_events 在 Notion Macro_Events 中存在：按 db_id_prop 查询，有则更新，无则创建。返回该条在 Notion 中的 page_id（用于 Relation）。"""
    id_val = macro_row[0]
    resp = client.data_sources.query(
        macro_events_data_source_id,
        filter={"property": db_id_prop, "rich_text": {"equals": str(id_val)}},
        page_size=1,
    )
    existing = resp.get("results")
    props = _notion_props_from_macro_row(macro_row, db_id_prop=db_id_prop)
    if existing:
        page_id = existing[0]["id"]
        client.pages.update(page_id=page_id, properties=props)
        return page_id
    created = client.pages.create(parent={"data_source_id": macro_events_data_source_id}, properties=props)
    return created["id"]


def _load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _notion_props_from_reaction_row(row, driver_event_page_id=None):
    """将 cross_market_reactions 一行转为 Notion Cross_Market_Reactions 的 properties。
    - Driver_Event: Relation 类型，关联到 Macro_Events，来源与 Macro_Events.Event 对应（通过 page_id 关联后 Notion 会显示该事件的 Event 值）。
    - Asset: Select 类型。
    driver_event_page_id: 该条反应所对应 Macro_Events 行在 Notion 中的 page_id，用于填写 Driver_Event 关联。
    """
    id_, event_id, asset, direction, magnitude, reason, created_at, sync_status = row

    def text(v):
        if v is None:
            return ""
        return str(v).strip()

    props = {
        "Record": {"title": [{"text": {"content": text(asset) or str(id_)[:50]}}]},
        "Asset": {"select": {"name": text(asset) or "—"}},
    }
    if driver_event_page_id:
        props["Driver_Event"] = {"relation": [{"id": driver_event_page_id}]}
    if direction:
        props["Direction"] = {"select": {"name": text(direction)}}
    if magnitude:
        props["Magnitude"] = {"select": {"name": text(magnitude)}}
    if reason:
        props["Reaction_Note"] = {"rich_text": [{"text": {"content": text(reason)[:2000]}}]}
    return props


def run(db_config, notion_config, log_config=None):
    """
    同步 cross_market_reactions (pending) 到 Notion，并将 sync_status 更新为 done。
    log_config: 若提供则使用 logs/sync 子目录写日志
    """
    if log_config:
        from logger import setup_logger
        from sync import get_sync_log_config
        global logger
        logger = setup_logger("sync_cross_market_reactions", get_sync_log_config(log_config))

    api_token = notion_config.get("api_token") or os.environ.get("NOTION_API_TOKEN")
    if not api_token or api_token.startswith("YOUR_"):
        logger.warning("Notion api_token 未配置，跳过 cross_market_reactions 同步")
        return

    reactions_db_id = notion_config.get("databases", {}).get("cross_market_reactions")
    macro_events_db_id = notion_config.get("databases", {}).get("macro_events")
    if not reactions_db_id or reactions_db_id.startswith("YOUR_"):
        logger.warning("Notion databases.cross_market_reactions 未配置，跳过同步")
        return
    if not macro_events_db_id or macro_events_db_id.startswith("YOUR_"):
        logger.warning("Notion databases.macro_events 未配置，无法同步关联事件，跳过")
        return

    # Notion 中“存数据库主键”的属性名，需与 Macro_Events 表里该列名完全一致（可在 config.notion.property_names 中配置）
    prop_names = notion_config.get("property_names") or {}
    macro_events_db_id_prop = prop_names.get("macro_events_db_id", "DB_Id")

    logger.info("cross_market_reactions 同步开始，连接数据库与 Notion（Macro_Events 主键属性名: %s）", macro_events_db_id_prop)
    client = Client(auth=api_token)
    try:
        macro_events_ds_id = _get_data_source_id(client, macro_events_db_id)
        reactions_ds_id = _get_data_source_id(client, reactions_db_id)
    except ValueError as e:
        logger.error("解析 Notion data_source_id 失败: %s", e)
        return
    except Exception as e:
        logger.exception("解析 Notion data_source_id 失败: %s", e)
        return
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, event_id, asset, direction, magnitude, reason, created_at, sync_status
        FROM cross_market_reactions
        WHERE sync_status = 'pending'
        ORDER BY created_at ASC
    """)
    rows = cur.fetchall()

    pending_count = len(rows)
    logger.info("cross_market_reactions 待同步(pending) 共 %d 条，开始写入 Notion（仅同步 event process_status=done）", pending_count)

    created = 0
    errors = 0
    skipped = 0
    synced_ids = []

    macro_events_columns = (
        "id, event, country, category, event_date, actual, forecast, previous, surprise, "
        "impact_valid, risk_bias, core_view, created_at, updated_at, process_status, ai_summary"
    )

    for i, row in enumerate(rows, 1):
        id_val = row[0]
        event_id = row[1]
        asset = row[2] if len(row) > 2 else ""
        try:
            cur.execute(
                f"SELECT {macro_events_columns} FROM macro_events WHERE id = %s AND process_status = 'done'",
                (event_id,),
            )
            event_row = cur.fetchone()
            if not event_row:
                logger.warning("[%d/%d] 跳过 reaction id=%s event_id=%s：对应 macro_event 不存在或 process_status 非 done", i, pending_count, id_val, event_id)
                skipped += 1
                continue

            macro_page_id = _ensure_macro_event_in_notion(client, macro_events_ds_id, event_row, db_id_prop=macro_events_db_id_prop)
            props = _notion_props_from_reaction_row(row, driver_event_page_id=macro_page_id)
            client.pages.create(parent={"data_source_id": reactions_ds_id}, properties=props)
            created += 1
            synced_ids.append(id_val)
            logger.debug("[%d/%d] 已同步 event_id=%s 与 reaction id=%s asset=%s", i, pending_count, event_id, id_val, asset)
        except Exception as e:
            errors += 1
            logger.exception("[%d/%d] 同步失败 reaction id=%s event_id=%s asset=%s: %s", i, pending_count, id_val, event_id, asset, e)

    for sid in synced_ids:
        cur.execute(
            "UPDATE cross_market_reactions SET sync_status = 'done' WHERE id = %s",
            (sid,),
        )
    conn.commit()
    cur.close()
    conn.close()

    logger.info(
        "cross_market_reactions 同步结束: 新建=%d, 已标 done=%d, 跳过(事件非done)=%d, 失败=%d, 待同步合计=%d",
        created,
        len(synced_ids),
        skipped,
        errors,
        pending_count,
    )
    return {"created": created, "done": len(synced_ids), "skipped": skipped, "errors": errors, "pending_total": pending_count}


if __name__ == "__main__":
    config = _load_config()
    from logger import setup_logger
    from sync import get_sync_log_config
    logger = setup_logger("sync_cross_market_reactions", get_sync_log_config(config.get("logging", {})))
    run(config["database"], config["notion"], config.get("logging"))
