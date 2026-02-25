#!/usr/bin/env python3
"""
增强版金融股票数据抓取脚本 v1
功能：
1. A股主要指数（上证、深证、创业板、科创50）
2. 美股主要指数（道琼斯、纳斯达克、标普500）
3. A股涨幅榜前10名
4. 生成中英文双版本简报
"""
import requests
import json
import re
from datetime import datetime
import time

TIMEOUT = 10
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://quote.eastmoney.com/',
    'Accept': 'application/json, text/plain, */*',
}


def fetch_cn_indices():
    """获取A股主要指数"""
    print("📡 抓取A股指数...")
    
    indices = [
        ('上证指数', '1.000001'),
        ('深证成指', '0.399001'),
        ('创业板指', '0.399006'),
        ('科创50', '1.000688'),
        ('沪深300', '1.000300'),
        ('中证500', '1.000905'),
    ]
    
    results = []
    
    try:
        # 东方财富批量查询API
        codes = ','.join([code for _, code in indices])
        url = f'https://push2.eastmoney.com/api/qt/ulist.np/get?fields=f1,f2,f3,f4,f12,f13,f14&secids={codes}'
        
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('data', {}).get('diff', [])
            
            code_map = {code: name for name, code in indices}
            
            for item in items:
                secid = f"{item.get('f13')}.{item.get('f12')}"
                if secid in code_map:
                    current = item.get('f2', 0) / 100 if item.get('f2') else 0
                    change = item.get('f4', 0) / 100 if item.get('f4') else 0
                    change_percent = item.get('f3', 0) / 100 if item.get('f3') else 0
                    
                    results.append({
                        'name': code_map[secid],
                        'name_en': get_en_name(code_map[secid]),
                        'code': item.get('f12'),
                        'current': round(current, 2),
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2),
                        'trend': '📈' if change_percent > 0 else ('📉' if change_percent < 0 else '➡️'),
                        'source': '东方财富',
                        'timestamp': datetime.now().isoformat()
                    })
        
        return results
    
    except Exception as e:
        print(f"  ❌ A股指数抓取失败: {e}")
        return []


def fetch_us_indices():
    """获取美股主要指数"""
    print("📡 抓取美股指数...")
    
    results = []
    
    try:
        # 使用新浪美股指数API
        # 道琼斯: gb_$dji, 纳斯达克: gb_$ixic, 标普500: gb_$inx
        url = 'https://hq.sinajs.cn/list=gb_$dji,gb_$ixic,gb_$inx'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn/usstock/',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            text = resp.text
            print(f"  原始响应长度: {len(text)}")
            
            indices_info = [
                ('道琼斯', 'gb_\\$dji', 'DJI'),
                ('纳斯达克', 'gb_\\$ixic', 'IXIC'),
                ('标普500', 'gb_\\$inx', 'SPX'),
            ]
            
            for name, var_pattern, code in indices_info:
                # 匹配变量内容
                pattern = f'var hq_str_{var_pattern}="(.*?)";'
                match = re.search(pattern, text)
                
                if match:
                    data = match.group(1).split(',')
                    if len(data) >= 7 and data[0]:
                        try:
                            # 数据格式: 名称,今开,昨收,最高,最低,当前价,涨跌额,涨跌幅
                            current = float(data[1])
                            change = float(data[5])
                            change_percent = float(data[6])
                            
                            results.append({
                                'name': name,
                                'name_en': get_en_name(name),
                                'code': code,
                                'current': round(current, 2),
                                'change': round(change, 2),
                                'change_percent': round(change_percent, 2),
                                'trend': '📈' if change_percent > 0 else ('📉' if change_percent < 0 else '➡️'),
                                'source': '新浪财经',
                                'timestamp': datetime.now().isoformat()
                            })
                            print(f"  ✅ {name}: {current:.2f} ({change_percent:+.2f}%)")
                        except Exception as e:
                            print(f"  ❌ {name} 解析失败: {e}")
                    else:
                        print(f"  ❌ {name} 数据不足")
                else:
                    print(f"  ❌ {name} 变量未找到")
        
        # 如果新浪失败，尝试备用API
        if len(results) < 3:
            print("  尝试备用API...")
            backup_results = fetch_us_indices_backup()
            if backup_results:
                # 合并结果，去重
                existing_codes = {r['code'] for r in results}
                for r in backup_results:
                    if r['code'] not in existing_codes:
                        results.append(r)
        
        return results
    
    except Exception as e:
        print(f"  ❌ 美股指数抓取失败: {e}")
        return []


