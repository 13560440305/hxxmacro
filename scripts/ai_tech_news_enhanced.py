#!/usr/bin/env python3
"""
增强版 AI 与科技新闻抓取脚本
功能：
1. AI/科技新闻（Hacker News, Reddit）
2. 美国科技巨头新闻（Apple, Google, Microsoft, Amazon, Meta, Tesla, NVIDIA, OpenAI）
3. GitHub AI 开源项目
"""
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote
import re

TIMEOUT = 15

# 科技巨头关键词
TECH_GIANTS = [
    "Apple", "Google", "Microsoft", "Amazon", "Meta", "Facebook",
    "Tesla", "NVIDIA", "OpenAI", "Anthropic"
]

# AI 相关关键词
AI_KEYWORDS = [
    'ai', 'gpt', 'llm', 'openai', 'machine learning', 'neural',
    'deep learning', 'artificial intelligence', 'chatgpt', 'claude',
    'gemini', 'copilot', 'transformer', 'diffusion'
]


def parse_rss_feed(xml_content):
    """手动解析 RSS feed"""
    items = []
    try:
        root = ET.fromstring(xml_content)
        # 处理命名空间
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        # 尝试标准 RSS 格式
        for item in root.findall('.//item'):
            entry = {}
            title_elem = item.find('title')
            link_elem = item.find('link')
            pub_elem = item.find('pubDate')
            desc_elem = item.find('description')
            
            entry['title'] = title_elem.text if title_elem is not None else ''
            entry['link'] = link_elem.text if link_elem is not None else ''
            entry['published'] = pub_elem.text if pub_elem is not None else ''
            entry['description'] = desc_elem.text if desc_elem is not None else ''
            items.append(entry)
        
        # 如果没找到 item，尝试 Atom 格式
        if not items:
            for entry in root.findall('.//atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                link_elem = entry.find('atom:link', ns)
                pub_elem = entry.find('atom:published', ns)
                
                item = {}
                item['title'] = title_elem.text if title_elem is not None else ''
                if link_elem is not None:
                    item['link'] = link_elem.get('href', '')
                item['published'] = pub_elem.text if pub_elem is not None else ''
                items.append(item)
    except Exception as e:
        print(f"  RSS 解析错误: {e}")
    
    return items


def fetch_hackernews():
    """获取 Hacker News 热门故事，分类过滤"""
    print("📡 抓取 Hacker News...")
    try:
        resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=TIMEOUT
        )
        ids = resp.json()[:50]

        ai_news = []
        tech_giant_news = []
        other_tech = []

        for sid in ids:
            try:
                item = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    timeout=TIMEOUT
                ).json()
                if not item:
                    continue

                title = item.get('title', '')
                title_lower = title.lower()
                url = item.get('url', '')

                is_ai = any(kw in title_lower for kw in AI_KEYWORDS)
                is_tech_giant = any(giant.lower() in title_lower for giant in TECH_GIANTS)

                news_item = {
                    "title": title,
                    "url": url,
                    "score": item.get('score', 0),
                    "comments": item.get('descendants', 0),
                    "hn_link": f"https://news.ycombinator.com/item?id={sid}",
                    "source": "Hacker News"
                }

                if is_ai:
                    ai_news.append(news_item)
                if is_tech_giant:
                    news_item["companies"] = [g for g in TECH_GIANTS if g.lower() in title_lower]
                    tech_giant_news.append(news_item)
                elif not is_ai:
                    other_tech.append(news_item)

            except Exception:
                continue

        return {
            "ai_news": ai_news[:15],
            "tech_giant_news": tech_giant_news[:15],
            "other_tech": other_tech[:10]
        }
    except Exception as e:
        print(f"  ❌ Hacker News 抓取失败: {e}")
        return {"ai_news": [], "tech_giant_news": [], "other_tech": []}


def fetch_reddit_tech():
    """抓取 Reddit 科技板块热门"""
    print("📡 抓取 Reddit...")
    try:
        subreddits = ["technology", "artificial", "MachineLearning"]
        all_posts = []

        for sub in subreddits:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
                headers = {"User-Agent": "Mozilla/5.0 (compatible; hxxmacro/1.0)"}
                resp = requests.get(url, headers=headers, timeout=TIMEOUT)
                data = resp.json()

                for post in data['data']['children']:
                    p = post['data']
                    all_posts.append({
                        "title": p['title'],
                        "url": p.get('url', ''),
                        "score": p['score'],
                        "comments": p['num_comments'],
                        "subreddit": sub,
                        "source": f"Reddit r/{sub}",
                        "link": f"https://reddit.com{p['permalink']}"
                    })
            except Exception:
                continue

        return all_posts[:15]
    except Exception as e:
        print(f"  ❌ Reddit 抓取失败: {e}")
        return []


