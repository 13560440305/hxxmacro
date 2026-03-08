#!/usr/bin/env python3
"""
A股数据抓取脚本
数据源：新浪财经 A股指数
"""
import requests
import json
import re
from datetime import datetime

TIMEOUT = 6
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}

def fetch_a_stock_indices():
    """抓取A股主要指数"""
    indices = [
        ('上证指数', '000001', 'https://hq.sinajs.cn/list=sh000001'),
        ('深证成指', '399001', 'https://hq.sinajs.cn/list=sz399001'),
        ('创业板指', '399006', 'https://hq.sinajs.cn/list=sz399006'),
        ('科创50', '000688', 'https://hq.sinajs.cn/list=sh000688'),
    ]
    
    results = []
    for name, code, url in indices:
        try:
            print(f"正在抓取 {name}...")
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            
            if resp.status_code == 200:
                # 新浪财经返回的数据格式：var hq_str_sh000001="上证指数,3275.123,3268.456,...";
                content = resp.text
                
                # 提取数据部分
                match = re.search(r'="([^"]+)"', content)
                if match:
                    data_str = match.group(1)
                    parts = data_str.split(',')
                    
                    if len(parts) >= 3:
                        # 解析数据
                        current_price = parts[1]  # 当前价
                        prev_close = parts[2]     # 昨收
                        
                        if current_price and prev_close:
                            try:
                                current = float(current_price)
                                prev = float(prev_close)
                                change = current - prev
                                change_percent = (change / prev) * 100
                                
                                results.append({
                                    'name': name,
                                    'code': code,
                                    'current': round(current, 2),
                                    'prev_close': round(prev, 2),
                                    'change': round(change, 2),
                                    'change_percent': round(change_percent, 2),
                                    'source': '新浪财经',
                                    'url': f'https://finance.sina.com.cn/realstock/company/{code}/nc.shtml',
                                    'timestamp': datetime.now().isoformat()
                                })
                                print(f"  ✅ {name}: {current} ({change_percent:+.2f}%)")
                                continue
                            except ValueError:
                                pass
                
                # 如果正则解析失败，尝试其他方式
                results.append({
                    'name': name,
                    'code': code,
                    'raw_data': content[:100],
                    'source': '新浪财经',
                    'timestamp': datetime.now().isoformat(),
                    'status': '解析成功但格式异常'
                })
                print(f"  ⚠️  {name}: 数据格式异常")
                
            else:
                print(f"  ❌ {name}: HTTP {resp.status_code}")
                
        except Exception as e:
            print(f"  ❌ {name} 抓取失败: {e}")
            results.append({
                'name': name,
                'code': code,
                'error': str(e),
                'source': '新浪财经',
                'timestamp': datetime.now().isoformat()
            })
    
    return results

def fetch_popular_a_stocks():
    """抓取热门A股股票"""
    stocks = [
        ('贵州茅台', '600519'),
        ('宁德时代', '300750'),
        ('招商银行', '600036'),
        ('中国平安', '601318'),
        ('五粮液', '000858'),
    ]
    
    results = []
    for name, code in stocks:
        try:
            # 构建URL（沪市sh，深市sz）
            market = 'sh' if code.startswith('6') else 'sz'
            url = f"https://hq.sinajs.cn/list={market}{code}"
            
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            
            if resp.status_code == 200:
                content = resp.text
                match = re.search(r'="([^"]+)"', content)
                
                if match:
                    data_str = match.group(1)
                    parts = data_str.split(',')
                    
                    if len(parts) >= 3:
                        current_price = parts[3]  # 股票当前价在位置3
                        prev_close = parts[2]     # 昨收
                        
                        if current_price and prev_close:
                            try:
                                current = float(current_price)
                                prev = float(prev_close)
                                change = current - prev
                                change_percent = (change / prev) * 100
                                
                                results.append({
                                    'name': name,
                                    'code': code,
                                    'current': round(current, 2),
                                    'change_percent': round(change_percent, 2),
                                    'source': '新浪财经',
                                    'timestamp': datetime.now().isoformat()
                                })
                                print(f"  ✅ {name}: {current} ({change_percent:+.2f}%)")
                                continue
                            except ValueError:
                                pass
                
                results.append({
                    'name': name,
                    'code': code,
                    'raw_preview': content[:80],
                    'source': '新浪财经',
                    'timestamp': datetime.now().isoformat(),
                    'status': '数据已获取但需解析'
                })
                
        except Exception as e:
            print(f"  ❌ {name} 抓取失败: {e}")
    
    return results

def main():
    print("=== A股数据抓取测试 ===")
    print(f"时间: {datetime.now().strftime('%H:%M:%S')}\n")
    
    all_data = {'meta': {'generated_at': datetime.now().isoformat()}}
    
    # 抓取A股指数
    print("1. 抓取A股指数...")
    indices = fetch_a_stock_indices()
    all_data['indices'] = indices
    
    # 抓取热门个股
    print("\n2. 抓取热门个股...")
    stocks = fetch_popular_a_stocks()
    all_data['stocks'] = stocks
    
    # 统计
    success_indices = len([i for i in indices if 'current' in i])
    success_stocks = len([s for s in stocks if 'current' in s])
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    json_path = f"/home/work/hxxworkspace/data/a_stock_{timestamp}.json"
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 抓取完成:")
    print(f"   指数: {success_indices}/{len(indices)} 成功")
    print(f"   个股: {success_stocks}/{len(stocks)} 成功")
    print(f"   文件: {json_path}")
    
    # 显示关键数据
    if success_indices > 0:
        print("\n📈 A股指数概览:")
        for idx in indices:
            if 'current' in idx:
                print(f"   {idx['name']}: {idx['current']} ({idx['change_percent']:+.2f}%)")
    
    return success_indices > 0 or success_stocks > 0

if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)