def fetch_us_indices_backup():
    """备用美股指数API"""
    results = []
    
    try:
        # 使用东方财富美股指数
        url = 'https://push2.eastmoney.com/api/qt/ulist.np/get?fields=f1,f2,f3,f4,f12,f13,f14&secids=100.DJI,100.IXIC,100.SPX'
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('data', {}).get('diff', [])
            
            name_map = {'DJI': ('道琼斯', 'Dow Jones'), 'IXIC': ('纳斯达克', 'NASDAQ'), 'SPX': ('标普500', 'S&P 500')}
            
            for item in items:
                code = item.get('f12', '')
                if code in name_map:
                    name, name_en = name_map[code]
                    current = item.get('f2', 0)
                    change = item.get('f4', 0)
                    change_percent = item.get('f3', 0)
                    
                    if current:
                        results.append({
                            'name': name,
                            'name_en': name_en,
                            'code': code,
                            'current': round(current / 100, 2),
                            'change': round(change / 100, 2) if change else 0,
                            'change_percent': round(change_percent / 100, 2) if change_percent else 0,
                            'trend': '📈' if change_percent > 0 else ('📉' if change_percent < 0 else '➡️'),
                            'source': '东方财富',
                            'timestamp': datetime.now().isoformat()
                        })
                        print(f"  ✅ {name}: {current/100:.2f}")
    except Exception as e:
        print(f"  备用API失败: {e}")
    
    return results


def fetch_top_gainers():
    """获取A股涨幅榜前10名"""
    print("📡 抓取A股涨幅榜...")
    
    try:
        # 使用新浪财经涨幅榜API
        url = 'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData'
        params = {
            'page': 1,
            'num': 80,  # 多取一些数据
            'sort': 'changepercent',
            'asc': 0,  # 降序
            'node': 'hs_a',  # 沪深A股
            'symbol': '',
            '_s_r_a': 'page'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://vip.stock.finance.sina.com.cn/q/go.php/vFinanceAnalyze/kind/mainindex/'
        }
        
        resp = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            
            gainers = []
            for item in data:
                name = item.get('name', '')
                change_percent = item.get('changepercent')
                current = item.get('trade')
                
                # 过滤
                if not name or change_percent is None or current is None:
                    continue
                if 'ST' in name or '退' in name or 'N' in name:  # 排除ST、退市、新股
                    continue
                try:
                    change_percent = float(change_percent)
                    current = float(current)
                except:
                    continue
                # 放宽涨幅限制到25%，包含涨停股
                if change_percent > 25:
                    continue
                
                gainers.append({
                    'rank': len(gainers) + 1,
                    'name': name,
                    'code': item.get('code', ''),
                    'current': round(current, 2),
                    'change_percent': round(change_percent, 2),
                    'change': round(float(item.get('pricechange', 0) or 0), 2),
                    'high': round(float(item.get('high', 0) or 0), 2),
                    'low': round(float(item.get('low', 0) or 0), 2),
                    'open': round(float(item.get('open', 0) or 0), 2),
                    'volume': float(item.get('volume', 0) or 0) * 100,
                    'source': '新浪财经',
                    'timestamp': datetime.now().isoformat()
                })
                
                if len(gainers) >= 10:
                    break
            
            return gainers
        
        return []
    
    except Exception as e:
        print(f"  ❌ 涨幅榜抓取失败: {e}")
        return []


