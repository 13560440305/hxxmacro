#!/usr/bin/env python3
"""
增强版 AI 与科技新闻抓取脚本 v3
功能：
1. AI/科技新闻（Hacker News, Reddit, TechCrunch）
2. 美国科技巨头新闻（Apple, Google, Microsoft, Amazon, Meta, Tesla, NVIDIA, OpenAI）
3. GitHub AI 开源项目
4. 生成30条带摘要的简报，可直接使用
5. 同时生成英文版和中文版
"""
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote
import re
import textwrap
import time

TIMEOUT = 15

# 常用词汇翻译表
TRANSLATION_DICT = {
    # AI 相关
    "artificial intelligence": "人工智能",
    "machine learning": "机器学习",
    "deep learning": "深度学习",
    "neural network": "神经网络",
    "language model": "语言模型",
    "large language model": "大语言模型",
    "chatbot": "聊天机器人",
    "generative AI": "生成式AI",
    "AI agent": "AI智能体",
    "AI": "AI",
    "GPT": "GPT",
    "LLM": "大语言模型",
    
    # 公司名
    "OpenAI": "OpenAI",
    "Google": "谷歌",
    "Microsoft": "微软",
    "Apple": "苹果",
    "Amazon": "亚马逊",
    "Meta": "Meta",
    "Facebook": "Facebook",
    "Tesla": "特斯拉",
    "NVIDIA": "英伟达",
    "Anthropic": "Anthropic",
    
    # 科技词汇
    "cloud": "云",
    "cloud computing": "云计算",
    "data center": "数据中心",
    "chip": "芯片",
    "semiconductor": "半导体",
    "software": "软件",
    "hardware": "硬件",
    "startup": "初创公司",
    "venture capital": "风险投资",
    "funding": "融资",
    "investment": "投资",
    "acquisition": "收购",
    "merger": "合并",
    "IPO": "上市",
    "stock": "股票",
    "shares": "股份",
    "revenue": "营收",
    "profit": "利润",
    "technology": "技术",
    "innovation": "创新",
    "breakthrough": "突破",
    "launch": "发布",
    "release": "发布",
    "update": "更新",
    "security": "安全",
    "privacy": "隐私",
    "cybersecurity": "网络安全",
    "hacking": "黑客",
    "data breach": "数据泄露",
    "regulation": "监管",
    "government": "政府",
    "military": "军方",
    "defense": "国防",
    "surveillance": "监控",
    
    # 常用词
    "announces": "宣布",
    "reveals": "透露",
    "reports": "报道",
    "says": "表示",
    "warns": "警告",
    "launches": "推出",
    "introduces": "引入",
    "expands": "扩展",
    "acquires": "收购",
    "raises": "融资",
    "invests": "投资",
    "develops": "开发",
    "plans": "计划",
    "expects": "预期",
    "predicts": "预测",
    "according to": "据",
    "new": "新",
    "latest": "最新",
    "first": "首个",
    "major": "重大",
    "biggest": "最大",
    "largest": "最大",
    "leading": "领先",
    "top": "顶级",
    "key": "关键",
    "important": "重要",
    "significant": "重要",
    "critical": "关键",
}

def translate_text(text, max_retries=2):
    """翻译文本为中文（使用免费API）"""
    if not text or len(text) < 3:
        return text
    
    # 先检查是否包含中文（已经是中文）
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return text
    
    # 尝试使用免费翻译API
    for attempt in range(max_retries):
        try:
            # 使用 MyMemory 免费翻译API
            url = f"https://api.mymemory.translated.net/get?q={quote(text[:500])}&langpair=en|zh"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            if data.get('responseStatus') == 200:
                translated = data.get('responseData', {}).get('translatedText', '')
                if translated and translated != text:
                    return translated
        except Exception:
            pass
        
        time.sleep(0.5)
    
    # API失败，使用关键词替换
    translated = text
    for en, zh in TRANSLATION_DICT.items():
        if en.lower() in translated.lower():
            # 保持大小写敏感性
            pattern = re.compile(re.escape(en), re.IGNORECASE)
            translated = pattern.sub(zh, translated)
    
    return translated

