#!/bin/bash
# OpenClaw 定时抓取任务配置脚本
# 运行: bash crontab_setup.sh

WORKSPACE="/home/work/hxxworkspace"
LOGS_DIR="$WORKSPACE/logs"

# 创建日志目录
mkdir -p "$LOGS_DIR"

# 生成 cron 配置
cat > /tmp/openclaw_cron << EOF
# OpenClaw 数据抓取定时任务
# 每2小时抓取一次 AI 新闻
0 */2 * * * cd $WORKSPACE && python3 scripts/automation_orchestrator.py >> $LOGS_DIR/cron_automation.log 2>&1

# 每天上午9点生成完整日报
0 9 * * * cd $WORKSPACE && python3 scripts/automation_orchestrator.py --full >> $LOGS_DIR/cron_daily.log 2>&1

# 每周一清理旧日志（保留7天）
0 2 * * 1 find $LOGS_DIR -name "*.log" -mtime +7 -delete
EOF

# 显示配置
echo "=== 生成的 Cron 配置 ==="
cat /tmp/openclaw_cron

echo -e "\n=== 安装选项 ==="
echo "1. 直接添加到当前用户的 crontab"
echo "2. 保存到文件 ($WORKSPACE/crontab.conf)，手动安装"
echo "3. 仅预览，不安装"
read -p "请选择 (1/2/3): " choice

case $choice in
    1)
        crontab -l > /tmp/current_cron 2>/dev/null
        cat /tmp/openclaw_cron >> /tmp/current_cron
        crontab /tmp/current_cron
        echo "✅ 已添加到当前用户的 crontab"
        crontab -l | grep -A2 "OpenClaw"
        ;;
    2)
        cp /tmp/openclaw_cron "$WORKSPACE/crontab.conf"
        echo "✅ 已保存到 $WORKSPACE/crontab.conf"
        echo "手动安装命令: crontab $WORKSPACE/crontab.conf"
        ;;
    3)
        echo "✅ 仅预览完成"
        ;;
    *)
        echo "无效选择，仅保存配置文件"
        cp /tmp/openclaw_cron "$WORKSPACE/crontab.conf"
        ;;
esac

echo -e "\n=== 后续检查 ==="
echo "• 日志目录: $LOGS_DIR"
echo "• 数据目录: $WORKSPACE/data"
echo "• 脚本目录: $WORKSPACE/scripts"
echo "\n手动测试命令:"  
echo "  cd $WORKSPACE && python3 scripts/automation_orchestrator.py"