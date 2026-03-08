#!/usr/bin/env python3
"""
快速获取 AI 新闻 + GitHub AI 开源项目（使用公开 API，避免复杂解析）
"""
import requests
import json
from datetime import datetime

TIMEOUT = 5

def fetch_hackernews_simple():
    """获取 Hacker News 前20条中与 AI 相关的"""
    try:
        resp = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=TIMEOUT)
        ids = resp.json()[:20]
        ai_news = []
        ai_keywords = ['ai', 'gpt', 'llm', 'openai', 'machine learning', 'neural', 'deep learning', 'artificial intelligence']
        
        for sid in ids:
            item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=TIMEOUT).json()
            title = item.get('title', '').lower()
            if any(kw in title for kw in ai_keywords):
                ai_news.append({
                    "title": item.get('title'),
                    "url": item.get('url', ''),
                    "score": item.get('score', 0),
                    "source": "Hacker News"
                })
            if len(ai_news) >= 10:
                break
        return ai_news
    except:
        return []

def fetch_github_ai_repos():
    """通过 GitHub API 搜索 AI 相关的 Python 项目"""
    try:
        # 搜索最近一周创建的 AI 相关 Python 项目
        query = "ai OR machine-learning OR deep-learning language:python created:>2026-02-07"
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=5"
        resp = requests.get(url, timeout=TIMEOUT)
        data = resp.json()
        
        repos = []
        for item in data.get('items', [])[:5]:
            repos.append({
                "name": item['full_name'],
                "url": item['html_url'],
                "description": item.get('description', '')[:150],
                "stars": item['stargazers_count'],
                "language": item.get('language', ''),
                "created": item['created_at'],
                "source": "GitHub API"
            })
        return repos
    except:
        return []

def main():
    print("快速抓取 AI 新闻与 GitHub 开源项目...")
    
    ai_news = fetch_hackernews_simple()
    github_repos = fetch_github_ai_repos()
    
    # 合并数据
    combined = {
        "ai_news": ai_news,
        "github_ai_repos": github_repos,
        "updated": datetime.now().isoformat()
    }
    
    # 保存 JSON
    json_path = "/home/work/hxxworkspace/data/ai_combined.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    
    # 生成 Markdown 简报
    md_path = "/home/work/hxxworkspace/data/ai_combined.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# AI 新闻与开源项目速报\n")
        f.write(f"> 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        
        f.write("## 📰 AI/科技新闻（最新10条）\n")
        if ai_news:
            for i, news in enumerate(ai_news, 1):
                f.write(f"{i}. **{news['title']}**\n")
                f.write(f"   链接: {news['url']} | 热度: {news['score']}\n\n")
        else:
            f.write("（暂无抓取到AI相关新闻）\n\n")
        
        f.write("## 💻 GitHub AI 开源项目（Python）\n")
        if github_repos:
            for repo in github_repos:
                f.write(f"- **[{repo['name']}]({repo['url']})**\n")
                f.write(f"  描述: {repo['description']}\n")
                f.write(f"  语言: {repo['language']} | 星数: {repo['stars']}\n\n")
        else:
            f.write("（暂无抓取到开源项目）\n\n")
        
        f.write("---\n*数据源: Hacker News + GitHub Search API*")
    
    print(f"✅ 完成！\n   JSON: {json_path}\n   Markdown: {md_path}")
    
    # 输出摘要
    print(f"\n📊 抓取统计:")
    print(f"   AI新闻: {len(ai_news)} 条")
    print(f"   GitHub 项目: {len(github_repos)} 个")

if __name__ == "__main__":
    main()