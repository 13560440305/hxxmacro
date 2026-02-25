#!/bin/bash
# 最终整理数据目录

BASE="/home/work/hxxworkspace/data"
cd "$BASE"

echo "=== 最终整理数据目录 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"

echo "\n📂 当前文件分布:"
for dir in ai_tech finance_a_stock gov_economy finance_global temp; do
    count=$(find "$dir" -type f 2>/dev/null | wc -l)
    echo "  $dir/: $count 个文件"
done

echo "\n🔧 重新分类文件..."

# 1. AI/科技文件
mv ai_tech/tech_news*.json ai_tech/tech_news*.txt ai_tech/tech_news*.md ai_tech/ai_news*.md ai_tech/ai_combined*.json ai_tech/ 2>/dev/null

# 2. 财经文件
mv ai_tech/finance_*.json ai_tech/finance_*.md ai_tech/a_stock_*.json finance_a_stock/ 2>/dev/null

# 3. 政府经济文件
mv ai_tech/gov_stats_*.json ai_tech/gov_stats_*.md gov_economy/ 2>/dev/null

# 4. 全球财经文件
mv ai_tech/finance_final_*.json ai_tech/finance_fallback_*.json finance_global/ 2>/dev/null

# 5. README.md留在根目录
mv ai_tech/README.md . 2>/dev/null

# 清理空目录
find . -type d -empty -delete 2>/dev/null

# 确保目录存在
mkdir -p ai_tech finance_a_stock gov_economy finance_global temp

echo "\n📁 最终目录结构:"
tree -L 2 --filelimit 10

echo "\n📊 各类别文件统计:"
for dir in ai_tech finance_a_stock gov_economy finance_global temp; do
    echo -n "  $dir/: "
    ls "$dir" | wc -l | tr -d '\n'
    echo " 个文件"
done

echo "\n✅ 整理完成!"
echo "数据已按类别存放至对应目录。"