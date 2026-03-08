#!/usr/bin/env python3
"""
直接解析微信公众号文章内容
使用web_fetch工具但通过系统调用
"""
import re
import json
import subprocess
from datetime import datetime

TIMEOUT = 10

def call_web_fetch(url):
    """通过命令行调用web_fetch工具"""
    import sys
    # 在OpenClaw环境中，web_fetch通常是可用的
    try:
        from web_fetch import web_fetch
        result = web_fetch(url=url, extractMode="markdown")
        return result
    except ImportError:
        # 尝试通过exec调用
        import os
        env = os.environ.copy()
        env['PYTHONPATH'] = '/usr/lib/node_modules/openclaw:' + env.get('PYTHONPATH', '')
        
        cmd = [
            sys.executable, '-c',
            f'''
from web_fetch import web_fetch
import json
result = web_fetch(url="{url}", extractMode="markdown")
print(json.dumps(result, ensure_ascii=False))
'''
        ]
        
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.PIPE, 
                                           timeout=TIMEOUT, env=env, text=True)
            return json.loads(output)
        except subprocess.CalledProcessError as e:
            print(f"命令行调用失败: {e}")
            print(f"stderr: {e.stderr[:200]}")
            return None
        except subprocess.TimeoutExpired:
            print(f"调用超时")
            return None

def extract_and_format(content, title):
    """提取并格式化内容"""
    # 清理内容
    lines = content.split('\n')
    cleaned = []
    
    in_content = False
    for line in lines:
        line = line.strip()
        
        # 跳过安全警告
        if 'SECURITY NOTICE' in line or 'EXTERNAL' in line:
            continue
        if line == '---' and not in_content:
            in_content = True
            continue
        if '<<<' in line:
            continue
        
        # 跳过微信特定内容
        skip_phrases = [
            '继续滑动看下一个',
            '向上滑动看下一个',
            '阅读原文',
            '关注我们',
            '分享收藏',
            '迦勒底Chaldean'
        ]
        
        if any(phrase in line for phrase in skip_phrases):
            continue
        
        if len(line) < 2:
            continue
            
        cleaned.append(line.lstrip())
    
    # 构建Markdown
    formatted = f"<div align='center'>\n\n# {title}\n\n</div>\n\n"
    
    for line in cleaned:
        if not line:
            formatted += '\n'
            continue
            
        # 判断是否为子标题
        line_len = len(line)
        has_special = any(char in line for char in ['｜', '|', '·', '、', '：', ':', '-', '—'])
        
        if line_len < 50 and has_special:
            formatted += f"\n<div align='center'>\n\n**{line}**\n\n</div>\n\n"
        else:
            formatted += f"{line}\n"
    
    return formatted.strip()

def main():
    url = "https://mp.weixin.qq.com/s/VdWX37PWxmA8IPsnWRPm2Q"
    
    print(f"正在解析: {url}")
    
    # 调用web_fetch
    result = call_web_fetch(url)
    
    if not result:
        print("❌ 无法获取文章内容")
        return False
    
    if result.get('status') != 200:
        print(f"❌ 获取失败: HTTP {result.get('status')}")
        return False
    
    # 提取标题
    raw_title = result.get('title', '')
    title_match = re.search(r'[^\n<]+', raw_title)
    title = title_match.group(0).strip() if title_match else "蒂姆周运｜隐秘的突破口"
    
    # 提取内容
    content = result.get('text', '')
    
    # 格式化
    formatted = extract_and_format(content, title)
    
    # 保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title[:30])
    filename = f"{safe_title}_{timestamp}.md"
    filepath = f"/home/work/hxxmacro/horoscope/{filename}"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(formatted)
    
    print(f"\n✅ 解析完成!")
    print(f"标题: {title}")
    print(f"文件: {filepath}")
    print(f"大小: {len(formatted)} 字符")
    
    # 预览
    print("\n📄 预览:")
    print("=" * 50)
    print(formatted[:400])
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)