# 科技巨头关键词
TECH_GIANTS = [
    "Apple", "Google", "Microsoft", "Amazon", "Meta", "Facebook",
    "Tesla", "NVIDIA", "OpenAI", "Anthropic"
]

# AI 相关关键词
AI_KEYWORDS = [
    'ai', 'gpt', 'llm', 'openai', 'machine learning', 'neural',
    'deep learning', 'artificial intelligence', 'chatgpt', 'claude',
    'gemini', 'copilot', 'transformer', 'diffusion', 'agent'
]


def parse_rss_feed(xml_content):
    """手动解析 RSS feed"""
    items = []
    try:
        root = ET.fromstring(xml_content)
        for item in root.findall('.//item'):
            entry = {}
            title_elem = item.find('title')
            link_elem = item.find('link')
            pub_elem = item.find('pubDate')
            desc_elem = item.find('description')
            
            entry['title'] = title_elem.text if title_elem is not None else ''
            entry['link'] = link_elem.text if link_elem is not None else ''
            entry['published'] = pub_elem.text if pub_elem is not None else ''
            # 清理 HTML 标签
            desc = desc_elem.text if desc_elem is not None else ''
            entry['description'] = re.sub(r'<[^>]+>', '', desc).strip()
            items.append(entry)
    except Exception as e:
        pass
    return items


def clean_text(text, max_len=200):
    """清理并截断文本"""
    if not text:
        return ''
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除多余空白
    text = ' '.join(text.split())
    # 截断
    if len(text) > max_len:
        text = text[:max_len].rsplit(' ', 1)[0] + '...'
    return text


def fetch_hackernews():
    """获取 Hacker News 热门故事"""
    print("📡 抓取 Hacker News...")
    try:
        resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=TIMEOUT
        )
        ids = resp.json()[:100]  # 取前100条

        all_news = []
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
                score = item.get('score', 0)
                
                # 只要有一定热度都收录
                if score < 50:
                    continue

                # 判断分类
                is_ai = any(kw in title_lower for kw in AI_KEYWORDS)
                companies = [g for g in TECH_GIANTS if g.lower() in title_lower]
                
                # 获取内容摘要
                text = item.get('text', '')
                summary = clean_text(text, 150) if text else ''

                all_news.append({
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "score": score,
                    "comments": item.get('descendants', 0),
                    "hn_link": f"https://news.ycombinator.com/item?id={sid}",
                    "source": "Hacker News",
                    "is_ai": is_ai,
                    "companies": companies,
                    "priority": (1 if is_ai else 0) + (1 if companies else 0)
                })

            except Exception:
                continue

        # 按优先级和热度排序
        all_news.sort(key=lambda x: (x['priority'], x['score']), reverse=True)
        return all_news[:30]
    except Exception as e:
        print(f"  ❌ Hacker News 抓取失败: {e}")
        return []


def fetch_reddit_tech():
    """抓取 Reddit 科技板块"""
    print("📡 抓取 Reddit...")
    try:
        subreddits = ["technology", "artificial", "MachineLearning", "singularity"]
        all_posts = []

        for sub in subreddits:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=15"
                headers = {"User-Agent": "Mozilla/5.0 (compatible; hxxmacro/1.0)"}
                resp = requests.get(url, headers=headers, timeout=TIMEOUT)
                data = resp.json()

                for post in data['data']['children']:
                    p = post['data']
                    title = p['title']
                    title_lower = title.lower()
                    
                    is_ai = any(kw in title_lower for kw in AI_KEYWORDS)
                    companies = [g for g in TECH_GIANTS if g.lower() in title_lower]
                    
                    # 获取摘要
                    selftext = p.get('selftext', '')
                    summary = clean_text(selftext, 150) if selftext else ''

                    all_posts.append({
                        "title": title,
                        "url": p.get('url', ''),
                        "summary": summary,
                        "score": p['score'],
                        "comments": p['num_comments'],
                        "subreddit": sub,
                        "source": f"Reddit r/{sub}",
                        "link": f"https://reddit.com{p['permalink']}",
                        "is_ai": is_ai,
                        "companies": companies
                    })
            except Exception:
                continue

        return all_posts[:20]
    except Exception as e:
        print(f"  ❌ Reddit 抓取失败: {e}")
        return []


