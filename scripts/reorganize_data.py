#!/usr/bin/env python3
"""
重新组织数据目录结构
"""
import os
import shutil
from datetime import datetime

BASE_DIR = "/home/work/hxxworkspace/data"

# 创建分类目录
categories = {
    'ai_tech': ['ai_news_', 'tech_news', 'ai_combined'],
    'finance_a_stock': ['a_stock', 'finance_data', 'finance_api'],
    'gov_economy': ['gov_stats', 'worldbank'],
    'finance_global': ['finance_final', 'finance_fallback'],
    'temp': ['test_output', 'real_test', 'real_time']
}

# 确保目录存在
for category in categories.keys():
    os.makedirs(os.path.join(BASE_DIR, category), exist_ok=True)

def move_files():
    moved = {cat: 0 for cat in categories.keys()}
    
    for filename in os.listdir(BASE_DIR):
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.isfile(filepath):
            # 查找匹配的类别
            moved_flag = False
            for category, prefixes in categories.items():
                for prefix in prefixes:
                    if filename.startswith(prefix):
                        dest = os.path.join(BASE_DIR, category, filename)
                        shutil.move(filepath, dest)
                        moved[category] += 1
                        moved_flag = True
                        break
                if moved_flag:
                    break
            
            # 按扩展名分类未匹配的文件
            if not moved_flag:
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.json', '.md', '.txt']:
                    # 检查内容决定分类
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read(500).lower()
                        
                        if 'hacker' in content or 'ai' in content or 'github' in content:
                            dest = os.path.join(BASE_DIR, 'ai_tech', filename)
                        elif 'gdp' in content or 'cpi' in content or '统计局' in content:
                            dest = os.path.join(BASE_DIR, 'gov_economy', filename)
                        elif 'stock' in content or 'finance' in content or '指数' in content:
                            dest = os.path.join(BASE_DIR, 'finance_a_stock', filename)
                        else:
                            dest = os.path.join(BASE_DIR, 'temp', filename)
                        
                        shutil.move(filepath, dest)
                        moved['temp' if dest.endswith('temp/' + filename) else 
                              'ai_tech' if 'ai_tech' in dest else 
                              'gov_economy' if 'gov_economy' in dest else 
                              'finance_a_stock'] += 1
                    except:
                        dest = os.path.join(BASE_DIR, 'temp', filename)
                        shutil.move(filepath, dest)
                        moved['temp'] += 1
                else:
                    dest = os.path.join(BASE_DIR, 'temp', filename)
                    shutil.move(filepath, dest)
                    moved['temp'] += 1
    
    return moved

def print_structure():
    """打印目录结构"""
    print("\n📁 数据目录结构:")
    for root, dirs, files in os.walk(BASE_DIR):
        level = root.replace(BASE_DIR, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/") if level > 0 else print(f"{os.path.basename(root)}/")
        
        subindent = ' ' * 2 * (level + 1)
        for file in sorted(files)[:5]:  # 显示前5个文件
            print(f"{subindent}{file}")
        if len(files) > 5:
            print(f"{subindent}... 共 {len(files)} 个文件")
        if not files and dirs:
            print(f"{subindent}(空)")

def main():
    print("=== 重新组织数据目录 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 移动文件
    moved = move_files()
    
    # 打印结果
    print(f"\n📊 文件移动统计:")
    total = 0
    for category, count in moved.items():
        if count > 0:
            print(f"  {category}: {count} 个文件")
            total += count
    print(f"  总计: {total} 个文件")
    
    # 打印目录结构
    print_structure()
    
    print(f"\n✅ 数据目录重组完成!")
    print(f"   根目录: {BASE_DIR}")
    print(f"   类别: {len(categories)} 个")
    
    return True

if __name__ == "__main__":
    main()