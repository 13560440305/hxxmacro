"""
Notion 同步控制总脚本：按配置依次执行各表到 Notion 的同步。
同步日志写入 logs/sync 子目录。
新增同步时：在 sync 子目录下新增对应脚本，再在本脚本的 SYNC_TASKS 中注册即可。
"""
import json
import os

from logger import setup_logger
from sync import get_sync_log_config

# ---------- 同步任务配置 ----------
# 仅同步 cross_market_reactions：会按 event_id 拉取 macro_events（process_status=done）并写入 Notion，再写入反应，避免 macro_events 重复
from sync.sync_cross_market_reactions import run as sync_cross_market_reactions

SYNC_TASKS = [
    ("cross_market_reactions", sync_cross_market_reactions),
]


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    config = load_config()
    log_config = config.get("logging", {})
    sync_log_config = get_sync_log_config(log_config)
    logger = setup_logger("sync_notion", sync_log_config)

    db_config = config["database"]
    notion_config = config.get("notion", {})

    logger.info("Notion 同步启动，日志目录: %s", sync_log_config.get("dir", ""))

    if not notion_config.get("api_token") or notion_config["api_token"].startswith("YOUR_"):
        logger.warning("Notion 未配置 api_token，请先在 config.json 的 notion.api_token 中填写 Integration Token")
        return

    logger.info("开始 Notion 同步，共 %d 个任务: %s", len(SYNC_TASKS), [t[0] for t in SYNC_TASKS])
    results = {}
    for name, run_fn in SYNC_TASKS:
        try:
            logger.info("执行同步任务: %s", name)
            out = run_fn(db_config, notion_config, sync_log_config)
            results[name] = out
            logger.info("同步任务完成: %s -> %s", name, out)
        except Exception as e:
            logger.exception("同步任务失败: %s, 错误: %s", name, e)
            results[name] = {"error": str(e)}

    logger.info("Notion 同步结束，汇总结果: %s", results)
    return results


if __name__ == "__main__":
    main()
