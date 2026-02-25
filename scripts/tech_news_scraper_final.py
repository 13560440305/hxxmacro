#!/usr/bin/env python3
"""
极简稳定版 AI/科技新闻抓取（仅 Hacker News）
避免外部依赖问题，确保可靠执行。
"""
import requests
import json
import time
from datetime import datetime

def fetch_hackernews_simple(max_items=10):
    """只抓取 Hacker News 头条，无外部依赖"""
    try:
        # 1. 获取头条ID列表
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        resp = requests.get(top_url, timeout=5)
        resp.raise_for_status()
        top_ids = resp.json()[:max_items]
        
        stories = []
        for sid in top_ids:
            # 2. 获取每条详情
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
            item_resp = requests.get(item_url, timeout=5)
            if item_resp.status_code == 200:
                story = item_resp.json()
                # 仅保留关键字段
                stories.append({
                    "id": story.get("id"),
                    "title": story.get("title", ""),
                    "url": story.get("url", ""),
                    "score": story.get("score", 0),
                    "time": story.get("time", 0),
                    "source": "Hacker News"
                })
        return stories
    except Exception as e:
        print(f"[Hacker News] 错误: {e}")
        return []

def save_outputs(data):
    """保存 JSON 和文本摘要"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON 完整数据
    json_path = f"/home/work/hxxworkspace/tech_news_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"完整数据保存至: {json_path}")
    
    # 文本摘要
    txt_path = f"/home/work/hxxworkspace/tech_news_latest.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"AI/科技新闻摘要 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
        f.write("="*50 + "\n")
        for i, news in enumerate(data, 1):
            f.write(f"{i}. [{news['source']}] {news['title']}\n")
            f.write(f"   链接: {news.get('url', '无')}\n")
            f.write(f"   分数: {news.get('score', 0)} | 时间: {time.ctime(news.get('time', 0))}\n")
            f.write("\n")
    print(f"文本摘要保存至: {txt_path}")
    
    return json_path, txt_path

def main():
    print(f"=== AI/科技新闻抓取启动 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    # 抓取数据
    news = fetch_hackernews_simple(8)  # 获取8条
    
    # 输出预览
    print(f"\n成功抓取 {len(news)} 条新闻:\n")
    for i, item in enumerate(news, 1):
        print(f"{i}. {item['title']}")
        print(f"   链接: {item.get('url', '无')}")
        print(f"   分数: {item['score']} | 来源: {item['source']}\n")
    
    # 保存文件
    json_path, txt_path = save_outputs(news)
    
    # 输出结果路径（便于后续使用）
    print("\n=== 抓取完成 ===")
    print(f"JSON 文件: {json_path}")
    print(f"文本摘要: {txt_path}")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)