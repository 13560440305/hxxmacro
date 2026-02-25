#!/usr/bin/env python3
"""
财经与投资理财数据抓取脚本
第一阶段：抓取美股指数（东方财富）
"""
import requests
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

TIMEOUT = 8
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}

def fetch_us_indices():
    """抓取美股三大指数（东方财富）"""
    indices = [
        ('道琼斯', 'DJI', 'https://quote.eastmoney.com/us/DJI.html'),
        ('纳斯达克', 'IXIC', 'https://quote.eastmoney.com/us/IXIC.html'),
        ('标普500', 'INX', 'https://quote.eastmoney.com/us/INX.html'),
    ]
    
    results = []
    for name, code, url in indices:
        try:
            print(f"正在抓取 {name} ({code})...")
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 提取价格 - 多个可能的CSS选择器
            price_sel = [
                '.stock-quote-wrap .price',
                '#gt6_1',
                '.price'  # 通用选择器
            ]
            
            price = None
            for sel in price_sel:
                elem = soup.select_one(sel)
                if elem and elem.text.strip():
                    price = elem.text.strip()
                    break
            
            # 提取涨跌幅
            change_sel = [
                '.stock-quote-wrap .change',
                '#gt7_1',
                '.change'
            ]
            
            change = None
            for sel in change_sel:
                elem = soup.select_one(sel)
                if elem and elem.text.strip():
                    change = elem.text.strip()
                    break
            
            # 提取涨跌额
            change_amount = None
            if change and '/' in change:
                change_amount = change.split('/')[0].strip()
                change = change.split('/')[1].strip() if len(change.split('/')) > 1 else change
            
            results.append({
                'name': name,
                'code': code,
                'price': price or 'N/A',
                'change': change or 'N/A',
                'change_amount': change_amount or 'N/A',
                'url': url,
                'source': '东方财富',
                'timestamp': datetime.now().isoformat()
            })
            print(f"  {name}: {price} {change if change else ''}")
            
        except Exception as e:
            print(f"  ❌ {name} 抓取失败: {e}")
            results.append({
                'name': name,
                'code': code,
                'price': '抓取失败',
                'change': 'N/A',
                'change_amount': 'N/A',
                'url': url,
                'source': '东方财富',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
        
        # 礼貌延迟
        import time
        time.sleep(1)
    
    return results

def fetch_gold_price():
    """抓取黄金价格（新浪财经）"""
    url = "https://finance.sina.com.cn/nmetal/"
    try:
        print("正在抓取黄金价格...")
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 尝试多种选择器
        gold_selectors = [
            '.hq_box .hq_title',  # 常见结构
            '.price',
            '#goldPrice',
            '[id*="gold"]',
            '[class*="gold"]'
        ]
        
        gold_price = 'N/A'
        for sel in gold_selectors:
            elem = soup.select_one(sel)
            if elem and any(char.isdigit() for char in elem.text):
                gold_price = elem.text.strip()[:20]
                break
        
        # 如果选择器失败，尝试正则匹配
        if gold_price == 'N/A':
            gold_match = re.search(r'[0-9,]+\.[0-9]+', resp.text)
            if gold_match:
                gold_price = gold_match.group()
        
        return {
            'name': '黄金现货',
            'price': gold_price,
            'url': url,
            'source': '新浪财经',
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"  ❌ 黄金价格抓取失败: {e}")
        return {
            'name': '黄金现货',
            'price': '抓取失败',
            'url': url,
            'source': '新浪财经',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

def save_results(data, filename=None):
    """保存结果到文件"""
    if filename is None:
        filename = f"finance_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    
    filepath = f"/home/work/hxxworkspace/data/{filename}"
    
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown简报
    md_file = filepath.replace('.json', '.md')
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# 财经数据简报\n")
        f.write(f"> 抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if 'us_indices' in data:
            f.write("## 📈 美股指数\n\n")
            for idx in data['us_indices']:
                f.write(f"### {idx['name']} ({idx['code']})\n")
                f.write(f"- **价格**: {idx['price']}\n")
                if idx['change'] != 'N/A':
                    f.write(f"- **涨跌幅**: {idx['change']}\n")
                if idx['change_amount'] != 'N/A':
                    f.write(f"- **涨跌额**: {idx['change_amount']}\n")
                f.write(f"- **来源**: {idx['source']} | [查看详情]({idx['url']})\n\n")
        
        if 'gold' in data:
            f.write("## 🥇 黄金价格\n\n")
            f.write(f"- **品种**: {data['gold']['name']}\n")
            f.write(f"- **价格**: {data['gold']['price']}\n")
            f.write(f"- **来源**: {data['gold']['source']} | [查看详情]({data['gold']['url']})\n\n")
        
        f.write("---\n*数据来源: 东方财富、新浪财经*")
    
    return filepath, md_file

def main():
    print(f"=== 财经数据抓取开始 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_data = {
        'meta': {
            'generated_at': datetime.now().isoformat(),
            'source': '财经抓取脚本 v1.0'
        }
    }
    
    # 抓取美股指数
    us_indices = fetch_us_indices()
    all_data['us_indices'] = us_indices
    
    # 抓取黄金价格
    gold = fetch_gold_price()
    all_data['gold'] = gold
    
    # 保存结果
    json_path, md_path = save_results(all_data)
    
    # 输出摘要
    print(f"\n✅ 抓取完成:")
    print(f"   美股指数: {len([i for i in us_indices if i['price'] != '抓取失败'])}/{len(us_indices)} 条成功")
    print(f"   黄金价格: {'成功' if gold['price'] != '抓取失败' else '失败'}")
    print(f"   JSON文件: {json_path}")
    print(f"   简报文件: {md_path}")
    
    # 显示关键数据
    print(f"\n📊 关键数据预览:")
    for idx in us_indices:
        if idx['price'] != '抓取失败':
            print(f"   {idx['name']}: {idx['price']} {idx['change'] if idx['change'] != 'N/A' else ''}")
    if gold['price'] != '抓取失败':
        print(f"   黄金: {gold['price']}")
    
    return True

if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)