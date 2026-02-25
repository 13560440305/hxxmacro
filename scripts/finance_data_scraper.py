#!/usr/bin/env python3
"""
财经数据抓取脚本（示例）
可扩展为抓取股票、指数、外汇、黄金等数据。
"""
import requests
import json
from datetime import datetime, timedelta
import pandas as pd

def get_sina_us_stock_index():
    """从新浪财经获取美股指数（示例 - 需解析页面）"""
    url = "https://finance.sina.com.cn/stock/usstock/"
    try:
        resp = requests.get(url, timeout=10)
        # 此处需根据实际页面结构解析（示例仅返回状态）
        return {"status": resp.status_code, "len": len(resp.text)}
    except Exception as e:
        return {"error": str(e)}

def get_forex_rate(base="USD", target="CNY"):
    """从公开API获取汇率（示例使用免费API，实际需密钥）"""
    # 示例：使用 exchangerate-api（需注册后替换API_KEY）
    API_KEY = "your_api_key_here"
    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{base}/{target}"
    try:
        resp = requests.get(url)
        data = resp.json()
        return {
            "base": data.get("base_code"),
            "target": data.get("target_code"),
            "rate": data.get("conversion_rate"),
        }
    except Exception as e:
        return {"error": str(e)}

def get_gold_price():
    """获取黄金价格（示例：从公开页面抓取）"""
    # 示例：Kitco 现货黄金页面
    url = "https://www.kitcometals.com/charts/livegold.html"
    try:
        resp = requests.get(url, timeout=10)
        # 实际需解析页面提取价格
        return {"status": resp.status_code, "note": "需解析页面"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("=== 美股指数抓取示例 ===")
    print(get_sina_us_stock_index())
    
    print("\n=== 汇率获取示例（需API密钥） ===")
    print("提示：请先在代码中设置API_KEY")
    # print(get_forex_rate("USD", "CNY"))
    
    print("\n=== 黄金价格抓取示例 ===")
    print(get_gold_price())
