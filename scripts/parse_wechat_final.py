#!/usr/bin/env python3
"""
最终版：微信公众号文章解析器
使用requests直接获取并解析HTML
"""
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

TIMEOUT = 8
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}

def fetch_wechat_article(url):
    """直接获取微信公众号文章内容"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"获取文章失败: {e}")
        return None

def extract_content(html):
    """从HTML中提取标题和内容"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # 提取标题
    title = ""
    # 尝试从meta标签获取
    og_title = soup.find('meta', property='og:title')
    if og_title:
        title = og_title.get('content', '').strip()
    else:
        # 尝试从标题标签获取
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.text.strip()
    
    # 清理标题
    if '<<<' in title:
        title = re.sub(r'<<<.*?>>>', '', title)
    title = title.replace('\n', ' ').strip()
    
    # 提取主要内容
    content_selectors = [
        '#js_content',
        '.rich_media_content',
        '.article-content',
        'div[class*="content"]'
    ]
    
    content_div = None
    for selector in content_selectors:
        elem = soup.select_one(selector)
        if elem:
            content_div = elem
            break
    
    if not content_div:
        # 如果没有找到特定选择器，尝试获取body内容
        content_div = soup.body or soup
    
    # 清理不需要的元素
    for elem in content_div.select('script, style, iframe, noscript, img'):
        elem.decompose()
    
    # 获取纯文本
    text = content_div.get_text(separator='\n', strip=True)
    
    return title, text

def format_markdown(title, content):
    """格式化为Markdown"""
    # 主标题居中
    md = f"<div align='center'>\n\n# {title}\n\n</div>\n\n"
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            md += '\n'
            continue
            
        # 跳过微信特有内容
        skip_words = [
            '继续滑动看下一个',
            '向上滑动看下一个',
            '阅读原文',
            '关注我们',
            '分享收藏',
            '迦勒底Chaldean'
        ]
        
        if any(word in line for word in skip_words):
            continue
            
        # 过短的忽略
        if len(line) < 2:
            continue
            
        # 判断是否为子标题
        line_len = len(line)
        has_special = any(char in line for char in ['｜', '|', '·', '、', '：', ':', '-', '—', '○', '●', '▲', '►'])
        
        if line_len < 50 and has_special:
            # 子标题居中
            md += f"\n<div align='center'>\n\n**{line}**\n\n</div>\n\n"
        else:
            # 普通段落左对齐
            md += f"{line}\n"
    
    return md.strip()

def main():
    url = "https://mp.weixin.qq.com/s/VdWX37PWxmA8IPsnWRPm2Q"
    
    print(f"正在解析微信公众号文章...")
    print(f"URL: {url}")
    
    # 获取HTML
    html = fetch_wechat_article(url)
    if not html:
        return False
    
    # 提取内容
    title, content = extract_content(html)
    
    if not title:
        title = "蒂姆周运｜隐秘的突破口"
    
    print(f"标题: {title}")
    print(f"原始内容长度: {len(content)} 字符")
    
    # 格式化
    formatted = format_markdown(title, content)
    
    # 保存文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title[:30])
    filename = f"{safe_title}_{timestamp}.md"
    filepath = f"/home/work/hxxmacro/horoscope/{filename}"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(formatted)
    
    print(f"\n✅ 解析完成!")
    print(f"保存位置: {filepath}")
    print(f"格式化后长度: {len(formatted)} 字符")
    
    # 预览
    print("\n📄 内容预览:")
    print("=" * 60)
    preview = formatted[:500]
    lines = preview.split('\n')
    for line in lines[:20]:  # 只显示前20行
        print(line[:80])  # 限制每行宽度
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)