def fetch_top_losers():
    """获取A股跌幅榜前10名"""
    print("📡 抓取A股跌幅榜...")
    
    try:
        # 使用新浪财经跌幅榜API
        url = 'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData'
        params = {
            'page': 1,
            'num': 40,
            'sort': 'changepercent',
            'asc': 1,  # 升序（跌幅最大在前）
            'node': 'hs_a',
            'symbol': '',
            '_s_r_a': 'page'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://vip.stock.finance.sina.com.cn/q/go.php/vFinanceAnalyze/kind/mainindex/'
        }
        
        resp = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        
        if resp.status_code == 200:
            data = resp.json()
            
            losers = []
            for item in data[:15]:
                name = item.get('name', '')
                change_percent = item.get('changepercent')
                current = item.get('trade')
                
                if not name or not change_percent or not current:
                    continue
                if 'ST' in name or '退' in name:
                    continue
                try:
                    change_percent = float(change_percent)
                    current = float(current)
                except:
                    continue
                if change_percent >= 0:  # 只取跌的
                    continue
                
                losers.append({
                    'rank': len(losers) + 1,
                    'name': name,
                    'code': item.get('code', ''),
                    'current': round(current, 2),
                    'change_percent': round(change_percent, 2),
                    'change': round(float(item.get('pricechange', 0)), 2),
                    'high': round(float(item.get('high', 0)), 2),
                    'low': round(float(item.get('low', 0)), 2),
                    'source': '新浪财经',
                    'timestamp': datetime.now().isoformat()
                })
                
                if len(losers) >= 10:
                    break
            
            return losers
        
        return []
    
    except Exception as e:
        print(f"  ❌ 跌幅榜抓取失败: {e}")
        return []


def get_en_name(name):
    """获取英文名称"""
    mapping = {
        '上证指数': 'Shanghai Composite',
        '深证成指': 'Shenzhen Component',
        '创业板指': 'ChiNext Index',
        '科创50': 'STAR 50',
        '沪深300': 'CSI 300',
        '中证500': 'CSI 500',
        '道琼斯': 'Dow Jones',
        '纳斯达克': 'NASDAQ',
        '标普500': 'S&P 500',
    }
    return mapping.get(name, name)


