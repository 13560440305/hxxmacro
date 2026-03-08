#!/usr/bin/env python3
"""
星座周运标准化清理脚本 V2
修复文件名特殊字符问题
"""
import requests
import re
import sys
import os
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path

TIMEOUT = 10
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}

class HoroscopeParserV2:
    def __init__(self, url):
        self.url = url
        self.html = None
        self.soup = None
        self.title = ""
        self.clean_title = ""
        self.date_range = ""
        self.content = ""
        
    def fetch_article(self):
        """获取微信公众号文章HTML"""
        try:
            resp = requests.get(self.url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            self.html = resp.text
            self.soup = BeautifulSoup(self.html, 'html.parser')
            return True
        except Exception as e:
            print(f"❌ 获取文章失败: {e}")
            return False
    
    def extract_title(self):
        """提取并清理标题"""
        # 从meta标签获取
        og_title = self.soup.find('meta', property='og:title')
        if og_title:
            self.title = og_title.get('content', '').strip()
        else:
            # 从title标签获取
            title_tag = self.soup.find('title')
            if title_tag:
                self.title = title_tag.text.strip()
        
        # 清理标题中的特殊字符和空格
        self.title = re.sub(r'<<<.*?>>>', '', self.title)
        self.title = self.title.replace('\n', ' ').strip()
        
        # 如果没有标题，使用默认
        if not self.title:
            self.title = "蒂姆周运"
        
        # 生成清理后的标题（用于文件名）
        self.clean_title = self.clean_filename(self.title)
        
        return self.title, self.clean_title
    
    def clean_filename(self, text):
        """清理文件名中的特殊字符和空格"""
        # 定义需要移除的特殊字符
        special_chars = r'[\\/*?:"<>|]'
        
        # 移除特殊字符
        cleaned = re.sub(special_chars, '', text)
        
        # 替换中文标点符号
        chinese_punctuation = r'[，。！？、；：（）【】《》『』「」·]'
        cleaned = re.sub(chinese_punctuation, '-', cleaned)
        
        # 替换其他特殊符号
        cleaned = cleaned.replace('｜', '-')
        cleaned = cleaned.replace('|', '-')
        cleaned = cleaned.replace(' ', '-')
        cleaned = cleaned.replace('  ', '-')
        
        # 移除连续多个连字符
        cleaned = re.sub(r'-+', '-', cleaned)
        
        # 移除首尾的连字符
        cleaned = cleaned.strip('-')
        
        return cleaned
    
    def extract_date_range(self):
        """提取日期范围"""
        patterns = [
            r'本周[：:]?\s*([0-9]+\.[0-9]+)\s*-\s*([0-9]+\.[0-9]+)',
            r'([0-9]+\.[0-9]+)\s*-\s*([0-9]+\.[0-9]+)',
            r'([0-9]+月[0-9]+日)\s*-\s*([0-9]+月[0-9]+日)',
            r'([0-9]{1,2}\.[0-9]{1,2})\s*[-~]\s*([0-9]{1,2}\.[0-9]{1,2})'
        ]
        
        text = self.soup.get_text()
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                start_date, end_date = match.groups()
                start_date = self.normalize_date(start_date)
                end_date = self.normalize_date(end_date)
                
                if start_date and end_date:
                    self.date_range = f"{start_date}-{end_date}"
                    return self.date_range
        
        # 如果没有找到，使用当前周
        today = datetime.now()
        start = today.strftime('%Y.%m.%d')
        end = (today.replace(day=today.day+6)).strftime('%Y.%m.%d')
        self.date_range = f"{start}-{end}"
        return self.date_range
    
    def normalize_date(self, date_str):
        """标准化日期格式"""
        # 移除中文
        date_str = re.sub(r'[年月日]', '.', date_str)
        
        # 处理不同格式
        parts = re.split(r'[\.\-]', date_str)
        
        if len(parts) == 2:  # 只有月和日
            month, day = parts
            year = datetime.now().year
            return f"{year}.{month.zfill(2)}.{day.zfill(2)}"
        elif len(parts) == 3:  # 年.月.日
            year, month, day = parts
            if len(year) == 2:  # 两位年份
                year = f"20{year}"
            return f"{year}.{month.zfill(2)}.{day.zfill(2)}"
        
        return date_str
    
    def extract_content(self):
        """提取并清理内容"""
        content_selectors = [
            '#js_content',
            '.rich_media_content',
            '.article-content',
            'div[class*="content"]'
        ]
        
        content_div = None
        for selector in content_selectors:
            elem = self.soup.select_one(selector)
            if elem:
                content_div = elem
                break
        
        if not content_div:
            content_div = self.soup.body or self.soup
        
        for elem in content_div.select('script, style, iframe, noscript, img, a'):
            elem.decompose()
        
        text = content_div.get_text(separator='\n', strip=True)
        
        lines = text.split('\n')
        cleaned_lines = []
        
        remove_keywords = [
            '继续滑动看下一个', '向上滑动看下一个', '阅读原文', '关注我们',
            '分享收藏', '迦勒底Chaldean', '点击图片查看', '可用作手帐',
            '原文：', '译者：', '转载文章中请务必注明', '禁止用于商业用途',
            '参考太阳&上升星座', '后台回复', '点歌请走这边', '晚安',
            '甩手掌柜时间', '月空时段避免开启新事务', '运势请参考',
            '序', '上周的满月', '本周你会发现', '但请注意水星',
            '周一晚上到周二黎明前', '从整体星象来看'
        ]
        
        for line in lines:
            line = line.strip()
            
            if any(keyword in line for keyword in remove_keywords):
                continue
            
            if len(line) < 2:
                continue
                
            if re.search(r'[0-9]+\.[0-9]+\s*-\s*[0-9]+\.[0-9]+', line):
                continue
                
            cleaned_lines.append(line)
        
        self.content = '\n'.join(cleaned_lines)
        return self.content
    
    def format_markdown(self):
        """格式化为标准化Markdown"""
        md = f"<div align='center'>\n\n# {self.title}\n\n</div>\n\n"
        
        if self.date_range:
            md += f"<div align='center'>\n\n**本周：{self.date_range}**\n\n</div>\n\n"
        
        lines = self.content.split('\n')
        
        for line in lines:
            if not line.strip():
                md += '\n'
                continue
                
            zodiac_signs = ['白羊座', '金牛座', '双子座', '巨蟹座', '狮子座', 
                          '处女座', '天秤座', '天蝎座', '射手座', '摩羯座', 
                          '水瓶座', '双鱼座']
            
            if any(sign in line for sign in zodiac_signs):
                md += f"\n\n<div align='center'>\n\n**{line}**\n\n</div>\n\n"
            else:
                md += f"{line}\n"
        
        return md.strip()
    
    def generate_filename(self):
        """生成标准化文件名（无特殊字符和空格）"""
        # 如果clean_title为空，重新清理
        if not self.clean_title:
            self.clean_title = self.clean_filename(self.title)
        
        # 从日期范围提取开始日期
        if '-' in self.date_range:
            start_date = self.date_range.split('-')[0]
        else:
            start_date = datetime.now().strftime('%Y.%m.%d')
        
        # 文件名格式：清理后的标题-日期范围.md
        filename = f"{self.clean_title}-{self.date_range}.md"
        
        # 最终检查，确保没有特殊字符
        filename = re.sub(r'[\\/*?:"<>|]', '', filename)
        filename = filename.replace(' ', '-')
        
        return filename
    
    def save_to_file(self, output_dir=None):
        """保存到文件"""
        if output_dir is None:
            output_dir = "/home/work/hxxmacro/horoscope"
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        filename = self.generate_filename()
        filepath = os.path.join(output_dir, filename)
        
        # 检查文件是否已存在
        if os.path.exists(filepath):
            print(f"⚠️  文件已存在: {filename}")
            # 添加时间戳
            timestamp = datetime.now().strftime('%H%M%S')
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            filepath = os.path.join(output_dir, filename)
        
        formatted = self.format_markdown()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(formatted)
        
        return filepath, len(formatted), filename

def main():
    if len(sys.argv) < 2:
        print("使用方法: python3 horoscope_clean_parser_v2.py <微信公众号URL> [输出目录]")
        print("示例: python3 horoscope_clean_parser_v2.py https://mp.weixin.qq.com/s/xxx")
        return 1
    
    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/home/work/hxxmacro/horoscope"
    
    print(f"🔍 开始处理: {url}")
    
    parser = HoroscopeParserV2(url)
    
    if not parser.fetch_article():
        return 1
    
    title, clean_title = parser.extract_title()
    date_range = parser.extract_date_range()
    parser.extract_content()
    
    print(f"  原始标题: {title}")
    print(f"  清理标题: {clean_title}")
    print(f"  日期范围: {date_range}")
    
    filepath, length, filename = parser.save_to_file(output_dir)
    
    print(f"\n✅ 处理完成!")
    print(f"  文件名: {filename}")
    print(f"  文件路径: {filepath}")
    print(f"  文件大小: {length} 字符")
    
    # 显示预览
    print(f"\n📄 预览:")
    print("=" * 60)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        for line in lines[:15]:
            print(line[:80])
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())