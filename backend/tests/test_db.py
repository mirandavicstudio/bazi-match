"""数据库操作测试"""

import os
import tempfile

import pytest

# 测试时使用临时数据库
TEST_DB_PATH: str = ""


@pytest.fixture(autouse=True)
def _use_temp_db(monkeypatch, tmp_path):
    """每个测试用例使用独立的临时数据库。"""
    global TEST_DB_PATH
    TEST_DB_PATH = str(tmp_path / "test_bazi.db")
    monkeypatch.setattr("backend.db.config.DB_PATH", TEST_DB_PATH)
    from backend import db
    db.init_db()
    yield
    # 清理
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


class TestInitDb:
    """测试数据库初始化。"""

    def test_init_creates_table(self):
        from backend import db
        # init_db 不应抛异常
        db.init_db()
        # 表应存在
        conn = db.get_conn()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_init_idempotent(self):
        from backend import db
        # 多次调用不应抛异常
        db.init_db()
        db.init_db()


class TestInsertUser:
    """测试用户插入。"""

    def test_insert_single_user(self):
        from backend import db
        user = {
            "name": "张三",
            "gender": "男",
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 15,
            "birth_hour": 14,
            "birth_minute": 30,
            "year_pillar": "庚午",
            "month_pillar": "辛巳",
            "day_pillar": "壬申",
            "hour_pillar": "丁未",
            "day_master": "壬",
            "wuxing_dist": {"金": 2, "木": 1, "水": 2, "火": 2, "土": 1},
            "nayin": "路旁土",
            "nayin_wuxing": "土",
            "tiangan_list": ["庚", "辛", "壬", "丁"],
            "dizhi_list": ["午", "巳", "申", "未"],
        }
        uid = db.insert_user(user)
        assert uid > 0
        assert db.count_users() == 1

    def test_insert_with_json_dict(self):
        from backend import db
        user = {
            "name": "李四",
            "gender": "女",
            "birth_year": 1985,
            "birth_month": 8,
            "birth_day": 20,
            "birth_hour": 9,
            "birth_minute": 0,
            "year_pillar": "乙丑",
            "month_pillar": "甲申",
            "day_pillar": "丙寅",
            "hour_pillar": "癸巳",
            "day_master": "丙",
            "wuxing_dist": {"金": 1, "木": 2, "水": 1, "火": 2, "土": 2},
            "nayin": "海中金",
            "nayin_wuxing": "金",
            "tiangan_list": ["乙", "甲", "丙", "癸"],
            "dizhi_list": ["丑", "申", "寅", "巳"],
        }
        uid = db.insert_user(user)
        assert uid > 0
        # 读取回来验证 JSON 反序列化
        result = db.get_user_by_id(uid)
        assert isinstance(result["wuxing_dist"], dict)
        assert isinstance(result["tiangan_list"], list)
        assert isinstance(result["dizhi_list"], list)


class TestBatchInsert:
    """测试批量插入。"""

    def test_batch_insert(self):
        from backend import db
        users = []
        for i in range(10):
            users.append({
                "name": f"用户{i}",
                "gender": "男" if i % 2 == 0 else "女",
                "birth_year": 1990 + i,
                "birth_month": (i % 12) + 1,
                "birth_day": (i % 28) + 1,
                "birth_hour": i % 24,
                "birth_minute": 0,
                "year_pillar": "庚午",
                "month_pillar": "辛巳",
                "day_pillar": "壬申",
                "hour_pillar": "丁未",
                "day_master": "壬",
                "wuxing_dist": {"金": 2, "木": 1, "水": 2, "火": 2, "土": 1},
                "nayin": "路旁土",
                "nayin_wuxing": "土",
                "tiangan_list": ["庚", "辛", "壬", "丁"],
                "dizhi_list": ["午", "巳", "申", "未"],
            })
        count = db.batch_insert_users(users)
        assert count == 10
        assert db.count_users() == 10

    def test_batch_insert_empty(self):
        from backend import db
        count = db.batch_insert_users([])
        assert count == 0


