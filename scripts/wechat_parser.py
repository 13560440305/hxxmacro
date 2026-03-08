#!/usr/bin/env python3
"""
微信公众号文章解析器
专门解析并格式化微信公众号文章
"""
import re
from bs4 import BeautifulSoup

def clean_wechat_content(html_content):
    """清理微信公众号文章HTML，提取纯净内容"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 提取标题 - 微信公众号标题通常在meta标签或h1/h2中
    title = ""
    title_meta = soup.find('meta', property='og:title')
    if title_meta:
        title = title_meta.get('content', '').strip()
    else:
        # 尝试从h1/h2中找
        h1 = soup.find('h1')
        if h1:
            title = h1.text.strip()
    
    # 清理微信特有的元素
    unwanted_selectors = [
        'script', 'style', 'iframe', 'noscript',
        '.qr_code', '.share', '.ad', 'img[src*="qlogo"]',
        '.author-info', '.copyright', '.related-articles',
        '.weui-msg__extra-area', '.weui-footer',
        'a[href*="mp.weixin.qq.com"]',
        'span[style*="display:none"]'
    ]
    
    for selector in unwanted_selectors:
        for elem in soup.select(selector):
            elem.decompose()
    
    # 提取主要内容区域
    content_selectors = [
        '#js_content',
        '.rich_media_content',
        '.article-content',
        'div[class*="content"]',
        'div[class*="article"]'
    ]
    
    main_content = None
    for selector in content_selectors:
        elem = soup.select_one(selector)
        if elem:
            main_content = elem
            break
    
    if not main_content:
        # 如果没有找到特定选择器，使用body内容
        main_content = soup.body or soup
    
    # 清理文本
    text = main_content.get_text(separator='\n', strip=True)
    
    # 进一步清理
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # 移除微信特有文字
        if any(word in line for word in ['继续滑动', '向上滑动', '阅读原文', '关注我们', '分享收藏']):
            continue
        # 移除纯数字行
        if line.isdigit():
            continue
        # 移除空行和过短行（可能是广告）
        if len(line) < 2:
            continue
        cleaned_lines.append(line)
    
    return title, '\n'.join(cleaned_lines)

def format_to_markdown(title, content):
    """将清理后的内容格式化为Markdown"""
    # 标题居中
    md_content = f"<div align='center'>\n\n# {title}\n\n</div>\n\n"
    
    lines = content.split('\n')
    for line in lines:
        # 判断是否为标题行（短文本且可能包含特殊字符）
        line_len = len(line.strip())
        
        # 可能是小标题的行（包含数字、点、冒号等）
        if line_len < 50 and any(char in line for char in ['、', '：', '｜', '|', '·']):
            # 小标题居中
            md_content += f"\n<div align='center'>\n\n**{line}**\n\n</div>\n\n"
        else:
            # 普通段落左对齐，移除开头空格
            cleaned_line = line.lstrip()
            # 确保段落之间有换行
            if md_content and not md_content.endswith('\n\n'):
                md_content += '\n'
            md_content += f"{cleaned_line}\n"
    
    return md_content.strip()

def parse_wechat_url(url):
    """主函数：解析微信公众号文章"""
    import requests
    from web_fetch import web_fetch
    
    try:
        # 使用web_fetch获取内容
        result = web_fetch(url=url, extractMode="markdown")
        
        if result.get('status') == 200:
            # 获取原始HTML内容
            resp = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if resp.status_code == 200:
                title, cleaned_content = clean_wechat_content(resp.text)
                
                # 如果标题为空，使用web_fetch的标题
                if not title:
                    title = result.get('title', '').replace('<<<EXTERNAL_UNTRUSTED_CONTENT>>>', '').strip()
                
                # 格式化
                md_content = format_to_markdown(title, cleaned_content)
                
                return {
                    'success': True,
                    'title': title,
                    'markdown': md_content,
                    'raw_length': len(resp.text),
                    'clean_length': len(cleaned_content)
                }
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
    return {'success': False, 'error': '解析失败'}

if __name__ == "__main__":
    # 测试代码
    url = "https://mp.weixin.qq.com/s/VdWX37PWxmA8IPsnWRPm2Q"
    result = parse_wechat_url(url)
    
    if result['success']:
        print(f"标题: {result['title']}")
        print(f"原始长度: {result['raw_length']}")
        print(f"清理后长度: {result['clean_length']}")
        print("\nMarkdown预览（前500字符）:")
        print(result['markdown'][:500])
    else:
        print(f"错误: {result['error']}")