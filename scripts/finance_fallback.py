#!/usr/bin/env python3
"""
财经数据回退方案：使用无需API的公开数据源
"""
import requests
import json
from datetime import datetime

TIMEOUT = 5

def fetch_marketwatch():
    """从 MarketWatch 获取指数数据"""
    try:
        # MarketWatch 市场数据页面（无需API密钥）
        url = "https://www.marketwatch.com/investing/index/djia"
        resp = requests.get(url, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            # 简化：提取页面中的关键数字
            import re
            text = resp.text
            
            # 查找价格模式
            price_match = re.search(r'data-last-price="([0-9.,]+)"', text)
            price = price_match.group(1) if price_match else None
            
            change_match = re.search(r'data-net-change="([-0-9.,]+)"', text)
            change = change_match.group(1) if change_match else None
            
            if price:
                return [{
                    'name': '道琼斯指数',
                    'symbol': 'DJIA',
                    'price': price,
                    'change': change or 'N/A',
                    'source': 'MarketWatch',
                    'url': url,
                    'timestamp': datetime.now().isoformat()
                }]
    except Exception as e:
        print(f"MarketWatch 抓取失败: {e}")
    return []

def fetch_coinbase_btc():
    """从 Coinbase 获取比特币价格（公开API）"""
    try:
        url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
        resp = requests.get(url, timeout=TIMEOUT)
        data = resp.json()
        
        if 'data' in data:
            return {
                'name': '比特币 (BTC)',
                'price': data['data']['amount'],
                'currency': 'USD',
                'source': 'Coinbase',
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"比特币价格抓取失败: {e}")
    return None

def fetch_public_apis():
    """测试多个公开API"""
    results = {}
    
    # 1. CoinGecko（加密货币）
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            results['bitcoin'] = {
                'price': data['bitcoin']['usd'],
                'source': 'CoinGecko'
            }
    except:
        pass
    
    # 2. 汇率API（备用）
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            results['forex'] = {
                'USDCNY': data['rates']['CNY'],
                'source': 'ExchangeRate-API'
            }
    except:
        pass
    
    return results

def main():
    print("=== 财经数据回退方案测试 ===")
    
    all_data = {'meta': {'generated_at': datetime.now().isoformat(), 'note': '回退方案数据'}}
    
    # 测试公开API
    print("1. 测试公开API...")
    api_data = fetch_public_apis()
    all_data['api_results'] = api_data
    
    if api_data:
        print(f"   成功获取 {len(api_data)} 个数据点")
        for key, val in api_data.items():
            print(f"   {key}: {val.get('price', 'N/A')}")
    
    # 比特币价格
    print("\n2. 获取比特币价格...")
    btc = fetch_coinbase_btc()
    if btc:
        all_data['crypto'] = btc
        print(f"   ✅ 比特币: ${btc['price']}")
    else:
        print("   ❌ 比特币数据不可用")
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    json_path = f"/home/work/hxxworkspace/data/finance_fallback_{timestamp}.json"
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2)
    
    print(f"\n✅ 数据已保存: {json_path}")
    
    # 显示内容
    print("\n📊 数据内容:")
    print(json.dumps(all_data, indent=2, ensure_ascii=False))
    
    return True

if __name__ == "__main__":
    main()