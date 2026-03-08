#!/usr/bin/env python3
"""
AI与科技新闻抓取脚本（示例）
使用 RSS 或 API 获取最新科技新闻。
"""
import feedparser
import requests
import json
from datetime import datetime

def fetch_techcrunch_rss(max_items=10):
    """抓取 TechCrunch RSS"""
    url = "https://techcrunch.com/feed/"
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:max_items]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", ""),
            "summary": entry.get("summary", ""),
        })
    return articles

def fetch_hackernews_top(max_items=10):
    """抓取 Hacker News 头条"""
    top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    item_url = "https://hacker-news.firebaseio.com/v0/item/{}.json"
    
    top_ids = requests.get(top_url).json()[:max_items]
    stories = []
    for sid in top_ids:
        story = requests.get(item_url.format(sid)).json()
        stories.append({
            "id": story.get("id"),
            "title": story.get("title", ""),
            "url": story.get("url", ""),
            "score": story.get("score", 0),
        })
    return stories

if __name__ == "__main__":
    print("=== TechCrunch RSS 示例 ===")
    tech = fetch_techcrunch_rss(3)
    for a in tech:
        print(f"{a['title']}\n  {a['link']}\n")
    
    print("=== Hacker News 头条示例 ===")
    hn = fetch_hackernews_top(3)
    for s in hn:
        print(f"{s['title']} (分数: {s['score']})\n  {s['url']}\n")
