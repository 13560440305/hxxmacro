# Sync subpackage: one script per table to sync to Notion.
import os


def get_sync_log_config(log_config):
    """返回用于同步日志的配置，日志目录为 logs/sync 子目录。"""
    if not log_config:
        return {"dir": "../logs/sync", "level": "INFO", "console": True}
    base_dir = log_config.get("dir", "../logs")
    sync_dir = log_config.get("sync_dir", "sync")
    sync_log_dir = os.path.normpath(os.path.join(base_dir, sync_dir))
    return {**log_config, "dir": sync_log_dir}