def fetch_google_news_rss():
    """通过 Google News RSS 获取科技巨头新闻"""
    print("📡 抓取 Google News RSS...")
    all_news = []
    seen_titles = set()

    search_terms = [
        "Apple iPhone OR Apple technology",
        "Google AI OR Google Cloud",
        "Microsoft AI OR Microsoft Azure",
        "Amazon AWS OR Amazon technology",
        "Meta AI OR Meta Platforms",
        "Tesla news",
        "NVIDIA AI OR NVIDIA chip",
        "OpenAI ChatGPT"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for term in search_terms:
        try:
            encoded = quote(term)
            url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
            items = parse_rss_feed(resp.content)

            for entry in items[:5]:
                title = entry.get('title', '')
                # 去重
                title_key = title[:50].lower()
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

                # 清理标题（移除来源标记）
                clean_title = re.sub(r'\s*-\s*[^-]+$', '', title)
                company = term.split()[0]

                all_news.append({
                    "title": clean_title,
                    "url": entry.get('link', ''),
                    "published": entry.get('published', ''),
                    "company": company,
                    "source": "Google News"
                })
        except Exception as e:
            print(f"  Google News '{term}' 抓取失败: {e}")
            continue

    return all_news[:25]


def fetch_techcrunch():
    """抓取 TechCrunch RSS"""
    print("📡 抓取 TechCrunch...")
    try:
        url = "https://techcrunch.com/feed/"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; hxxmacro/1.0)"}
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        items = parse_rss_feed(resp.content)

        articles = []
        for entry in items[:20]:
            title = entry.get('title', '')
            title_lower = title.lower()

            companies = [g for g in TECH_GIANTS if g.lower() in title_lower]
            is_ai = any(kw in title_lower for kw in AI_KEYWORDS)

            articles.append({
                "title": title,
                "url": entry.get('link', ''),
                "published": entry.get('published', ''),
                "companies": companies if companies else None,
                "is_ai": is_ai,
                "source": "TechCrunch"
            })

        return articles
    except Exception as e:
        print(f"  ❌ TechCrunch 抓取失败: {e}")
        return []


def fetch_github_ai():
    """GitHub AI 开源项目"""
    print("📡 抓取 GitHub AI 项目...")
    try:
        queries = [
            "ai OR machine-learning language:python",
            "llm OR gpt language:python",
            "transformer language:python"
        ]

        all_repos = []
        seen = set()

        for query in queries:
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=10"
            resp = requests.get(url, timeout=TIMEOUT)
            data = resp.json()

            for item in data.get('items', []):
                full_name = item['full_name']
                if full_name in seen:
                    continue
                seen.add(full_name)

                all_repos.append({
                    "name": full_name,
                    "url": item['html_url'],
                    "description": (item.get('description') or '')[:150],
                    "stars": item['stargazers_count'],
                    "language": item.get('language', ''),
                    "forks": item['forks_count'],
                    "source": "GitHub"
                })

        return all_repos[:15]
    except Exception as e:
        print(f"  ❌ GitHub 抓取失败: {e}")
        return []


