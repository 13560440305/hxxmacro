#!/usr/bin/env python3
"""
财经数据抓取 v2 - 使用公开API与改进解析
"""
import requests
import json
from datetime import datetime

TIMEOUT = 6

def fetch_yahoo_indices():
    """使用 Yahoo Finance API 获取美股指数"""
    symbols = {
        '^DJI': '道琼斯工业平均指数',
        '^IXIC': '纳斯达克综合指数',
        '^GSPC': '标普500指数'
    }
    
    results = []
    for symbol, name in symbols.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            resp = requests.get(url, timeout=TIMEOUT)
            data = resp.json()
            
            chart = data.get('chart', {})
            result = chart.get('result', [{}])[0]
            meta = result.get('meta', {})
            
            price = meta.get('regularMarketPrice')
            prev_close = meta.get('previousClose')
            
            if price and prev_close:
                change = price - prev_close
                change_percent = (change / prev_close) * 100
                
                results.append({
                    'name': name,
                    'symbol': symbol,
                    'price': round(price, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2),
                    'currency': meta.get('currency', 'USD'),
                    'source': 'Yahoo Finance',
                    'timestamp': datetime.now().isoformat()
                })
                print(f"✅ {name}: ${price} ({change_percent:+.2f}%)")
            else:
                print(f"⚠️  {name}: 数据不完整")
                
        except Exception as e:
            print(f"❌ {name} 抓取失败: {e}")
            results.append({
                'name': name,
                'symbol': symbol,
                'error': str(e),
                'source': 'Yahoo Finance',
                'timestamp': datetime.now().isoformat()
            })
    
    return results

def fetch_forex_simple():
    """获取主要汇率（简单API）"""
    try:
        # FreeForexAPI（免费，无需密钥）
        url = "https://www.freeforexapi.com/api/live?pairs=USDCNY,EURUSD,USDJPY"
        resp = requests.get(url, timeout=TIMEOUT)
        data = resp.json()
        
        rates = []
        if data.get('rates'):
            for pair, info in data['rates'].items():
                rates.append({
                    'pair': pair,
                    'rate': info.get('rate'),
                    'timestamp': info.get('timestamp'),
                    'source': 'FreeForexAPI'
                })
            print(f"✅ 汇率数据: {len(rates)} 对")
        return rates
    except Exception as e:
        print(f"❌ 汇率抓取失败: {e}")
        return []

def save_results(data):
    """保存结果"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    json_path = f"/home/work/hxxworkspace/data/finance_api_{timestamp}.json"
    md_path = json_path.replace('.json', '.md')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 生成简报
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# 财经数据简报 (API版本)\n")
        f.write(f"> 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if 'indices' in data:
            f.write("## 📈 美股指数 (Yahoo Finance)\n\n")
            for idx in data['indices']:
                if 'price' in idx:
                    f.write(f"### {idx['name']} ({idx['symbol']})\n")
                    f.write(f"- **价格**: ${idx['price']} {idx['currency']}\n")
                    f.write(f"- **涨跌**: {idx['change']:+.2f} ({idx['change_percent']:+.2f}%)\n")
                    f.write(f"- **来源**: {idx['source']}\n\n")
        
        if 'forex' in data:
            f.write("## 💱 主要汇率\n\n")
            for fx in data['forex']:
                if 'rate' in fx:
                    f.write(f"- **{fx['pair']}**: {fx['rate']}\n")
            f.write(f"\n来源: {data['forex'][0]['source'] if data['forex'] else ''}\n\n")
        
        f.write("---\n*数据来源: Yahoo Finance + FreeForexAPI*")
    
    return json_path, md_path

def main():
    print("=== 财经数据抓取 v2 (API版本) ===")
    print(f"时间: {datetime.now().strftime('%H:%M:%S')}\n")
    
    all_data = {'meta': {'generated_at': datetime.now().isoformat()}}
    
    # 抓取美股指数
    print("1. 抓取美股指数...")
    indices = fetch_yahoo_indices()
    all_data['indices'] = indices
    
    # 抓取汇率
    print("\n2. 抓取汇率...")
    forex = fetch_forex_simple()
    all_data['forex'] = forex
    
    # 保存
    json_path, md_path = save_results(all_data)
    
    print(f"\n✅ 抓取完成:")
    print(f"   美股指数: {len([i for i in indices if 'price' in i])}/{len(indices)} 条")
    print(f"   汇率对: {len(forex)} 对")
    print(f"   JSON文件: {json_path}")
    print(f"   简报文件: {md_path}")
    
    return True

if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)