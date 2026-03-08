#!/usr/bin/env python3
"""
简化的微信公众号解析器
直接从web_fetch结果提取和格式化内容
"""
import re
import json
from datetime import datetime

def clean_wechat_markdown(markdown_text, title):
    """清理从web_fetch获取的Markdown内容"""
    # 移除安全警告
    lines = markdown_text.split('\n')
    cleaned_lines = []
    
    in_content = False
    for line in lines:
        line = line.strip()
        
        # 跳过安全警告
        if 'SECURITY NOTICE' in line or 'EXTERNAL_UNTRUSTED_CONTENT' in line:
            continue
        if line == '---' and not in_content:
            in_content = True
            continue
        if '<<<' in line:
            continue
            
        # 清理微信特有的元素
        if any(word in line for word in [
            '继续滑动看下一个',
            '向上滑动看下一个', 
            '阅读原文',
            '关注我们',
            '分享收藏',
            '迦勒底Chaldean'
        ]):
            continue
            
        # 移除纯数字行和过短行
        if len(line) < 2 or line.isdigit():
            continue
            
        # 移除开头的空格
        line = line.lstrip()
        cleaned_lines.append(line)
    
    # 合并连续空行
    result_lines = []
    prev_empty = False
    for line in cleaned_lines:
        if not line:  # 空行
            if not prev_empty:
                result_lines.append('')
                prev_empty = True
        else:
            result_lines.append(line)
            prev_empty = False
    
    content = '\n'.join(result_lines).strip()
    
    # 格式化标题和内容
    formatted = f"<div align='center'>\n\n# {title}\n\n</div>\n\n"
    
    # 处理内容行
    content_lines = content.split('\n')
    for line in content_lines:
        if not line.strip():
            formatted += '\n'
            continue
            
        # 判断是否为子标题（短文本，可能包含特殊字符）
        line_len = len(line.strip())
        has_special = any(char in line for char in ['｜', '|', '·', '、', '：', ':', '-', '—'])
        
        if line_len < 50 and has_special and not line.startswith(('  ', '   ')):
            # 子标题居中
            formatted += f"\n<div align='center'>\n\n**{line.strip()}**\n\n</div>\n\n"
        else:
            # 普通段落，左对齐，不加空格
            formatted += f"{line.strip()}\n"
    
    return formatted.strip()

def main():
    """主函数"""
    # 导入web_fetch（假设在OpenClaw环境中可用）
    try:
        from web_fetch import web_fetch
    except ImportError:
        print("错误: 无法导入web_fetch工具")
        return False
    
    url = "https://mp.weixin.qq.com/s/VdWX37PWxmA8IPsnWRPm2Q"
    
    print(f"正在解析微信公众号文章...")
    print(f"URL: {url}")
    
    # 获取内容
    result = web_fetch(url=url, extractMode="markdown")
    
    if result.get('status') != 200:
        print(f"获取失败: {result.get('error', '未知错误')}")
        return False
    
    # 提取标题
    raw_title = result.get('title', '')
    # 清理标题
    title_match = re.search(r'蒂姆周运[｜|].+', raw_title)
    title = title_match.group(0) if title_match else "蒂姆周运｜隐秘的突破口"
    title = title.replace('<<<EXTERNAL_UNTRUSTED_CONTENT>>>', '').strip()
    
    # 清理内容
    raw_content = result.get('text', '')
    formatted_content = clean_wechat_markdown(raw_content, title)
    
    # 保存文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title[:50])
    filename = f"wechat_{safe_title}_{timestamp}.md"
    filepath = f"/home/work/hxxmacro/horoscope/{filename}"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(formatted_content)
    
    print(f"\n✅ 解析完成!")
    print(f"标题: {title}")
    print(f"保存位置: {filepath}")
    print(f"文件大小: {len(formatted_content)} 字符")
    
    # 显示预览
    print("\n📄 内容预览（前300字符）:")
    print("=" * 50)
    print(formatted_content[:300])
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)