class TestQueryUsers:
    """测试用户查询。"""

    def test_get_all_users_empty(self):
        from backend import db
        result = db.get_all_users()
        assert result == []

    def test_get_all_users_with_data(self):
        from backend import db
        user = {
            "name": "王五",
            "gender": "男",
            "birth_year": 1995,
            "birth_month": 3,
            "birth_day": 15,
            "birth_hour": 10,
            "birth_minute": 0,
            "year_pillar": "乙亥",
            "month_pillar": "己卯",
            "day_pillar": "壬申",
            "hour_pillar": "乙巳",
            "day_master": "壬",
            "wuxing_dist": {"金": 1, "木": 2, "水": 2, "火": 1, "土": 2},
            "nayin": "山头火",
            "nayin_wuxing": "火",
            "tiangan_list": ["乙", "己", "壬", "乙"],
            "dizhi_list": ["亥", "卯", "申", "巳"],
        }
        db.insert_user(user)
        result = db.get_all_users()
        assert len(result) == 1
        assert result[0]["name"] == "王五"

    def test_get_user_by_id(self):
        from backend import db
        user = {
            "name": "赵六",
            "gender": "女",
            "birth_year": 1988,
            "birth_month": 11,
            "birth_day": 5,
            "birth_hour": 20,
            "birth_minute": 0,
            "year_pillar": "戊辰",
            "month_pillar": "癸亥",
            "day_pillar": "庚午",
            "hour_pillar": "丙戌",
            "day_master": "庚",
            "wuxing_dist": {"金": 1, "木": 0, "水": 2, "火": 2, "土": 3},
            "nayin": "大林木",
            "nayin_wuxing": "木",
            "tiangan_list": ["戊", "癸", "庚", "丙"],
            "dizhi_list": ["辰", "亥", "午", "戌"],
        }
        uid = db.insert_user(user)
        result = db.get_user_by_id(uid)
        assert result is not None
        assert result["name"] == "赵六"
        assert result["gender"] == "女"

    def test_get_user_by_id_not_found(self):
        from backend import db
        result = db.get_user_by_id(99999)
        assert result is None


class TestCountAndClear:
    """测试计数和清空。"""

    def test_count_empty(self):
        from backend import db
        assert db.count_users() == 0

    def test_count_after_insert(self):
        from backend import db
        user = {
            "name": "测试",
            "gender": "男",
            "birth_year": 2000,
            "birth_month": 1,
            "birth_day": 1,
            "birth_hour": 12,
            "birth_minute": 0,
            "year_pillar": "己卯",
            "month_pillar": "丙子",
            "day_pillar": "甲寅",
            "hour_pillar": "庚午",
            "day_master": "甲",
            "wuxing_dist": {"金": 1, "木": 3, "水": 1, "火": 2, "土": 1},
            "nayin": "城头土",
            "nayin_wuxing": "土",
            "tiangan_list": ["己", "丙", "甲", "庚"],
            "dizhi_list": ["卯", "子", "寅", "午"],
        }
        db.insert_user(user)
        assert db.count_users() == 1

    def test_clear_users(self):
        from backend import db
        user = {
            "name": "清除测试",
            "gender": "女",
            "birth_year": 1999,
            "birth_month": 6,
            "birth_day": 20,
            "birth_hour": 8,
            "birth_minute": 0,
            "year_pillar": "己卯",
            "month_pillar": "庚午",
            "day_pillar": "壬子",
            "hour_pillar": "甲辰",
            "day_master": "壬",
            "wuxing_dist": {"金": 1, "木": 2, "水": 2, "火": 1, "土": 2},
            "nayin": "城头土",
            "nayin_wuxing": "土",
            "tiangan_list": ["己", "庚", "壬", "甲"],
            "dizhi_list": ["卯", "午", "子", "辰"],
        }
        db.insert_user(user)
        assert db.count_users() == 1
        db.clear_users()
        assert db.count_users() == 0
