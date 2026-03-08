#!/usr/bin/env python3
"""
优化版：极简 Hacker News 抓取，快速返回
"""
import sys
import requests
import json
from datetime import datetime

TIMEOUT = 3  # 更短的超时

def fetch_hn_fast():
    """快速抓取 Hacker News 前5条"""
    try:
        # 只取前5个ID
        ids = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json', timeout=TIMEOUT).json()[:5]
        stories = []
        for sid in ids:
            item = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{sid}.json', timeout=TIMEOUT).json()
            stories.append({
                'title': item.get('title', '无标题'),
                'url': item.get('url', ''),
                'score': item.get('score', 0)
            })
        return stories
    except Exception as e:
        print(f'抓取失败: {e}')
        return []

def main():
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 开始快速抓取...')
    
    stories = fetch_hn_fast()
    
    if stories:
        print(f'✅ 成功抓取 {len(stories)} 条新闻')
        for i, s in enumerate(stories, 1):
            print(f'{i}. {s["title"]}')
            if s['url']:
                print(f'   链接: {s["url"][:50]}...')
            print(f'   热度: {s["score"]}\n')
        
        # 极简保存
        with open('/home/work/hxxworkspace/data/test_output.json', 'w') as f:
            json.dump(stories, f, indent=2)
        print('📁 数据已保存至: /home/work/hxxworkspace/data/test_output.json')
    else:
        print('❌ 未抓取到数据')
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 完成')
    return bool(stories)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)