def fetch_google_news_rss():
    """通过 Google News RSS 获取科技巨头新闻"""
    print("📡 抓取 Google News RSS...")
    all_news = []
    seen_titles = set()

    search_terms = [
        "Apple technology news",
        "Google AI Cloud",
        "Microsoft AI Azure",
        "Amazon AWS technology",
        "Meta AI Facebook",
        "Tesla Elon Musk",
        "NVIDIA AI chip",
        "OpenAI ChatGPT",
        "artificial intelligence breakthrough",
        "tech industry news"
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

            for entry in items[:8]:
                title = entry.get('title', '')
                # 去重
                title_key = title[:40].lower()
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

                # 清理标题
                clean_title = re.sub(r'\s*-\s*[^-]+$', '', title)
                company = term.split()[0]
                
                # 获取摘要
                desc = entry.get('description', '')
                summary = clean_text(desc, 150)

                all_news.append({
                    "title": clean_title,
                    "url": entry.get('link', ''),
                    "summary": summary,
                    "published": entry.get('published', ''),
                    "company": company,
                    "source": "Google News",
                    "companies": [company] if company in TECH_GIANTS else [],
                    "is_ai": 'ai' in term.lower() or 'intelligence' in term.lower()
                })
        except Exception:
            continue

    return all_news[:30]


def fetch_techcrunch():
    """抓取 TechCrunch RSS"""
    print("📡 抓取 TechCrunch...")
    try:
        url = "https://techcrunch.com/feed/"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; hxxmacro/1.0)"}
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        items = parse_rss_feed(resp.content)

        articles = []
        for entry in items[:25]:
            title = entry.get('title', '')
            title_lower = title.lower()

            companies = [g for g in TECH_GIANTS if g.lower() in title_lower]
            is_ai = any(kw in title_lower for kw in AI_KEYWORDS)
            
            # 获取摘要
            desc = entry.get('description', '')
            summary = clean_text(desc, 150)

            articles.append({
                "title": title,
                "url": entry.get('link', ''),
                "summary": summary,
                "published": entry.get('published', ''),
                "companies": companies if companies else None,
                "is_ai": is_ai,
                "source": "TechCrunch"
            })

        return articles
    except Exception as e:
        print(f"  ❌ TechCrunch 抓取失败: {e}")
        return []


def fetch_the_verge():
    """抓取 The Verge RSS"""
    print("📡 抓取 The Verge...")
    try:
        url = "https://www.theverge.com/rss/index.xml"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; hxxmacro/1.0)"}
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        items = parse_rss_feed(resp.content)

        articles = []
        for entry in items[:20]:
            title = entry.get('title', '')
            title_lower = title.lower()

            companies = [g for g in TECH_GIANTS if g.lower() in title_lower]
            is_ai = any(kw in title_lower for kw in AI_KEYWORDS)
            
            desc = entry.get('description', '')
            summary = clean_text(desc, 150)

            articles.append({
                "title": title,
                "url": entry.get('link', ''),
                "summary": summary,
                "published": entry.get('published', ''),
                "companies": companies if companies else None,
                "is_ai": is_ai,
                "source": "The Verge"
            })

        return articles
    except Exception as e:
        print(f"  ❌ The Verge 抓取失败: {e}")
        return []


