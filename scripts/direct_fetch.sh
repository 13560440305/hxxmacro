#!/bin/bash
# 直接命令行抓取 Hacker News 真实数据

WORKDIR="/home/work/hxxworkspace"
OUTFILE="$WORKDIR/data/real_time_hn_$(date +%Y%m%d_%H%M%S).json"

echo "=== 开始直接抓取 Hacker News 实时数据 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"

# 1. 获取头条ID
ID_FILE="/tmp/hn_ids.txt"
curl -m 8 -s 'https://hacker-news.firebaseio.com/v0/topstories.json' | \
    tr -d '[]' | tr ',' '\n' | head -10 > "$ID_FILE"

if [ ! -s "$ID_FILE" ]; then
    echo "❌ 无法获取 ID 列表"
    exit 1
fi

echo "获取到 $(wc -l < $ID_FILE) 个ID"

# 2. 逐个获取详情
RESULTS="[]"
count=0

while read sid; do
    if [ -z "$sid" ]; then continue; fi
    
    echo -n "处理 ID $sid... "
    
    # 获取项目数据
    DATA=$(curl -m 5 -s "https://hacker-news.firebaseio.com/v0/item/$sid.json" 2>/dev/null)
    
    if [ -n "$DATA" ] && [ "$DATA" != "null" ]; then
        # 提取关键字段
        TITLE=$(echo "$DATA" | grep -o '"title":"[^"]*' | cut -d'"' -f4 | head -1)
        URL=$(echo "$DATA" | grep -o '"url":"[^"]*' | cut -d'"' -f4 | head -1)
        SCORE=$(echo "$DATA" | grep -o '"score":[0-9]*' | cut -d':' -f2 | head -1)
        
        if [ -n "$TITLE" ]; then
            # 构建 JSON 记录
            RECORD="{\"id\":$sid,\"title\":\"$TITLE\",\"url\":\"${URL:-}\",\"score\":${SCORE:-0},\"source\":\"Hacker News\"}"
            
            if [ "$RESULTS" = "[]" ]; then
                RESULTS="[$RECORD]"
            else
                RESULTS=$(echo "$RESULTS" | sed 's/\]$//')
                RESULTS="$RESULTS,$RECORD]"
            fi
            echo "✅"
            count=$((count+1))
        else
            echo "⚠️ 无标题"
        fi
    else
        echo "❌ 无数据"
    fi
    
    sleep 0.2  # 礼貌延迟
    
    if [ $count -ge 8 ]; then
        break
    fi
done < "$ID_FILE"

# 3. 保存结果
if [ "$RESULTS" != "[]" ]; then
    echo "$RESULTS" | python3 -m json.tool > "$OUTFILE"
    echo "\n✅ 抓取完成!"
    echo "共获取 $count 条实时新闻"
    echo "保存至: $OUTFILE"
    
    # 显示前3条
    echo "\n=== 前3条新闻 ==="
    head -20 "$OUTFILE" | tail -15
else
    echo "❌ 未获取到任何有效数据"
    exit 1
fi