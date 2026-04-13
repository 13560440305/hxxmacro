#!/usr/bin/env python3
"""
国际金融数据抓取脚本 v3.0
数据源：美股、港股、黄金、外汇
针对新加坡服务器优化，使用国外数据源
"""
import requests
import json
import re
from datetime import datetime
import time
import os

# 配置
TIMEOUT = 15
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

DATA_DIR = "/home/work/workspace/hxxmacro/data"

# ============== Stooq 数据源 (波兰，国际可用) ==============

def fetch_from_stooq(symbol, name):
    """从 Stooq 获取金融数据"""
    try:
        url = f"https://stooq.com/q/?s={symbol}"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        
        # 提取价格数据
        # Stooq 页面中价格通常在表格中
        prices = re.findall(r'[0-9]{4,5}\.[0-9]{2}', resp.text)
        if prices:
            return {
                'name': name,
                'symbol': symbol,
                'price': prices[0],
                'source': 'Stooq',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    except Exception as e:
        print(f"   Stooq 错误 ({symbol}): {e}")
    return None


# ============== 美股数据 ==============

def fetch_us_stocks():
    """获取美股三大指数"""
    print("📈 正在抓取美股指数...")
    
    results = []
    
    # 使用 Stooq 数据源
    indices = [
        ('^dji', '道琼斯工业平均指数'),
        ('^spx', '标普500指数'),
        ('^ndq', '纳斯达克综合指数'),
    ]
    
    for symbol, name in indices:
        data = fetch_from_stooq(symbol, name)
        if data:
            results.append(data)
            print(f"   ✅ {name}: {data['price']}")
        else:
            # 尝试备用数据源: Yahoo Finance (通过 cors 代理)
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.replace('^', '%5E')}?interval=1d&range=1d"
                resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
                if resp.status_code == 200:
                    d = resp.json()
                    chart = d.get('chart', {}).get('result', [])
                    if chart:
                        meta = chart[0].get('meta', {})
                        price = meta.get('regularMarketPrice')
                        if price:
                            results.append({
                                'name': name,
                                'symbol': symbol,
                                'price': round(price, 2),
                                'source': 'Yahoo Finance',
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            print(f"   ✅ {name}: {price:.2f} (Yahoo)")
                            continue
            except Exception as e:
                pass
            print(f"   ⚠️  {name}: 数据获取失败")
            results.append({'name': name, 'symbol': symbol, 'error': '数据源不可用'})
        time.sleep(0.5)
    
    return results


# ============== 港股数据 ==============

def fetch_hk_stocks():
    """获取港股恒生指数"""
    print("\n📊 正在抓取港股数据...")
    
    # 使用 Stooq 数据源
    data = fetch_from_stooq('^hsi', '恒生指数')
    if data:
        print(f"   ✅ 恒生指数: {data['price']}")
        return [data]
    
    print("   ⚠️  恒生指数: 数据获取失败")
    return [{'name': '恒生指数', 'symbol': '^hsi', 'error': '数据源不可用'}]


# ============== 黄金数据 ==============

def fetch_gold_price():
    """获取黄金价格"""
    print("\n🥇 正在抓取黄金价格...")
    
    results = []
    
    # 方法1: 金价API (goldprice.org)
    try:
        url = "https://www.goldprice.org/ajax-gayjx.php?cure=USD"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            # 尝试解析 JSON
            try:
                data = resp.json()
                if isinstance(data, dict) and 'gold_bid_usd_oz' in data:
                    results.append({
                        'name': '黄金现货',
                        'code': 'XAU',
                        'price': data['gold_bid_usd_oz'],
                        'unit': '美元/盎司',
                        'source': 'GoldPrice.org',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    print(f"   ✅ 黄金现货: ${data['gold_bid_usd_oz']}/盎司")
                    return results
            except:
                pass
    except Exception as e:
        print(f"   ⚠️  GoldPrice: {e}")
    
    # 方法2: Stooq 黄金期货
    data = fetch_from_stooq('gc.f', '黄金期货')
    if data:
        # Stooq 的黄金期货价格可能是人民币/克
        data['unit'] = '期货价格'
        results.append(data)
        print(f"   ✅ 黄金期货: {data['price']}")
        return results
    
    # 方法3: 使用 Metal Price API
    try:
        url = "https://api.metalpriceapi.com/v1/latest?api_key=demo&base=USD&currencies=XAU"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            d = resp.json()
            if d.get('success') and 'rates' in d:
                # XAU 汇率是 1 USD = X XAU，所以需要取倒数
                xau_rate = d['rates'].get('XAU')
                if xau_rate:
                    gold_price = 1 / xau_rate
                    results.append({
                        'name': '黄金现货',
                        'code': 'XAU',
                        'price': round(gold_price, 2),
                        'unit': '美元/盎司',
                        'source': 'MetalPriceAPI',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    print(f"   ✅ 黄金现货: ${gold_price:.2f}/盎司")
                    return results
    except Exception as e:
        print(f"   ⚠️  MetalPriceAPI: {e}")
    
    if not results:
        results.append({'name': '黄金现货', 'code': 'XAU', 'error': '数据源不可用'})
        print("   ❌ 黄金价格获取失败")
    
    return results


# ============== 外汇数据 ==============

def fetch_forex_rates():
    """获取主要外汇汇率"""
    print("\n💱 正在抓取外汇汇率...")
    
    results = []
    
    # 方法1: ExchangeRate-API (可靠的国外数据源)
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            rates = data.get('rates', {})
            
            # 主要货币对
            pairs = [
                ('USDCNY', 'CNY', '美元/人民币'),
                ('USDHKD', 'HKD', '美元/港币'),
                ('USDEUR', 'EUR', '美元/欧元'),
                ('USDJPY', 'JPY', '美元/日元'),
                ('USDGBP', 'GBP', '美元/英镑'),
                ('USDAUD', 'AUD', '美元/澳元'),
                ('USDSGD', 'SGD', '美元/新加坡元'),
            ]
            
            for pair_code, currency, name in pairs:
                if currency in rates:
                    results.append({
                        'pair': pair_code,
                        'name': name,
                        'rate': round(rates[currency], 4),
                        'source': 'ExchangeRate-API',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            print(f"   ✅ 成功获取 {len(results)} 个汇率")
            return results
    except Exception as e:
        print(f"   ⚠️  ExchangeRate API: {e}")
    
    # 方法2: Open Exchange Rate (备用)
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            rates = data.get('rates', {})
            
            pairs = [
                ('USDCNY', 'CNY', '美元/人民币'),
                ('USDHKD', 'HKD', '美元/港币'),
                ('USDEUR', 'EUR', '美元/欧元'),
                ('USDJPY', 'JPY', '美元/日元'),
                ('USDSGD', 'SGD', '美元/新加坡元'),
            ]
            
            for pair_code, currency, name in pairs:
                if currency in rates:
                    results.append({
                        'pair': pair_code,
                        'name': name,
                        'rate': round(rates[currency], 4),
                        'source': 'Open Exchange Rate',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            print(f"   ✅ 备用API成功获取 {len(results)} 个汇率")
    except Exception as e:
        print(f"   ❌ 外汇数据获取失败: {e}")
    
    return results


# ============== 保存结果 ==============

def save_results(data):
    """保存抓取结果"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # 保存JSON
    json_path = f"{DATA_DIR}/intl_finance_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown简报
    md_path = json_path.replace('.json', '.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# 🌍 国际金融数据简报\n\n")
        f.write(f"> 抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
        f.write(f"> 服务器位置: 新加坡 | 数据源: Stooq、Yahoo Finance、ExchangeRate-API\n\n")
        
        # 美股
        if data.get('us_stocks'):
            f.write("## 📈 美股指数\n\n")
            f.write("| 指数 | 价格 | 来源 |\n")
            f.write("|------|------|------|\n")
            for item in data['us_stocks']:
                if 'price' in item and item.get('price') != 'N/A':
                    f.write(f"| {item['name']} | {item['price']} | {item.get('source', '')} |\n")
            f.write("\n")
        
        # 港股
        if data.get('hk_stocks'):
            f.write("## 📊 港股指数\n\n")
            f.write("| 指数 | 价格 | 来源 |\n")
            f.write("|------|------|------|\n")
            for item in data['hk_stocks']:
                if 'price' in item:
                    f.write(f"| {item['name']} | {item['price']} | {item.get('source', '')} |\n")
            f.write("\n")
        
        # 黄金
        if data.get('gold'):
            f.write("## 🥇 贵金属\n\n")
            f.write("| 品种 | 价格 | 单位 | 来源 |\n")
            f.write("|------|------|------|------|\n")
            for item in data['gold']:
                if 'price' in item:
                    f.write(f"| {item['name']} | {item['price']} | {item.get('unit', '')} | {item.get('source', '')} |\n")
            f.write("\n")
        
        # 外汇
        if data.get('forex'):
            f.write("## 💱 主要汇率\n\n")
            f.write("| 货币对 | 汇率 | 来源 |\n")
            f.write("|--------|------|------|\n")
            for item in data['forex']:
                if 'rate' in item:
                    f.write(f"| {item['name']} | {item['rate']} | {item.get('source', '')} |\n")
            f.write("\n")
        
        f.write("---\n*数据来源: Stooq (波兰)、Yahoo Finance、ExchangeRate-API*")
    
    return json_path, md_path


# ============== 主函数 ==============

def main():
    print("=" * 60)
    print("🌍 国际金融数据抓取工具 v3.0")
    print("=" * 60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 数据源: Stooq、Yahoo Finance、ExchangeRate-API\n")
    
    all_data = {
        'meta': {
            'generated_at': datetime.now().isoformat(),
            'version': '3.0',
            'description': '国际金融数据：美股、港股、黄金、外汇',
            'data_source': 'Stooq (波兰) + Yahoo Finance + ExchangeRate-API',
            'optimized_for': '新加坡服务器'
        }
    }
    
    # 抓取各类数据
    all_data['us_stocks'] = fetch_us_stocks()
    all_data['hk_stocks'] = fetch_hk_stocks()
    all_data['gold'] = fetch_gold_price()
    all_data['forex'] = fetch_forex_rates()
    
    # 统计结果
    us_count = len([x for x in all_data['us_stocks'] if 'price' in x])
    hk_count = len([x for x in all_data['hk_stocks'] if 'price' in x])
    gold_count = len([x for x in all_data['gold'] if 'price' in x])
    forex_count = len(all_data['forex'])
    
    # 保存结果
    json_path, md_path = save_results(all_data)
    
    # 输出摘要
    print("\n" + "=" * 60)
    print("📊 抓取结果摘要")
    print("=" * 60)
    print(f"📈 美股指数: {us_count}/3 条成功")
    print(f"📊 港股指数: {hk_count}/1 条成功")
    print(f"🥇 黄金价格: {gold_count} 条成功")
    print(f"💱 外汇汇率: {forex_count} 条成功")
    print(f"\n📁 数据文件:")
    print(f"   JSON: {json_path}")
    print(f"   MD:   {md_path}")
    print("=" * 60)
    
    return all_data


if __name__ == "__main__":
    result = main()