def generate_report(data, output_dir):
    """生成报告"""
    timestamp = datetime.now()
    date_str = timestamp.strftime('%Y-%m-%d')
    time_str = timestamp.strftime('%H:%M')

    # JSON 输出
    json_path = f"{output_dir}/finance_stock_{date_str.replace('-', '')}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "generated": timestamp.isoformat(),
            **data
        }, f, ensure_ascii=False, indent=2)

    # ========== 中文版 Markdown ==========
    md_path = f"{output_dir}/finance_stock_latest.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# 📈 股票金融日报\n")
        f.write(f"> 日期：{date_str} | 更新时间：{time_str} UTC\n\n")
        f.write("---\n\n")

        # A股指数
        f.write("## 🇨🇳 A股主要指数\n\n")
        f.write("| 指数 | 代码 | 当前价 | 涨跌额 | 涨跌幅 |\n")
        f.write("|------|------|--------|--------|--------|\n")
        for idx in data.get('cn_indices', []):
            trend = idx.get('trend', '')
            change_str = f"{idx['change']:+.2f}" if idx['change'] else '-'
            pct_str = f"{idx['change_percent']:+.2f}%" if idx['change_percent'] else '-'
            f.write(f"| {trend} {idx['name']} | {idx['code']} | {idx['current']:.2f} | {change_str} | **{pct_str}** |\n")
        f.write("\n")

        # 美股指数
        f.write("## 🇺🇸 美股主要指数\n\n")
        f.write("| 指数 | 代码 | 当前价 | 涨跌额 | 涨跌幅 |\n")
        f.write("|------|------|--------|--------|--------|\n")
        for idx in data.get('us_indices', []):
            trend = idx.get('trend', '')
            change_str = f"{idx['change']:+.2f}" if idx['change'] else '-'
            pct_str = f"{idx['change_percent']:+.2f}%" if idx['change_percent'] else '-'
            f.write(f"| {trend} {idx['name']} | {idx['code']} | {idx['current']:.2f} | {change_str} | **{pct_str}** |\n")
        f.write("\n")

        # 涨幅榜
        f.write("## 🚀 A股涨幅榜 TOP 10\n\n")
        f.write("| 排名 | 股票名称 | 代码 | 现价 | 涨幅 | 最高 | 最低 |\n")
        f.write("|------|----------|------|------|------|------|------|\n")
        for stock in data.get('top_gainers', []):
            pct_str = f"+{stock['change_percent']:.2f}%"
            f.write(f"| {stock['rank']} | **{stock['name']}** | {stock['code']} | {stock['current']:.2f} | 🔴 {pct_str} | {stock['high']:.2f} | {stock['low']:.2f} |\n")
        f.write("\n")

        # 跌幅榜
        f.write("## 📉 A股跌幅榜 TOP 10\n\n")
        f.write("| 排名 | 股票名称 | 代码 | 现价 | 跌幅 | 最高 | 最低 |\n")
        f.write("|------|----------|------|------|------|------|------|\n")
        for stock in data.get('top_losers', []):
            pct_str = f"{stock['change_percent']:.2f}%"
            f.write(f"| {stock['rank']} | **{stock['name']}** | {stock['code']} | {stock['current']:.2f} | 🟢 {pct_str} | {stock['high']:.2f} | {stock['low']:.2f} |\n")
        f.write("\n")

        f.write("---\n\n")
        f.write("*数据来源：东方财富*\n")

    # ========== 英文版 Markdown ==========
    md_en_path = f"{output_dir}/finance_stock_latest_en.md"
    with open(md_en_path, 'w', encoding='utf-8') as f:
        f.write(f"# 📈 Stock & Finance Daily Report\n")
        f.write(f"> Date: {date_str} | Updated: {time_str} UTC\n\n")
        f.write("---\n\n")

        # A股指数
        f.write("## 🇨🇳 China A-Share Indices\n\n")
        f.write("| Index | Code | Price | Change | Change % |\n")
        f.write("|-------|------|-------|--------|----------|\n")
        for idx in data.get('cn_indices', []):
            trend = idx.get('trend', '')
            name_en = idx.get('name_en', idx['name'])
            change_str = f"{idx['change']:+.2f}" if idx['change'] else '-'
            pct_str = f"{idx['change_percent']:+.2f}%" if idx['change_percent'] else '-'
            f.write(f"| {trend} {name_en} | {idx['code']} | {idx['current']:.2f} | {change_str} | **{pct_str}** |\n")
        f.write("\n")

        # 美股指数
        f.write("## 🇺🇸 US Stock Indices\n\n")
        f.write("| Index | Code | Price | Change | Change % |\n")
        f.write("|-------|------|-------|--------|----------|\n")
        for idx in data.get('us_indices', []):
            trend = idx.get('trend', '')
            name_en = idx.get('name_en', idx['name'])
            change_str = f"{idx['change']:+.2f}" if idx['change'] else '-'
            pct_str = f"{idx['change_percent']:+.2f}%" if idx['change_percent'] else '-'
            f.write(f"| {trend} {name_en} | {idx['code']} | {idx['current']:.2f} | {change_str} | **{pct_str}** |\n")
        f.write("\n")

        # 涨幅榜
        f.write("## 🚀 Top 10 Gainers (A-Share)\n\n")
        f.write("| Rank | Stock | Code | Price | Change % | High | Low |\n")
        f.write("|------|-------|------|-------|----------|------|-----|\n")
        for stock in data.get('top_gainers', []):
            pct_str = f"+{stock['change_percent']:.2f}%"
            f.write(f"| {stock['rank']} | **{stock['name']}** | {stock['code']} | {stock['current']:.2f} | 🔴 {pct_str} | {stock['high']:.2f} | {stock['low']:.2f} |\n")
        f.write("\n")

        # 跌幅榜
        f.write("## 📉 Top 10 Losers (A-Share)\n\n")
        f.write("| Rank | Stock | Code | Price | Change % | High | Low |\n")
        f.write("|------|-------|------|-------|----------|------|-----|\n")
        for stock in data.get('top_losers', []):
            pct_str = f"{stock['change_percent']:.2f}%"
            f.write(f"| {stock['rank']} | **{stock['name']}** | {stock['code']} | {stock['current']:.2f} | 🟢 {pct_str} | {stock['high']:.2f} | {stock['low']:.2f} |\n")
        f.write("\n")

        f.write("---\n\n")
        f.write("*Data Source: EastMoney*\n")

    # 纯文本版本
    txt_path = f"{output_dir}/finance_stock_latest.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"股票金融日报 | {date_str}\n")
        f.write("=" * 50 + "\n\n")

        f.write("【A股指数】\n")
        for idx in data.get('cn_indices', []):
            trend = '涨' if idx['change_percent'] > 0 else ('跌' if idx['change_percent'] < 0 else '平')
            f.write(f"  {idx['name']}: {idx['current']:.2f} ({idx['change_percent']:+.2f}% {trend})\n")
        f.write("\n")

        f.write("【美股指数】\n")
        for idx in data.get('us_indices', []):
            trend = '涨' if idx['change_percent'] > 0 else ('跌' if idx['change_percent'] < 0 else '平')
            f.write(f"  {idx['name']}: {idx['current']:.2f} ({idx['change_percent']:+.2f}% {trend})\n")
        f.write("\n")

        f.write("【涨幅榜 TOP 10】\n")
        for stock in data.get('top_gainers', []):
            f.write(f"  {stock['rank']}. {stock['name']}({stock['code']}): {stock['current']:.2f} (+{stock['change_percent']:.2f}%)\n")
        f.write("\n")

        f.write("【跌幅榜 TOP 10】\n")
        for stock in data.get('top_losers', []):
            f.write(f"  {stock['rank']}. {stock['name']}({stock['code']}): {stock['current']:.2f} ({stock['change_percent']:.2f}%)\n")

    return json_path, md_path, md_en_path, txt_path


