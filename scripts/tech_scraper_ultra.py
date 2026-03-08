#!/usr/bin/env python3
"""
超稳定版：仅用 requests 抓取 Hacker News，极简超时控制。
"""
import sys
import requests
import json
import time
from datetime import datetime

# 全局超时设置
TIMEOUT = 4

def safe_get(url, max_retries=1):
    """安全的 GET 请求"""
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return r
    except:
        return None

def fetch_hn():
    """抓取 Hacker News 头条（最多5条）"""
    # 1. 获取ID列表
    top_resp = safe_get("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not top_resp:
        return []
    ids = top_resp.json()[:5]
    
    stories = []
    for sid in ids:
        item_resp = safe_get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
        if item_resp:
            s = item_resp.json()
            stories.append({
                "title": s.get("title", ""),
                "url": s.get("url", ""),
                "score": s.get("score", 0),
                "source": "Hacker News"
            })
    return stories

def main():
    print(f"[启动] {datetime.now().strftime('%H:%M:%S')}")
    
    data = fetch_hn()
    
    if not data:
        print("警告: 未抓到数据")
        sys.exit(1)
    
    # 输出
    print(f"\n抓取到 {len(data)} 条科技新闻:\n")
    for i, d in enumerate(data, 1):
        print(f"{i}. {d['title']}")
        if d['url']:
            print(f"   链接: {d['url']}")
        print(f"   分数: {d['score']}\n")
    
    # 保存
    out_path = "/home/work/hxxworkspace/tech_latest.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存至: {out_path}")
    print(f"[完成] {datetime.now().strftime('%H:%M:%S')}")
    sys.exit(0)

if __name__ == "__main__":
    main()