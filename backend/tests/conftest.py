"""pytest 公共 fixture — mock BaziData 工厂函数"""

import pytest
from backend.models import BaziData


@pytest.fixture
def make_bazi_data():
    """BaziData 工厂 fixture，可自定义字段。"""
    def _make(
        year_pillar: str = "庚辰",
        month_pillar: str = "己卯",
        day_pillar: str = "壬申",
        hour_pillar: str = "甲辰",
        day_master: str = "壬",
        wuxing_dist: dict = None,
        nayin: str = "白蜡金",
        nayin_wuxing: str = "金",
        tiangan_list: list = None,
        dizhi_list: list = None,
    ) -> BaziData:
        if wuxing_dist is None:
            wuxing_dist = {"金": 2, "木": 2, "水": 1, "火": 1, "土": 2}
        if tiangan_list is None:
            tiangan_list = ["庚", "己", "壬", "甲"]
        if dizhi_list is None:
            dizhi_list = ["辰", "卯", "申", "辰"]
        return BaziData(
            year_pillar=year_pillar,
            month_pillar=month_pillar,
            day_pillar=day_pillar,
            hour_pillar=hour_pillar,
            day_master=day_master,
            wuxing_dist=wuxing_dist,
            nayin=nayin,
            nayin_wuxing=nayin_wuxing,
            tiangan_list=tiangan_list,
            dizhi_list=dizhi_list,
        )
    return _make


@pytest.fixture
def sample_bazi_a(make_bazi_data):
    """示例八字 A：庚辰年 己卯月 壬申日 甲辰时"""
    return make_bazi_data()


@pytest.fixture
def sample_bazi_b(make_bazi_data):
    """示例八字 B：与 A 不同"""
    return make_bazi_data(
        year_pillar="丙午",
        month_pillar="庚寅",
        day_pillar="丁巳",
        hour_pillar="壬寅",
        day_master="丁",
        wuxing_dist={"金": 1, "木": 1, "水": 1, "火": 3, "土": 2},
        nayin="天河水",
        nayin_wuxing="水",
        tiangan_list=["丙", "庚", "丁", "壬"],
        dizhi_list=["午", "寅", "巳", "寅"],
    )
