import psycopg2
import json
from openai import OpenAI
import os
import time

from logger import setup_logger


# ========= 读取配置 =========
def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


config = load_config()

DB_CONFIG = config["database"]
AI_CONFIG = config["ai"]
LOG_CONFIG = config.get("logging", {})

# ========= 初始化 日志 =========
logger = setup_logger("macro_ai_engine", LOG_CONFIG)

# ========= 初始化 AI 客户端 =========
client = OpenAI(
    api_key=AI_CONFIG["api_key"],
    base_url=AI_CONFIG["base_url"]
)


# ========= AI 分析 =========
def generate_ai_analysis(event):

    prompt = f"""
    宏观事件：
    事件名称: {event['event']}
    国家: {event['country']}
    实际值: {event['actual']}
    预期值: {event['forecast']}
    前值: {event['previous']}
    Surprise: {event['surprise']}

    请输出：
    1. 一段专业宏观解读（不超过150字）
    2. 3-4条跨市场影响

    输出格式为JSON：
    {{
        "summary": "...",
        "reactions": [
            {{
                "asset": "US10Y/DXY/SPX/Gold",
                "direction": "上涨/下跌",
                "magnitude": "强/中/弱",
                "reason": "简要原因"
            }}
        ]
    }}
    """

    max_retries = AI_CONFIG.get("max_retries", 3)
    attempt = 0
    last_exc = None

    while attempt < max_retries:
        attempt += 1
        try:
            logger.debug("AI request attempt %d for event %s", attempt, event.get('event'))
            response = client.chat.completions.create(
                model=AI_CONFIG["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=AI_CONFIG.get("temperature", 0.3)
            )

            content = response.choices[0].message.content
            parsed = json.loads(content)
            logger.info("AI analysis successful for event %s (attempt %d)", event.get('event'), attempt)
            return parsed

        except Exception as e:
            last_exc = e
            logger.exception("AI request failed on attempt %d/%d: %s", attempt, max_retries, e)
            if attempt >= max_retries:
                logger.error("Max retries reached for event %s", event.get('event'))
                raise
            sleep_seconds = 2 ** (attempt - 1)
            logger.info("Retrying after %s seconds", sleep_seconds)
            time.sleep(sleep_seconds)

    # If somehow loop exits without returning
    raise last_exc


# ========= 主逻辑 =========
def process_events():
    logger.info("Connecting to database")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, event, country, actual, forecast, previous, surprise
        FROM macro_events
        WHERE process_status = 'pending'
        ORDER BY updated_at DESC
        LIMIT 5
    """)

    rows = cur.fetchall()

    if not rows:
        logger.info("没有待处理事件")
        cur.close()
        conn.close()
        return

    logger.info("Fetched %d pending events", len(rows))

    for row in rows:

        event_id = row[0]

        event_data = {
            "event": row[1],
            "country": row[2],
            "actual": row[3],
            "forecast": row[4],
            "previous": row[5],
            "surprise": row[6]
        }

        logger.info("Processing event id=%s, name=%s", event_id, event_data['event'])

        try:

            ai_result = generate_ai_analysis(event_data)

            summary = ai_result.get("summary")
            reactions = ai_result.get("reactions", [])

            # 更新事件
            cur.execute("""
                UPDATE macro_events
                SET ai_summary = %s,
                    process_status = 'done'
                WHERE id = %s
            """, (summary, event_id))
            logger.debug("Updated macro_events id=%s with AI summary", event_id)

            # 插入市场反应
            for r in reactions:
                cur.execute("""
                    INSERT INTO cross_market_reactions
                    (event_id, asset, direction, magnitude, reason)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    event_id,
                    r.get("asset"),
                    r.get("direction"),
                    r.get("magnitude"),
                    r.get("reason")
                ))
                logger.debug("Inserted reaction for event %s: %s", event_id, r)

            conn.commit()
            logger.info("处理完成 for event id=%s\n", event_id)

        except Exception as e:
            logger.exception("处理失败 for event id=%s: %s", event_id, e)
            conn.rollback()

    cur.close()
    conn.close()


if __name__ == "__main__":
    process_events()

