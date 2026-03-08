#!/usr/bin/env python3
"""
抓取 AI 新闻与 GitHub 开源项目
1. Hacker News 前10条（技术/AI类）
2. GitHub Trending（Python/JavaScript/AI 类别）
"""
import requests
import json
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

TIMEOUT = 8
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def fetch_hackernews_ai(limit=15):
    """从 Hacker News 抓取技术/AI 相关新闻"""
    print("正在抓取 Hacker News AI/技术新闻...")
    ai_keywords = ['ai', 'artificial intelligence', 'gpt', 'llm', 'machine learning', 'deep learning', 'openai', 'neural']
    
    try:
        # 获取头条ID
        resp = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=TIMEOUT)
        top_ids = resp.json()[:30]  # 多取一些用于过滤
        
        stories = []
        for sid in top_ids:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
            item_resp = requests.get(item_url, timeout=TIMEOUT)
            if item_resp.status_code == 200:
                story = item_resp.json()
                title = story.get('title', '').lower()
                url = story.get('url', '')
                # 过滤：标题含AI关键词或分数高
                if any(kw in title for kw in ai_keywords) or story.get('score', 0) > 50:
                    stories.append({
                        "id": story['id'],
                        "title": story['title'],
                        "url": url,
                        "score": story.get('score', 0),
                        "time": story.get('time', 0),
                        "source": "Hacker News"
                    })
            if len(stories) >= limit:
                break
        return stories[:limit]
    except Exception as e:
        print(f"Hacker News 抓取失败: {e}")
        return []

def fetch_github_trending(language='python', since='daily'):
    """抓取 GitHub Trending 项目"""
    print(f"正在抓取 GitHub Trending ({language})...")
    url = f"https://github.com/trending/{language}?since={since}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'html.parser')
        repos = []
        
        for article in soup.select('article.Box-row')[:10]:
            # 提取仓库信息
            title_elem = article.select_one('h2.h3')
            if not title_elem:
                continue
            repo_full = title_elem.text.strip().replace('\n', '').replace(' ', '')
            
            # 描述
            desc_elem = article.select_one('p')
            desc = desc_elem.text.strip() if desc_elem else ''
            
            # 星数
            stars_elem = article.select_one("[aria-label='star']")
            stars = stars_elem.parent.text.strip() if stars_elem else '0'
            
            # 今日星增
            stars_today_elem = article.select_one("span.d-inline-block.float-sm-right")
            stars_today = stars_today_elem.text.strip() if stars_today_elem else ''
            
            # 语言
            lang_elem = article.select_one("[itemprop='programmingLanguage']")
            lang = lang_elem.text.strip() if lang_elem else ''
            
            repos.append({
                "repository": repo_full,
                "url": f"https://github.com/{repo_full}",
                "description": desc,
                "stars": stars,
                "stars_today": stars_today,
                "language": lang,
                "source": f"GitHub Trending {language.capitalize()}"
            })
        return repos
    except Exception as e:
        print(f"GitHub Trending 抓取失败: {e}")
        return []

def save_results(ai_news, github_repos):
    """保存结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    # 合并数据
    combined = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "ai_news_count": len(ai_news),
            "github_repos_count": len(github_repos)
        },
        "ai_news": ai_news,
        "github_trending": github_repos
    }
    
    # JSON 文件
    json_path = f"/home/work/hxxworkspace/data/ai_github_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"完整数据保存至: {json_path}")
    
    # 生成 Markdown 简报
    md_path = f"/home/work/hxxworkspace/data/ai_github_latest.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# AI 新闻与 GitHub 开源项目简报\n")
        f.write(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 🚀 AI/科技新闻（最新10条）\n")
        for i, news in enumerate(ai_news[:10], 1):
            f.write(f"### {i}. {news['title']}\n")
            f.write(f"- **链接**: {news['url']}\n")
            f.write(f"- **热度分**: {news['score']} | **来源**: {news['source']}\n")
            f.write(f"- **时间**: {datetime.fromtimestamp(news['time']).strftime('%Y-%m-%d')}\n\n")
        
        f.write("## 🌟 GitHub 热门开源项目（Python）\n")
        for i, repo in enumerate(github_repos[:5], 1):
            f.write(f"### {i}. {repo['repository']}\n")
            f.write(f"- **描述**: {repo['description']}\n")
            f.write(f"- **语言**: {repo['language']} | **星数**: {repo['stars']}\n")
            f.write(f"- **今日新增**: {repo['stars_today']}\n")
            f.write(f"- **链接**: {repo['url']}\n\n")
        
        f.write("---\n")
        f.write("*数据源: Hacker News + GitHub Trending | 抓取脚本: ai_github_scraper.py*")
    print(f"Markdown 简报保存至: {md_path}")
    
    return json_path, md_path

def main():
    print("=== AI 新闻 + GitHub 开源项目抓取 ===")
    
    # 并行抓取
    ai_news = fetch_hackernews_ai(limit=12)  # 多抓几条，后续过滤
    github_python = fetch_github_trending(language='python', since='daily')
    
    # 保存
    json_path, md_path = save_results(ai_news, github_python)
    
    # 输出摘要
    print(f"\n✅ 抓取完成:")
    print(f"   AI新闻: {len(ai_news)} 条")
    print(f"   GitHub 项目: {len(github_python)} 个")
    print(f"   JSON 文件: {json_path}")
    print(f"   简报文件: {md_path}")

if __name__ == "__main__":
    main()