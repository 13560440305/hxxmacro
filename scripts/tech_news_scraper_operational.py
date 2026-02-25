#!/usr/bin/env python3
"""
可运行的 AI/科技新闻抓取脚本（生产就绪）
功能：
1. 抓取 Hacker News 头条（带重试与超时）
2. 保存为 JSON 和文本摘要
3. 可配置抓取数量与源
"""
import requests
import json
import time
import sys
from datetime import datetime

# 配置
TIMEOUT = 5
MAX_ITEMS = 10
OUTPUT_JSON = "/home/work/hxxworkspace/data/tech_news.json"
OUTPUT_TXT = "/home/work/hxxworkspace/data/tech_news.txt"

class TechNewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    def fetch_with_retry(self, url, retries=2):
        for i in range(retries):
            try:
                resp = self.session.get(url, timeout=TIMEOUT)
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                if i == retries - 1:
                    print(f"请求失败 {url}: {e}")
                time.sleep(1)
        return None
    
    def fetch_hackernews(self, limit=MAX_ITEMS):
        """抓取 Hacker News 头条"""
        print("正在抓取 Hacker News...")
        ids_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        ids_resp = self.fetch_with_retry(ids_url)
        if not ids_resp:
            return []
        
        story_ids = ids_resp.json()[:limit]
        stories = []
        for sid in story_ids:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
            item_resp = self.fetch_with_retry(item_url)
            if item_resp:
                item = item_resp.json()
                if item.get('type') == 'story' and item.get('title'):
                    stories.append({
                        "id": item['id'],
                        "title": item['title'],
                        "url": item.get('url', ''),
                        "score": item.get('score', 0),
                        "time": item.get('time', 0),
                        "source": "Hacker News"
                    })
            time.sleep(0.1)  # 礼貌延迟
        return stories
    
    def save_results(self, stories):
        """保存结果到文件"""
        # 确保目录存在
        import os
        os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
        
        # 保存 JSON
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(stories, f, ensure_ascii=False, indent=2)
        
        # 保存文本摘要
        with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
            f.write(f"AI/科技新闻摘要 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
            f.write("="*60 + "\n\n")
            for i, s in enumerate(stories, 1):
                f.write(f"{i}. [{s['source']}] {s['title']}\n")
                if s['url']:
                    f.write(f"   链接: {s['url']}\n")
                f.write(f"   分数: {s['score']} | ID: {s['id']}\n\n")
        
        print(f"数据已保存:\n  JSON: {OUTPUT_JSON}\n  文本: {OUTPUT_TXT}")
    
    def run(self):
        print(f"=== AI/科技新闻抓取开始 ===")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 抓取数据
        stories = self.fetch_hackernews(limit=MAX_ITEMS)
        
        if not stories:
            print("警告: 未抓取到任何新闻")
            sys.exit(1)
        
        # 输出预览
        print(f"\n成功抓取 {len(stories)} 条新闻:\n")
        for i, s in enumerate(stories[:3], 1):  # 只显示前3条
            print(f"{i}. {s['title']}")
            if s['url']:
                print(f"   链接: {s['url']}")
            print(f"   分数: {s['score']} | 来源: {s['source']}\n")
        
        # 保存
        self.save_results(stories)
        print("\n=== 抓取完成 ===")
        return True

def main():
    scraper = TechNewsScraper()
    success = scraper.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()