"""API 端到端测试"""

import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _use_temp_db(monkeypatch, tmp_path):
    """每个测试用例使用独立的临时数据库。"""
    test_db = str(tmp_path / "test_api_bazi.db")
    monkeypatch.setattr("backend.db.config.DB_PATH", test_db)
    monkeypatch.setattr("backend.paipan.config.DB_PATH", test_db)
    from backend import db
    db.init_db()
    yield
    if os.path.exists(test_db):
        os.remove(test_db)


@pytest.fixture
def client():
    """FastAPI 测试客户端。"""
    from backend.main import app
    return TestClient(app)


class TestHealthCheck:
    """测试健康检查端点。"""

    def test_health_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestMatchEndpoint:
    """测试匹配端点。"""

    def test_match_validation_missing_fields(self, client):
        """缺少必填字段应返回 422。"""
        resp = client.post("/api/match", json={})
        assert resp.status_code == 422

    def test_match_validation_invalid_year(self, client):
        """年份超出范围应返回 422。"""
        resp = client.post("/api/match", json={
            "birth_year": 1800,
            "birth_month": 5,
            "birth_day": 15,
            "birth_hour": 14,
            "birth_minute": 0,
            "gender": "男",
            "top_n": 5,
        })
        assert resp.status_code == 422

    def test_match_validation_invalid_gender(self, client):
        """性别字段非法应返回 422。"""
        resp = client.post("/api/match", json={
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 15,
            "birth_hour": 14,
            "birth_minute": 0,
            "gender": "X",
            "top_n": 5,
        })
        assert resp.status_code == 422

    def test_match_with_empty_db(self, client):
        """空数据库时匹配应返回成功但无匹配结果。"""
        resp = client.post("/api/match", json={
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 15,
            "birth_hour": 14,
            "birth_minute": 0,
            "gender": "男",
            "top_n": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["matches"]) == 0
        assert data["user_bazi"] is not None

    def test_match_with_seed_data(self, client):
        """有数据时匹配应返回结果。"""
        from backend import db
        # 插入几条测试用户
        for i in range(10):
            db.insert_user({
                "name": f"测试用户{i}",
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

        resp = client.post("/api/match", json={
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 15,
            "birth_hour": 14,
            "birth_minute": 0,
            "gender": "男",
            "top_n": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["matches"]) <= 5
        assert data["total_time_ms"] >= 0

        # 验证匹配结果结构
        if len(data["matches"]) > 0:
            m = data["matches"][0]
            assert "id" in m
            assert "name" in m
            assert "gender" in m
            assert "match_score" in m
            assert "match_grade" in m
            assert "match_stars" in m
            assert "dimensions" in m
            assert "interpretation" in m
