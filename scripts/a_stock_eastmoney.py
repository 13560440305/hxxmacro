#!/usr/bin/env python3
"""
东方财富A股数据抓取（API方式）
"""
import requests
import json
from datetime import datetime

TIMEOUT = 5
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://quote.eastmoney.com/'
}

def fetch_eastmoney_api():
    """使用东方财富API获取A股指数"""
    # 东方财富API（无需密钥）
    indices = [
        ('上证指数', '1.000001'),
        ('深证成指', '0.399001'),
        ('创业板指', '0.399006'),
        ('科创50', '1.000688'),
    ]
    
    results = []
    
    try:
        # 批量查询API
        codes = ','.join([code for _, code in indices])
        url = f'https://push2.eastmoney.com/api/qt/ulist.np/get?fields=f1,f2,f3,f4,f12,f13,f14&secids={codes}'
        
        resp = requests.get(url, headers=HEADERS, timeout=TEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('data', {}).get('diff', [])
            
            # 创建代码映射
            code_map = {code: name for name, code in indices}
            
            for item in items:
                secid = f"{item.get('f13')}.{item.get('f12')}"
                if secid in code_map:
                    current = item.get('f2')  # 当前价
                    change = item.get('f4')   # 涨跌额
                    change_percent = item.get('f3')  # 涨跌幅
                    
                    results.append({
                        'name': code_map[secid],
                        'code': item.get('f12'),
                        'current': current,
                        'change': change,
                        'change_percent': change_percent,
                        'source': '东方财富API',
                        'timestamp': datetime.now().isoformat()
                    })
                    print(f"✅ {code_map[secid]}: {current} ({change_percent}%)")
        
        return results
        
    except Exception as e:
        print(f"API请求失败: {e}")
        return []

def fetch_stock_simple():
    """简化版：直接获取主要指数"""
    try:
        # 使用更简单的API
        url = "https://api-ddc-wscn.awtmt.com/market/real?prod_code=000001.SS,399001.SZ&fields=prod_name,last_px,px_change_rate"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            results = []
            
            for item in data.get('data', []):
                results.append({
                    'name': item.get('prod_name'),
                    'current': item.get('last_px'),
                    'change_percent': item.get('px_change_rate'),
                    'source': 'WallStreetCN API',
                    'timestamp': datetime.now().isoformat()
                })
                print(f"✅ {item.get('prod_name')}: {item.get('last_px')} ({item.get('px_change_rate')}%)")
            
            return results
    except Exception as e:
        print(f"简化API失败: {e}")
    
    return []

def main():
    print("=== A股数据抓取（API版本） ===")
    print(f"时间: {datetime.now().strftime('%H:%M:%S')}\n")
    
    all_data = {'meta': {'generated_at': datetime.now().isoformat()}}
    
    # 尝试多个API源
    print("1. 尝试东方财富API...")
    data1 = fetch_eastmoney_api()
    
    if data1:
        all_data['eastmoney'] = data1
    else:
        print("2. 尝试备用API...")
        data2 = fetch_stock_simple()
        all_data['backup'] = data2
    
    # 保存结果
    if all_data.get('eastmoney') or all_data.get('backup'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        json_path = f"/home/work/hxxworkspace/data/a_stock_api_{timestamp}.json"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 数据已保存: {json_path}")
        print(f"\n📊 数据内容:")
        print(json.dumps(all_data, indent=2, ensure_ascii=False))
        
        return True
    else:
        print("❌ 所有API源均失败")
        return False

if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)