def main():
    print("=" * 50)
    print("📈 金融股票数据抓取 v1")
    print("=" * 50)

    output_dir = "/home/work/workspace/hxxmacro/data/finance_a_stock"

    # 抓取数据
    cn_indices = fetch_cn_indices()
    us_indices = fetch_us_indices()
    top_gainers = fetch_top_gainers()
    top_losers = fetch_top_losers()

    # 合并数据
    all_data = {
        'cn_indices': cn_indices,
        'us_indices': us_indices,
        'top_gainers': top_gainers,
        'top_losers': top_losers
    }

    # 生成报告
    json_path, md_path, md_en_path, txt_path = generate_report(all_data, output_dir)

    print("\n" + "=" * 50)
    print("✅ 抓取完成!")
    print(f"📄 JSON: {json_path}")
    print(f"📄 中文版: {md_path}")
    print(f"📄 英文版: {md_en_path}")
    print(f"📄 纯文本: {txt_path}")
    print("\n📊 数据统计:")
    print(f"   A股指数: {len(cn_indices)} 条")
    print(f"   美股指数: {len(us_indices)} 条")
    print(f"   涨幅榜: {len(top_gainers)} 条")
    print(f"   跌幅榜: {len(top_losers)} 条")


if __name__ == "__main__":
    main()
