#!/usr/bin/env python3
import requests
import json

def fetch_hackernews():
    """仅获取 Hacker News 前5条标题"""
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    resp = requests.get(url, timeout=5)
    top_ids = resp.json()[:5]
    results = []
    for sid in top_ids:
        story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json").json()
        results.append({
            "id": story.get("id"),
            "title": story.get("title", ""),
            "url": story.get("url", ""),
            "score": story.get("score", 0)
        })
    return results

if __name__ == "__main__":
    try:
        print("=== Hacker News 前5条头条 ===")
        stories = fetch_hackernews()
        for s in stories:
            print(f"{s['title']} (分数: {s['score']})\n  链接: {s['url']}\n")
    except Exception as e:
        print(f"错误: {e}")