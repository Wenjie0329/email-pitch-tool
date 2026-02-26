"""
轻量级邮件追踪服务 V2
用于Render部署
"""

from flask import Flask, request, send_file, jsonify
import datetime
import io
import os
from pathlib import Path

app = Flask(__name__)

# 数据库配置 - 支持 PostgreSQL 和 SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    # 使用 PostgreSQL
    import psycopg2
    from psycopg2.extras import RealDictCursor
    USE_POSTGRES = True
else:
    # 本地测试使用 SQLite
    import sqlite3
    DB_FILE = "tracker.db"
    USE_POSTGRES = False

def get_db_connection():
    """获取数据库连接"""
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS opens (
                id SERIAL PRIMARY KEY,
                uid INTEGER,
                timestamp TEXT,
                ip TEXT,
                user_agent TEXT,
                synced INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clicks (
                id SERIAL PRIMARY KEY,
                uid INTEGER,
                url TEXT,
                timestamp TEXT,
                ip TEXT,
                synced INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opens_uid ON opens(uid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opens_synced ON opens(synced)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clicks_synced ON clicks(synced)")
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS opens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid INTEGER,
                timestamp TEXT,
                ip TEXT,
                user_agent TEXT,
                synced INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid INTEGER,
                url TEXT,
                timestamp TEXT,
                ip TEXT,
                synced INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opens_uid ON opens(uid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_opens_synced ON opens(synced)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clicks_synced ON clicks(synced)")

    conn.commit()
    conn.close()

# 启动时初始化数据库
init_db()

def fetchone_value(cursor, query, params=()):
    """统一获取单个值"""
    cursor.execute(query, params)
    result = cursor.fetchone()
    if result:
        if USE_POSTGRES:
            # PostgreSQL RealDictCursor 返回字典，获取第一个值
            return list(result.values())[0]
        else:
            # SQLite 返回 Row 对象，可以用索引访问
            return result[0]
    return 0

@app.route("/")
def home():
    """服务状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    opens_count = fetchone_value(cursor, "SELECT COUNT(*) FROM opens")
    clicks_count = fetchone_value(cursor, "SELECT COUNT(*) FROM clicks")
    unsynced = fetchone_value(cursor, "SELECT COUNT(*) FROM opens WHERE synced=0")
    conn.close()

    return jsonify({
        "service": "Email Tracker V2",
        "status": "running",
        "version": "2.0",
        "database": "PostgreSQL" if USE_POSTGRES else "SQLite",
        "total_opens": opens_count,
        "total_clicks": clicks_count,
        "unsynced_opens": unsynced
    })

@app.route("/health")
def health():
    """健康检查"""
    return jsonify({"status": "ok"})

@app.route("/open")
def open_tracker():
    """追踪邮件打开"""
    uid = request.args.get("uid", "unknown")
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get("User-Agent", "")[:500]  # 限制长度
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute(
                "INSERT INTO opens (uid, timestamp, ip, user_agent) VALUES (%s, %s, %s, %s)",
                (uid, ts, ip, ua)
            )
        else:
            cursor.execute(
                "INSERT INTO opens (uid, timestamp, ip, user_agent) VALUES (?, ?, ?, ?)",
                (uid, ts, ip, ua)
            )
        conn.commit()
        conn.close()
        print(f"[{ts}] Open: uid={uid}, ip={ip}")
    except Exception as e:
        print(f"Error: {e}")

    # 返回1x1透明GIF
    gif_bytes = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
        b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
        b"D\x01\x00;"
    )
    return send_file(
        io.BytesIO(gif_bytes),
        mimetype="image/gif",
        as_attachment=False,
        download_name='pixel.gif'
    )

@app.route("/click")
def click_tracker():
    """追踪链接点击"""
    uid = request.args.get("uid", "unknown")
    url = request.args.get("url", "")
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute(
                "INSERT INTO clicks (uid, url, timestamp, ip) VALUES (%s, %s, %s, %s)",
                (uid, url, ts, ip)
            )
        else:
            cursor.execute(
                "INSERT INTO clicks (uid, url, timestamp, ip) VALUES (?, ?, ?, ?)",
                (uid, url, ts, ip)
            )
        conn.commit()
        conn.close()
        print(f"[{ts}] Click: uid={uid}, url={url}")
    except Exception as e:
        print(f"Error: {e}")

    from flask import redirect
    return redirect(url) if url else jsonify({"error": "No URL provided"})

@app.route("/api/opens")
def get_opens():
    """获取打开记录（供本地应用同步）"""
    limit = request.args.get("limit", 1000, type=int)
    all_records = request.args.get("all", "false").lower() == "true"

    conn = get_db_connection()
    cursor = conn.cursor()

    if USE_POSTGRES:
        if all_records:
            cursor.execute(
                "SELECT * FROM opens ORDER BY id DESC LIMIT %s",
                (limit,)
            )
        else:
            cursor.execute(
                "SELECT * FROM opens WHERE synced=0 ORDER BY id ASC LIMIT %s",
                (limit,)
            )
    else:
        if all_records:
            cursor.execute(
                "SELECT * FROM opens ORDER BY id DESC LIMIT ?",
                (limit,)
            )
        else:
            cursor.execute(
                "SELECT * FROM opens WHERE synced=0 ORDER BY id ASC LIMIT ?",
                (limit,)
            )

    opens = cursor.fetchall()
    result = [dict(row) for row in opens]
    conn.close()

    return jsonify({
        "count": len(result),
        "opens": result
    })

@app.route("/api/clicks")
def get_clicks():
    """获取点击记录（供本地应用同步）"""
    limit = request.args.get("limit", 1000, type=int)
    all_records = request.args.get("all", "false").lower() == "true"

    conn = get_db_connection()
    cursor = conn.cursor()

    if USE_POSTGRES:
        if all_records:
            cursor.execute(
                "SELECT * FROM clicks ORDER BY id DESC LIMIT %s",
                (limit,)
            )
        else:
            cursor.execute(
                "SELECT * FROM clicks WHERE synced=0 ORDER BY id ASC LIMIT %s",
                (limit,)
            )
    else:
        if all_records:
            cursor.execute(
                "SELECT * FROM clicks ORDER BY id DESC LIMIT ?",
                (limit,)
            )
        else:
            cursor.execute(
                "SELECT * FROM clicks WHERE synced=0 ORDER BY id ASC LIMIT ?",
                (limit,)
            )

    clicks = cursor.fetchall()
    result = [dict(row) for row in clicks]
    conn.close()

    return jsonify({
        "count": len(result),
        "clicks": result
    })

@app.route("/api/mark_synced", methods=["POST"])
def mark_synced():
    """标记记录为已同步"""
    data = request.get_json()
    open_ids = data.get("open_ids", [])
    click_ids = data.get("click_ids", [])

    conn = get_db_connection()
    cursor = conn.cursor()

    marked = 0
    placeholder = "%s" if USE_POSTGRES else "?"

    for oid in open_ids:
        cursor.execute(f"UPDATE opens SET synced=1 WHERE id={placeholder}", (oid,))
        marked += cursor.rowcount

    for cid in click_ids:
        cursor.execute(f"UPDATE clicks SET synced=1 WHERE id={placeholder}", (cid,))
        marked += cursor.rowcount

    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "marked": marked})

@app.route("/api/stats")
def get_stats():
    """统计信息"""
    conn = get_db_connection()
    cursor = conn.cursor()

    total_opens = fetchone_value(cursor, "SELECT COUNT(*) FROM opens")
    total_clicks = fetchone_value(cursor, "SELECT COUNT(*) FROM clicks")
    unsynced_opens = fetchone_value(cursor, "SELECT COUNT(*) FROM opens WHERE synced=0")
    unsynced_clicks = fetchone_value(cursor, "SELECT COUNT(*) FROM clicks WHERE synced=0")

    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    placeholder = "%s" if USE_POSTGRES else "?"
    recent_opens = fetchone_value(
        cursor,
        f"SELECT COUNT(*) FROM opens WHERE timestamp > {placeholder}",
        (yesterday,)
    )

    conn.close()

    return jsonify({
        "total_opens": total_opens,
        "total_clicks": total_clicks,
        "unsynced_opens": unsynced_opens,
        "unsynced_clicks": unsynced_clicks,
        "recent_opens_24h": recent_opens
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