def fetch_github_ai():
    """GitHub AI 开源项目"""
    print("📡 抓取 GitHub AI 项目...")
    try:
        queries = [
            "ai OR machine-learning language:python",
            "llm OR gpt OR chatbot language:python",
            "artificial-intelligence OR deep-learning language:python"
        ]

        all_repos = []
        seen = set()

        for query in queries:
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=15"
            resp = requests.get(url, timeout=TIMEOUT)
            data = resp.json()

            for item in data.get('items', []):
                full_name = item['full_name']
                if full_name in seen:
                    continue
                seen.add(full_name)

                all_repos.append({
                    "title": item['name'],
                    "name": full_name,
                    "url": item['html_url'],
                    "summary": (item.get('description') or '暂无描述')[:150],
                    "stars": item['stargazers_count'],
                    "language": item.get('language', ''),
                    "forks": item['forks_count'],
                    "source": "GitHub"
                })

        return all_repos[:10]
    except Exception as e:
        print(f"  ❌ GitHub 抓取失败: {e}")
        return []


def generate_brief(all_news, output_dir):
    """生成可直接使用的简报（英文版和中文版）"""
    timestamp = datetime.now()
    date_str = timestamp.strftime('%Y-%m-%d')
    time_str = timestamp.strftime('%H:%M')

    # 合并所有新闻，去重
    seen_titles = set()
    unique_news = []
    for news in all_news:
        title_key = news['title'][:30].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(news)

    # 排序：AI相关优先，然后按热度
    def get_priority(n):
        score = 0
        if n.get('is_ai'):
            score += 100
        if n.get('companies'):
            score += 50
        return -score, -n.get('score', 0)

    unique_news.sort(key=get_priority)

    # 取前30条
    top_news = unique_news[:30]

    # ========== 翻译新闻 ==========
    print("🌐 翻译新闻为中文...")
    translated_news = []
    for i, news in enumerate(top_news):
        print(f"  翻译 {i+1}/{len(top_news)}...", end='\r')
        translated = news.copy()
        translated['title_zh'] = translate_text(news['title'])
        translated['summary_zh'] = translate_text(news.get('summary', ''))
        translated_news.append(translated)
        time.sleep(0.3)  # 避免API限流
    print(f"  翻译完成！{' ' * 20}")

    # JSON 输出
    json_path = f"{output_dir}/ai_tech_news_{date_str.replace('-', '')}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "generated": timestamp.isoformat(),
            "total": len(top_news),
            "news": translated_news
        }, f, ensure_ascii=False, indent=2)

    # ========== 英文版 Markdown ==========
    md_path = f"{output_dir}/ai_tech_news_latest.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# 🤖 AI 与科技新闻简报 (英文版)\n")
        f.write(f"> 日期：{date_str} | 更新时间：{time_str} UTC | 共 {len(top_news)} 条\n\n")
        f.write("---\n\n")

        # === AI 前沿 ===
        f.write("## 📰 AI 前沿动态\n\n")
        ai_count = 0
        for news in top_news:
            if news.get('is_ai') and ai_count < 10:
                ai_count += 1
                f.write(f"### {ai_count}. {news['title']}\n\n")
                if news.get('summary'):
                    f.write(f"**摘要**：{news['summary']}\n\n")
                f.write(f"**来源**：{news['source']}")
                if news.get('score'):
                    f.write(f" | 热度：{news['score']}")
                f.write("\n\n")
                if news.get('url'):
                    f.write(f"🔗 [阅读原文]({news['url']})")
                if news.get('hn_link'):
                    f.write(f" | [HN讨论]({news['hn_link']})")
                f.write("\n\n---\n\n")

        # === 科技巨头 ===
        f.write("## 🏢 科技巨头动态\n\n")
        
        company_news = {}
        for news in top_news:
            companies = news.get('companies') or []
            if not companies and news.get('company'):
                companies = [news['company']]
            for company in companies:
                if company in TECH_GIANTS:
                    if company not in company_news:
                        company_news[company] = []
                    company_news[company].append(news)

        count = 0
        for company in TECH_GIANTS:
            if company not in company_news:
                continue
            for news in company_news[company][:3]:
                count += 1
                if count > 15:
                    break
                f.write(f"### {count}. {news['title']}\n\n")
                f.write(f"**公司**：{company}\n\n")
                if news.get('summary'):
                    f.write(f"**摘要**：{news['summary']}\n\n")
                f.write(f"**来源**：{news['source']}\n\n")
                if news.get('url'):
                    f.write(f"🔗 [阅读原文]({news['url']})\n\n")
                f.write("---\n\n")
            if count > 15:
                break

        # === 科技要闻 ===
        f.write("## 📱 科技要闻\n\n")
        tech_count = 0
        for news in top_news:
            if not news.get('is_ai') and not news.get('companies'):
                tech_count += 1
                if tech_count > 8:
                    break
                f.write(f"### {tech_count}. {news['title']}\n\n")
                if news.get('summary'):
                    f.write(f"**摘要**：{news['summary']}\n\n")
                f.write(f"**来源**：{news['source']}")
                if news.get('score'):
                    f.write(f" | 热度：{news['score']}")
                f.write("\n\n")
                if news.get('url'):
                    f.write(f"🔗 [阅读原文]({news['url']})\n\n")
                f.write("---\n\n")

        f.write("\n---\n\n")
        f.write("*数据来源：Hacker News + Reddit + Google News + TechCrunch + The Verge*\n")

    # ========== 中文版 Markdown ==========
    md_zh_path = f"{output_dir}/ai_tech_news_latest_zh.md"
    with open(md_zh_path, 'w', encoding='utf-8') as f:
        f.write(f"# 🤖 AI 与科技新闻简报\n")
        f.write(f"> 日期：{date_str} | 更新时间：{time_str} UTC | 共 {len(top_news)} 条\n\n")
        f.write("---\n\n")

        # === AI 前沿 ===
        f.write("## 📰 AI 前沿动态\n\n")
        ai_count = 0
        for news in translated_news:
            if news.get('is_ai') and ai_count < 10:
                ai_count += 1
                f.write(f"### {ai_count}. {news['title_zh']}\n\n")
                f.write(f"*原文：{news['title']}*\n\n")
                if news.get('summary_zh'):
                    f.write(f"**摘要**：{news['summary_zh']}\n\n")
                f.write(f"**来源**：{news['source']}")
                if news.get('score'):
                    f.write(f" | 热度：{news['score']}")
                f.write("\n\n")
                if news.get('url'):
                    f.write(f"🔗 [阅读原文]({news['url']})")
                if news.get('hn_link'):
                    f.write(f" | [HN讨论]({news['hn_link']})")
                f.write("\n\n---\n\n")

        # === 科技巨头 ===
        f.write("## 🏢 科技巨头动态\n\n")
        
        company_news = {}
        for news in translated_news:
            companies = news.get('companies') or []
            if not companies and news.get('company'):
                companies = [news['company']]
            for company in companies:
                if company in TECH_GIANTS:
                    if company not in company_news:
                        company_news[company] = []
                    company_news[company].append(news)

        count = 0
        for company in TECH_GIANTS:
            if company not in company_news:
                continue
            for news in company_news[company][:3]:
                count += 1
                if count > 15:
                    break
                f.write(f"### {count}. {news['title_zh']}\n\n")
                f.write(f"*原文：{news['title']}*\n\n")
                f.write(f"**公司**：{company}\n\n")
                if news.get('summary_zh'):
                    f.write(f"**摘要**：{news['summary_zh']}\n\n")
                f.write(f"**来源**：{news['source']}\n\n")
                if news.get('url'):
                    f.write(f"🔗 [阅读原文]({news['url']})\n\n")
                f.write("---\n\n")
            if count > 15:
                break

        # === 科技要闻 ===
        f.write("## 📱 科技要闻\n\n")
        tech_count = 0
        for news in translated_news:
            if not news.get('is_ai') and not news.get('companies'):
                tech_count += 1
                if tech_count > 8:
                    break
                f.write(f"### {tech_count}. {news['title_zh']}\n\n")
                f.write(f"*原文：{news['title']}*\n\n")
                if news.get('summary_zh'):
                    f.write(f"**摘要**：{news['summary_zh']}\n\n")
                f.write(f"**来源**：{news['source']}")
                if news.get('score'):
                    f.write(f" | 热度：{news['score']}")
                f.write("\n\n")
                if news.get('url'):
                    f.write(f"🔗 [阅读原文]({news['url']})\n\n")
                f.write("---\n\n")

        f.write("\n---\n\n")
        f.write("*数据来源：Hacker News + Reddit + Google News + TechCrunch + The Verge*\n")

    # ========== 英文版纯文本 ==========
    txt_path = f"{output_dir}/ai_tech_news_latest.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"AI 与科技新闻简报 (英文版) | {date_str}\n")
        f.write("=" * 50 + "\n\n")
        
        for i, news in enumerate(top_news, 1):
            f.write(f"【{i}】{news['title']}\n")
            if news.get('summary'):
                f.write(f"    摘要：{news['summary']}\n")
            f.write(f"    来源：{news['source']}")
            if news.get('companies'):
                f.write(f" | 相关公司：{', '.join(news['companies'])}")
            f.write("\n\n")

    # ========== 中文版纯文本 ==========
    txt_zh_path = f"{output_dir}/ai_tech_news_latest_zh.txt"
    with open(txt_zh_path, 'w', encoding='utf-8') as f:
        f.write(f"AI 与科技新闻简报 | {date_str}\n")
        f.write("=" * 50 + "\n\n")
        
        for i, news in enumerate(translated_news, 1):
            f.write(f"【{i}】{news['title_zh']}\n")
            f.write(f"    原文：{news['title']}\n")
            if news.get('summary_zh'):
                f.write(f"    摘要：{news['summary_zh']}\n")
            f.write(f"    来源：{news['source']}")
            if news.get('companies'):
                f.write(f" | 相关公司：{', '.join(news['companies'])}")
            f.write("\n\n")

    return json_path, md_path, md_zh_path, txt_path, txt_zh_path, len(top_news)


