#!/usr/bin/env python3
"""
自动化抓取编排脚本
按顺序执行：
1. AI/科技新闻抓取
2. 财经数据抓取（待实现）
3. 生成统一简报
"""
import subprocess
import sys
import os
from datetime import datetime

LOG_DIR = "/home/work/hxxworkspace/logs"
DATA_DIR = "/home/work/hxxworkspace/data"

def ensure_dirs():
    """确保目录存在"""
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

def run_script(name, script_path, timeout=30):
    """运行指定脚本"""
    log_file = os.path.join(LOG_DIR, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始: {name}")
    
    try:
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"=== {name} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            result = subprocess.run(
                [sys.executable, script_path],
                timeout=timeout,
                capture_output=True,
                text=True
            )
            log.write(result.stdout)
            if result.stderr:
                log.write("\n[STDERR]\n" + result.stderr)
            log.write(f"\n[退出码: {result.returncode}]\n\n")
            
        if result.returncode == 0:
            print(f"  ✅ 成功")
            return True
        else:
            print(f"  ⚠️  完成但有警告 (退出码: {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ❌ 超时 ({timeout}秒)")
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"超时 ({timeout}秒)\n")
        return False
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        with open(log_file, 'a', encoding='utf-8') as log:
            log.write(f"异常: {e}\n")
        return False

def generate_daily_summary():
    """生成每日汇总简报"""
    summary_file = os.path.join(DATA_DIR, f"daily_summary_{datetime.now().strftime('%Y%m%d')}.md")
    try:
        # 读取最新数据
        ai_news_file = os.path.join(DATA_DIR, "ai_news_latest.md")
        tech_news_file = os.path.join(DATA_DIR, "tech_news_latest.md")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# 每日数据汇总\n")
            f.write(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # AI 新闻部分
            if os.path.exists(ai_news_file):
                f.write("## 📰 AI/科技新闻\n\n")
                with open(ai_news_file, 'r', encoding='utf-8') as ai:
                    # 跳过标题行，取主要内容
                    lines = ai.readlines()[2:]
                    for line in lines:
                        if line.strip() and not line.startswith('---'):
                            f.write(line)
                f.write("\n")
            
            # 技术新闻部分
            if os.path.exists(tech_news_file):
                f.write("## 💻 技术动态\n\n")
                with open(tech_news_file, 'r', encoding='utf-8') as tech:
                    lines = tech.readlines()[2:]
                    for line in lines:
                        if line.strip() and not line.startswith('---'):
                            f.write(line)
                f.write("\n")
            
            f.write("---\n*本报告由自动化抓取流水线生成*\n")
        
        print(f"  ✅ 汇总简报已生成: {summary_file}")
        return True
    except Exception as e:
        print(f"  ❌ 生成汇总失败: {e}")
        return False

def main():
    print(f"=== 自动化抓取流水线启动 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    ensure_dirs()
    
    # 执行顺序
    scripts = [
        ("AI新闻", "/home/work/hxxworkspace/scripts/tech_news_scraper_operational.py"),
        # ("财经数据", "/home/work/hxxworkspace/scripts/finance_data_scraper.py"),  # 待测试
    ]
    
    success_count = 0
    for name, path in scripts:
        if os.path.exists(path):
            if run_script(name, path):
                success_count += 1
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 跳过: {name} (脚本不存在)")
    
    # 生成汇总
    generate_daily_summary()
    
    print(f"\n=== 完成 ===")
    print(f"成功脚本: {success_count}/{len(scripts)}")
    print(f"日志目录: {LOG_DIR}")
    print(f"数据目录: {DATA_DIR}")

if __name__ == "__main__":
    main()