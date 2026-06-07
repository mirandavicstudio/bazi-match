"""八字合盘匹配系统 — 数据库操作层"""

import json
import os
import sqlite3
from typing import Any, Optional

from backend import config


def get_conn() -> sqlite3.Connection:
    """获取 SQLite 数据库连接。"""
    db_dir = os.path.dirname(config.DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """初始化数据库：创建 users 表及索引。"""
    conn = get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT NOT NULL,
                birth_year INTEGER NOT NULL,
                birth_month INTEGER NOT NULL,
                birth_day INTEGER NOT NULL,
                birth_hour INTEGER NOT NULL,
                birth_minute INTEGER NOT NULL DEFAULT 0,
                year_pillar TEXT NOT NULL,
                month_pillar TEXT NOT NULL,
                day_pillar TEXT NOT NULL,
                hour_pillar TEXT NOT NULL,
                day_master TEXT NOT NULL,
                wuxing_dist TEXT NOT NULL,
                nayin TEXT NOT NULL,
                nayin_wuxing TEXT NOT NULL,
                tiangan_list TEXT NOT NULL,
                dizhi_list TEXT NOT NULL,
                shishen_list TEXT NOT NULL DEFAULT '[]',
                minggua TEXT NOT NULL DEFAULT '',
                shengxiao TEXT NOT NULL DEFAULT '',
                pattern TEXT NOT NULL DEFAULT ''
            )
        """)
        
        # 添加新增列（如果不存在）
        for col_sql in [
            "ALTER TABLE users ADD COLUMN shishen_list TEXT NOT NULL DEFAULT '[]'",
            "ALTER TABLE users ADD COLUMN minggua TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE users ADD COLUMN shengxiao TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE users ADD COLUMN pattern TEXT NOT NULL DEFAULT ''",
        ]:
            try:
                conn.execute(col_sql)
            except sqlite3.OperationalError:
                pass  # 列已存在
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_gender ON users(gender)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_birth_year ON users(birth_year)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_day_master ON users(day_master)")
        conn.commit()
    finally:
        conn.close()


def insert_user(user_dict: dict[str, Any]) -> int:
    """插入单条用户记录，返回自增 ID。"""
    conn = get_conn()
    try:
        # 需要 JSON 序列化的字段
        shishen_list = user_dict.get("shishen_list", [])
        if isinstance(shishen_list, list):
            shishen_list = json.dumps(shishen_list, ensure_ascii=False)
        
        minggua = user_dict.get("minggua", {})
        if isinstance(minggua, dict):
            minggua = json.dumps(minggua, ensure_ascii=False)
        
        pattern = user_dict.get("pattern", "")
        if not isinstance(pattern, str):
            pattern = str(pattern)
        
        cursor = conn.execute(
            """INSERT INTO users (
                name, gender, birth_year, birth_month, birth_day,
                birth_hour, birth_minute, year_pillar, month_pillar,
                day_pillar, hour_pillar, day_master, wuxing_dist,
                nayin, nayin_wuxing, tiangan_list, dizhi_list,
                shishen_list, minggua, shengxiao, pattern
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_dict["name"],
                user_dict["gender"],
                user_dict["birth_year"],
                user_dict["birth_month"],
                user_dict["birth_day"],
                user_dict["birth_hour"],
                user_dict.get("birth_minute", 0),
                user_dict["year_pillar"],
                user_dict["month_pillar"],
                user_dict["day_pillar"],
                user_dict["hour_pillar"],
                user_dict["day_master"],
                user_dict["wuxing_dist"] if isinstance(user_dict["wuxing_dist"], str) else json.dumps(user_dict["wuxing_dist"], ensure_ascii=False),
                user_dict["nayin"],
                user_dict["nayin_wuxing"],
                user_dict["tiangan_list"] if isinstance(user_dict["tiangan_list"], str) else json.dumps(user_dict["tiangan_list"], ensure_ascii=False),
                user_dict["dizhi_list"] if isinstance(user_dict["dizhi_list"], str) else json.dumps(user_dict["dizhi_list"], ensure_ascii=False),
                shishen_list,
                minggua,
                user_dict.get("shengxiao", ""),
                pattern,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def batch_insert_users(users_list: list[dict[str, Any]]) -> int:
    """批量插入用户记录（事务），返回插入条数。"""
    if not users_list:
        return 0
    conn = get_conn()
    try:
        rows = []
        for u in users_list:
            # 需要 JSON 序列化的字段
            shishen_list = u.get("shishen_list", [])
            if isinstance(shishen_list, list):
                shishen_list = json.dumps(shishen_list, ensure_ascii=False)
            
            minggua = u.get("minggua", {})
            if isinstance(minggua, dict):
                minggua = json.dumps(minggua, ensure_ascii=False)
            
            pattern = u.get("pattern", "")
            if not isinstance(pattern, str):
                pattern = str(pattern)
            
            rows.append((
                u["name"], u["gender"], u["birth_year"], u["birth_month"],
                u["birth_day"], u["birth_hour"], u.get("birth_minute", 0),
                u["year_pillar"], u["month_pillar"], u["day_pillar"],
                u["hour_pillar"], u["day_master"],
                u["wuxing_dist"] if isinstance(u["wuxing_dist"], str) else json.dumps(u["wuxing_dist"], ensure_ascii=False),
                u["nayin"], u["nayin_wuxing"],
                u["tiangan_list"] if isinstance(u["tiangan_list"], str) else json.dumps(u["tiangan_list"], ensure_ascii=False),
                u["dizhi_list"] if isinstance(u["dizhi_list"], str) else json.dumps(u["dizhi_list"], ensure_ascii=False),
                shishen_list,
                minggua,
                u.get("shengxiao", ""),
                pattern,
            ))
        conn.executemany(
            """INSERT INTO users (
                name, gender, birth_year, birth_month, birth_day,
                birth_hour, birth_minute, year_pillar, month_pillar,
                day_pillar, hour_pillar, day_master, wuxing_dist,
                nayin, nayin_wuxing, tiangan_list, dizhi_list,
                shishen_list, minggua, shengxiao, pattern
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """将 sqlite3.Row 转为 dict，并反序列化 JSON 字段。"""
    d = dict(row)
    for key in ("wuxing_dist", "tiangan_list", "dizhi_list", "shishen_list", "minggua"):
        if key in d and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def get_all_users() -> list[dict[str, Any]]:
    """获取全部用户，返回 list[dict]。"""
    conn = get_conn()
    try:
        cursor = conn.execute("SELECT * FROM users")
        return [_row_to_dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_users_by_gender(gender: str) -> list[dict[str, Any]]:
    """根据性别获取用户列表。
    
    Args:
        gender: 性别 ("男" / "女")
    
    Returns:
        符合条件的用户列表
    """
    conn = get_conn()
    try:
        cursor = conn.execute("SELECT * FROM users WHERE gender = ?", (gender,))
        return [_row_to_dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_users_exclude_gender(gender: str) -> list[dict[str, Any]]:
    """获取排除指定性别外的所有用户（用于异性匹配）。
    
    Args:
        gender: 要排除的性别 ("男" / "女")
    
    Returns:
        异性用户列表
    """
    conn = get_conn()
    try:
        cursor = conn.execute("SELECT * FROM users WHERE gender != ?", (gender,))
        return [_row_to_dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_user_by_id(uid: int) -> Optional[dict[str, Any]]:
    """根据 ID 获取单条用户记录。"""
    conn = get_conn()
    try:
        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (uid,))
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_dict(row)
    finally:
        conn.close()


def count_users() -> int:
    """统计用户总数。"""
    conn = get_conn()
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def clear_users() -> None:
    """清空用户表。"""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM users")
        conn.commit()
    finally:
        conn.close()