def main():
    print("=" * 50)
    print("🚀 AI 与科技新闻增强版抓取 v3")
    print("=" * 50)

    output_dir = "/home/work/workspace/hxxmacro/data/ai_tech"

    # 抓取各数据源
    hn_data = fetch_hackernews()
    reddit_data = fetch_reddit_tech()
    google_news = fetch_google_news_rss()
    techcrunch = fetch_techcrunch()
    verge = fetch_the_verge()

    # 合并所有新闻
    all_news = hn_data + reddit_data + google_news + techcrunch + verge

    # 生成简报
    json_path, md_path, md_zh_path, txt_path, txt_zh_path, total = generate_brief(all_news, output_dir)

    print("\n" + "=" * 50)
    print("✅ 抓取完成!")
    print(f"📄 JSON: {json_path}")
    print(f"📄 英文版 MD: {md_path}")
    print(f"📄 中文版 MD: {md_zh_path}")
    print(f"📄 英文版 TXT: {txt_path}")
    print(f"📄 中文版 TXT: {txt_zh_path}")
    print(f"\n📊 生成简报：{total} 条")
    print(f"   - Hacker News: {len(hn_data)} 条")
    print(f"   - Reddit: {len(reddit_data)} 条")
    print(f"   - Google News: {len(google_news)} 条")
    print(f"   - TechCrunch: {len(techcrunch)} 条")
    print(f"   - The Verge: {len(verge)} 条")


if __name__ == "__main__":
    main()
