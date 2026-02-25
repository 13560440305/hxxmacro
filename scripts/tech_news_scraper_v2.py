#!/usr/bin/env python3
"""
稳定版 AI/科技新闻抓取脚本
集成 Hacker News、TechCrunch RSS，支持超时与重试。
"""
import requests
import feedparser
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup

def fetch_with_retry(url, max_retries=2, timeout=5):
    """带重试的请求"""
    for i in range(max_retries):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            if i == max_retries - 1:
                raise e
            time.sleep(1)
    return None

def fetch_hackernews_top(max_items=10):
    """抓取 Hacker News 头条"""
    try:
        # 获取头条ID
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        resp = fetch_with_retry(top_url)
        top_ids = resp.json()[:max_items]
        
        stories = []
        for sid in top_ids:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
            item_resp = fetch_with_retry(item_url)
            if item_resp:
                story = item_resp.json()
                # 过滤出技术相关（可根据标题关键词进一步过滤）
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
        print(f"[Hacker News] 抓取失败: {e}")
        return []

def fetch_techcrunch_rss(max_items=10):
    """抓取 TechCrunch RSS"""
    try:
        # 使用 feedparser 解析 RSS
        feed = feedparser.parse("https://techcrunch.com/feed/")
        articles = []
        for entry in feed.entries[:max_items]:
            articles.append({
                "title": entry.title,
                "url": entry.link,
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "")[:200],  # 截断
                "source": "TechCrunch"
            })
        return articles
    except Exception as e:
        print(f"[TechCrunch RSS] 抓取失败: {e}")
        return []

def save_to_json(data, filename):
    """保存为 JSON 文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存至: {filename}")

def main():
    """主函数"""
    print(f"=== AI/科技新闻抓取 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    # 抓取各源数据
    hn_news = fetch_hackernews_top(5)
    tc_news = fetch_techcrunch_rss(5)
    
    # 合并结果
    all_news = hn_news + tc_news
    
    # 输出预览
    print(f"\n共获取 {len(all_news)} 条新闻:")
    for i, news in enumerate(all_news, 1):
        print(f"{i}. [{news['source']}] {news['title']}")
        if news.get('url'):
            print(f"   链接: {news['url']}")
        print()
    
    # 保存原始数据
    save_to_json(all_news, "/home/work/hxxworkspace/tech_news_latest.json")
    
    # 同时生成简化的文本摘要
    with open("/home/work/hxxworkspace/tech_news_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"AI/科技新闻摘要 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
        f.write("="*50 + "\n")
        for news in all_news:
            f.write(f"[{news['source']}] {news['title']}\n")
            if news.get('url'):
                f.write(f"链接: {news['url']}\n")
            f.write("\n")
    
    return all_news

if __name__ == "__main__":
    main()