def generate_report(data, output_dir):
    """生成 Markdown 报告"""
    timestamp = datetime.now()
    date_str = timestamp.strftime('%Y-%m-%d')
    time_str = timestamp.strftime('%H:%M')

    # JSON 输出
    json_path = f"{output_dir}/ai_tech_news_{date_str.replace('-', '')}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "generated": timestamp.isoformat(),
            "data": data
        }, f, ensure_ascii=False, indent=2)

    # Markdown 报告
    md_path = f"{output_dir}/ai_tech_news_latest.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# 🤖 AI 与科技新闻日报\n")
        f.write(f"> 更新时间: {date_str} {time_str} UTC\n\n")

        # === AI 新闻 ===
        f.write("## 📰 AI 前沿动态\n\n")
        hn_ai = data['hackernews']['ai_news']
        if hn_ai:
            for i, news in enumerate(hn_ai[:10], 1):
                f.write(f"### {i}. {news['title']}\n")
                if news['url']:
                    f.write(f"- 🔗 [原文]({news['url']}) | ")
                f.write(f"[HN讨论]({news['hn_link']})\n")
                f.write(f"- 💯 {news['score']} pts | 💬 {news['comments']} 评论\n\n")
        else:
            f.write("暂无 AI 相关新闻\n\n")

        # === 科技巨头新闻 ===
        f.write("## 🏢 美国科技巨头动态\n\n")
        
        # 按公司分类
        company_news = {}
        for news in data['hackernews']['tech_giant_news']:
            companies = news.get('companies', [])
            for company in companies:
                if company not in company_news:
                    company_news[company] = []
                company_news[company].append(news)

        for news in data['google_news']:
            company = news.get('company', 'Other')
            if company not in company_news:
                company_news[company] = []
            company_news[company].append(news)

        for company in TECH_GIANTS:
            if company in company_news and company_news[company]:
                f.write(f"### {company}\n\n")
                for news in company_news[company][:5]:
                    title = news['title']
                    url = news.get('url', '')
                    source = news.get('source', '')
                    f.write(f"- **{title}**\n")
                    if url:
                        f.write(f"  [{source}]({url})\n")
                    f.write("\n")

        # === TechCrunch ===
        f.write("## 📱 TechCrunch 热门\n\n")
        tc_articles = data['techcrunch']
        for article in tc_articles[:12]:
            tags = []
            if article.get('is_ai'):
                tags.append("🤖AI")
            if article.get('companies'):
                tags.extend(article['companies'])
            tag_str = f" `{'` `'.join(tags)}`" if tags else ""

            f.write(f"- **{article['title']}**{tag_str}\n")
            f.write(f"  [TechCrunch]({article['url']})\n\n")

        # === Reddit 热门 ===
        f.write("## 💬 Reddit 热门讨论\n\n")
        reddit_posts = data['reddit']
        for post in reddit_posts[:10]:
            f.write(f"- **{post['title']}**\n")
            f.write(f"  r/{post['subreddit']} | {post['score']}↑ {post['comments']}💬\n")
            f.write(f"  [链接]({post['link']})\n\n")

        # === GitHub 项目 ===
        f.write("## 💻 GitHub AI 热门项目\n\n")
        github_repos = data['github']
        for repo in github_repos:
            f.write(f"### [{repo['name']}]({repo['url']})\n")
            f.write(f"- 描述: {repo['description']}\n")
            f.write(f"- 语言: {repo['language']} | ⭐ {repo['stars']:,} | 🍴 {repo['forks']:,}\n\n")

        f.write("---\n")
        f.write("*数据源: Hacker News + Reddit + Google News + TechCrunch + GitHub*\n")

    return json_path, md_path


def main():
    print("=" * 50)
    print("🚀 AI 与科技新闻增强版抓取")
    print("=" * 50)

    output_dir = "/home/work/workspace/hxxmacro/data/ai_tech"

    # 抓取各数据源
    hn_data = fetch_hackernews()
    reddit_data = fetch_reddit_tech()
    google_news = fetch_google_news_rss()
    techcrunch = fetch_techcrunch()
    github = fetch_github_ai()

    # 合并数据
    all_data = {
        "hackernews": hn_data,
        "reddit": reddit_data,
        "google_news": google_news,
        "techcrunch": techcrunch,
        "github": github
    }

    # 生成报告
    json_path, md_path = generate_report(all_data, output_dir)

    print("\n" + "=" * 50)
    print("✅ 抓取完成!")
    print(f"📄 JSON: {json_path}")
    print(f"📄 Markdown: {md_path}")
    print("\n📊 统计:")
    print(f"   Hacker News AI: {len(hn_data['ai_news'])} 条")
    print(f"   科技巨头新闻: {len(hn_data['tech_giant_news'])} 条")
    print(f"   Reddit: {len(reddit_data)} 条")
    print(f"   Google News: {len(google_news)} 条")
    print(f"   TechCrunch: {len(techcrunch)} 条")
    print(f"   GitHub: {len(github)} 个项目")


if __name__ == "__main__":
    main()
